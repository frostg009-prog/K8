# -*- coding: utf-8 -*-
"""
CM5-DETECT rev0.3 (Path A) - single source of truth for the circuit.

Every component is described once:  REF -> (footprint, value, LCSC part, {pad: net}, note)
The PCB generator (build_board.py) places these footprints and assigns nets,
the BOM/CPL generator (make_fab.py) produces factory files from the same table.

Reference circuits used:
  * Raspberry Pi CM5 IO Board rev2 KiCad design (cameras, SD, USB, CM5 pinout)
  * Raspberry Pi "Connector for PCIe" spec (16-pin FFC pinout, Pi 5 compatible)
  * Datasheets: RT6365 (Richtek), SCT2650 (SCT, pin-compatible alt), SGM6611C (SG Micro),
    SY6280 / SY8089A1 (Silergy), CH213K / CH32V003 (WCH), ME6211 (Microne), NST175H (Novosense)
"""

# ---------------------------------------------------------------- CM5 pin map
GND_CM5 = [1, 2, 7, 8, 13, 14, 22, 23, 32, 33, 42, 43, 52, 53, 59, 60, 65, 66, 71, 74, 98, 107, 108,
           113, 114, 119, 120, 125, 126, 131, 132, 137, 138, 144, 150, 155, 156, 161, 162, 167, 168,
           173, 174, 179, 180, 185, 186, 191, 192, 197, 198]
GPIO_PIN = {2: 58, 3: 56, 4: 54, 5: 34, 6: 30, 7: 37, 8: 39, 9: 40, 10: 44, 11: 38, 12: 31, 13: 28,
            14: 55, 15: 51, 16: 29, 17: 50, 18: 49, 19: 26, 20: 27, 21: 25, 22: 46, 23: 47, 24: 45,
            25: 41, 26: 24, 27: 48}

cm5 = {str(p): 'GND' for p in GND_CM5}
for p in (77, 79, 81, 83, 85, 87):
    cm5[str(p)] = '+5V_CM5'
cm5.update({'84': '+3V3_CM5', '86': '+3V3_CM5', '78': 'GPIO_VREF', '76': 'VBAT_RTC',
            '94': 'USB1_CC1', '96': 'USB1_CC2', '103': 'USB1_DN', '105': 'USB1_DP',
            '134': 'USB2_DP', '136': 'USB2_DN', '163': 'THU_DP', '165': 'THU_DN', '111': 'VBUS_EN',
            '102': 'PCIE_CLKREQ_N', '104': 'PCIE_DET_WAKE', '106': 'PCIE_PWR_EN', '109': 'PCIE_RST_N',
            '110': 'PCIE_CLK_P', '112': 'PCIE_CLK_N', '116': 'PCIE_RX_P', '118': 'PCIE_RX_N',
            '122': 'PCIE_TX_P', '124': 'PCIE_TX_N',
            # CAM1 = MIPI0 (DPHY0), I2C on dedicated SCL0/SDA0
            '115': 'CAM1_D0_N', '117': 'CAM1_D0_P', '121': 'CAM1_D1_N', '123': 'CAM1_D1_P',
            '127': 'CAM1_C_N', '129': 'CAM1_C_P', '133': 'CAM1_D2_N', '135': 'CAM1_D2_P',
            '139': 'CAM1_D3_N', '141': 'CAM1_D3_P', '80': 'CAM1_SCL', '82': 'CAM1_SDA',
            '97': 'CAM1_GPIO0', '100': 'CAM1_GPIO1',
            # CAM2 = MIPI1 (DPHY1), I2C on ID_SC/ID_SD (GPIO1/GPIO0) like CM5IO with J6 fitted
            '175': 'CAM2_D0_N', '177': 'CAM2_D0_P', '181': 'CAM2_D1_N', '183': 'CAM2_D1_P',
            '187': 'CAM2_C_N', '189': 'CAM2_C_P', '193': 'CAM2_D2_N', '195': 'CAM2_D2_P',
            '194': 'CAM2_D3_N', '196': 'CAM2_D3_P', '35': 'CAM2_SCL', '36': 'CAM2_SDA',
            '19': 'FAN_PWM', '16': 'FAN_TACH', '92': 'PWR_BUT', '93': 'NRPIBOOT', '99': 'PMIC_EN',
            '57': 'SD_CLK', '62': 'SD_CMD', '63': 'SD_D0', '67': 'SD_D1', '69': 'SD_D2', '61': 'SD_D3',
            '75': 'SD_PWR_ON'})
