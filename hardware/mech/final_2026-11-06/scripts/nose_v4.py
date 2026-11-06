# nose v4 = nose v2 (inner camera plates removed, lens windows, M2 pilots) + ONLY the hook teeth removed (tongues kept)
import cadquery as cq, sys
SRC,OUT=sys.argv[1:3]
n=cq.importers.importStep(SRC).val(); v0=n.Volume()
r=n
for s in (1,-1):
    y0,y1=(20.3,23.45) if s>0 else (-23.45,-20.3)
    box=cq.Workplane().box(11.4,y1-y0,4.8,centered=(True,False,False)).translate((0,y0,-295.3)).val()
    r=r.cut(box)
sol=r.Solids(); r=max(sol,key=lambda x:x.Volume())
print(SRC,'valid',r.isValid(),'solids before keep',len(sol),'removed mm3',round(v0-r.Volume(),1))
for z in (-293,-300,-310): print('  z',z,'tongue still there (x=0,y=24..):',r.isInside(cq.Vector(0,24.5,z)),' tooth gone (x=0,y=22):',not r.isInside(cq.Vector(0,22,-293)))
cq.exporters.export(cq.Workplane(obj=r),OUT)
cq.exporters.export(cq.Workplane(obj=r),OUT.replace('.step','.stl'),tolerance=0.02,angularTolerance=0.1)
