import cadquery as cq, sys, trimesh
src,ang,tag=sys.argv[1],float(sys.argv[2]),sys.argv[3]
s=cq.importers.importStep(src).val()
def half(sign):
    b=cq.Workplane().box(300,600,600,centered=(False,True,True)).translate((0,0,0))
    if sign<0: b=b.translate((-300,0,0))
    return b.rotate((0,0,0),(0,0,1),ang).val()
for n,sg in (('A',-1),('B',1)):
    sol=s.intersect(half(sg)); print(tag,n,sol.isValid(),round(sol.Volume()/1000,2),len(sol.Solids()))
    cq.exporters.export(cq.Workplane(obj=sol),f'{tag}_{n}.step')
    vs,tr=sol.tessellate(0.02,0.1); m=trimesh.Trimesh([(v.x,v.y,v.z) for v in vs],tr); m.merge_vertices(); m.export(f'{tag}_{n}.stl')