GPIO_NET = {2: 'I2C1_SDA', 3: 'I2C1_SCL', 4: 'UART2_TX', 5: 'UART2_RX', 6: 'TH_SYNC', 7: 'IO_GPIO7',
            8: 'MCU_RX', 9: 'MCU_TX', 10: 'IO_GPIO10', 11: 'IO_GPIO11', 12: 'SERVO1_G', 13: 'SERVO2_G',
            14: 'UART0_TX', 15: 'UART0_RX', 16: 'IO_GPIO16', 17: 'IO_GPIO17', 18: 'SERVO3_G',
            19: 'SERVO4_G', 20: 'LED_RUN_N', 22: 'HEARTBEAT', 23: 'PFAIL_N', 24: 'IO_GPIO24'}
for g, n in GPIO_NET.items():
    cm5[str(GPIO_PIN[g])] = n

C = {}   # ref -> dict(fp=, val=, lcsc=, pins={}, note=, dnp=False)


def add(ref, fp, val, lcsc, pins, note='', dnp=False):
    assert ref not in C, ref
    C[ref] = dict(fp=fp, val=val, lcsc=lcsc, pins={str(k): v for k, v in pins.items()}, note=note, dnp=dnp)


R0402 = 'Resistor_SMD:R_0402_1005Metric'
C0402 = 'Capacitor_SMD:C_0402_1005Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
C1206 = 'Capacitor_SMD:C_1206_3216Metric'
C1210 = 'Capacitor_SMD:C_1210_3225Metric'
LED = 'LED_SMD:LED_0603_1608Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'
SOT235 = 'Package_TO_SOT_SMD:SOT-23-5'
SOT236 = 'Package_TO_SOT_SMD:SOT-23-6'
GH = lambda n: 'Connector_JST:JST_GH_SM%02dB-GHS-TB_1x%02d-1MP_P1.25mm_Horizontal' % (n, n)
GH_LCSC = {2: 'C189893', 3: 'C514175', 4: 'C189895', 6: 'C133065', 8: 'C42376901'}

_n = {'R': 0, 'C': 0}


def R(val, a, b, lcsc='', note='', fp=R0402, dnp=False, ref=None):
    if ref is None:
        _n['R'] += 1
        ref = 'R%d' % _n['R']
    add(ref, fp, val, lcsc or RLCSC.get(val, ''), {1: a, 2: b}, note, dnp)
    return ref


def Cap(val, a, b='GND', fp=C0402, lcsc='', note='', ref=None):
    if ref is None:
        _n['C'] += 1
        ref = 'C%d' % _n['C']
    add(ref, fp, val, lcsc or CLCSC.get((val, fp), ''), {1: a, 2: b}, note)
    return ref


# common passives (LCSC basic/extended parts, verified in JLC catalogue 2026-11)
RLCSC = {'0R': 'C17168', '220R': 'C25091', '1k': 'C11702', '2.2k': 'C25879', '4.7k': 'C25900', '5.1k': 'C25905',
         '10k': 'C25744', '15k': 'C25756', '18k': 'C25762', '22k': 'C25768', '47k': 'C25792', '56k': 'C25796',
         '100k': 'C25741', '127k': 'C25751', '6.8k': 'C93940', '3.4k': 'C4940', '10.5k': 'C25850', '45.3k': 'C2933099',
         '53.6k': 'C5153961', '249k': 'C2998084', '340k': 'C2933090', '107k': 'C25743', '30k': 'C25776', '1M': 'C26083'}
CLCSC = {('100nF', C0402): 'C1525', ('1uF', C0402): 'C52923', ('1uF', C0603): 'C15849', ('10uF', C0805): 'C15850',
         ('22uF', C0805): 'C45783', ('2.2uF 100V', C1206): 'C170101', ('47uF 16V', C1210): 'C77101',
         ('100pF', C0402): 'C1546', ('8.2nF', C0402): 'C45186', ('4.7nF', C0402): 'C1538', ('2.2uF', C0402): 'C12530',
         ('4.7uF', C0603): 'C19666'}

# ===================================================================== CM5
add('M1', 'CM5IO:Raspberry-Pi-5-Compute-Module', 'Raspberry Pi CM5 (CM5108032 / CM5116032 / Lite)',
    'Amphenol 10164227-1001A1RLF x2 (C6782225)', cm5,
    'Two 100-pin board-to-board connectors are soldered at the factory; CM5 is plugged in and screwed (4xM2.5)')
R('0R', 'GPIO_VREF', '+3V3_CM5', note='GPIO bank voltage = 3.3 V', ref='R_VREF')
for i in range(4):
    Cap('22uF', '+5V_CM5', fp=C0805, lcsc='C45783', note='CM5 5V input bulk')
Cap('100nF', '+5V_CM5'); Cap('100nF', '+5V_CM5')
Cap('10uF', '+3V3_CM5', fp=C0805)

