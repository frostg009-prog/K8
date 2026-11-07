# lightened MOULD wing half: skin t, rib grid, perimeter screw bosses (M2), motors zone denser
import cadquery as cq, numpy as np, trimesh, sys, shapely.geometry as sg
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid
from OCP.TopTools import TopTools_ListOfShape
from OCP.BRepOffset import BRepOffset_Skin
from OCP.GeomAbs import GeomAbs_Intersection
name,role,tag,other=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]   # role: top (pilot holes) / bot (through holes)
T=1.6; RIB=1.2; PITCH=16.0; BOSS_R=2.8; PILOT=1.8; THRU=2.4; STEP_N=20.0; STEP_M=10.0
motor=np.array([95.0,95.0,62.5]) if tag=='big' else None
H=cq.importers.importStep(name+'.step').val()
P=max([f for f in H.Faces() if f.geomType()=='PLANE'],key=lambda f:f.Area())
n=P.normalAt(); n=np.array([n.x,n.y,n.z]); d=-n; c=P.Center(); c=np.array([c.x,c.y,c.z])
# shared in-plane basis (same for both halves)
n0=np.array([-0.7071,0.7071,0.0]) if abs(abs(n[0])-0.7071)<0.05 else n
u=np.cross([0,0,1.0],n0); u/=np.linalg.norm(u); v=np.cross(n0,u)
from shapely.ops import polygonize, unary_union
_v,_t=H.tessellate(0.1,0.3); _m=trimesh.Trimesh([(p.x,p.y,p.z) for p in _v],_t)
sec=_m.section(plane_origin=c+d*0.1,plane_normal=d)
cands=[]
for loop in sec.discrete:
    q=np.asarray(loop)-c; cands.append(sg.Polygon(np.c_[q@u,q@v]).buffer(0))
poly=max(cands,key=lambda g:g.area)
print('footprint area',round(poly.area),'valid',poly.is_valid,flush=True)
# ---- shell (vertical lowering of the skin by T + in-plane inset T; open at parting face)
def vec(a): return cq.Vector(*a)
dv=vec(d)
ins=poly.buffer(-T); ins=ins if ins.geom_type=='Polygon' else max(ins.geoms,key=lambda g:g.area)
plp=cq.Plane(origin=vec(c),xDir=vec(u),normal=dv)
prism=cq.Workplane(plp).polyline([(x,y) for x,y in list(ins.exterior.coords)[:-1]]).close().extrude(300).val()
Hl=H.translate(dv*(-T))
cav=Hl.intersect(prism)
for f in H.Faces():
    if f.geomType()=='CYLINDER':
        cyl=f._geomAdaptor().Cylinder(); r=cyl.Radius()
        if r<8:
            ax=cyl.Axis(); loc=ax.Location(); dr=ax.Direction()
            cav=cav.cut(cq.Solid.makeCylinder(r+T,600,cq.Vector(loc.X()-dr.X()*300,loc.Y()-dr.Y()*300,loc.Z()-dr.Z()*300),cq.Vector(dr.X(),dr.Y(),dr.Z())))
shell=H.cut(cav); print('shell valid',shell.isValid(),'solids',len(shell.Solids()),'vol %.1f -> %.1f'%(H.Volume()/1e3,shell.Volume()/1e3),flush=True)
# ---- ribs
pl=cq.Plane(origin=vec(c),xDir=vec(u),normal=vec(d))
nn=int(600/PITCH)
slab=cq.Workplane(pl).rect(600,600).extrude(40)
cells=cq.Workplane(pl).rarray(PITCH,PITCH,nn,nn).rect(PITCH-RIB,PITCH-RIB).extrude(40)
ribs=cav.cut(cells.val()); print('ribs vol %.1f'%(ribs.Volume()/1e3),flush=True)
# ---- boss positions
inner=poly.buffer(-(T+BOSS_R+0.5)); ring=inner.exterior if inner.geom_type=='Polygon' else max(inner.geoms,key=lambda g:g.area).exterior
vs,tr=H.tessellate(0.1,0.3); m=trimesh.Trimesh([(p.x,p.y,p.z) for p in vs],tr)
mc=None if motor is None else np.array([np.dot(motor-c,u),np.dot(motor-c,v)])
O2=cq.importers.importStep(other+'.step').val(); _v2,_t2=O2.tessellate(0.1,0.3); m2=trimesh.Trimesh([(p.x,p.y,p.z) for p in _v2],_t2)
pts=[]; s=0.0; Lr=ring.length
while s<Lr:
    p=ring.interpolate(s); q=np.array([p.x,p.y]); near=mc is not None and np.linalg.norm(q-mc)<45
    P3=c+u*q[0]+v*q[1]
    hit=m.ray.intersects_location([P3+d*0.05],[d])[0]
    dep=np.linalg.norm(hit-P3,axis=1).max() if len(hit) else 0
    h2=m2.ray.intersects_location([P3-d*0.05],[-d])[0]
    dep2=np.linalg.norm(h2-P3,axis=1).max() if len(h2) else 0
    if dep>4.5 and dep2>4.5: pts.append((P3,min(dep,14.0)))
    s+=STEP_M if near else STEP_N
