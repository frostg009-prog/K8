import cadquery as cq, trimesh, sys
SRC=sys.argv[1]; OUT=sys.argv[2]
LENS_D=18.5; PITCH_Y=9.25; BOLT_D=2.4; HX=10.5
n=cq.importers.importStep(SRC).val(); v0=n.Volume()
ZF=-329.5; L=14.0                       # cutters start in front of the tip, go 14 mm back
def cyl(d,x,y): return cq.Workplane('XY').circle(d/2).extrude(L).translate((x,y,ZF)).val()
cut=[]
for s in (+1,-1):
    ly=s*PITCH_Y                       # lens centre (cameras stacked along Y, pitch 2*PITCH_Y)
    cut.append(cyl(LENS_D,0,ly))
    for dy in (-7.5,5.0):              # Pi-camera pattern 21 x 12.5: holes 7.5 mm one side and 5.0 mm other side of lens axis
        for hx in (-HX,HX): cut.append(cyl(BOLT_D,hx,ly+s*dy))
r=n
for c in cut: r=r.cut(c)
print('valid',r.isValid(),'removed cm3',round((v0-r.Volume())/1000,3),len(r.Solids()))
cq.exporters.export(cq.Workplane(obj=r),OUT)
vs,tr=r.tessellate(0.03,0.15); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export(OUT.replace('.step','.stl'))