# ===================================================================== battery input & protection
add('J_BAT', 'Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal', 'XT60PW-M (battery 3S-6S)', 'C98732',
    {1: 'GND', 2: 'VBAT_RAW'}, 'pad 2 = +, pad 1 = -')
add('J_BAT2', 'Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal', 'XT30PW-M (alternative input)', 'C53373776',
    {1: 'GND', 2: 'VBAT_RAW'}, 'fit XT60 OR XT30, not both', dnp=True)
add('F1', 'custom:Fuse_2410', '10A fast 2410 125V', 'C2838934', {1: 'VBAT_RAW', 2: 'VBAT_F'})
add('D_TVS', 'Diode_SMD:D_SMC', 'SMCJ33A TVS 1.5kW', 'C152083', {1: 'VBAT_F', 2: 'GND'}, 'K=pad1')
add('Q_RP', 'lcsc:TO-252-2_L6.5-W6.1-P4.58-LS10.0-TL', 'NCE60P12K P-MOS 60V reverse-polarity', 'C326372',
    {1: 'QRP_G', 3: 'VIN_PROT', 4: 'VBAT_F'}, 'G=1 S=3 D=tab')
add('D_RPZ', 'Diode_SMD:D_SOD-123', 'BZT52C12 Vgs clamp', 'C43491', {1: 'VIN_PROT', 2: 'QRP_G'})
R('47k', 'QRP_G', 'GND', note='P-MOS gate pull-down')
add('C_BULK', 'Capacitor_SMD:CP_Elec_8x10', '100uF 50V low-ESR', 'C48935390', {1: 'VIN_PROT', 2: 'GND'},
    'input damping / hold-up for motor transients')
Cap('2.2uF 100V', 'VIN_PROT', fp=C1206)
R('100k', 'VIN_PROT', 'VBAT_SENSE', note='VBAT divider 100k/10k -> MCU ADC (max 36 V)')
R('10k', 'VBAT_SENSE', 'GND'); Cap('100nF', 'VBAT_SENSE')

# ===================================================================== bucks (RT6365GSP, alt SCT2650STER pin-compatible)
BUCK_FP = 'lcsc:SOP-8_L5.0-W3.9-P1.27-LS6.0-BL-EP'


def buck(n, vin, vout, en_ctrl=None):
    u = 'U_B%d' % n
    add(u, BUCK_FP, 'RT6365GSP 60V 5A buck (alt SCT2650STER)', 'C3024482',
        {1: 'B%d_BOOT' % n, 2: vin, 3: 'B%d_EN' % n, 4: 'B%d_RT' % n, 5: 'B%d_FB' % n, 6: 'B%d_COMP' % n,
         7: 'GND', 8: 'B%d_SW' % n, 9: 'GND'}, '5.09 V / 5 A, 400 kHz, UVLO 7.9 V')
    for _ in range(3):
        Cap('2.2uF 100V', vin, fp=C1206)
    Cap('100nF', vin)
    R('100k', vin, 'B%d_EN' % n, note='UVLO top'); R('18k', 'B%d_EN' % n, 'GND', note='UVLO bottom: 7.9 V on')
    R('249k', 'B%d_RT' % n, 'GND', note='fsw 400 kHz')
    R('10.5k', 'B%d_COMP' % n, 'B%d_CC' % n); Cap('8.2nF', 'B%d_CC' % n); Cap('100pF', 'B%d_COMP' % n)
    Cap('100nF', 'B%d_BOOT' % n, 'B%d_SW' % n)
    add('L_B%d' % n, 'lcsc:IND-SMD_L7.0-W6.6', '6.8uH 6A FXL0630-6R8-M', 'C167221', {1: 'B%d_SW' % n, 2: vout})
    add('D_B%d' % n, 'Diode_SMD:D_SMC', 'SS510C 5A 100V Schottky', 'C19229', {1: 'B%d_SW' % n, 2: 'GND'}, 'K=pad1')
    R('53.6k', vout, 'B%d_FB' % n, note='Vout=0.8*(1+53.6/10)=5.09 V'); R('10k', 'B%d_FB' % n, 'GND')
    for _ in range(3):
        Cap('47uF 16V', vout, fp=C1210)
    if en_ctrl:
        add('Q_%s' % en_ctrl, SOT23, '2N7002', 'C8545', {1: en_ctrl, 2: 'GND', 3: 'B%d_EN' % n}, 'MCU can switch rail off')
        R('100k', en_ctrl, 'GND')


