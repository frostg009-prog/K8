import cadquery as cq, numpy as np, sys
from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
from OCP.TopTools import TopTools_ListOfShape
a=cq.importers.importStep(sys.argv[1]).val()
cy=[f for f in a.Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-3.1)<0.01]
wc=np.array([[f.Center().x,f.Center().y,f.Center().z] for f in cy]).mean(0); n=np.array([-0.70710678,0.70710678,0.0])
pl=cq.Face.makePlane(600,600,basePnt=tuple(wc),dir=tuple(n))
sp=BRepAlgoAPI_Splitter(); L1=TopTools_ListOfShape(); L1.Append(a.wrapped); L2=TopTools_ListOfShape(); L2.Append(pl.wrapped)
sp.SetArguments(L1); sp.SetTools(L2); sp.SetFuzzyValue(1e-3); sp.Build()
sols=sorted(cq.Shape.cast(sp.Shape()).Solids(),key=lambda s:np.dot([s.Center().x,s.Center().y,s.Center().z],n))
print('aileron halves',[round(s.Volume()/1000,2) for s in sols])
for nm,s in zip('AB',sols):
    cq.exporters.export(cq.Workplane(obj=s),f'ail_half{nm}.step'); cq.exporters.export(cq.Workplane(obj=s),f'ail_half{nm}.stl',tolerance=0.02,angularTolerance=0.1)
