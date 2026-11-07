import cadquery as cq, trimesh, glob, os, sys
R=sys.argv[1]; bad=0
for d in sorted(glob.glob(R+'/*/STEP')):
    print('==',os.path.dirname(d).split('/')[-1])
    for st in sorted(glob.glob(d+'/*.STEP')):
        n=os.path.basename(st)[:-5]; sl=os.path.join(os.path.dirname(d),'STL',n+'.stl')
        s=cq.importers.importStep(st).val(); V=s.Volume()/1e3; ok=s.isValid(); ns=len(s.Solids())
        m=trimesh.load(sl); wt=m.is_watertight; nb=len(m.split(only_watertight=False)); vs=m.volume/1e3; e=abs(vs-V)/V*100
        flag='OK' if ok and ns==1 and wt and nb==1 and e<3.0 else 'CHECK'
        if flag!='OK': bad+=1
        print(f'  {flag:5} {n:58} STEP {V:7.2f} valid={ok} solids={ns} | STL {vs:7.2f} watertight={wt} bodies={nb} diff {e:.1f}%',flush=True)
print('problems:',bad)