# buck1: battery -> +5V_CM5 (CM5, cameras, MCU). Input through Schottky so that hold-up energy
# on +5V_CM5 can not flow back into the battery/aux side.
add('D_B1IN', 'Diode_SMD:D_SMC', 'SS510C (blocks hold-up back-feed)', 'C19229', {1: 'VIN_B1', 2: 'VIN_PROT'}, 'K=pad1')
buck(1, 'VIN_B1', '+5V_CM5')
# buck2: battery -> +5V_AUX (Hailo, USB host ports, fan, thermal camera, GPS). MCU sheds it on power fail.
buck(2, 'VIN_PROT', '+5V_AUX', en_ctrl='AUX_OFF')

# ===================================================================== hold-up (supercap + boost)
add('U_CHG', SOT235, 'SY6280AAC supercap charger 1A', 'C55136',
    {1: 'SCAP_CHG', 2: 'GND', 3: 'CHG_ISET', 4: 'SCAP_CHG_EN', 5: '+5V_CM5'})
R('6.8k', 'CHG_ISET', 'GND', note='Ilim = 6800/Rset = 1.0 A')
R('100k', 'SCAP_CHG_EN', '+3V3_AON')
add('D_CHG', 'Diode_SMD:D_SMA', 'SS34 (cap max 4.8 V = 2.4 V/cell)', 'C8678', {1: 'VSCAP', 2: 'SCAP_CHG'}, 'K=pad1')
add('SC1', 'custom:SuperCap_D10_L20_Horizontal', '10F 2.7V supercap (Jianghai SCCDQR2R7106 / Kamcap)', 'SCCDQR2R7106',
    {1: 'VSCAP', 2: 'SCAP_MID'}, 'lay flat, glue')
add('SC2', 'custom:SuperCap_D10_L20_Horizontal', '10F 2.7V supercap', 'SCCDQR2R7106', {1: 'SCAP_MID', 2: 'GND'})
R('10k', 'VSCAP', 'SCAP_MID', note='balancing', fp='Resistor_SMD:R_0603_1608Metric', lcsc='C25804')
R('10k', 'SCAP_MID', 'GND', note='balancing', fp='Resistor_SMD:R_0603_1608Metric', lcsc='C25804')
add('U_HB', 'lcsc:VQFN-11_L2.5-W2.0-P0.50-TL_TI_RNR', 'SGM6611C boost 7A (hold-up 5.03 V)', 'C699669',
    {1: '', 2: 'HB_VCC', 3: 'HB_FB', 4: 'HB_COMP', 5: 'GND', 6: '+5V_CM5', 7: 'HOLD_EN', 8: 'HB_ILIM', 9: 'VSCAP',
     10: 'HB_BOOT', 11: 'HB_SW'})
add('L_HB', 'lcsc:IND-SMD_L7.1-W6.6_SLO0650H', '2.2uH 9.5A SLO0650H2R2MTT', 'C216163', {1: 'VSCAP', 2: 'HB_SW'})
Cap('22uF', 'VSCAP', fp=C0805); Cap('22uF', 'VSCAP', fp=C0805)
Cap('22uF', '+5V_CM5', fp=C0805); Cap('22uF', '+5V_CM5', fp=C0805)
Cap('2.2uF', 'HB_VCC'); Cap('100nF', 'HB_BOOT', 'HB_SW')
R('340k', '+5V_CM5', 'HB_FB', note='Vout=1.205*(1+340/107)=5.03 V'); R('107k', 'HB_FB', 'GND')
R('30k', 'HB_COMP', 'HB_CC'); Cap('4.7nF', 'HB_CC')
R('127k', 'HB_ILIM', 'GND', note='9.5 A peak')
R('100k', 'HOLD_EN', 'VSCAP', note='hold-up enabled by default')

# ===================================================================== always-on 3.3 V (MCU, LED, temp)
add('U_AON', SOT235, 'ME6211C33M5G LDO 3.3V', 'C82942', {1: '+5V_CM5', 2: 'GND', 3: '+5V_CM5', 4: '', 5: '+3V3_AON'})
Cap('1uF', '+5V_CM5', fp=C0603); Cap('1uF', '+3V3_AON', fp=C0603)

# ===================================================================== camera 3.3 V (CM5 3V3 is only 600 mA total)
add('U_C33', SOT235, 'SY8089A1AAC 2A buck 3.3V cameras', 'C479074',
    {1: '+3V3_CM5', 2: 'GND', 3: 'C33_LX', 4: '+5V_CM5', 5: 'C33_FB'}, 'on only while CM5 is on (EN=CM5 3V3)')
add('L_C33', 'Inductor_SMD:L_Changjiang_FNR4012S', '2.2uH 2.3A FNR4012S2R2MT', 'C167776', {1: 'C33_LX', 2: '+3V3_CAM'})
Cap('10uF', '+5V_CM5', fp=C0805); Cap('22uF', '+3V3_CAM', fp=C0805)
R('45.3k', '+3V3_CAM', 'C33_FB', note='0.6*(1+45.3/10)=3.32 V'); R('10k', 'C33_FB', 'GND')

