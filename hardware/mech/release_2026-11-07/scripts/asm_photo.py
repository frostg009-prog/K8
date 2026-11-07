import glob, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,'.'); from wr import render
COL={'Nose':'#d98f8f','Tail':'#bdbdbd','Aileron':'#e6b84d','Servo':'#3a3a3a','Tube':'#222222','Wing_Large':'#7fa8dc','Wing_Front':'#7fd6be','Tube_Holder':'#888888','Tail_Mount':'#666666','Battery_Support':'#666666','Motor_Mount':'#555555','Battery':'#4a6a4a','Carbon':'#303030','Body_Panel':'#b49be0'}
def col(n):
    for k,v in COL.items():
        if k in n: return v
    return '#aaaaaa'
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',24); f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
tiles=[]
for var,lab in [('4_large_panels','4.1  Assembly with 4 large body panels'),('12_separate_panels','4.2  Assembly with 12 separate body panels')]:
    fs=sorted(glob.glob(f'asm/Drone_Assembly_{var}_parts_in_place/*.stl'))
    items=[(f,col(os.path.basename(f))) for f in fs]
    for k,v in enumerate([(25,-50),(20,130),(80,-45)]):
        out=f'/tmp/asm_{var}_{k}.png'; render(items,out,views=(v,),size=(800,640),maxtri=300000,pad=1.0); tiles.append((f'{lab}  view {k+1}',out))
W,H=800,680; img=Image.new('RGB',(3*W,2*H+70),'white'); d=ImageDraw.Draw(img)
d.text((15,15),'ARCHIVE 4 - FULL ASSEMBLY (STEP + STL, each part also separately in place). Wings whole, as original.',fill='black',font=F)
for i,(t,p) in enumerate(tiles):
    x,y=(i%3)*W,(i//3)*H+70; img.paste(Image.open(p),(x,y)); d.text((x+10,y+648),t,fill='black',font=f2)
img.save('../release2_photos/4_ASSEMBLY_full.png'); print('ok')
