from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os, sys
S=sys.argv[1] if len(sys.argv)>1 else os.environ["PROMO_WORK"]
D=S+"/assets/drive/"; G=S+"/assets/gen/"
v=Image.open(D+"9bedb650.png").convert("RGB"); W,H=v.size
# find split: two cards side-by-side on black; detect column gap
arr=np.asarray(v).astype(int).sum(2); colmean=arr.mean(0)
mid=W//2; gap=min(range(mid-80,mid+80), key=lambda x: colmean[x]); print('gap',gap,W,H)
def crop_card(im, aspect=0.7):
    a=np.asarray(im).astype(int).sum(2); ys=np.where(a.mean(1)>40)[0]; xs=np.where(a.mean(0)>40)[0]
    im=im.crop((xs[0],ys[0],xs[-1]+1,ys[-1]+1)); w,h=im.size
    if w/h>aspect: nw=int(h*aspect); im=im.crop(((w-nw)//2,0,(w-nw)//2+nw,h))
    else: nh=int(w/aspect); im=im.crop((0,(h-nh)//2,w,(h-nh)//2+nh))
    return im.resize((700,1000), Image.LANCZOS)
crop_card(v.crop((0,0,gap,H))).save(G+"card_place.png")
crop_card(v.crop((gap,0,W,H))).save(G+"card_main.png")
crop_card(Image.open(D+"chatgpt_2026-05-18.png").convert("RGB")).save(G+"card_back.png")
# vignette overlay (RGBA) 1920x1080
W,H=1920,1080; y,x=np.mgrid[0:H,0:W]; d=np.sqrt(((x-W/2)/(W/2))**2+((y-H/2)/(H/2))**2)
a=np.clip((d-0.55)/0.75,0,1)**1.6*0.92
img=np.zeros((H,W,4),np.uint8); img[...,3]=(a*255).astype(np.uint8); Image.fromarray(img,'RGBA').save(G+"vignette.png")
# bottom gradient for captions
g=np.clip((y-H*0.55)/(H*0.45),0,1)**1.3*0.85; img=np.zeros((H,W,4),np.uint8); img[...,3]=(g*255).astype(np.uint8); Image.fromarray(img,'RGBA').save(G+"bottomgrad.png")
for f in ["card_place","card_main","card_back"]: print(f, Image.open(G+f+".png").size)