# ===================================================================== USB-C #1 : PC / firmware / USB gadget
USBC = 'lcsc:USB-C-SMD_TYPE-C-16PIN-2MD-073'
add('J_USB1', USBC, 'USB-C #1 FW/PC (rpiboot + USB gadget)', 'C2765186',
    {'A1B12': 'GND', 'B1A12': 'GND', 'A4B9': 'VBUS1', 'B4A9': 'VBUS1', 'A5': 'USB1_CC1', 'B5': 'USB1_CC2',
     'A6': 'USB1_DP', 'B6': 'USB1_DP', 'A7': 'USB1_DN', 'B7': 'USB1_DN', '13': 'GND', '14': 'GND'})
add('U_ESD1', SOT236, 'USBLC6-2SC6 ESD', 'C2827654', {1: 'USB1_DP', 6: 'USB1_DP', 3: 'USB1_DN', 4: 'USB1_DN', 2: 'GND', 5: 'VBUS1'})
add('U_ID1', SOT23, 'CH213K ideal diode VBUS1->5V', 'C5456874', {1: 'GND', 2: '+5V_CM5', 3: 'VBUS1'})
add('U_ID2', SOT23, 'CH213K ideal diode VBUS1->5V', 'C5456874', {1: 'GND', 2: '+5V_CM5', 3: 'VBUS1'})
Cap('10uF', 'VBUS1', fp=C0805)
add('SW_BOOT', 'lcsc:SW-SMD_4P-L5.2-W5.2-P3.70-LS6.4', 'BOOT (nRPIBOOT)', 'C42420254', {1: 'NRPIBOOT', 2: 'NRPIBOOT', 3: 'GND', 4: 'GND'})
add('SW_PWR', 'lcsc:SW-SMD_4P-L5.2-W5.2-P3.70-LS6.4', 'POWER (PWR_BUT)', 'C42420254', {1: 'PWR_BUT', 2: 'PWR_BUT', 3: 'GND', 4: 'GND'})

# ===================================================================== USB-C #2 : USB host (Matek USB, flash drive, keyboard)
add('J_USB2', USBC, 'USB-C #2 HOST', 'C2765186',
    {'A1B12': 'GND', 'B1A12': 'GND', 'A4B9': 'VBUS2', 'B4A9': 'VBUS2', 'A5': 'USB2_CC1', 'B5': 'USB2_CC2',
     'A6': 'USB2_DP', 'B6': 'USB2_DP', 'A7': 'USB2_DN', 'B7': 'USB2_DN', '13': 'GND', '14': 'GND'})
R('56k', 'USB2_CC1', 'VBUS2', note='Rp: source (host) role'); R('56k', 'USB2_CC2', 'VBUS2')
add('U_ESD2', SOT236, 'USBLC6-2SC6 ESD', 'C2827654', {1: 'USB2_DP', 6: 'USB2_DP', 3: 'USB2_DN', 4: 'USB2_DN', 2: 'GND', 5: 'VBUS2'})
add('U_VB2', SOT235, 'SY6280AAC VBUS switch 1A', 'C55136', {1: 'VBUS2', 2: 'GND', 3: 'VB2_ISET', 4: 'VBUS_EN', 5: '+5V_AUX'})
R('6.8k', 'VB2_ISET', 'GND'); Cap('22uF', 'VBUS2', fp=C0805)

# ===================================================================== thermal camera: USB (UVC) + aux
add('J_THU', GH(4), 'THERMAL USB (VBUS,D-,D+,GND)', GH_LCSC[4], {1: 'VBUS3', 2: 'THU_DN', 3: 'THU_DP', 4: 'GND', 'MP': 'GND'})
add('U_ESD3', SOT236, 'USBLC6-2SC6 ESD', 'C2827654', {1: 'THU_DP', 6: 'THU_DP', 3: 'THU_DN', 4: 'THU_DN', 2: 'GND', 5: 'VBUS3'})
add('U_VB3', SOT235, 'SY6280AAC VBUS switch 1A', 'C55136', {1: 'VBUS3', 2: 'GND', 3: 'VB3_ISET', 4: 'VBUS_EN', 5: '+5V_AUX'})
R('6.8k', 'VB3_ISET', 'GND'); Cap('10uF', 'VBUS3', fp=C0805)
add('J_THA', GH(6), 'THERMAL AUX (5V,3V3,SCL,SDA,SYNC,GND)', GH_LCSC[6],
    {1: '+5V_AUX', 2: '+3V3_CM5', 3: 'I2C1_SCL', 4: 'I2C1_SDA', 5: 'TH_SYNC', 6: 'GND', 'MP': 'GND'})

