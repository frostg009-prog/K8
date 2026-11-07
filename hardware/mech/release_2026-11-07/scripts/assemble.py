import cadquery as cq, numpy as np, trimesh, glob, sys, os
O=cq.Vector(0,0,0); Z=cq.Vector(0,0,1)
new=cq.importers.importStep('oldasm/new1.step').val().Solids()
old=cq.importers.importStep('oldasm/model.step').val().Solids()
def L(f): return cq.importers.importStep(f).val()
USED=set()
def matchvol(ref,tol=0.04):
    r=L('oldasm/'+ref+'.step'); v=r.Volume(); rc=r.Center()
    out=[]
    for i,s in enumerate(old):
        if i in USED or abs(s.Volume()-v)>=tol*v: continue
        if ref.startswith('holder') and (s.Center()-rc).Length>5: continue
        USED.add(i); out.append(s)
    return out
common=[]; names=[]
def add(s,n): common.append(s); names.append(n)
add(L('nose_v4.step'),'Nose'); add(L('tail_v12.step'),'Tail')
v6=L('eleron_v6.step')
tgt=[new[i] for i in (14,15,16,17)]
for k in range(4):
    a=v6.rotate(O,Z,90*k); c=a.Center(); best=min(tgt,key=lambda t:(t.Center()-c).Length)
    print('aileron',k,'center dist to user aileron %.2f'%(best.Center()-c).Length); add(a,f'Aileron_{k+1}')
for i,n in zip(range(18,26),['Servo_1','Servo_2','Servo_3','Servo_4','Tube_1','Tube_2','Tube_3','Tube_4']): add(new[i],n)
for ref,nm in [('wing_big_q1','Wing_Large'),('wing_front_q1','Wing_Front'),('holder_big','Tube_Holder_Large'),('holder_front','Tube_Holder_Front'),('tail_mount','Tail_Mount'),('batt_support','Battery_Support'),('motor_mount','Motor_Mount'),('battery','Battery')]:
    try:
        ms=matchvol(ref); print(ref,len(ms))
        for j,s in enumerate(ms): add(s,f'{nm}_{j+1}')
    except Exception as e: print('skip',ref,e)
add(L('frame/rama_verh_2.5mm.step'),'Carbon_Plate_Top'); add(L('frame/rama_niz_2.5mm.step'),'Carbon_Plate_Bottom')
CACHE={}
def build(variant,out):
    parts=list(zip(names,common))
    if variant==4:
        for k in ['PLUS_Y','MINUS_Y','PLUS_X','MINUS_X']: parts.append((f'Body_Panel_{k}',L(f'panel3_{k}.step')))
    else:
        for f in sorted(glob.glob('p12/*.step')): parts.append(('Body_Panel_'+os.path.basename(f)[:-5],L(f)))
    import struct, gc
    asm=cq.Assembly(name='Drone_assembly')
    pd=out+'_parts_in_place'; os.makedirs(pd,exist_ok=True)
    merged=open(out+'.stl','wb'); merged.write(b'Drone assembly'.ljust(80,b' ')); merged.write(struct.pack('<I',0)); ntot=0
    for j,(n,sh) in enumerate(parts):
        asm.add(sh,name=n)
        fn=f'{pd}/{j+1:02d}_{n}'
        import shutil
        src=CACHE.get(n)
        if src and os.path.exists(src+'.stl'):
            shutil.copy(src+'.step',fn+'.step'); shutil.copy(src+'.stl',fn+'.stl')
        else:
            cq.exporters.export(cq.Workplane(obj=sh),fn+'.step')
            tol,ang=((0.05,0.15) if 'Wing' in n else (0.02,0.08))
            cq.exporters.export(cq.Workplane(obj=sh),fn+'.stl',tolerance=tol,angularTolerance=ang)
            CACHE[n]=fn
        print('  part',j+1,n,flush=True)
        d=open(fn+'.stl','rb').read(); k=struct.unpack('<I',d[80:84])[0]; merged.write(d[84:84+50*k]); ntot+=k
        del d; gc.collect()
    merged.seek(80); merged.write(struct.pack('<I',ntot)); merged.close()
    asm.save(out+'.step'); print(out,len(parts),'parts',ntot,'triangles',flush=True)
os.makedirs('asm',exist_ok=True)
build(4,'asm/Drone_Assembly_4_large_panels'); build(12,'asm/Drone_Assembly_12_separate_panels')
