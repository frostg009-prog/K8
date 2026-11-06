# Full tail edit pipeline (same for the print tail and the mold base):
# central walls removed, servo pocket +0.25, insertion window 14.6 x (ears+2.4), tube passage, wire space,
# M2 screw bosses + pilots behind the servo ears, 4 THROUGH holes D3.2 for the Tail_Mount plate, protruding pads removed.
import cadquery as cq, math, trimesh, sys
SRC,OUT,ZTOP=sys.argv[1],sys.argv[2],float(sys.argv[3])
U='/root/.claude/uploads/8fc48cad-6552-5b7a-a937-c0e8e217cdce/'
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1); Y=cq.Vector(0,1,0)
tail=cq.importers.importStep(SRC).val(); V0=tail.Volume()
sv=cq.importers.importStep(U+'6feda855-______4x_MG90S______________1.STEP').val().Solids()
servo=sv[0].rotate(O,Z,-45)
PIV=cq.Vector(30,0,194.5)
lev=servo.rotate(PIV,PIV+Y,-7.5); dz=201.3-lev.Center().z; lev=lev.translate(cq.Vector(0,0,dz))
def Tinv(s): return s.translate(cq.Vector(0,0,-dz)).rotate(PIV,PIV+Y,7.5)
fl=[]
for xr in [x*0.5 for x in range(40,76)]:
    sl=lev.intersect(cq.Workplane().box(0.2,40,60).translate((xr,0,201)).val())
    if sl.Volume()>0 and sl.BoundingBox().zlen>30: fl.append(xr)
XF=min(fl); bb=lev.BoundingBox(); zmin,zmax=bb.zmin,bb.zmax; zc=(zmin+zmax)/2
zs=[f.Center().z for f in lev.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-2.45)<0.01 and f.Area()>8][0]
def safe(op,a,b,name):
    try:
        n=getattr(a,op)(b)
        if n.isValid() and len(n.Solids())>=1: return n
    except Exception as e: pass
    print('  rejected',name); return a
def env(s,c=0.25):
    e=s
    for v in ((0,c,0),(0,-c,0),(0,0,c),(0,0,-c),(-c,0,0)): e=safe('fuse',e,s.translate(cq.Vector(*v)),'env')
    return e.clean()
cut=[env(servo),
     Tinv(cq.Workplane().box(70,12.2+2.4,(zmax-zmin)+2.4,centered=(False,True,False)).translate((XF-0.1,0,zmin-1.2)).val()),
     Tinv(cq.Workplane('YZ').circle(4.0).extrude(40).translate((26,0,zs)).val()),
     Tinv(cq.Workplane().box(7,9,9.5,centered=(False,True,False)).translate((2.5,0,206.5)).val())]
H=9.0
res=safe('cut',tail,cq.Workplane().box(2*H,2*H,ZTOP-184,centered=(True,True,False)).edges('|Z').fillet(2.5).translate((0,0,184)).val(),'centre')
for k in range(4):
    for i,c in enumerate(cut): res=safe('cut',res,c.rotate(O,Z,45+90*k),'cut%d'%i)
# ear screw bosses + pilots
for dzp in (-14.0,14.0):
    zh=zc+dzp
    zlo,zhi=(zh-2.8,min(zh+2.8,zmin+4.6)) if dzp<0 else (max(zh-2.8,zmax-4.6),zh+2.8)
    pad=Tinv(cq.Workplane().box(8.4,13.2,zhi-zlo,centered=(False,True,False)).translate((14.0,0,zlo)).val())
    pil=Tinv(cq.Workplane('YZ').circle(0.85).extrude(-7.5).translate((XF-0.1,0,zh)).val())
    for k in range(4):
        res=safe('fuse',res,pad.rotate(O,Z,45+90*k),'boss').clean()
        res=safe('cut',res,pil.rotate(O,Z,45+90*k),'pilot')
# Tail_Mount: 4 through holes D3.2 (pattern 21.1 x 21.1) + remove the thin raised pads around them
for sx in (1,-1):
    for sy in (1,-1):
        res=safe('cut',res,cq.Workplane('XY').circle(3.4).extrude(3.2).translate((sx*10.55,sy*10.55,187.9)).val(),'pad')
        res=safe('cut',res,cq.Workplane('XY').circle(1.6).extrude(9.0).translate((sx*10.55,sy*10.55,183.5)).val(),'hole')
print(SRC,'->',OUT,'valid',res.isValid(),'solids',len(res.Solids()),'vol %.1f -> %.1f'%(V0/1000,res.Volume()/1000))
print('servo overlap',[round(res.intersect(s).Volume(),1) for s in sv])
ax=cq.Vector(math.cos(math.radians(7.5)),0,-math.sin(math.radians(7.5)))
r=res.rotate(O,Z,-45); v0=r.Volume(); bad=[]
for d in [x*1.5 for x in range(0,27)]:
    ov=v0-r.cut(servo.translate(ax*d)).Volume()
    if ov>1: bad.append((d,round(ov)))
print('insert sweep collisions:',bad or 'none')
for sx,sy in ((1,1),(-1,1),(1,-1),(-1,-1)):
    print(' mount hole',(sx*10.55,sy*10.55),''.join('#' if res.isInside(cq.Vector(sx*10.55,sy*10.55,183.5+k*0.5)) else '.' for k in range(18)))
cq.exporters.export(cq.Workplane(obj=res),OUT)
vs,tr=res.tessellate(0.02,0.1); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export(OUT.replace('.step','.stl'))