# ===================================================================== AI accelerator (Hailo) via FFC like Raspberry Pi 5
add('J_PCIE', 'Connector_FFC-FPC:Hirose_FH12-16S-0.5SH_1x16-1MP_P0.50mm_Horizontal',
    'PCIe x1 FFC 16p (Pi 5 pinout) -> Hailo AI HAT+/M.2 HAT+', 'C596731',
    {1: '+5V_AI', 2: '+5V_AI', 3: 'GND', 4: 'PCIE_CLK_P', 5: 'PCIE_CLK_N', 6: 'GND', 7: 'PCIE_RX_P', 8: 'PCIE_RX_N',
     9: 'GND', 10: 'PCIE_TX_P', 11: 'PCIE_TX_N', 12: 'GND', 13: 'PCIE_PWR_EN', 14: 'PCIE_DET_WAKE',
     15: 'PCIE_CLKREQ_N', 16: 'PCIE_RST_N', 'MP': 'GND'}, 'FFC <= 50 mm, 90 ohm, alt HCTL XW05202-160R-00')
add('U_VB4', SOT235, 'SY6280AAC 5V for AI board 2A', 'C55136', {1: '+5V_AI', 2: 'GND', 3: 'VB4_ISET', 4: '+5V_AUX', 5: '+5V_AUX'})
R('3.4k', 'VB4_ISET', 'GND', note='2.0 A'); Cap('22uF', '+5V_AI', fp=C0805)
add('J_AIPWR', GH(4), 'AI POWER 5V (5V,5V,GND,GND) for Hailo HAT', GH_LCSC[4],
    {1: '+5V_AI', 2: '+5V_AI', 3: 'GND', 4: 'GND', 'MP': 'GND'})

# ===================================================================== cameras (identical connectors)
FH22 = 'Connector_FFC-FPC:Hirose_FH12-22S-0.5SH_1x22-1MP_P0.50mm_Horizontal'


def cam(n, i2c_scl, i2c_sda, g0, g1):
    m = {1: 'GND', 4: 'GND', 7: 'GND', 10: 'GND', 13: 'GND', 16: 'GND', 19: 'GND', 'MP': 'GND',
         2: 'CAM%d_D0_N' % n, 3: 'CAM%d_D0_P' % n, 5: 'CAM%d_D1_N' % n, 6: 'CAM%d_D1_P' % n, 8: 'CAM%d_C_N' % n,
         9: 'CAM%d_C_P' % n, 11: 'CAM%d_D2_N' % n, 12: 'CAM%d_D2_P' % n, 14: 'CAM%d_D3_N' % n, 15: 'CAM%d_D3_P' % n,
         17: g0, 18: g1, 20: i2c_scl, 21: i2c_sda, 22: '+3V3_CAM'}
    add('J_CAM%d' % n, FH22, 'CAM%d MIPI CSI-2 4-lane FFC 22p 0.5mm (Pi 5 / CM5IO pinout)' % n, 'C597981', m,
        'alt HCTL XW05202-220R-00 (C2906120); cable 22p 0.5 mm up to 300-400 mm')


cam(1, 'CAM1_SCL', 'CAM1_SDA', 'CAM1_GPIO0', 'CAM1_GPIO1')
cam(2, 'CAM2_SCL', 'CAM2_SDA', 'CAM2_EN', '')
R('2.2k', 'CAM2_EN', '+3V3_CAM', note='camera 2 power enable (as CM5IO)')
R('2.2k', 'CAM2_SCL', '+3V3_CM5'); R('2.2k', 'CAM2_SDA', '+3V3_CM5')
Cap('10uF', '+3V3_CAM', fp=C0805); Cap('100nF', '+3V3_CAM'); Cap('100nF', '+3V3_CAM')

# ===================================================================== microSD (for CM5 Lite)
add('J_SD', 'lcsc:TF-SMD_TF-01A', 'microSD push-push TF-01A', 'C91145',
    {1: 'SD_D2', 2: 'SD_D3', 3: 'SD_CMD', 4: 'SD_VDD', 5: 'SD_CLK', 6: 'GND', 7: 'SD_D0', 8: 'SD_D1',
     10: 'GND', 11: 'GND', 12: 'GND', 13: 'GND'}, 'works with CM5 Lite (no eMMC)')
add('U_SD', 'Package_TO_SOT_SMD:TSOT-23-5', 'RT9742GGJ5 SD power switch', 'C250547',
    {1: 'SD_VDD', 2: 'GND', 3: '', 4: 'SD_PWR_ON', 5: '+3V3_CM5'})
R('10k', 'SD_PWR_ON', '+3V3_CM5'); Cap('10uF', 'SD_VDD', fp=C0805); Cap('100nF', 'SD_VDD')

