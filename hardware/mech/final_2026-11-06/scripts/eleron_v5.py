# aileron v5 = v4 + relief where it rubs the big wing at +-30 deg (0.8 mm clearance)
import cadquery as cq, numpy as np, trimesh, time
t0=time.time()
ld=lambda f: cq.importers.importStep(f).val()
a=ld('eleron_v4.step'); W=ld('oldasm/wing_big_q1.step'); T=ld('tail_v10.step')
cy=[f for f in a.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]
P=np.array([[f.Center().x,f.Center().y,f.Center().z] for f in cy]).mean(0); d=cy[0]._geomAdaptor().Cylinder().Axis().Direction()
Pv=cq.Vector(*P); D=cq.Vector(d.X(),d.Y(),d.Z())
b=a.BoundingBox(); zone=cq.Workplane().box(b.xlen+30,b.ylen+30,b.zlen+30).translate(((b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2)).val()
Wz=W.intersect(zone); print('wing zone vol %.1f t=%.0f'%(Wz.Volume()/1000,time.time()-t0))
r=a; fails=0
for g in range(-33,34,3):
    base=Wz.rotate(Pv,Pv+D,-g)
    for s in [(0,0,0),(0.8,0,0),(-0.8,0,0),(0,0.8,0),(0,-0.8,0),(0,0,0.8),(0,0,-0.8)]:
        try:
            n=r.cut(base.translate(cq.Vector(*s)))
            if n.isValid() and n.Volume()>0.85*a.Volume(): r=max(n.Solids(),key=lambda x:x.Volume())
            else: fails+=1
        except Exception: fails+=1
print('fails',fails,'vol %.2f -> %.2f t=%.0f'%(a.Volume()/1000,r.Volume()/1000,time.time()-t0))
def ov(x,y):
    try: return round(x.intersect(y).Volume(),1)
    except Exception: return -1
print('aileron v5 vs wing:',[(g,ov(r.rotate(Pv,Pv+D,g),W)) for g in (-30,-25,-20,0,20,25,30)])
print('aileron v5 gap to tail:',[(g,round(r.rotate(Pv,Pv+D,g).distance(T),2)) for g in (-30,0,30)])
print('tube still enters channel: channel faces',len([f for f in r.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]))
cq.exporters.export(cq.Workplane(obj=r),'eleron_v5.step'); cq.exporters.export(cq.Workplane(obj=r),'eleron_v5.stl',tolerance=0.02,angularTolerance=0.1)
m=trimesh.load('eleron_v5.stl'); print('stl watertight',m.is_watertight,'bodies',len(m.split(only_watertight=False)))
