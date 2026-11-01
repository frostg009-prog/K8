/*
 * CM5-DETECT rev0.3 - board supervisor firmware for WCH CH32V003F4P6 (TSSOP-20)
 * Build with ch32v003fun (https://github.com/cnlohr/ch32v003fun):  make  (see Makefile)
 * Flash: WCH-LinkE on pads TP_SWIO / TP_3V3 / TP_GND  (minichlink -w supervisor.bin flash -b)
 *
 * Functions
 *  1. Hardware watchdog for the CM5: CM5 toggles HEARTBEAT (GPIO22) at least every 2 s
 *     (systemd service cm5-heartbeat). If no edge for WDT_TIMEOUT_S after boot grace:
 *       - ERR LED on, PMIC_EN pulled low 1.5 s (cold reset of CM5), released -> CM5 boots again.
 *     Watchdog can be disabled by closing solder jumper JP_WDT (bench work).
 *  2. Power-fail handling: battery voltage (VBAT_SENSE, divider 100k/10k) < VBAT_FAIL_MV
 *     for 20 ms, or the 5 V rail < 4.85 V:
 *       - +5V_AUX switched off (Hailo, USB, fan) to save hold-up energy (AUX_OFF high)
 *       - PFAIL_N (GPIO23) driven low -> CM5 gpio-shutdown overlay -> checkpoint + clean poweroff
 *       - supercap boost keeps +5V_CM5 at 5.03 V for ~5 s
 *       - when CM5 3.3 V goes away (CM5 halted) the boost is disabled (HOLD_EN low)
 *     If the battery comes back while CM5 is halted -> short PWR_BUT press to boot it again.
 *  3. Status: ERR LED blink codes: 1 = watchdog reset happened, 2 = power fail, 3 = over-temperature,
 *     solid = CM5 not booting (3 resets in a row).
 *  4. UART 115200 8N1 to CM5 UART3 (GPIO8/9): one status line per second
 *     "SUP v=<vbat mV> v5=<mV> sc=<mV> wd=<s> rst=<n> pf=<n> t=<alert>"  and commands:
 *     "W0"/"W1" disable/enable watchdog, "T<n>" timeout seconds, "R" request reset.
 *  Back-feeding protection: all lines to the CM5 are driven only while CM5 3.3 V is present
 *  (CM5_ON_SENSE), otherwise they are inputs (hi-Z) so the powered-down CM5 is not back-fed.
 */
#include "ch32v003fun.h"
#include <stdio.h>

/* ---- pin map (see design.py U_MCU) */
#define PIN_LED_ERR   PD4   /* low = LED on */
#define PIN_UTX       PD5
#define PIN_URX       PD6
#define PIN_VBAT      PA1   /* ADC ch1 */
#define PIN_V5        PA2   /* ADC ch0 */
#define PIN_TALERT    PD0   /* temp sensor ALERT, active low */
#define PIN_HB        PC0   /* heartbeat input from CM5 */
#define PIN_PFAIL     PC1   /* power-fail output to CM5, active low */
#define PIN_PMIC_OFF  PC2   /* high = pull CM5 PMIC_EN low */
#define PIN_PWRBTN    PC3   /* high = press CM5 PWR_BUT */
#define PIN_VSCAP     PC4   /* ADC ch2 */
#define PIN_HOLD_EN   PC5   /* boost enable */
#define PIN_SCAP_CHG  PC6   /* supercap charger enable */
#define PIN_AUX_OFF   PC7   /* high = 5V_AUX buck off */
#define PIN_CM5_ON    PD2   /* CM5 3.3 V present */
#define PIN_WDT_DIS   PD3   /* low = watchdog disabled (JP_WDT closed) */

#define VBAT_FAIL_MV   9000   /* below: battery lost/disconnected (works for 3S..6S) */
#define VBAT_OK_MV     10500
#define V5_FAIL_MV     4850
#define BOOT_GRACE_S   120    /* first heartbeat must come within 2 min after power-on */
static uint16_t wdt_timeout_s = 20;

static volatile uint32_t ms;
void SysTick_Handler(void) __attribute__((interrupt));
void SysTick_Handler(void) { SysTick->CMP += (FUNCONF_SYSTEM_CORE_CLOCK / 1000); SysTick->SR = 0; ms++; }

