import cadquery as cq, math, trimesh
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1)
CLR=3.0; SPAN=40
tail=cq.importers.importStep('tail_v11.step').val().rotate(O,Z,-45)
wing0=cq.importers.importStep('in/wingM.step').val()
wl=wing0.rotate(O,Z,-45)
cy=[f for f in wl.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]
cc=[f.Center() for f in cy]; wc=cq.Vector(sum(p.x for p in cc)/2,sum(p.y for p in cc)/2,sum(p.z for p in cc)/2)
d=cy[0]._geomAdaptor().Cylinder().Axis().Direction(); dn=cq.Vector(d.X(),d.Y(),d.Z()).normalized()
if dn.x<0: dn=dn*-1
zone=cq.Workplane().box(50,80,80,centered=(False,True,False)).translate((10,0,178)).val()
root=tail.intersect(zone); print('tail root zone vol',round(root.Volume()/1000,1))
def gap_profile(ail,label):
    out=[]
    for a in range(-SPAN,SPAN+1,5):
        out.append((a,round(ail.rotate(wc,wc+dn,a).distance(tail),2)))
    print(label,out); return min(g for _,g in out)
g0=gap_profile(wl,'BEFORE gaps (deg, mm):')
ail=wl; fails=0
import itertools; shifts=[(0,0,0)]+[(CLR*x,CLR*y,CLR*z) for x,y,z in itertools.product((-1,0,1),repeat=3) if (x,y,z)!=(0,0,0) and abs(x)+abs(y)+abs(z)<=2]
for a in range(-SPAN-5,SPAN+6,5):
    base=root.rotate(wc,wc+dn,-a)                 # tail seen from the wing frame when the wing is turned by +a
    for s in shifts:
        try:
            n=ail.cut(base.translate(cq.Vector(*s)))
            if n.isValid() and n.Volume()>0.9*wl.Volume(): ail=n
            else: fails+=1
        except Exception: fails+=1
print('cut failures',fails,' volume cm3',round(wl.Volume()/1000,2),'->',round(ail.Volume()/1000,2),'solids',len(ail.Solids()))
g1=gap_profile(ail,'AFTER  gaps (deg, mm):')
print('min gap before %.2f -> after %.2f mm over +-%d deg'%(g0,g1,SPAN))
glob=ail.rotate(O,Z,45)
cq.exporters.export(cq.Workplane(obj=glob),'eleron_v6.step')
vs,tr=glob.tessellate(0.03,0.15); m=trimesh.Trimesh([(x.x,x.y,x.z) for x in vs],tr); m.merge_vertices(); m.export('eleron_v6.stl'); print('stl ok',len(m.faces))
