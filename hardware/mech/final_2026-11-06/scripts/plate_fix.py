# plate fix: (1) remove the 4 thin raised pads/dimples at (+-9.5,+-9.5) (2) 4 THROUGH holes D3.2 at (+-10.55,+-10.55) = hole pattern of 16_Tail_Mount plate
import cadquery as cq, trimesh, sys
src,out=sys.argv[1:3]
t=cq.importers.importStep(src).val(); v0=t.Volume()
H=10.55
cut=[]
for sx in (1,-1):
    for sy in (1,-1):
        cut.append(cq.Workplane('XY').circle(3.4).extrude(3.2).translate((sx*H,sy*H,187.9)).val())      # pad / protrusion removal, z 187.9..191.1
        cut.append(cq.Workplane('XY').circle(1.6).extrude(9.0).translate((sx*H,sy*H,183.5)).val())      # through hole D3.2 z 183.5..192.5
r=t
for c in cut:
    n=r.cut(c)
    if n.isValid() and n.Volume()<=r.Volume()+1e-6: r=n
    else: print('cut rejected')
print('valid',r.isValid(),'solids',len(r.Solids()),'removed cm3',round((v0-r.Volume())/1000,3))
for sx in (1,-1):
    for sy in (1,-1):
        print((sx*H,sy*H),''.join('#' if r.isInside(cq.Vector(sx*H,sy*H,183.5+k*0.5)) else '.' for k in range(0,18)))
cq.exporters.export(cq.Workplane(obj=r),out)
vs,tr=r.tessellate(0.02,0.1); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export(out.replace('.step','.stl'))
