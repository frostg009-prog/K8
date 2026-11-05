import cadquery as cq, trimesh
from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
from OCP.TopTools import TopTools_ListOfShape
t=cq.importers.importStep('in/tail.step').val(); v0=t.Volume()
H=5.2
for ang in (0,45):
    box=cq.Workplane().box(2*H,2*H,215.5-184.0,centered=(True,True,False)).edges('|Z').fillet(1.5).translate((0,0,184.0)).rotate((0,0,0),(0,0,1),ang).val()
    r=t.cut(box); print(ang,r.isValid(),round((v0-r.Volume())/1000,2),'cm3 removed',len(r.Solids()))
    if (v0-r.Volume())>3000: break
r=r.Solids()[0] if len(r.Solids())==1 else r
cq.exporters.export(cq.Workplane(obj=r),'tail_v3_print.step')
def stl(sol,n):
    vs,tr=sol.tessellate(0.02,0.1); m=trimesh.Trimesh([(a.x,a.y,a.z) for a in vs],tr); m.merge_vertices(); m.export(n); return m
stl(r,'tail_v3_print.stl')
for ang,tag in ((0,'x0'),(45,'d45')):
    pl=cq.Face.makePlane(800,800,basePnt=(0,0,200),dir=(1,0,0)).rotate((0,0,0),(0,0,1),ang)
    sp=BRepAlgoAPI_Splitter(); a=TopTools_ListOfShape(); a.Append(r.wrapped); tl=TopTools_ListOfShape(); tl.Append(pl.wrapped)
    sp.SetArguments(a); sp.SetTools(tl); sp.SetFuzzyValue(1e-3); sp.Build()
    sols=cq.Shape.cast(sp.Shape()).Solids(); print(tag,len(sols),[round(x.Volume()/1000,2) for x in sols],round(r.Volume()/1000,2))
    if len(sols)==2 and abs(sum(x.Volume() for x in sols)-r.Volume())<500:
        sols=sorted(sols,key=lambda x:x.Center().x)
        for n,s in zip('AB',sols):
            cq.exporters.export(cq.Workplane(obj=s),f'tail_mold_{n}.step'); stl(s,f'tail_mold_{n}.stl')
        print('mold split via',tag); break
