import cadquery as cq, numpy as np, math, sys, glob
side=sys.argv[1]; CLR=1.0
tag={'PLUS_Y':'PlusY','MINUS_Y':'MinusY','PLUS_X':'PlusX','MINUS_X':'MinusX'}[side]
rot={'PLUS_Y':0,'PLUS_X':90,'MINUS_Y':180,'MINUS_X':-90}[side]
O=cq.Vector(0,0,0); Zv=cq.Vector(0,0,1)
segf=sorted(glob.glob(f'p12/{tag}_*.step')); seg=[cq.importers.importStep(f).val() for f in segf]
if side=='MINUS_Y': seg=[cq.importers.importStep('panel180_balance_slot.step').val() if 'z0_to_180' in f else s for f,s in zip(segf,seg)]
R_OUT=35.41; R_IN=32.74; HW=24.84
z0=-266.0 if side in ('PLUS_Y','MINUS_Y') else -201.5; z1=180.0
th=math.asin(HW/R_OUT); p=lambda r,a:(r*math.sin(a),r*math.cos(a))
shell=(cq.Workplane('XY').workplane(offset=z0).moveTo(*p(R_OUT,-th)).threePointArc(p(R_OUT,0),p(R_OUT,th)).lineTo(*p(R_IN,th)).threePointArc(p(R_IN,0),p(R_IN,-th)).close().extrude(z1-z0).val())
shell=shell.rotate(O,Zv,-rot)          # into the side position (global frame)
print(side,'base shell vol %.2f'%(shell.Volume()/1e3),flush=True)
# exact openings from the originals (window / balance-plug slot): void = (shell ∩ bbox) - original, near the centre line only
out=shell
ZONES={'PLUS_Y':[('z0_to_180',(-14,14,30,60))],'MINUS_Y':[('z0_to_180',(-14,14,70,110))]}.get(side,[])
for key,(x0,x1,zA,zB) in ZONES:
    s_=[s for f,s in zip(segf,seg) if key in f][0]
    zb=cq.Solid.makeBox(x1-x0,20,zB-zA,cq.Vector(x0,25,zA)).rotate(O,Zv,-rot)
    for v in shell.intersect(zb).cut(s_).Solids():
        vb=v.rotate(O,Zv,rot).BoundingBox()
        if v.Volume()>20 and vb.ylen>2.0:
            print('  exact opening: x %.1f..%.1f z %.1f..%.1f vol %.0f mm3'%(vb.xmin,vb.xmax,vb.zmin,vb.zmax,v.Volume()),flush=True); out=out.cut(v)
# clearance cut-outs for every assembly part that crosses the panel (dilated by CLR)
import pickle
parts=[]
for f in sorted(glob.glob('asm/Drone_Assembly_4_large_panels_parts_in_place/*.step')):
    n=f.split('/')[-1]
    if any(k in n for k in ('Body_Panel','Nose','Tail.','Carbon','Battery.','Servo')): continue
    s=cq.importers.importStep(f).val(); 
    sb=s.BoundingBox(); ob=out.BoundingBox()
    if sb.xmax<ob.xmin-2 or sb.xmin>ob.xmax+2 or sb.ymax<ob.ymin-2 or sb.ymin>ob.ymax+2 or sb.zmax<ob.zmin-2 or sb.zmin>ob.zmax+2: continue
    if s.intersect(cq.Solid.makeBox(ob.xlen+4,ob.ylen+4,ob.zlen+4,cq.Vector(ob.xmin-2,ob.ymin-2,ob.zmin-2))).Volume()<1e-3: continue
    parts.append((n,s))
print('  parts crossing the panel zone:',[n for n,_ in parts],flush=True)
shifts=[(0,0,0)]+[(a*CLR,b*CLR,c*CLR) for a,b,c in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(.7,.7,0),(-.7,.7,0),(.7,-.7,0),(-.7,-.7,0))]
for n,s in parts:
    v0=out.Volume()
    for sh in shifts:
        try:
            r=out.cut(s.translate(cq.Vector(*sh)))
            if r.isValid() and r.Volume()>0.5*v0: out=r
        except Exception as e: print('   cut fail',n,sh)
    print('  cut',n,'removed %.0f mm3'%(v0-out.Volume()),flush=True)
out=max(out.Solids(),key=lambda x:x.Volume())
if side in ('PLUS_X','MINUS_X'):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
    from OCP.TopTools import TopTools_ListOfShape
    lou=[s for f,s in zip(segf,seg) if 'z-266_to_-201' in f][0]
    fz=BRepAlgoAPI_Fuse(); a1=TopTools_ListOfShape(); t1=TopTools_ListOfShape(); a1.Append(out.wrapped); t1.Append(lou.wrapped); fz.SetArguments(a1); fz.SetTools(t1); fz.SetFuzzyValue(0.05); fz.Build()
    fu=cq.Shape.cast(fz.Shape()).clean(); assert len(fu.Solids())==1, 'louvre not joined'; out=fu.Solids()[0]; print('  louvre block fused, solids',len(fu.Solids()),flush=True)
print('FINAL',side,'valid',out.isValid(),'vol %.2f cm3'%(out.Volume()/1e3),flush=True)
cq.exporters.export(cq.Workplane(obj=out),f'panel3_{side}.step')
