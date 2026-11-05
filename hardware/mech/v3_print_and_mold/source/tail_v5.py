import cadquery as cq, math, trimesh
U='/root/.claude/uploads/8fc48cad-6552-5b7a-a937-c0e8e217cdce/'
Z=cq.Vector(0,0,1); O=cq.Vector(0,0,0)
t0=cq.importers.importStep('in/tail.step').val()
sv=cq.importers.importStep(U+'6feda855-______4x_MG90S______________1.STEP').val().Solids()[0]
loc=sv.rotate(O,Z,-45)                              # radial = +X
def shaft_dir(s):
    for f in s.Faces():
        if f.geomType()=='CYLINDER':
            cy=f._geomAdaptor().Cylinder()
            if abs(cy.Radius()-2.45)<0.01 and f.Area()>8: d=cy.Axis().Direction(); return d.X(),d.Y(),d.Z()
PIV=cq.Vector(30,0,194.5)
best=None
for a in (7.5,-7.5):
    r=loc.rotate(PIV,PIV+cq.Vector(0,1,0),a); d=shaft_dir(r)
    print('rot',a,[round(v,3) for v in d])
    if best is None or abs(d[2])<abs(best[1][2]): best=(r,d)
servo=best[0]
dz=201.3-servo.Center().z; servo=servo.translate(cq.Vector(0,0,dz))
bb=servo.BoundingBox(); print('servo levelled: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f'%(bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax))
def env(s,c=0.25):                                   # servo + clearance (Minkowski with a cross of shifts)
    e=s
    for v in ((0,c,0),(0,-c,0),(0,0,c),(0,0,-c),(-c,0,0)): e=e.fuse(s.translate(cq.Vector(*v)))
    return e.clean()
E_=env(servo)
zs=[f.Center().z for f in servo.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-2.45)<0.01 and f.Area()>8][0]
print('shaft axis z =',round(zs,2))
# wire space: servo wire leaves the high-z end on the inner side -> free box towards the centre channel
wire=cq.Workplane().box(7,9,9.5,centered=(False,True,False)).translate((2.5,0,206.5)).val()
# tube passage: shaft tip radius ~ 36.7 ; carbon tube OD6 -> hole OD8 from the boss outward
shaft=cq.Workplane('YZ').circle(4.0).extrude(30).translate((29,0,zs)).val()
# flange (ears) radial range of the levelled servo: slices where z-extent > 30
fl=[]
for xr in [x*0.5 for x in range(40,76)]:
    sl=servo.intersect(cq.Workplane().box(0.2,40,60).translate((xr,0,201)).val())
    if sl.Volume()>0:
        b=sl.BoundingBox()
        if b.zlen>30: fl.append(xr)
XF_IN=min(fl); XF_OUT=max(fl); print('flange radial range',XF_IN,XF_OUT)
zmin,zmax=servo.BoundingBox().zmin,servo.BoundingBox().zmax
# insertion window through the shell: everything outward of the flange inner face, servo width+1.2, ears length+1.2
win=cq.Workplane().box(60,12.2+1.4,(zmax-zmin)+1.4,centered=(False,True,False)).translate((XF_IN-0.1,0,zmin-0.7)).val()
H=9.0
chan=cq.Workplane().box(2*H,2*H,215.5-184,centered=(True,True,False)).edges('|Z').fillet(2.5).translate((0,0,184)).val()
res=t0.cut(chan)
for k in range(4):
    a=45+90*k
    for cutter in (E_,wire,shaft,win): res=res.cut(cutter.rotate(O,Z,a))
for k in range(4):
    a=45+90*k
    for dz in (-14.0,14.0):
        ph=cq.Workplane('YZ').circle(0.85).extrude(-7).translate((XF_IN-0.1,0,(zmin+zmax)/2+dz)).val()
        res=res.cut(ph.rotate(O,Z,a))
print('valid',res.isValid(),'solids',len(res.Solids()),'vol cm3',round(res.Volume()/1000,1))
ov=sum(res.intersect(servo.rotate(O,Z,45+90*k)).Volume() for k in range(4)); print('servo/tail overlap mm3',round(ov,1))
cq.exporters.export(cq.Workplane(obj=res),'tail_v5.step')
vs,tr=res.tessellate(0.02,0.1); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export('tail_v5.stl')
# assembly check export: servos + carbon tubes
asm=[servo.rotate(O,Z,45+90*k) for k in range(4)]
tube=cq.Workplane('YZ').circle(3.0).extrude(45).translate((34,0,zs)).val()
tubes=[tube.rotate(O,Z,45+90*k) for k in range(4)]
cq.exporters.export(cq.Workplane(obj=cq.Compound.makeCompound(asm+tubes)),'servos_tubes_v4.step')
for n,objs in (('servos',asm),('tubes',tubes)):
    for i,o in enumerate(objs):
        vs,tr=o.tessellate(0.05,0.2); trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr).export(f'{n}{i}.stl')
# insertion sweep: servo moved from outside (dx=+30) to seat (dx=0) along its radial axis; any overlap = cannot be inserted
bad=[]
for dx in range(30,-1,-2):
    mv=servo.translate(cq.Vector(dx,0,0)).rotate(O,Z,45)
    v=res.intersect(mv).Volume()
    if v>1: bad.append((dx,round(v,1)))
print('INSERT SWEEP collisions (dx, mm3):',bad if bad else 'none - servo can be inserted from outside')
