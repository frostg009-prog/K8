import cadquery as cq, glob, sys, os, trimesh
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL, TopAbs_EDGE
from OCP.BRep import BRep_Tool
from OCP.BRepCheck import BRepCheck_Analyzer
def free_edges(shape):
    fb=ShapeAnalysis_FreeBounds(shape.wrapped,1e-4,False,False)
    n=0; e=TopExp_Explorer(fb.GetClosedWires(),TopAbs_EDGE)
    while e.More(): n+=1; e.Next()
    e=TopExp_Explorer(fb.GetOpenWires(),TopAbs_EDGE)
    while e.More(): n+=1; e.Next()
    return n
rows=[]
for f in sorted(glob.glob('*/**/*.STEP',recursive=True)+glob.glob('*/*.STEP')):
    if f in [r[0] for r in rows]: continue
    try:
        s=cq.importers.importStep(f).val()
        sol=s.Solids(); ok=BRepCheck_Analyzer(s.wrapped).IsValid()
        fe=free_edges(s); vol=s.Volume()/1000
        closed=all(sh.Closed() for sh in s.Shells())
        stl=None
        for cand in (f[:-5]+'.stl', f.replace('/STEP/','/STL/')[:-5]+'.stl'):
            if os.path.exists(cand): stl=trimesh.load(cand).volume/1000; break
        status='OK' if ok and fe==0 and closed and vol>0 else 'BAD'
        rows.append((f,status,len(sol),ok,closed,fe,round(vol,2),None if stl is None else round(stl,2)))
    except Exception as e: rows.append((f,'ERR',str(e)[:60]))
for r in rows: print(r)
