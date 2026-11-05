# tail v6: based on the USER'S LATEST tail (f5286cce..MG90S.STEP, already has MG90S pockets) - keeps its servo geometry (as designed, tilted 7.5 deg),
# removes the central walls completely, enlarges the shell window so the servo (with ears) can be inserted from outside, adds M2 pilots.
import cadquery as cq, math, trimesh
U='/root/.claude/uploads/8fc48cad-6552-5b7a-a937-c0e8e217cdce/'
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1); Y=cq.Vector(0,1,0)
tail=cq.importers.importStep('in/tailM.step').val()
sv0=cq.importers.importStep(U+'6feda855-______4x_MG90S______________1.STEP').val().Solids()[0]
servo=sv0.rotate(O,Z,-45)                       # actual (tilted) servo, local frame: +X = radial
PIV=cq.Vector(30,0,194.5)
lev=servo.rotate(PIV,PIV+Y,-7.5); dz=201.3-lev.Center().z; lev=lev.translate(cq.Vector(0,0,dz))
def Tinv(s): return s.translate(cq.Vector(0,0,-dz)).rotate(PIV,PIV+Y,7.5)       # levelled frame -> actual frame
chk=Tinv(lev); print('frame check: centre diff',[round(a-b,3) for a,b in zip((chk.Center().x,chk.Center().y,chk.Center().z),(servo.Center().x,servo.Center().y,servo.Center().z))])
# servo flange / extents in the levelled frame
fl=[]
for xr in [x*0.5 for x in range(40,76)]:
    sl=lev.intersect(cq.Workplane().box(0.2,40,60).translate((xr,0,201)).val())
    if sl.Volume()>0 and sl.BoundingBox().zlen>30: fl.append(xr)
XF_IN=min(fl); bb=lev.BoundingBox(); zmin,zmax=bb.zmin,bb.zmax
zs=[f.Center().z for f in lev.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-2.45)<0.01 and f.Area()>8][0]
print('flange x',XF_IN,'servo z',round(zmin,1),round(zmax,1),'shaft z(lev)',round(zs,1))
def env(s,c=0.25):
    e=s
    for v in ((0,c,0),(0,-c,0),(0,0,c),(0,0,-c),(-c,0,0)): e=e.fuse(s.translate(cq.Vector(*v)))
    return e.clean()
cutters_local=[]
cutters_local.append(env(servo))                                                        # pocket = servo + 0.25
win=cq.Workplane().box(70,12.2+2.4,(zmax-zmin)+2.4,centered=(False,True,False)).translate((XF_IN-0.1,0,zmin-1.2)).val()
cutters_local.append(Tinv(win))                                                         # insertion window along the servo axis
shaft=cq.Workplane('YZ').circle(4.0).extrude(40).translate((26,0,zs)).val()
cutters_local.append(Tinv(shaft))                                                       # tube passage
wire=cq.Workplane().box(7,9,9.5,centered=(False,True,False)).translate((2.5,0,206.5)).val()
cutters_local.append(Tinv(wire))                                                        # wire space at the inner end
for dzp in (-14.0,14.0):                                                                # M2 pilots in the ledge
    cutters_local.append(Tinv(cq.Workplane('YZ').circle(0.85).extrude(-7).translate((XF_IN-0.1,0,(zmin+zmax)/2+dzp)).val()))
H=9.0
chan=cq.Workplane().box(2*H,2*H,219.0-184,centered=(True,True,False)).edges('|Z').fillet(2.5).translate((0,0,184)).val()
res=tail.cut(chan)
for k in range(4):
    for c in cutters_local: res=res.cut(c.rotate(O,Z,45+90*k))
print('valid',res.isValid(),'solids',len(res.Solids()),'vol',round(tail.Volume()/1000,1),'->',round(res.Volume()/1000,1))
sv=[servo.rotate(O,Z,45+90*k) for k in range(4)]
print('servo overlap with new tail mm3:',[round(res.intersect(s).Volume(),1) for s in sv])
bad=[]
for d in range(40,-1,-2):                       # insertion sweep along the real servo axis (tilted)
    ax=cq.Vector(math.cos(math.radians(7.5)),0,-math.sin(math.radians(7.5)))
    mv=servo.translate(ax*d).rotate(O,Z,45)
    v=res.intersect(mv).Volume()
    if v>1: bad.append((d,round(v,1)))
print('INSERT SWEEP along servo axis:',bad if bad else 'no collisions - servo can be inserted from outside')
cq.exporters.export(cq.Workplane(obj=res),'tail_v6.step')
vs,tr=res.tessellate(0.02,0.1); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export('tail_v6.stl'); print('stl watertight',m.is_watertight)
