import numpy as np, trimesh, base64, json, sys, os
import subprocess
THREE=open('/tmp/three.min.js').read()
PAL=['#8fb0dc','#e1aa7d','#96d296','#d796be','#c8c878','#96c8d2']
def enc(a): return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
def render(items,out,views=((25,-50),),size=(1000,760),maxtri=700000,pad=1.0):
    # items: list of (stl_path_or_mesh, '#hex')
    ms=[]
    for k,(f,c) in enumerate(items):
        m=trimesh.load(f) if isinstance(f,str) else f
        if len(m.faces)>maxtri//max(1,len(items)):
            try: m=m.simplify_quadric_decimation(face_count=maxtri//max(1,len(items)))
            except Exception as e: pass
        ms.append(dict(p=enc(m.vertices.astype('f4')),i=enc(m.faces.astype('u4')),n=enc(m.vertex_normals.astype('f4')),c=c or PAL[k%6]))
    allv=np.vstack([trimesh.load(f).vertices if isinstance(f,str) else f.vertices for f,_ in items]); ctr=((allv.max(0)+allv.min(0))/2).tolist(); R=float(np.ptp(allv,axis=0).max())
    html=f"""<html><body style='margin:0;background:#fff'><canvas id=c></canvas><script>{THREE}</script><script>
const D={json.dumps(ms)},CT={json.dumps(ctr)},R={R},V={json.dumps(views)},W={size[0]},H={size[1]};
function b(s,T){{const x=atob(s),a=new Uint8Array(x.length);for(let i=0;i<x.length;i++)a[i]=x.charCodeAt(i);return new T(a.buffer)}}
const r=new THREE.WebGLRenderer({{canvas:document.getElementById('c'),antialias:true,preserveDrawingBuffer:true}});r.setSize(W,H*V.length);r.setClearColor(0xffffff);r.setScissorTest(true);
const sc=new THREE.Scene();sc.add(new THREE.AmbientLight(0xffffff,0.55));const dl=new THREE.DirectionalLight(0xffffff,0.8);sc.add(dl);const dl2=new THREE.DirectionalLight(0xffffff,0.3);sc.add(dl2);
for(const d of D){{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(b(d.p,Float32Array),3));g.setAttribute('normal',new THREE.BufferAttribute(b(d.n,Float32Array),3));g.setIndex(new THREE.BufferAttribute(b(d.i,Uint32Array),1));
 sc.add(new THREE.Mesh(g,new THREE.MeshStandardMaterial({{color:d.c,roughness:0.55,metalness:0.1,side:THREE.DoubleSide}})))}}
V.forEach((v,k)=>{{const el=v[0]*Math.PI/180,az=v[1]*Math.PI/180;const cam=new THREE.PerspectiveCamera(30,W/H,R*0.01,R*20);cam.up.set(0,0,1);
 const dist=R*{pad}*2.1;cam.position.set(CT[0]+dist*Math.cos(el)*Math.cos(az),CT[1]+dist*Math.cos(el)*Math.sin(az),CT[2]+dist*Math.sin(el));cam.lookAt(CT[0],CT[1],CT[2]);
 dl.position.copy(cam.position);dl2.position.set(-1,-1,1).multiplyScalar(R);
 r.setViewport(0,H*(V.length-1-k),W,H);r.setScissor(0,H*(V.length-1-k),W,H);r.render(sc,cam)}});window.done=1;</script></body></html>"""
    open('/tmp/_r.html','w').write(html)
    subprocess.run(['node','shot.js','/tmp/_r.html',os.path.abspath(out),str(size[0]),str(size[1]*len(views))],check=True,env=dict(os.environ,NODE_PATH=subprocess.check_output(['npm','root','-g']).decode().strip()))
if __name__=='__main__': render([(f,None) for f in sys.argv[2:]],sys.argv[1])
