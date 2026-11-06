import cadquery as cq, numpy as np, sys, math, colorsys, matplotlib, json
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
src,out,title=sys.argv[1:4]
t=cq.importers.importStep(src).val()
PR=np.load('tail_profile.npy')
def rev(prof): return cq.Workplane('XZ').polyline(prof).close().revolve(360,(0,0,0),(0,1,0)).val()
inner=rev([(0.0,174.0)]+[(max(r-2.6,0.5),z) for z,r in PR[::4]]+[(0.0,272.6)])      # region inside the 2.6 mm skin
def box(z0,z1): return cq.Workplane().box(200,200,z1-z0,centered=(True,True,False)).translate((0,0,z0)).val()
def wedge(a0,a1,z0,z1):
    pts=[(0,0)]+[(120*math.cos(math.radians(a)),120*math.sin(math.radians(a))) for a in np.linspace(a0,a1,8)]
    return cq.Workplane('XY').polyline(pts).close().extrude(z1-z0).translate((0,0,z0)).val()
cells=[]
cells.append(('Кольцо-гнездо (торец)', t.intersect(box(170,185.2))))
skin=t.cut(inner)
cells.append(('Обшивка', skin.intersect(box(185.2,240))))
core=t.intersect(inner)
cells.append(('Плита у торца', core.intersect(box(185.2,189.5))))
for k in range(8):
    a=k*45; nm=('держатель серво (диагональ)' if k%2 else 'ребро/лепесток (между серво)')
    cells.append(('%s %d°'%(nm,a), core.intersect(box(189.5,219)).intersect(wedge(a-22.5,a+22.5,189.5,219))))
cells.append(('Переход к наконечнику', core.intersect(box(219,240))))
cells.append(('Наконечник', t.intersect(box(240,280))))
items=[]
for nm,sh in cells:
    for s in sh.Solids():
        if s.Volume()>2: items.append((nm,s))
print(len(items),'items')
N=len(items); cols=[colorsys.hsv_to_rgb((i*0.61803)%1,0.75,0.92) for i in range(N)]
mesh=[]
for i,(nm,s) in enumerate(items):
    vs,tr=s.tessellate(0.1,0.3); V=np.array([(v.x,v.y,v.z) for v in vs]); c=s.Center()
    mesh.append((V[np.array(tr)],np.array([c.x,c.y,c.z]),s.Volume()/1000))
def view(ax,el,az,hi=None):
    e,a=np.radians(el),np.radians(az); cam=np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)])
    allp=[]
    for j,(T,C,vol) in enumerate(mesh):
        nr=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); nr/=np.linalg.norm(nr,axis=1)[:,None]+1e-12
        sh=0.45+0.55*np.abs(nr@cam)
        if hi is None: base=np.array(cols[j]); al=1.0
        elif j==hi: base=np.array([0.9,0.1,0.1]); al=1.0
        else: base=np.array([0.82,0.82,0.85]); al=0.18
        pc=Poly3DCollection(T,facecolors=np.c_[np.clip(base*sh[:,None],0,1),np.full(len(T),al)],edgecolors='none')
        ax.add_collection3d(pc); allp.append(T.reshape(-1,3))
    P=np.vstack(allp); c0=(P.max(0)+P.min(0))/2; R=(P.max(0)-P.min(0)).max()/2
    ax.set_xlim(c0[0]-R,c0[0]+R);ax.set_ylim(c0[1]-R,c0[1]+R);ax.set_zlim(c0[2]-R,c0[2]+R);ax.set_box_aspect((1,1,1));ax.view_init(el,az);ax.set_axis_off()
cols_n=6; rows=int(math.ceil(N/cols_n))
fig=plt.figure(figsize=(4.2*cols_n,4.6*rows+1),dpi=60)
for j,(nm,s) in enumerate(items):
    T,C,vol=mesh[j]
    el,az=(-35,math.degrees(math.atan2(C[1],C[0])) if abs(C[0])+abs(C[1])>3 else 30) if C[2]<222 else (25,30)
    ax=fig.add_subplot(rows,cols_n,j+1,projection='3d'); view(ax,el,az,hi=j)
    ax.set_title('%d. %s\n%.2f см³'%(j+1,nm,vol),fontsize=11,color='darkred')
fig.suptitle(title+' — каждый элемент выделен красным',fontsize=18); plt.tight_layout(); plt.savefig(out)
with open(out.replace('.png','.txt'),'w') as f:
    for i,(nm,s) in enumerate(items):
        c=s.Center(); f.write('%2d  %-40s объём %6.2f см3  центр (%.0f, %.0f, %.0f)\n'%(i+1,nm,s.Volume()/1000,c.x,c.y,c.z))
