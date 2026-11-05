import cadquery as cq, trimesh, numpy as np
exec(open('fitcheck.py').read().split("print('shaft axis z'")[0])   # reuse set-up (tail, servo, ail, zs ...)
zs=[f.Center().z for f in servo.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-2.45)<0.01 and f.Area()>8][0]
A0=cq.Vector(0,0,zs); A1=cq.Vector(1,0,zs)
# region of the tail that can touch the aileron root: x<45, z>212
zone=cq.Workplane().box(45,60,40,centered=(False,True,False)).translate((0,0,212)).val()
root=tail.intersect(zone)
ail2=ail; fails=0
for ang in range(-32,33,4):                      # swept envelope of +-30 deg deflection (+2 deg margin)
    for dx in (0.0,0.5):
        r=root.rotate(A0,A1,ang).translate(cq.Vector(dx,0,0))
        try:
            n=ail2.cut(r)
            if n.isValid() and n.Volume()>0.8*ail.Volume(): ail2=n
            else: fails+=1
        except Exception as e: fails+=1
print('cut failures',fails)
print('aileron volume cm3',round(ail.Volume()/1000,2),'->',round(ail2.Volume()/1000,2),'solids',len(ail2.Solids()),'valid',ail2.isValid())
bad=[(a,round(ail2.rotate(A0,A1,a).intersect(tail).Volume(),1)) for a in range(-30,31,5)]
print('after trim overlap with tail (deg,mm3):',bad)
print('overlap with servo:',round(ail2.intersect(servo).Volume(),1))
# back to global diag frames for 4 positions
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1)
def to_stl(s,n):
    vs,tr=s.tessellate(0.05,0.2); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export(n); return m
cq.exporters.export(cq.Workplane(obj=ail2.rotate(O,Z,45)),'aileron_trimmed_leveled.step'); to_stl(ail2.rotate(O,Z,45),'aileron_trimmed_leveled.stl')
tube=cq.Workplane('YZ').circle(3.0).circle(2.0).extrude(234.5-34).translate((34,0,zs)).val()
parts={'tail':cq.importers.importStep('tail_v5.step').val(),'servo':servo,'tube':tube,'ail':ail2}
allp=[]
for k in range(4):
    a=45+90*k
    for n in ('servo','tube','ail'): allp.append(parts[n].rotate(O,Z,a))
allp.append(parts['tail'])
cq.exporters.export(cq.Workplane(obj=cq.Compound.makeCompound(allp)),'full_assembly_v5.step')
for n,objs in (('tail',[parts['tail']]),('servo',[parts['servo'].rotate(O,Z,45+90*k) for k in range(4)]),('tube',[parts['tube'].rotate(O,Z,45+90*k) for k in range(4)]),('ail',[ail2.rotate(O,Z,45+90*k) for k in range(4)])):
    ms=[to_stl(o,f'asm_{n}{i}.stl') for i,o in enumerate(objs)]
