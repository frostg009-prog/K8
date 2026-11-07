import cadquery as cq, trimesh, numpy as np, pymeshfix, sys
for f in sys.argv[1:]:
    s=cq.importers.importStep(f+'.step').val(); V=s.Volume()/1e3; best=None
    for tol,ang in ((0.03,0.1),(0.02,0.08),(0.05,0.12)):
        cq.exporters.export(cq.Workplane(obj=s),'/tmp/q.stl',tolerance=tol,angularTolerance=ang)
        m=trimesh.load('/tmp/q.stl'); m.merge_vertices(digits_vertex=4); trimesh.repair.fill_holes(m)
        if not m.is_watertight:
            vv,ff=pymeshfix.clean_from_arrays(np.asarray(m.vertices,dtype=np.float64),np.asarray(m.faces,dtype=np.int32),joincomp=False,remove_smallest_components=False); m=trimesh.Trimesh(vv,ff)
        e=abs(m.volume/1e3-V)/V*100
        print(f,tol,len(m.faces),m.is_watertight,len(m.split(only_watertight=False)),'STL %.2f STEP %.2f diff %.1f%%'%(m.volume/1e3,V,e),flush=True)
        if m.is_watertight and (best is None or e<best[0]): best=(e,m)
        if best and best[0]<2.0: break
    best[1].export(f+'.stl'); print('saved',f,'diff %.1f%%'%best[0],flush=True)