static uint16_t adc_mv(uint8_t ch, uint32_t num, uint32_t den) {
    ADC1->RSQR3 = ch; ADC1->CTLR2 |= ADC_SWSTART;
    while (!(ADC1->STATR & ADC_EOC));
    uint32_t raw = ADC1->RDATAR & 0x3ff;              /* 10-bit, Vref = VDD = 3.3 V */
    return (uint16_t)(raw * 3300UL / 1023UL * num / den);
}
static void adc_init(void) {
    RCC->APB2PCENR |= RCC_APB2Periph_ADC1;
    RCC->CFGR0 = (RCC->CFGR0 & ~(0x1f << 11));         /* ADC clock = HCLK/2 */
    ADC1->RSQR1 = 0; ADC1->SAMPTR2 = 0x3fffffff;       /* longest sample time on all ch */
    ADC1->CTLR2 |= ADC_ADON | ADC_EXTSEL;
    ADC1->CTLR2 |= ADC_RSTCAL; while (ADC1->CTLR2 & ADC_RSTCAL);
    ADC1->CTLR2 |= ADC_CAL; while (ADC1->CTLR2 & ADC_CAL);
}
static void uart_init(void) {
    RCC->APB2PCENR |= RCC_APB2Periph_USART1;
    USART1->BRR = FUNCONF_SYSTEM_CORE_CLOCK / 115200;
    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx | USART_Mode_Rx | USART_CTLR1_UE;
}
static void uart_puts(const char *s) { while (*s) { while (!(USART1->STATR & USART_FLAG_TXE)); USART1->DATAR = *s++; } }

static int cm5_on(void) { return funDigitalRead(PIN_CM5_ON); }
static void cm5_lines(int on) {      /* drive CM5-facing outputs only while CM5 is powered */
    funPinMode(PIN_PFAIL, on ? GPIO_CFGLR_OUT_10Mhz_PP : GPIO_CFGLR_IN_FLOAT);
    funPinMode(PIN_UTX, on ? GPIO_CFGLR_OUT_10Mhz_AF_PP : GPIO_CFGLR_IN_FLOAT);
}