# ===================================================================== supervisor MCU (watchdog + power-fail + LEDs)
add('U_MCU', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', 'CH32V003F4P6 supervisor (HW watchdog, power-fail)', 'C5187096',
    {1: 'LED_ERR_N', 2: 'MCU_TX_R', 3: 'MCU_RX_R', 4: 'MCU_NRST', 5: 'VBAT_SENSE', 6: 'V5_SENSE', 7: 'GND',
     8: 'TEMP_ALERT', 9: '+3V3_AON', 10: 'HEARTBEAT_R', 11: 'PFAIL_R', 12: 'PMIC_OFF', 13: 'PWRBTN_PRESS',
     14: 'VSCAP_SENSE', 15: 'HOLD_EN_R', 16: 'SCAP_CHG_EN', 17: 'AUX_OFF', 18: 'MCU_SWIO', 19: 'CM5_ON_SENSE',
     20: 'WDT_DIS'})
Cap('100nF', '+3V3_AON'); Cap('1uF', '+3V3_AON', fp=C0603)
R('1k', 'MCU_TX_R', 'MCU_TX', note='series: no back-feed when CM5 is off')
R('1k', 'MCU_RX_R', 'MCU_RX'); R('1k', 'HEARTBEAT_R', 'HEARTBEAT'); R('1k', 'PFAIL_R', 'PFAIL_N')
R('1k', 'HOLD_EN_R', 'HOLD_EN'); R('10k', 'CM5_ON_SENSE', '+3V3_CM5')
R('10k', 'MCU_NRST', '+3V3_AON'); R('10k', 'TEMP_ALERT', '+3V3_AON')
R('10k', '+5V_CM5', 'V5_SENSE'); R('10k', 'V5_SENSE', 'GND'); Cap('100nF', 'V5_SENSE')
R('10k', 'VSCAP', 'VSCAP_SENSE'); R('10k', 'VSCAP_SENSE', 'GND')
add('Q_PMIC', SOT23, '2N7002 -> CM5 PMIC_EN (hard reset)', 'C8545', {1: 'PMIC_OFF', 2: 'GND', 3: 'PMIC_EN'})
R('100k', 'PMIC_OFF', 'GND')
add('Q_PWB', SOT23, '2N7002 -> CM5 PWR_BUT (wake / clean off)', 'C8545', {1: 'PWRBTN_PRESS', 2: 'GND', 3: 'PWR_BUT'})
R('100k', 'PWRBTN_PRESS', 'GND')
add('JP_WDT', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'close = watchdog disabled (bench)', '',
    {1: 'WDT_DIS', 2: 'GND'})
for tp, net in (('TP_SWIO', 'MCU_SWIO'), ('TP_3V3', '+3V3_AON'), ('TP_GND', 'GND'), ('TP_RST', 'MCU_NRST'),
                ('TP_5V', '+5V_CM5'), ('TP_VIN', 'VIN_PROT'), ('TP_5VA', '+5V_AUX')):
    add(tp, 'TestPoint:TestPoint_Pad_D1.0mm', tp[3:], '', {1: net})

# temperature sensor (always-on rail, CM5 I2C1 0x48, ALERT -> MCU)
add('U_TEMP', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'NST175H temp sensor 0x48', 'C917444',
    {1: 'I2C1_SDA', 2: 'I2C1_SCL', 3: 'TEMP_ALERT', 4: 'GND', 5: 'GND', 6: 'GND', 7: 'GND', 8: '+3V3_AON'})
Cap('100nF', '+3V3_AON')
R('2.2k', 'I2C1_SDA', '+3V3_CM5'); R('2.2k', 'I2C1_SCL', '+3V3_CM5')

# secure element: device keys / disk encryption key (LUKS), BirdWatch licence binding. I2C1 @0x60
add('U_SEC', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'ATECC608B secure element (I2C 0x60)', 'C1518769',
    {1: '', 2: '', 3: '', 4: 'GND', 5: 'I2C1_SDA', 6: 'I2C1_SCL', 7: '', 8: '+3V3_CM5'})
Cap('100nF', '+3V3_CM5')

# LEDs: PWR (green, always-on), RUN (blue, CM5 GPIO20 low = on), ERR (red, MCU)
add('D_PWR', LED, 'LED green PWR', 'C12624', {1: 'LEDP_K', 2: '+3V3_AON'}); R('1k', 'LEDP_K', 'GND')
add('D_RUN', LED, 'LED blue RUN', 'C2288', {1: 'LEDR_K', 2: '+3V3_CM5'}); R('220R', 'LEDR_K', 'LED_RUN_N')
add('D_ERR', LED, 'LED red ERROR', 'C2286', {1: 'LEDE_K', 2: '+3V3_AON'}); R('1k', 'LEDE_K', 'LED_ERR_N')

