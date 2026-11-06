#!/bin/bash
set -e
AIL=${1:-eleron_v4}
S=/tmp/claude-0/-home-user-K8/8fc48cad-6552-5b7a-a937-c0e8e217cdce/scratchpad; M=$S/mech; F=$S/final2; L=$M/litye/x/Litye_FINAL
rm -rf $F; P=$F/PECHAT_tselye_detali; Q=$F/LITYE_razdelnye_detali; mkdir -p $P/00_proverka_sborki $Q/STEP $Q/STL $Q/docs $Q/images
cd $M
# split aileron for mould
python3 -I split_ail.py $AIL.step
# ---- PRINT
cp nose_v4.step $P/01_Nos_1_iz_1.STEP; cp nose_v4.stl $P/01_Nos_1_iz_1.stl
cp tail_v10.step $P/02_Hvost_1_iz_1.STEP; cp tail_v10_fix.stl $P/02_Hvost_1_iz_1.stl
cp $AIL.step $P/03_Eleron.STEP; for i in 1 2 3 4; do cp $AIL.stl $P/03_Eleron_${i}_iz_4.stl; done
for f in vse/0[4-9]_*.stl vse/1[0-8]_*.stl; do b=$(basename "$f"); case "$b" in 07_*) ;; *) cp "$f" "$P/$b";; esac; done
cp panel180_balance_slot.stl "$P/07_Панель_180мм_с_пазом_балансира_1_iz_1.stl"; cp panel180_balance_slot.step "$P/07_Панель_180мм_с_пазом_балансира.STEP"
cp frame/rama_verh_2.5mm.step $P/19_Rama_karbon_verh_2.5mm_1_iz_1.STEP; cp frame/rama_niz_2.5mm.step $P/19_Rama_karbon_niz_2.5mm_1_iz_1.STEP
cp frame/top.dxf $P/19_Rama_karbon_verh.dxf; cp frame/bottom.dxf $P/19_Rama_karbon_niz.dxf
cp sborka_v10.step $P/00_proverka_sborki/sborka_proverka.STEP 2>/dev/null || true
cp photos/tail_v10_views.png photos/tail_v10_sections.png photos/nose_v3_views.png $P/00_proverka_sborki/ 2>/dev/null || true
# ---- MOULD
cp nose_v4.step $Q/STEP/01_Nos_tselyy.STEP; cp nose_v4.stl $Q/STL/01_Nos_tselyy.stl
cp tail_v10.step $Q/STEP/02_Hvost_tselyy_forma_3_chasti.STEP; cp tail_v10_fix.stl $Q/STL/02_Hvost_tselyy_forma_3_chasti.stl
cp ail_halfA.step $Q/STEP/03a_Eleron_polovina_A.STEP; cp ail_halfB.step $Q/STEP/03b_Eleron_polovina_B.STEP; cp ail_halfA.stl $Q/STL/03a_Eleron_polovina_A.stl; cp ail_halfB.stl $Q/STL/03b_Eleron_polovina_B.stl
for f in 04_Panel_130 05_Panel_156 06_Panel_160.5 08_Panel_okno_180 09_Panel_229.5 10_Zhalyuzi_pravaya 11_Zhalyuzi_levaya; do cp $L/STEP/$f.STEP $Q/STEP/; cp $L/STL/$f.stl $Q/STL/; done
cp panel180_balance_slot.step $Q/STEP/07_Panel_180_paz_balansira.STEP; cp panel180_balance_slot.stl $Q/STL/07_Panel_180_paz_balansira.stl
cp $L/STL/12a_Krylo_bolshoe_verkh.stl $Q/STL/; cp w12b_fix2.stl $Q/STL/12b_Krylo_bolshoe_niz_ispravleno.stl; cp $L/STL/12b_Krylo_bolshoe_niz.stl $Q/STL/12b_Krylo_bolshoe_niz_ISHODNIK.stl
cp w13a_fix2.stl $Q/STL/13a_Krylo_perednee_verkh_ispravleno.stl; cp $L/STL/13a_Krylo_perednee_verkh.stl $Q/STL/13a_Krylo_perednee_verkh_ISHODNIK.stl
cp w13b_fix2.stl $Q/STL/13b_Krylo_perednee_niz_ispravleno.stl; cp $L/STL/13b_Krylo_perednee_niz.stl $Q/STL/13b_Krylo_perednee_niz_ISHODNIK.stl
for f in 14_Derzhatel_trubki_bolshogo_kryla 15_Derzhatel_trubki_perednego_kryla 16_Tail_Mount 17_Opora_akkumulyatora 18_Kreplenie_motora; do cp $L/STL/$f.stl $Q/STL/; done
cp frame/rama_verh_2.5mm.step $Q/STEP/19_Rama_karbon_verh_2.5mm.STEP; cp frame/rama_niz_2.5mm.step $Q/STEP/19_Rama_karbon_niz_2.5mm.STEP; cp frame/top.dxf $Q/19_Rama_karbon_verh.dxf; cp frame/bottom.dxf $Q/19_Rama_karbon_niz.dxf
cp $L/docs/* $Q/docs/; cp $L/images/* $Q/images/; cp photos/tail_v10_views.png photos/tail_v10_sections.png $Q/images/ 2>/dev/null || true
echo packaged
