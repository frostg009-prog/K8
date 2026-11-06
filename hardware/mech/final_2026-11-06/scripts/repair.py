import trimesh, sys, numpy as np
def repair(src,dst):
    m=trimesh.load(src)
    for d in (5,4,3):
        mm=m.copy(); mm.merge_vertices(digits_vertex=d)
        mm.update_faces(mm.nondegenerate_faces()); mm.update_faces(mm.unique_faces()); mm.remove_unreferenced_vertices()
        trimesh.repair.fix_normals(mm); trimesh.repair.fill_holes(mm)
        parts=mm.split(only_watertight=False)
        if len(parts)>1:   # drop tiny debris (<0.5% of volume)
            big=max(parts,key=lambda p:abs(p.volume)); keep=[p for p in parts if abs(p.volume)>0.005*abs(big.volume)]
            mm=trimesh.util.concatenate(keep)
        if mm.is_watertight and len(mm.split(only_watertight=False))==1: break
    mm.export(dst)
    print(src.split('/')[-1],'-> watertight',mm.is_watertight,'bodies',len(mm.split(only_watertight=False)),'vol %.1f'%(mm.volume/1000),'(merge digits %d)'%d)
for a,b in zip(sys.argv[1::2],sys.argv[2::2]): repair(a,b)