# ===================================================================== JST-GH connectors
add('J_MATEK', GH(4), 'MATEK UART0 (5V*,TX,RX,GND)', GH_LCSC[4], {1: 'MATEK_5V', 2: 'UART0_TX', 3: 'UART0_RX', 4: 'GND', 'MP': 'GND'})
add('JP_MATEK', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'close = 5V to Matek pin1', '',
    {1: 'MATEK_5V', 2: '+5V_AUX'})
add('J_GPS', GH(4), 'GPS/TELEM UART2 (5V,TX,RX,GND)', GH_LCSC[4], {1: '+5V_AUX', 2: 'UART2_TX', 3: 'UART2_RX', 4: 'GND', 'MP': 'GND'})
add('J_I2C', GH(4), 'I2C1 (3V3,SCL,SDA,GND)', GH_LCSC[4], {1: '+3V3_CM5', 2: 'I2C1_SCL', 3: 'I2C1_SDA', 4: 'GND', 'MP': 'GND'})
add('J_IO', GH(8), 'GPIO (3V3,G7,G10,G11,G16,G17,G24,GND)', GH_LCSC[8],
    {1: '+3V3_CM5', 2: 'IO_GPIO7', 3: 'IO_GPIO10', 4: 'IO_GPIO11', 5: 'IO_GPIO16', 6: 'IO_GPIO17', 7: 'IO_GPIO24', 8: 'GND', 'MP': 'GND'})
add('J_FAN', GH(4), 'FAN 5V PWM (5V,PWM,GND,TACH)', GH_LCSC[4], {1: '+5V_AUX', 2: 'FAN_PWM', 3: 'GND', 4: 'FAN_TACH', 'MP': 'GND'})
R('10k', 'FAN_PWM', '+3V3_CM5')
add('J_RTC', GH(2), 'RTC battery 3V (+,-)', GH_LCSC[2], {1: 'VBAT_RTC', 2: 'GND', 'MP': 'GND'})
for i in range(1, 5):
    add('J_S%d' % i, GH(3), 'SERVO%d (SIG,V+,GND)' % i, GH_LCSC[3], {1: 'SERVO%d' % i, 2: 'VSERVO', 3: 'GND', 'MP': 'GND'})
    R('220R', 'SERVO%d_G' % i, 'SERVO%d' % i, note='servo signal series R')
add('J_SPWR', GH(4), 'SERVO POWER IN from BEC (V+,V+,GND,GND)', GH_LCSC[4], {1: 'VSERVO', 2: 'VSERVO', 3: 'GND', 4: 'GND', 'MP': 'GND'})
add('JP_SERVO', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 'close = servos from 5V_AUX (<=1.5 A total)', '',
    {1: 'VSERVO', 2: '+5V_AUX'})
Cap('47uF 16V', 'VSERVO', fp=C1210)

# mounting holes (board corners)
for i in range(1, 5):
    add('H%d' % i, 'MountingHole:MountingHole_2.7mm_M2.5', 'M2.5', '', {})

# ------------------------------------------------------------------ net classes (Rezonit 4L 1.5 mm, 18 um outer)
DIFF100 = [n for n in set(v for c in C.values() for v in c['pins'].values()) if n.startswith(('CAM1_D', 'CAM1_C', 'CAM2_D', 'CAM2_C', 'PCIE_CLK', 'PCIE_RX', 'PCIE_TX'))]
DIFF90 = ['USB1_DP', 'USB1_DN', 'USB2_DP', 'USB2_DN', 'THU_DP', 'THU_DN']
POWER_HI = ['VBAT_RAW', 'VBAT_F', 'VIN_PROT', 'VIN_B1', '+5V_CM5', '+5V_AUX', 'B1_SW', 'B2_SW', 'HB_SW', 'VSCAP',
            'GND', 'SCAP_MID', 'SCAP_CHG']
POWER_MID = ['+5V_AI', 'VBUS1', 'VBUS2', 'VBUS3', 'VSERVO', '+3V3_CAM', '+3V3_CM5', '+3V3_AON', 'C33_LX', 'SD_VDD', 'MATEK_5V']

if __name__ == '__main__':
    nets = sorted(set(v for c in C.values() for v in c['pins'].values() if v))
    print(len(C), 'components', len(nets), 'nets')
    # nets with a single pad = probably a bug
    cnt = {}
    for r, c in C.items():
        for p, n in c['pins'].items():
            if n:
                cnt.setdefault(n, []).append(r + '.' + p)
    for n, l in sorted(cnt.items()):
        if len(l) < 2:
            print('SINGLE', n, l)
