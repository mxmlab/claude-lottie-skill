import sys
from PIL import Image, ImageDraw
im=Image.open(sys.argv[1]).convert('RGB'); d=ImageDraw.Draw(im); W=im.width
step=int(sys.argv[3]) if len(sys.argv)>3 else 32
for x in range(0,W,step):
    d.line([(x,0),(x,im.height)],fill=(0,0,255) if x%128==0 else (170,170,255),width=1)
    d.text((x+2,2),str(x),fill=(0,0,160))
for y in range(0,im.height,step):
    d.line([(0,y),(W,y)],fill=(0,0,255) if y%128==0 else (170,170,255),width=1)
    d.text((2,y+2),str(y),fill=(0,0,160))
im.save(sys.argv[2])
