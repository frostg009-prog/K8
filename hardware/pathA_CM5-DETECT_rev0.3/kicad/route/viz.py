import json,sys,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
D=json.load(open('board.json')); R=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'routes.json'))
fig,ax=plt.subplots(figsize=(7,19),dpi=110); ax.set_xlim(0,D['W']); ax.set_ylim(D['L'],0); ax.set_aspect('equal')
for p in D['pads']:
    x0,y0,x1,y1=p['bb']; c={'F':'#f4a','B':'#4af'}.get(p['layers'][0],'#999') if len(p['layers'])==1 else '#888'
    ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,color=c,alpha=0.6,lw=0))
for n,l,a,b,w in R['tracks']:
    ax.plot([a[0],b[0]],[a[1],b[1]],color='r' if l=='F' else 'b',lw=max(w*4,0.4),alpha=0.7,solid_capstyle='round')
for n,x,y in R['vias']: ax.plot(x,y,'o',ms=2,color='k')
fails=set(f[0] for f in R['failed'])
for p in D['pads']:
    if p['net'] in fails: ax.plot(p['x'],p['y'],'x',color='lime',ms=4)
plt.tight_layout(); plt.savefig(sys.argv[2] if len(sys.argv)>2 else 'viz.png')
