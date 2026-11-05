import cadquery as cq, math
U='/root/.claude/uploads/8fc48cad-6552-5b7a-a937-c0e8e217cdce/'
Z=cq.Vector(0,0,1); O=cq.Vector(0,0,0); Y=cq.Vector(0,1,0)
tail=cq.importers.importStep('tail_v5.step').val().rotate(O,Z,-45)          # diagonal -> +X
servo0=cq.importers.importStep(U+'6feda855-______4x_MG90S______________1.STEP').val().Solids()[0].rotate(O,Z,-45)
ail0=cq.importers.importStep('in/aileron.step').val().rotate(O,Z,-45)
PIV=cq.Vector(30,0,194.5)
def lev(s): return s.rotate(PIV,PIV+Y,-7.5)
servo=lev(servo0); ail=lev(ail0)
dz=201.3-servo.Center().z; servo=servo.translate(cq.Vector(0,0,dz)); ail=ail.translate(cq.Vector(0,0,dz))
zs=[f.Center().z for f in servo.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-2.45)<0.01 and f.Area()>8][0]
print('shaft axis z',round(zs,2))
# aileron tube channel axis
ch=[f for f in ail.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]
c=[f.Center() for f in ch]; ax=ch[0]._geomAdaptor().Cylinder().Axis().Direction()
print('aileron channel dir',[round(v,3) for v in (ax.X(),ax.Y(),ax.Z())],'centres',[(round(p.x,1),round(p.y,1),round(p.z,1)) for p in c])
cy=sum(p.y for p in c)/2; cz=sum(p.z for p in c)/2; print('channel axis y=%.2f z=%.2f ; servo shaft axis y=0 z=%.2f -> offset dy=%.2f dz=%.2f'%(cy,cz,zs,cy,cz-zs))
bb=ail.BoundingBox(); print('aileron x %.1f..%.1f'%(bb.xmin,bb.xmax))
X0,X1=34.0,bb.xmax-2
tube=cq.Workplane('YZ').circle(3.0).circle(2.0).extrude(X1-X0).translate((X0,0,zs)).val()
tubeS=cq.Workplane('YZ').circle(3.0).extrude(X1-X0).translate((X0,0,zs)).val()
print('tube/aileron overlap mm3 (solid tube):',round(tubeS.intersect(ail).Volume(),1),' tube/tail overlap:',round(tubeS.intersect(tail).Volume(),1),' tube/servo overlap:',round(tubeS.intersect(servo).Volume(),1))
print('tube OD 6.0 vs aileron channel D 6.2 -> radial clearance 0.10 mm; servo spline D4.9 vs tube ID 4.0 -> interference')
print('servo/tail overlap',round(servo.intersect(tail).Volume(),1))
d=ail.distance(tail) if hasattr(ail,'distance') else None
print('min distance aileron-tail (neutral) mm:',None if d is None else round(d,2))
res=[]
axisP=cq.Vector(0,0,zs)
for ang in range(-60,61,5):
    r=ail.rotate(cq.Vector(0,cy,cz),cq.Vector(1,cy,cz),ang)
    res.append((ang,round(r.intersect(tail).Volume(),1)))
print('aileron rotation about tube axis -> overlap with tail (deg, mm3):',res)
free=[a for a,v in res if v<1]; print('collision-free deflection range deg:',min(free),max(free))
print('---- detail')
I=ail.intersect(tail)
for s in I.Solids():
    b=s.BoundingBox(); print(' ail/tail piece %.1f mm3 x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f'%(s.Volume(),b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax))
J=ail.intersect(servo); print('ail/servo overlap mm3',round(J.Volume(),1))
for s in J.Solids():
    b=s.BoundingBox(); print(' ail/servo piece %.1f x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f'%(s.Volume(),b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax))
# aileron profile near root: y,z extent at x=24,30,36,40,50
for xr in (23,26,30,34,38,45,60):
    sl=ail.intersect(cq.Workplane().box(0.4,40,80).translate((xr,0,200)).val())
    if sl.Volume()>0:
        b=sl.BoundingBox(); print('ail x=%d: y %.1f..%.1f z %.1f..%.1f'%(xr,b.ymin,b.ymax,b.zmin,b.zmax))
