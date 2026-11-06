# aileron v4: inside the tail clearance zone keep only a round collar around the tube (r=4.8); root face 2.3 mm beyond the tail's outermost point
import cadquery as cq, trimesh, numpy as np
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1)
tail=cq.importers.importStep('tail_print_final.step').val().rotate(O,Z,-45)
ail=cq.importers.importStep('eleron_v3_trimmed.step').val().rotate(O,Z,-45)
w0=cq.importers.importStep('in/wingM.step').val().rotate(O,Z,-45)
cy=[f for f in w0.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]
cc=[f.Center() for f in cy]; wc=cq.Vector(sum(p.x for p in cc)/2,sum(p.y for p in cc)/2,sum(p.z for p in cc)/2)
d=cy[0]._geomAdaptor().Cylinder().Axis().Direction(); dn=cq.Vector(d.X(),d.Y(),d.Z()).normalized()
if dn.x<0: dn=dn*-1
vs,_=tail.tessellate(0.1,0.3); s=np.array([ (v-wc).dot(dn) for v in vs]); smax=s.max(); print('tail max along tube axis s=%.2f'%smax)
S_CUT=smax+2.3; R=4.8
pl=cq.Plane(origin=wc+dn*(-150.0),xDir=cq.Vector(0,1,0).cross(dn) if abs(dn.y)<0.9 else cq.Vector(1,0,0),normal=dn)
L=150.0+S_CUT
box=cq.Workplane(pl).rect(200,200).extrude(L).val()
col=cq.Workplane(pl).circle(R).extrude(L).val()
cutter=box.cut(col)
a4=ail.cut(cutter); print('valid',a4.isValid(),'solids',len(a4.Solids()),'vol %.2f -> %.2f'%(ail.Volume()/1000,a4.Volume()/1000))
a4=max(a4.Solids(),key=lambda x:x.Volume())
g=[(a,round(a4.rotate(wc,wc+dn,a).distance(tail),2)) for a in range(-45,46,5)]
print('gaps after v4 (deg,mm):',g); print('min',min(x[1] for x in g))
gl=a4.rotate(O,Z,45)
cq.exporters.export(cq.Workplane(obj=gl),'eleron_v4.step')
cq.exporters.export(cq.Workplane(obj=gl),'eleron_v4.stl',tolerance=0.02,angularTolerance=0.1)
m=trimesh.load('eleron_v4.stl'); print('stl watertight',m.is_watertight,'bodies',len(m.split(only_watertight=False)))
