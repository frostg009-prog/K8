import cadquery as cq, math, trimesh, numpy as np
U='/root/.claude/uploads/8fc48cad-6552-5b7a-a937-c0e8e217cdce/'
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1); Y=cq.Vector(0,1,0)
t_old=cq.importers.importStep('in/tailM.step').val(); t_new=cq.importers.importStep('tail_v6.step').val()
servo=cq.importers.importStep(U+'6feda855-______4x_MG90S______________1.STEP').val().Solids()[0]
wing=cq.importers.importStep('in/wingM.step').val()
ax=cq.Vector(math.cos(math.radians(7.5)),0,-math.sin(math.radians(7.5)))
def sweep(tail,name):
    s=servo.rotate(O,Z,-45); bad=[]
    for d in range(40,-1,-2):
        v=tail.rotate(O,Z,-45).intersect(s.translate(ax*d)).Volume()
        if v>1: bad.append((d,round(v)))
    print(name,'insertion sweep collisions (mm outward, mm3):',bad[:12],'...' if len(bad)>12 else '')
sweep(t_old,'user tail (latest) ->'); sweep(t_new,'tail v6 ->')
tl=t_new.rotate(O,Z,-45); sl=servo.rotate(O,Z,-45); wl=wing.rotate(O,Z,-45)
# shaft axis in local frame
zs=[f.Center() for f in sl.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-2.45)<0.01 and f.Area()>8][0]
cy=[f for f in wl.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]
cc=[f.Center() for f in cy]; wc=cq.Vector(sum(p.x for p in cc)/2,sum(p.y for p in cc)/2,sum(p.z for p in cc)/2)
d=cq.Vector(cy[0]._geomAdaptor().Cylinder().Axis().Direction().X(),cy[0]._geomAdaptor().Cylinder().Axis().Direction().Y(),cy[0]._geomAdaptor().Cylinder().Axis().Direction().Z())
print('wing channel axis dir',[round(v,3) for v in (d.x,d.y,d.z)],'point',[round(v,1) for v in (wc.x,wc.y,wc.z)])
# perpendicular distance servo shaft point -> channel axis
v=zs-wc; dn=d.normalized(); cross=v.cross(dn); print('servo shaft point to wing channel axis distance mm:',round(cross.Length,3))
# tube along the channel axis
L0=cq.Vector(wc.x-dn.x*(wc.x-34)/dn.x,wc.y,wc.z-dn.z*(wc.x-34)/dn.x)   # point on axis at x=34
tube=cq.Solid.makeCylinder(3.0,200.0,L0,dn)
print('tube/wing overlap',round(tube.intersect(wl).Volume(),1),' tube/tail',round(tube.intersect(tl).Volume(),1),' tube/servo',round(tube.intersect(sl).Volume(),1))
print('wing/tail overlap at neutral mm3',round(wl.intersect(tl).Volume(),1),'  wing/servo',round(wl.intersect(sl).Volume(),1),' wing-tail min gap',round(wl.distance(tl),2))
res=[]
for a in range(-40,41,10):
    r=wl.rotate(wc,wc+dn,a); res.append((a,round(r.intersect(tl).Volume(),1)))
print('wing rotation about tube axis -> overlap with tail:',res)
