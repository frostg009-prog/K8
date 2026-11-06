# nose v3 = nose v2 (inner plates removed, lens windows, M2 pilots) + the two "locks" (blocks at y=+-23.5.., |x|<5.5) removed flush with the shell
import cadquery as cq, trimesh, sys
SRC,OUT=sys.argv[1:3]
n=cq.importers.importStep(SRC).val(); v0=n.Volume()
yin=[(-322.6,23.45),(-320,24.05),(-318,24.75),(-314,26.15),(-310,27.35),(-306,28.25),(-302,29.05),(-298,29.75),(-294.0,30.15)]
pts=[(22.6,-322.6)]+[(y,z) for z,y in yin]+[(22.6,-294.0)]
r=n
for s in (1,-1):
    prof=cq.Workplane('YZ').polyline([(s*y,z) for y,z in pts]).close().extrude(5.6,both=True).val()
    try:
        m=r.cut(prof)
        if m.isValid(): r=m
        else: print('rejected')
    except Exception as e: print('fail',e)
print(SRC,'valid',r.isValid(),'solids',len(r.Solids()),'removed cm3',round((v0-r.Volume())/1000,2))
for z in (-318,-310,-300):
    print(' z',z,'x=0 y>0 solid from:',[round(23+k*0.25,2) for k in range(0,44) if r.isInside(cq.Vector(0,23+k*0.25,z))][:1])
cq.exporters.export(cq.Workplane(obj=r),OUT)
vs,tr=r.tessellate(0.03,0.15); mm=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); mm.merge_vertices(); mm.export(OUT.replace('.step','.stl'))
