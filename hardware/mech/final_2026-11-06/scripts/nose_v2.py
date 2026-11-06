import cadquery as cq, trimesh, sys
SRC,OUT=sys.argv[1],sys.argv[2]
n=cq.importers.importStep(SRC).val(); v0=n.Volume()
# 1) remove the two protruding inner plates (x=+-(10.3..13.2), y -13..8, from the front wall rearwards)
cuts=[]
for sx in (1,-1):
    b=cq.Workplane().box(4.6,24.0,27.0,centered=(True,False,False)).translate((sx*11.8,-14.0,-322.9)).val()
    cuts.append(b)
# 2) camera lens windows (as before) + blind M2 pilots
LENS_D=18.5; PY=9.25; HX=10.5
def cyl(d,x,y,z0,L): return cq.Workplane('XY').circle(d/2).extrude(L).translate((x,y,z0)).val()
for s in (1,-1):
    ly=s*PY; cuts.append(cyl(LENS_D,0,ly,-330.0,12.0))
    for dy in (-7.5,5.0):
        for hx in (-HX,HX): cuts.append(cyl(1.7,hx,ly+s*dy,-325.9,2.6))   # blind pilot, 0.6 mm skin on the outside
r=n
for c in cuts: r=r.cut(c)
print('valid',r.isValid(),'solids',len(r.Solids()),'removed cm3',round((v0-r.Volume())/1000,2))
cq.exporters.export(cq.Workplane(obj=r),OUT)
vs,tr=r.tessellate(0.03,0.15); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export(OUT.replace('.step','.stl'))
