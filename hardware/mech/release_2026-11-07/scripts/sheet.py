import sys, glob, os, trimesh
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,'.'); from wr import render
d,out,title=sys.argv[1],sys.argv[2],sys.argv[3]
fs=sorted(glob.glob(d+'/*.stl'))
tiles=[]
os.makedirs('/tmp/tiles',exist_ok=True)
for i,f in enumerate(fs):
    t=f'/tmp/tiles/{i}.png'; render([(f,'#8fb0dc')],t,views=((28,-55),),size=(420,340),maxtri=400000)
    tiles.append((os.path.basename(f)[:-4],t))
cols=4; rows=(len(tiles)+cols-1)//cols; W,H=420,370
img=Image.new('RGB',(cols*W,rows*H+60),'white'); dr=ImageDraw.Draw(img)
try: F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15); FT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',26)
except: F=FT=ImageFont.load_default()
dr.text((15,15),title,fill='black',font=FT)
for k,(n,t) in enumerate(tiles):
    x,y=(k%cols)*W,(k//cols)*H+60; img.paste(Image.open(t),(x,y)); dr.text((x+8,y+342),n[:48],fill='black',font=F)
    dr.rectangle([x,y,x+W-1,y+H-1],outline='#ddd')
img.save(out); print(out,len(tiles))
