#!/bin/bash
set -e
S=/tmp/claude-0/-home-user-K8/8fc48cad-6552-5b7a-a937-c0e8e217cdce/scratchpad; M=$S/mech; R=$S/release2; rm -rf $R; mkdir -p $R; cd $M
cp_(){ cp "$1" "$2"; }
common_print(){  # $1 = dir
  P=$1; mkdir -p $P/STEP $P/STL
  cp nose_v4.step $P/STEP/01_Nose_x1.STEP;                 cp nose_v4_fix.stl $P/STL/01_Nose_x1.stl
  cp tail_v12.step $P/STEP/02_Tail_x1.STEP;                cp fine/tail_v12.stl $P/STL/02_Tail_x1.stl
  cp eleron_v6.step $P/STEP/03_Aileron_x4.STEP;            cp fine/eleron_v6.stl $P/STL/03_Aileron_x4.stl
}
tail_print(){ P=$1
  cp wing_big_q1.step $P/STEP/20_Wing_Large_x4.STEP;       cp fine/wing_big_q1.stl $P/STL/20_Wing_Large_x4.stl
  cp wing_front_q1.step $P/STEP/21_Wing_Front_x4.STEP;     cp fine/wing_front_q1.stl $P/STL/21_Wing_Front_x4.stl
  cp holder_big.step $P/STEP/22_Tube_Holder_Large_Wings_center_x1.STEP; cp fine/holder_big.stl $P/STL/22_Tube_Holder_Large_Wings_center_x1.stl
  cp holder_front.step $P/STEP/23_Tube_Holder_Front_Wings_center_x1.STEP; cp fine/holder_front.stl $P/STL/23_Tube_Holder_Front_Wings_center_x1.stl
  cp tail_mount.step $P/STEP/24_Tail_Mount_Plate_x1.STEP;  cp fine/tail_mount.stl $P/STL/24_Tail_Mount_Plate_x1.stl
  cp batt_support.step $P/STEP/25_Battery_Support_x1.STEP; cp fine/batt_support.stl $P/STL/25_Battery_Support_x1.stl
  cp motor_mount.step $P/STEP/26_Motor_Mount_x4.STEP;      cp fine/motor_mount.stl $P/STL/26_Motor_Mount_x4.stl
  mkdir -p $P/CARBON_cut_files; cp frame/top.dxf $P/CARBON_cut_files/30_Carbon_Frame_Plate_Top_x1.dxf; cp frame/bottom.dxf $P/CARBON_cut_files/31_Carbon_Frame_Plate_Bottom_x1.dxf
  cp frame/rama_verh_2.5mm.step $P/CARBON_cut_files/30_Carbon_Frame_Plate_Top_2.5mm.STEP; cp frame/rama_niz_2.5mm.step $P/CARBON_cut_files/31_Carbon_Frame_Plate_Bottom_2.5mm.STEP
}
# ===== 1 PRINT, 4 large panels
P=$R/1_PRINT_4_large_panels; common_print $P
cp panel3_PLUS_Y.step $P/STEP/04_Body_Panel_A_with_window_x1.STEP;  cp fine/panel3_PLUS_Y.stl $P/STL/04_Body_Panel_A_with_window_x1.stl
cp panel3_MINUS_Y.step $P/STEP/05_Body_Panel_B_with_battery_balance_plug_slot_x1.STEP; cp fine/panel3_MINUS_Y.stl $P/STL/05_Body_Panel_B_with_battery_balance_plug_slot_x1.stl
cp panel3_PLUS_X.step $P/STEP/06_Body_Panel_C_louvered_x1.STEP;     cp fine/panel3_PLUS_X.stl $P/STL/06_Body_Panel_C_louvered_x1.stl
cp panel3_MINUS_X.step $P/STEP/07_Body_Panel_D_louvered_x1.STEP;    cp fine/panel3_MINUS_X.stl $P/STL/07_Body_Panel_D_louvered_x1.stl
tail_print $P
# ===== 3 PRINT, 12 separate panels
P=$R/3_PRINT_12_separate_panels; common_print $P; i=4
for f in p12/*.step; do b=$(basename $f .step); n=$(printf "%02d" $i); cp $f $P/STEP/${n}_Body_Panel_${b}_x1.STEP; cp p12/$b.stl $P/STL/${n}_Body_Panel_${b}_x1.stl; i=$((i+1)); done
tail_print $P
# ===== 2 MOULD
Q=$R/2_MOULD_injection; mkdir -p $Q/STEP $Q/STL
cp nose_v4.step $Q/STEP/01_Nose_x1.STEP; cp nose_v4_fix.stl $Q/STL/01_Nose_x1.stl
cp tail_v12.step $Q/STEP/02_Tail_one_piece_for_3_part_tool_x1.STEP; cp fine/tail_v12.stl $Q/STL/02_Tail_one_piece_for_3_part_tool_x1.stl
cp ail_halfA.step $Q/STEP/03a_Aileron_half_A_x4.STEP; cp fine/ail_halfA.stl $Q/STL/03a_Aileron_half_A_x4.stl
cp ail_halfB.step $Q/STEP/03b_Aileron_half_B_x4.STEP; cp fine/ail_halfB.stl $Q/STL/03b_Aileron_half_B_x4.stl
cp panel3_PLUS_Y.step $Q/STEP/04_Body_Panel_A_with_window_x1.STEP;  cp fine/panel3_PLUS_Y.stl $Q/STL/04_Body_Panel_A_with_window_x1.stl
cp panel3_MINUS_Y.step $Q/STEP/05_Body_Panel_B_with_battery_balance_plug_slot_x1.STEP; cp fine/panel3_MINUS_Y.stl $Q/STL/05_Body_Panel_B_with_battery_balance_plug_slot_x1.stl
cp panel3_PLUS_X.step $Q/STEP/06_Body_Panel_C_louvered_x1.STEP;     cp fine/panel3_PLUS_X.stl $Q/STL/06_Body_Panel_C_louvered_x1.stl
cp panel3_MINUS_X.step $Q/STEP/07_Body_Panel_D_louvered_x1.STEP;    cp fine/panel3_MINUS_X.stl $Q/STL/07_Body_Panel_D_louvered_x1.stl
cp wm_big_top.step $Q/STEP/08a_Wing_Large_Top_half_lightened_x4.STEP;  cp wm_big_top.stl $Q/STL/08a_Wing_Large_Top_half_lightened_x4.stl
cp wm_big_bot.step $Q/STEP/08b_Wing_Large_Bottom_half_lightened_x4.STEP; cp wm_big_bot.stl $Q/STL/08b_Wing_Large_Bottom_half_lightened_x4.stl
cp wm_front_top.step $Q/STEP/09a_Wing_Front_Top_half_lightened_x4.STEP; cp wm_front_top.stl $Q/STL/09a_Wing_Front_Top_half_lightened_x4.stl
cp wm_front_bot.step $Q/STEP/09b_Wing_Front_Bottom_half_lightened_x4.STEP; cp wm_front_bot.stl $Q/STL/09b_Wing_Front_Bottom_half_lightened_x4.stl
for n in 22_Tube_Holder_Large_Wings_center_x1 23_Tube_Holder_Front_Wings_center_x1 24_Tail_Mount_Plate_x1 25_Battery_Support_x1 26_Motor_Mount_x4; do :; done
cp holder_big.step $Q/STEP/10_Tube_Holder_Large_Wings_center_x1.STEP; cp fine/holder_big.stl $Q/STL/10_Tube_Holder_Large_Wings_center_x1.stl
cp holder_front.step $Q/STEP/11_Tube_Holder_Front_Wings_center_x1.STEP; cp fine/holder_front.stl $Q/STL/11_Tube_Holder_Front_Wings_center_x1.stl
cp tail_mount.step $Q/STEP/12_Tail_Mount_Plate_x1.STEP; cp fine/tail_mount.stl $Q/STL/12_Tail_Mount_Plate_x1.stl
cp batt_support.step $Q/STEP/13_Battery_Support_x1.STEP; cp fine/batt_support.stl $Q/STL/13_Battery_Support_x1.stl
cp motor_mount.step $Q/STEP/14_Motor_Mount_x4.STEP; cp fine/motor_mount.stl $Q/STL/14_Motor_Mount_x4.stl
mkdir -p $Q/CARBON_cut_files; cp $R/1_PRINT_4_large_panels/CARBON_cut_files/* $Q/CARBON_cut_files/
# ===== 4 ASSEMBLY
A=$R/4_ASSEMBLY_full; mkdir -p $A
cp asm/Drone_Assembly_4_large_panels.step asm/Drone_Assembly_4_large_panels.stl asm/Drone_Assembly_12_separate_panels.step asm/Drone_Assembly_12_separate_panels.stl $A/
cp -r asm/Drone_Assembly_4_large_panels_parts_in_place $A/PARTS_IN_PLACE_4_large_panels; cp -r asm/Drone_Assembly_12_separate_panels_parts_in_place $A/PARTS_IN_PLACE_12_separate_panels
echo built