if role=='bot':
    T_=cq.importers.importStep(f'wm_{tag}_top.step').val(); pts=[]
    for fc in T_.Faces():
        if fc.geomType()=='CYLINDER' and abs(fc._geomAdaptor().Cylinder().Radius()-PILOT/2)<0.01:
            l=fc._geomAdaptor().Cylinder().Axis().Location(); q=np.array([l.X(),l.Y(),l.Z()])
            P3=q-np.dot(q-c,n)*n
            if any(np.linalg.norm(P3-p)<0.05 for p,_ in pts): continue
            hit=m.ray.intersects_location([P3+d*0.05],[d])[0]; dep=np.linalg.norm(hit-P3,axis=1).max() if len(hit) else 6.0
            pts.append((P3,min(max(dep,4.5),14.0)))
print('bosses',len(pts),flush=True)
def safe(op,a,b,tag):
    for fz in (0.0,1e-3,1e-2):
        try:
            r=a.fuse(b,tol=fz) if (op=='fuse' and fz) else (a.fuse(b) if op=='fuse' else a.intersect(b))
            if r.isValid() and len(r.Solids())==1 and r.Volume()>=0.995*max(a.Volume(),b.Volume()): print(tag,'ok fuzzy',fz,flush=True); return r
        except Exception as e: print(tag,'fail',fz,str(e)[:40],flush=True)
    return None
body=safe('fuse',shell,ribs,'shell+ribs') or shell
bos=None
for P3,dep in pts:
    cyl=cq.Solid.makeCylinder(BOSS_R,dep+1,vec(P3),vec(d)); bos=cyl if bos is None else bos.fuse(cyl)
bos=bos.intersect(H)
nb=safe('fuse',body,bos,'body+bosses')
if nb is None:
    for P3,dep in pts:
        c1=cq.Solid.makeCylinder(BOSS_R,dep+1,vec(P3),vec(d)).intersect(H)
        t=safe('fuse',body,c1,'boss1');  body=t if t is not None else body
else: body=nb
print('after bosses vol %.1f valid %s'%(body.Volume()/1e3,body.isValid()),flush=True)
# holes
for P3,dep in pts:
    if role=='top': h=cq.Solid.makeCylinder(PILOT/2,min(dep*0.8,7.0),vec(P3-d*0.1),vec(d))
    else: h=cq.Solid.makeCylinder(THRU/2,dep+3,vec(P3-d*0.1),vec(d))
    try:
        nb=body.cut(h)
        if nb.isValid() and nb.Volume()>0.5*body.Volume(): body=nb
        else: print('hole skipped (invalid)')
    except Exception as e: print('hole skipped',str(e)[:40])
print('final valid',body.isValid(),'solids',len(body.Solids()),'vol %.1f cm3'%(body.Volume()/1e3),flush=True)
out=f'wm_{tag}_{role}'
cq.exporters.export(cq.Workplane(obj=body),out+'.step')
cq.exporters.export(cq.Workplane(obj=body),out+'.stl',tolerance=0.02,angularTolerance=0.08)
import pymeshfix
mm=trimesh.load(out+'.stl'); mm.merge_vertices()
if not mm.is_watertight:
    trimesh.repair.fill_holes(mm)
    if not mm.is_watertight:
        vv,ff=pymeshfix.clean_from_arrays(np.asarray(mm.vertices,dtype=np.float64),np.asarray(mm.faces,dtype=np.int32)); mm=trimesh.Trimesh(vv,ff)
    mm.export(out+'.stl')
print('stl watertight',mm.is_watertight,len(mm.faces),'vol',round(mm.volume/1e3,1))
