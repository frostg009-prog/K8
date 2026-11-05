import cadquery as cq, trimesh, numpy as np, shapely.geometry as sg, sys
T=float(sys.argv[1]) if len(sys.argv)>1 else 2.0      # wall of the hollowed cone, mm
RC=22.8                                              # bore radius replacing the central cross core
t=cq.importers.importStep('in/tail.step').val()
m=trimesh.load('tail.stl')
# outer envelope r(z): outermost point of the y=0 section for z>=217
s=m.section(plane_origin=[0,0,0],plane_normal=[0,1,0])
pts=np.vstack([e for e in s.discrete])           # x,y,z
p=pts[(pts[:,0]>=0)&(pts[:,2]>=216.9)]
p=np.vstack([p,[[28.4,0,212.0]]])
p=p[np.argsort(p[:,2])]
zmax=p[:,2].max()
zs=np.linspace(212.0,zmax-0.01,140)
# outer curve = the points on the outermost boundary: take upper envelope via binned max
bins=np.linspace(216.9,zmax,200); zb=[];rb=[]
for a,b in zip(bins[:-1],bins[1:]):
    q=p[(p[:,2]>=a)&(p[:,2]<=b)]
    if len(q): zb.append(q[:,2][q[:,0].argmax()]); rb.append(q[:,0].max())
prof=[(z,float(np.interp(z,zb,rb))) for z in zs]
poly=sg.Polygon([(0,212.0)]+[(r,z) for z,r in prof]+[(0,prof[-1][0])]+[(-r,z) for z,r in prof[::-1]])   # (r,z) half-profile of the solid cone
inner=poly.buffer(-T,join_style=2).intersection(sg.box(0,150,100,300))
ip=list(inner.exterior.coords)
ip=[(max(r,0),z) for r,z in ip]
# inner cutter profile in (r,z) -> revolve about Z
core=[(0,170.0),(RC,170.0),(RC,217.0)]
cone=[p for p in ip if p[1]>=217.0-1e-6]
# merge: bore cylinder, then offset-cone cavity
cut_pts=[(0,170.0),(RC,170.0),(RC,217.0)]+sorted([p for p in ip if p[0]>RC-1e-6 or True],key=lambda p:p[1])[0:0]
# build cavity as union of two revolves (robust)
def rev(profile):
    w=cq.Workplane('XZ').polyline(profile).close().revolve(360,(0,0,0),(0,1,0))
    return w.val()
bore=rev([(0,170.0),(RC,170.0),(RC,217.5),(0,217.5)])
cav=rev([(max(r,0.0),z) for r,z in ip])
res=t.cut(bore).cut(cav)
print('valid',res.isValid(),'vol cm3',round(t.Volume()/1000,1),'->',round(res.Volume()/1000,1),'solids',len(res.Solids()))
cq.exporters.export(cq.Workplane(obj=res),'tail_print.step')
cq.exporters.export(cq.Workplane(obj=res),'tail_print.stl',tolerance=0.05,angularTolerance=0.1)
