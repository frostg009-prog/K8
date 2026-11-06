import cadquery as cq, numpy as np, math
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1)
ld=lambda f: cq.importers.importStep(f).val()
o={n:ld(f'oldasm/{n}.step') for n in ('wing_big_q1','aileron_old_q1','plate_bottom_old','plate_top_old','tail_mount','holder_front','holder_big','batt_support','battery','side_plate_top','side_plate_bot','bulkhead','camera_tf2')}
tail=ld('tail_print_final.step'); nose=ld('nose_v3.step'); ail=ld('eleron_v4.step')
U='/root/.claude/uploads/8fc48cad-6552-5b7a-a937-c0e8e217cdce/'
sv=cq.importers.importStep(U+'6feda855-______4x_MG90S______________1.STEP').val().Solids()
def ov(a,b):
    try: return round(a.intersect(b).Volume(),1)
    except Exception: return -1
# 1) DXF plates (2.5 mm) vs old plates
def plate(name,y0,t=2.5):
    f=cq.importers.importDXF(f'frame/{name}.dxf',tol=1e-3).faces().val()
    s=cq.Workplane('XY').add(f).wires().toPending().extrude(t).val().rotate(O,cq.Vector(1,0,0),90)
    b=s.BoundingBox(); return s.translate(cq.Vector(0,y0-b.ymin,0))
top=plate('top',20.8); bot=plate('bottom',-23.3)
for n,p,q in (('top',top,o['plate_top_old']),('bottom',bot,o['plate_bottom_old'])):
    print('plate',n,'DXF vol %.1f, old-asm vol %.1f, common %.1f cm3'%(p.Volume()/1000,q.Volume()/1000,p.intersect(q).Volume()/1000))
cq.exporters.export(cq.Workplane(obj=top),'frame/rama_verh_2.5mm.step'); cq.exporters.export(cq.Workplane(obj=bot),'frame/rama_niz_2.5mm.step')
cq.exporters.export(cq.Workplane(obj=top),'frame/rama_verh_2.5mm.stl',tolerance=0.01,angularTolerance=0.1); cq.exporters.export(cq.Workplane(obj=bot),'frame/rama_niz_2.5mm.stl',tolerance=0.01,angularTolerance=0.1)
# 2) interference matrix (new parts vs frame/mounts)
new={'Hvost(new)':tail,'Nos(new)':nose}
for k in range(4): new['Eleron%d'%k]=ail.rotate(O,Z,90*k)
others={'Rama_verh':top,'Rama_niz':bot,'Tail_Mount':o['tail_mount'],'Derzh_big':o['holder_big'],'Derzh_front':o['holder_front'],'Opora_AKB':o['batt_support'],'AKB':o['battery'],'Kamera_TF2':o['camera_tf2'],'Peregorodka':o['bulkhead']}
for k in range(4): others['Krylo_big%d'%k]=o['wing_big_q1'].rotate(O,Z,90*k)
print('\nINTERFERENCE (mm3), non-zero only:')
for a,A in new.items():
    for b,B in others.items():
        v=ov(A,B)
        if v!=0: print('  %-10s x %-12s %s'%(a,b,v))
for i,s in enumerate(sv):
    for b,B in others.items():
        v=ov(s,B)
        if v!=0: print('  Servo%d x %s %s'%(i,b,v))
# 3) tube axis vs big-wing hole
a0=ail
cy=[f for f in a0.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]
P=np.array([[f.Center().x,f.Center().y,f.Center().z] for f in cy]).mean(0); d=cy[0]._geomAdaptor().Cylinder().Axis().Direction(); D=np.array([d.X(),d.Y(),d.Z()]); D/=np.linalg.norm(D)
if D[0]<0: D=-D
W=o['wing_big_q1']
print('\nbig wing cylinders r 2.8..4:')
for f in W.Faces():
    if f.geomType()=='CYLINDER':
        c=f._geomAdaptor().Cylinder(); r=c.Radius()
        if 2.8<r<4.2 and f.Area()>5:
            dd=c.Axis().Direction(); dv=np.array([dd.X(),dd.Y(),dd.Z()]); cc=f.Center(); C=np.array([cc.x,cc.y,cc.z])
            ang=math.degrees(math.acos(min(1,abs(dv@D)))); dist=np.linalg.norm(np.cross(C-P,D))
            print('  r=%.2f centre (%.1f,%.1f,%.1f) angle to tube axis %.2f deg, distance from tube axis %.2f mm'%(r,*C,ang,dist))
# 4) tube through the wing hole: tube solid along the axis 34..260 mm
base=cq.Vector(*P)-cq.Vector(*D)*80
tube=cq.Solid.makeCylinder(3.0,330,base,cq.Vector(*D))
print('\ntube x wing overlap',ov(tube,W),' tube x aileron',ov(tube,a0),' tube x tail',ov(tube,tail))
# 5) wing vs aileron moving +-30
for ang in (-30,-15,0,15,30):
    print('aileron rot %+d: overlap with wing'%ang, ov(a0.rotate(cq.Vector(*P),cq.Vector(*(P+D)),ang),W))