int main(void) {
    SystemInit();
    funGpioInitAll();
    SysTick->CMP = FUNCONF_SYSTEM_CORE_CLOCK / 1000; SysTick->CNT = 0; SysTick->CTLR = 0xf; NVIC_EnableIRQ(SysTicK_IRQn);
    /* independent watchdog for the MCU itself (~4 s) */
    IWDG->CTLR = 0x5555; IWDG->PSCR = 6; IWDG->RLDR = 0xfff; IWDG->CTLR = 0xcccc;

    funPinMode(PIN_LED_ERR, GPIO_CFGLR_OUT_10Mhz_PP); funDigitalWrite(PIN_LED_ERR, 1);
    funPinMode(PIN_PMIC_OFF, GPIO_CFGLR_OUT_10Mhz_PP); funDigitalWrite(PIN_PMIC_OFF, 0);
    funPinMode(PIN_PWRBTN, GPIO_CFGLR_OUT_10Mhz_PP); funDigitalWrite(PIN_PWRBTN, 0);
    funPinMode(PIN_HOLD_EN, GPIO_CFGLR_OUT_10Mhz_PP); funDigitalWrite(PIN_HOLD_EN, 1);
    funPinMode(PIN_SCAP_CHG, GPIO_CFGLR_OUT_10Mhz_PP); funDigitalWrite(PIN_SCAP_CHG, 1);
    funPinMode(PIN_AUX_OFF, GPIO_CFGLR_OUT_10Mhz_PP); funDigitalWrite(PIN_AUX_OFF, 0);
    funPinMode(PIN_HB, GPIO_CFGLR_IN_PUPD); funPinMode(PIN_CM5_ON, GPIO_CFGLR_IN_FLOAT);
    funPinMode(PIN_TALERT, GPIO_CFGLR_IN_PUPD); funPinMode(PIN_WDT_DIS, GPIO_CFGLR_IN_PUPD);
    funDigitalWrite(PIN_WDT_DIS, 1); funDigitalWrite(PIN_HB, 1); funDigitalWrite(PIN_TALERT, 1);
    funPinMode(PIN_VBAT, GPIO_CFGLR_IN_ANALOG); funPinMode(PIN_V5, GPIO_CFGLR_IN_ANALOG); funPinMode(PIN_VSCAP, GPIO_CFGLR_IN_ANALOG);
    funPinMode(PIN_URX, GPIO_CFGLR_IN_PUPD);
    adc_init(); uart_init();

    enum { RUN, PFAIL, HALTED } st = RUN;
    uint32_t last_hb = ms, last_edge_level = funDigitalRead(PIN_HB), boot_t = ms, low_since = 0, last_tx = 0;
    uint16_t resets = 0, pfails = 0, consecutive = 0; int seen_hb = 0, err = 0;
    char line[96]; uint8_t cmd[8]; int ci = 0;

    for (;;) {
        IWDG->CTLR = 0xaaaa;                                   /* feed MCU watchdog */
        int on = cm5_on(); cm5_lines(on);
        uint16_t vbat = adc_mv(1, 110, 10), v5 = adc_mv(0, 2, 1), vsc = adc_mv(2, 2, 1);
        /* heartbeat edge detection */
        int hb = funDigitalRead(PIN_HB);
        if (hb != last_edge_level) { last_edge_level = hb; last_hb = ms; seen_hb = 1; consecutive = 0; }

        switch (st) {
        case RUN:
            if (vbat < VBAT_FAIL_MV || v5 < V5_FAIL_MV) { if (!low_since) low_since = ms; }
            else low_since = 0;
            if (low_since && ms - low_since > 20) {           /* power fail confirmed */
                funDigitalWrite(PIN_AUX_OFF, 1);              /* shed auxiliary loads */
                funDigitalWrite(PIN_SCAP_CHG, 0);
                if (on) funDigitalWrite(PIN_PFAIL, 0);        /* ask CM5 to checkpoint + power off */
                pfails++; err = 2; st = PFAIL; break;
            }
            if (on) funDigitalWrite(PIN_PFAIL, 1);
            if (funDigitalRead(PIN_WDT_DIS) && on) {
                uint32_t lim = seen_hb ? wdt_timeout_s * 1000UL : BOOT_GRACE_S * 1000UL;
                if (ms - (seen_hb ? last_hb : boot_t) > lim) {  /* CM5 hung -> cold reset */
                    funDigitalWrite(PIN_LED_ERR, 0);
                    funDigitalWrite(PIN_PMIC_OFF, 1); uint32_t t = ms; while (ms - t < 1500) IWDG->CTLR = 0xaaaa;
                    funDigitalWrite(PIN_PMIC_OFF, 0);
                    resets++; consecutive++; err = consecutive >= 3 ? 9 : 1;
                    boot_t = last_hb = ms; seen_hb = 0;
                }
            }
            if (!on && !low_since && ms - boot_t > 5000) {      /* CM5 is off but power is fine -> wake it */
                funDigitalWrite(PIN_PWRBTN, 1); uint32_t t = ms; while (ms - t < 200) IWDG->CTLR = 0xaaaa;
                funDigitalWrite(PIN_PWRBTN, 0); boot_t = ms; seen_hb = 0;
            }
            break;
        case PFAIL:
            if (!on) { funDigitalWrite(PIN_HOLD_EN, 0); st = HALTED; }   /* CM5 halted: stop drain */
            else if (vbat > VBAT_OK_MV && v5 > 5000) {                   /* battery back before shutdown */
                funDigitalWrite(PIN_PFAIL, 1); funDigitalWrite(PIN_AUX_OFF, 0); funDigitalWrite(PIN_SCAP_CHG, 1);
                low_since = 0; st = RUN;   /* software side decides whether to continue */
            }
            break;
        case HALTED:
            if (vbat > VBAT_OK_MV) {                                     /* power restored -> boot CM5 */
                funDigitalWrite(PIN_HOLD_EN, 1); funDigitalWrite(PIN_AUX_OFF, 0); funDigitalWrite(PIN_SCAP_CHG, 1);
                funDigitalWrite(PIN_PWRBTN, 1); uint32_t t = ms; while (ms - t < 200) IWDG->CTLR = 0xaaaa;
                funDigitalWrite(PIN_PWRBTN, 0); boot_t = ms; seen_hb = 0; low_since = 0; st = RUN;
            }
            break;
        }
        if (!funDigitalRead(PIN_TALERT)) err = 3;
        /* ERR LED pattern: n blinks every 3 s, 9 = solid */
        uint32_t ph = ms % 3000;
        int led = err == 9 ? 1 : (err && ph < (uint32_t)err * 400 && (ph % 400) < 200);
        funDigitalWrite(PIN_LED_ERR, !led);
        /* status line + commands */
        if (on && ms - last_tx > 1000) {
            last_tx = ms;
            snprintf(line, sizeof line, "SUP v=%u v5=%u sc=%u wd=%u rst=%u pf=%u t=%d st=%d\r\n", vbat, v5, vsc,
                     funDigitalRead(PIN_WDT_DIS) ? wdt_timeout_s : 0, resets, pfails, !funDigitalRead(PIN_TALERT), st);
            uart_puts(line);
        }
        while (USART1->STATR & USART_FLAG_RXNE) {
            uint8_t c = USART1->DATAR;
            if (c == '\n' || c == '\r') {
                if (ci >= 2 && cmd[0] == 'T') { int v = 0; for (int k = 1; k < ci; k++) v = v * 10 + cmd[k] - '0'; if (v >= 5 && v <= 600) wdt_timeout_s = v; }
                if (ci >= 1 && cmd[0] == 'C') err = 0;
                if (ci >= 1 && cmd[0] == 'R') { boot_t = ms - BOOT_GRACE_S * 1000UL - 1; seen_hb = 0; }
                ci = 0;
            } else if (ci < (int)sizeof cmd) cmd[ci++] = c;
        }
    }
}
