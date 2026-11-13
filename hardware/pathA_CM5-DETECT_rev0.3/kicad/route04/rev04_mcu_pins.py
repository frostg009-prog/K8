# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): U_MCU pin change on the routed board - VBAT_SENSE moves from pin 5 (PA1/A1) to pin 20 (PD3/A4),
pin 5 becomes NC, solder jumper JP_WDT and net WDT_DIS are removed (watchdog is disabled with UART command W0 instead).
   python3 rev04_mcu_pins.py in.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
src, out = sys.argv[1:3]
TM = pcbnew.ToMM
b = pcbnew.LoadBoard(src)
u = b.FindFootprintByReference('U_MCU')
p5 = [p for p in u.Pads() if p.GetNumber() == '5'][0]; p20 = [p for p in u.Pads() if p.GetNumber() == '20'][0]
vb, wd = p5.GetNetCode(), p20.GetNetCode()
kill = []
for t in b.GetTracks():
    if t.GetNetCode() == wd:
        kill.append(t)                                        # whole WDT_DIS net goes away
    elif t.GetNetCode() == vb and t.GetClass() == 'PCB_TRACK' and (p5.HitTest(t.GetStart()) or p5.HitTest(t.GetEnd())):
        kill.append(t)
for t in kill:
    b.Remove(t)
jp = b.FindFootprintByReference('JP_WDT')
if jp:
    b.Remove(jp)
p20.SetNet(b.FindNet('VBAT_SENSE'))
p5.SetNetCode(0)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('U_MCU pin 5 -> NC, pin 20 -> VBAT_SENSE, JP_WDT removed, ripped', len(kill))
