#!/bin/bash
set -e
S=/tmp/claude-0/-home-user-K8/8fc48cad-6552-5b7a-a937-c0e8e217cdce/scratchpad; M=$S/mech; R=$S/release; F3=$S/final3; L=$M/litye/x/Litye_FINAL
cd $M
# ------------------------------ PRINT (all parts single-piece)
P=$R/DRONE_PRINT_all_parts_single_piece; mkdir -p $P/STEP $P/STL
cp nose_v4.step $P/STEP/01_Nose_x1.STEP;                 cp nose_v4_fix.stl $P/STL/01_Nose_x1.stl
cp tail_v11.step $P/STEP/02_Tail_x1.STEP;                cp tail_v11_fix.stl $P/STL/02_Tail_x1.stl
cp eleron_v4.step $P/STEP/03_Aileron_x4.STEP;            cp eleron_v4.stl $P/STL/03_Aileron_x4.stl
cp korpus_PLUS_Y.step $P/STEP/04_Body_Panel_A_with_window_x1.STEP;            cp korpus_PLUS_Y_final.stl $P/STL/04_Body_Panel_A_with_window_x1.stl
cp korpus_MINUS_Y.step $P/STEP/05_Body_Panel_B_with_battery_balance_plug_slot_x1.STEP; cp korpus_MINUS_Y_final.stl $P/STL/05_Body_Panel_B_with_battery_balance_plug_slot_x1.stl
cp korpus_PLUS_X.step $P/STEP/06_Body_Panel_C_louvered_x1.STEP;               cp korpus_PLUS_X_final.stl $P/STL/06_Body_Panel_C_louvered_x1.stl
cp korpus_MINUS_X.step $P/STEP/07_Body_Panel_D_louvered_x1.STEP;              cp korpus_MINUS_X_final.stl $P/STL/07_Body_Panel_D_louvered_x1.stl
cp oldasm/wing_big_q1.step $P/STEP/08_Wing_Large_x4.STEP;       cp "vse/12_Крыло_большое_1_iz_4.stl" $P/STL/08_Wing_Large_x4.stl
cp oldasm/wing_front_q1.step $P/STEP/09_Wing_Front_x4.STEP;     cp "vse/13_Крыло_переднее_1_iz_4.stl" $P/STL/09_Wing_Front_x4.stl
cp oldasm/holder_big.step $P/STEP/10_Tube_Holder_Large_Wing_x4.STEP; cp "vse/14_Крепление_трубки_большого_крыла_1_iz_4.stl" $P/STL/10_Tube_Holder_Large_Wing_x4.stl
cp oldasm/holder_front.step $P/STEP/11_Tube_Holder_Front_Wing_x4.STEP; cp "vse/15_Крепление_трубки_переднего_крыла_1_iz_4.stl" $P/STL/11_Tube_Holder_Front_Wing_x4.stl
cp oldasm/tail_mount.step $P/STEP/12_Tail_Mount_Plate_x1.STEP;   cp "vse/16_Tail_Mount_плита_крепления_хвоста_1_iz_1.stl" $P/STL/12_Tail_Mount_Plate_x1.stl
cp oldasm/batt_support.step $P/STEP/13_Battery_Support_x1.STEP;  cp "vse/17_Опора_аккумулятора_между_пластин_1_iz_1.stl" $P/STL/13_Battery_Support_x1.stl
cp oldasm/motor_mount.step $P/STEP/14_Motor_Mount_x4.STEP;       cp "vse/18_Крепление_мотора_1_iz_4.stl" $P/STL/14_Motor_Mount_x4.stl
mkdir -p $P/CARBON_cut_files; cp frame/top.dxf $P/CARBON_cut_files/15_Carbon_Frame_Plate_Top_x1.dxf; cp frame/bottom.dxf $P/CARBON_cut_files/16_Carbon_Frame_Plate_Bottom_x1.dxf; cp frame/rama_verh_2.5mm.step $P/CARBON_cut_files/15_Carbon_Frame_Plate_Top_2.5mm.STEP; cp frame/rama_niz_2.5mm.step $P/CARBON_cut_files/16_Carbon_Frame_Plate_Bottom_2.5mm.STEP
# ------------------------------ MOULD 1 wings
W=$R/MOULD_1_WINGS_two_halves; mkdir -p $W/STEP $W/STL $W/lightened_halves_STL_only
cp wing_bolshoe_verkh.step $W/STEP/01_Wing_Large_Top_half_x4.STEP;   cp wing_bolshoe_verkh_fix.stl $W/STL/01_Wing_Large_Top_half_x4.stl
cp wing_bolshoe_niz.step $W/STEP/02_Wing_Large_Bottom_half_x4.STEP;  cp wing_bolshoe_niz_fix.stl $W/STL/02_Wing_Large_Bottom_half_x4.stl
cp wing_perednee_verkh.step $W/STEP/03_Wing_Front_Top_half_x4.STEP;  cp wing_perednee_verkh_fix.stl $W/STL/03_Wing_Front_Top_half_x4.stl
cp wing_perednee_niz.step $W/STEP/04_Wing_Front_Bottom_half_x4.STEP; cp wing_perednee_niz_fix.stl $W/STL/04_Wing_Front_Bottom_half_x4.stl
cp $L/STL/12a_Krylo_bolshoe_verkh.stl $W/lightened_halves_STL_only/Wing_Large_Top_lightened.stl; cp w12b_fix2.stl $W/lightened_halves_STL_only/Wing_Large_Bottom_lightened_repaired.stl
cp w13a_fix2.stl $W/lightened_halves_STL_only/Wing_Front_Top_lightened_repaired.stl; cp w13b_fix2.stl $W/lightened_halves_STL_only/Wing_Front_Bottom_lightened_repaired.stl
# ------------------------------ MOULD 2 body panels
B=$R/MOULD_2_BODY_PANELS_4_large; mkdir -p $B/STEP $B/STL
cp $P/STEP/04_*.STEP $P/STEP/05_*.STEP $P/STEP/06_*.STEP $P/STEP/07_*.STEP $B/STEP/; cp $P/STL/04_*.stl $P/STL/05_*.stl $P/STL/06_*.stl $P/STL/07_*.stl $B/STL/
# ------------------------------ MOULD 3 nose / tail / aileron
N=$R/MOULD_3_NOSE_TAIL_AILERON; mkdir -p $N/STEP $N/STL
cp nose_v4.step $N/STEP/01_Nose_one_piece_x1.STEP;  cp nose_v4_fix.stl $N/STL/01_Nose_one_piece_x1.stl
cp tail_v11.step $N/STEP/02_Tail_one_piece_for_3_part_tool_x1.STEP; cp tail_v11_fix.stl $N/STL/02_Tail_one_piece_for_3_part_tool_x1.stl
cp ail_halfA.step $N/STEP/03a_Aileron_half_A_x4.STEP; cp ail_halfA.stl $N/STL/03a_Aileron_half_A_x4.stl
cp ail_halfB.step $N/STEP/03b_Aileron_half_B_x4.STEP; cp ail_halfB.stl $N/STL/03b_Aileron_half_B_x4.stl
# ------------------------------ MOULD 4 small parts
Q=$R/MOULD_4_SMALL_PARTS; mkdir -p $Q/STEP $Q/STL
for n in 10_Tube_Holder_Large_Wing_x4 11_Tube_Holder_Front_Wing_x4 12_Tail_Mount_Plate_x1 13_Battery_Support_x1 14_Motor_Mount_x4; do cp $P/STEP/$n.STEP $Q/STEP/; cp $P/STL/$n.stl $Q/STL/; done
echo built
