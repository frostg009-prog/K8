# Tail v10 - clean parametric rebuild for printing AND a simple mould:
#   outer = solid of revolution (user's outer profile) -> cavity pulled along the axis
#   open end: socket bore + flat plate + round central channel + 4 holes (all straight along Z) -> core from the open end
#   4 servo pockets = straight STEPPED prisms along each servo axis (tilted 7.5 deg as in user's model) -> 4 side slides through the windows
import cadquery as cq, trimesh, numpy as np, math
U='/root/.claude/uploads/8fc48cad-6552-5b7a-a937-c0e8e217cdce/'
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1); Y=cq.Vector(0,1,0)
# ---------- outer profile from the user's tail (plane y=0, x>0 : no slots there)
PR=np.load('tail_profile.npy'); ZTIP=272.6
prof=[(float(r),float(z)) for z,r in PR[::2]]+[(0.0,ZTIP)]
pts=[(0.0,175.0)]+[(r,z) for r,z in prof]
outer=cq.Workplane('XZ').polyline(pts).close().revolve(360,(0,0,0),(0,1,0)).val()
print('outer valid',outer.isValid(),'vol %.1f'%(outer.Volume()/1000),'tip z %.1f'%ZTIP, 'r(175)=%.2f'%prof[0][0])
# ---------- open end: socket bore r=32.5 up to the plate, plate 185.2..188.7
R_SOCK=32.5; Z_PLATE0=185.2; Z_PLATE1=188.7
body=outer.cut(cq.Workplane('XY').circle(R_SOCK).extrude(Z_PLATE0-170).translate((0,0,170)).val())
# central round channel D18 (wires), straight along Z, to z=219
body=body.cut(cq.Workplane('XY').circle(9.0).extrude(255-170).translate((0,0,170)).val())   # straight core pin from the open end
# lightening cavities between shell and servo holder, open to the open end (formed by the axial core = 'upper' mould part)
PRr=np.load('tail_profile.npy'); rin=lambda z: float(np.interp(z,PRr[:,0],PRr[:,1]))-2.5
# one smooth conical outer wall (follows the skin at 2.5 mm, shrinks with depth -> pullable from the open end, no steps)
disk=cq.Workplane('XZ').polyline([(11.0,Z_PLATE0),(min(rin(Z_PLATE0+0.1),32.4),Z_PLATE0),(rin(225.0),225.0),(11.0,225.0)]).close().revolve(360,(0,0,0),(0,1,0)).val()
print('cavity cone r %.1f -> %.1f'%(min(rin(Z_PLATE0+0.1),32.4),rin(225.0)))
for k in range(4):
    strip=cq.Workplane('XY').rect(200,2*8.9).extrude(100).translate((0,0,150)).rotate((0,0,0),(0,0,1),45+90*k).val()
    disk=disk.cut(strip)
print('lightening cavities',len(disk.Solids()),'vol %.1f'%(disk.Volume()/1000))
body=body.cut(disk)
# ---------- servo frame (user's placement, 7.5 deg)
sv=cq.importers.importStep(U+'6feda855-______4x_MG90S______________1.STEP').val().Solids()
servo=sv[0].rotate(O,Z,-45)
PIV=cq.Vector(30,0,194.5)
lev=servo.rotate(PIV,PIV+Y,-7.5); dz=201.3-lev.Center().z; lev=lev.translate(cq.Vector(0,0,dz))
def Tinv(x): return x.translate(cq.Vector(0,0,-dz)).rotate(PIV,PIV+Y,7.5)
bb=lev.BoundingBox(); zmin,zmax=bb.zmin,bb.zmax; zc=(zmin+zmax)/2
sl=lev.intersect(cq.Workplane().box(0.4,40,60).translate((15,0,201)).val()).BoundingBox(); bz0,bz1=sl.zmin,sl.zmax
XF=22.4; C=0.3
print('servo body z %.1f..%.1f  ears z %.1f..%.1f'%(bz0,bz1,zmin,zmax))
inner=cq.Workplane().box(XF-0.0,2*(6.1+C),(bz1-bz0)+2*C,centered=(False,True,False)).translate((0.0,0,bz0-C)).val()      # body part (reaches the central channel)
outerslot=cq.Workplane().box(60,2*7.3,(zmax-zmin)+2*1.2,centered=(False,True,False)).translate((XF,0,zmin-1.2)).val()       # ears + boss + aileron collar clearance, opens through the shell
pilots=[cq.Workplane('YZ').circle(0.85).extrude(-7.5).translate((XF,0,zc+d)).val() for d in (-14.0,14.0)]                  # M2 screws for the ears (moulded by slide pins)
cut=[Tinv(inner),Tinv(outerslot)]+[Tinv(p) for p in pilots]
for k in range(4):
    for c in cut: body=body.cut(c.rotate(O,Z,45+90*k))
# ---------- 4 through holes D3.2 for the Tail Mount (pattern 21.1); they open into the servo pockets -> M3 nut from inside the pocket
for sx in (1,-1):
    for sy in (1,-1):
        body=body.cut(cq.Workplane('XY').circle(1.6).extrude(12).translate((sx*10.55,sy*10.55,183.0)).val())
body=max(body.Solids(),key=lambda x:x.Volume())
print('tail v10 valid',body.isValid(),'solids',len(body.Solids()),'vol %.1f cm3'%(body.Volume()/1000))
print('servo overlap',[round(body.intersect(x).Volume(),1) for x in sv])
ax=cq.Vector(math.cos(math.radians(7.5)),0,-math.sin(math.radians(7.5))); r=body.rotate(O,Z,-45); v0=r.Volume(); bad=[]
for d in [x*1.5 for x in range(0,27)]:
    ov=v0-r.cut(servo.translate(ax*d)).Volume()
    if ov>1: bad.append((d,round(ov)))
print('insert sweep collisions:',bad or 'none')
for sx,sy in ((1,1),(-1,-1)): print(' mount hole column',''.join('#' if body.isInside(cq.Vector(sx*10.55,sy*10.55,183.0+k*0.5)) else '.' for k in range(20)))
cq.exporters.export(cq.Workplane(obj=body),'tail_v11.step')
cq.exporters.export(cq.Workplane(obj=body),'tail_v11.stl',tolerance=0.02,angularTolerance=0.1)
mm=trimesh.load('tail_v11.stl'); print('stl watertight',mm.is_watertight,'bodies',len(mm.split(only_watertight=False)))
