# STARK DARK: GUI backgrounds + title banners, imported by build_pack.py
import os, json
from PIL import Image, ImageDraw
SL0=(13,16,22); SL1=(22,27,36); SL2=(33,40,52); SL3=(52,62,78); CY=(63,224,255); AM=(255,181,71); RD=(255,77,94); WH=(232,238,245)
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def gui_bg(accent, rows=6):
    W,H=176, 17+rows*18+97+8   # 222 for 6 rows
    H=114+rows*18
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([0,0,W-1,H-1],radius=5,fill=SL1+(250,),outline=SL3+(255,))
    # header glow line
    for x in range(6,W-6):
        t=abs((x-W/2)/(W/2-6)); c=lerp(accent,SL2,t**1.6)
        im.putpixel((x,15),c+(255,))
    def slot(x,y):
        d.rectangle([x-1,y-1,x+16,y+16],fill=SL0+(255,),outline=SL2+(255,))
        im.putpixel((x-1,y-1),accent+(140,))
    for r in range(rows):
        for c in range(9): slot(8+c*18,18+r*18)
    py=18+rows*18+13
    # divider
    for x in range(8,W-8): im.putpixel((x,py-6),lerp(SL3,accent,0.25)+(255,))
    for r in range(3):
        for c in range(9): slot(8+c*18,py+r*18)
    for c in range(9): slot(8+c*18,py+58)
    return im
def banner(accent, w=128, h=24):
    im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([0,0,w-1,h-1],radius=4,fill=SL1+(235,))
    for x in range(2,w-2):
        t=abs((x-w/2)/(w/2)); c=lerp(accent,SL1,t**1.3)
        im.putpixel((x,0),c+(255,)); im.putpixel((x,h-1),c+(255,)); im.putpixel((x,1),c+(120,))
    for y in range(4,h-4):
        im.putpixel((1,y),accent+(255,)); im.putpixel((w-2,y),accent+(255,))
    return im
def build(pack):
    fdir=os.path.join(pack,"assets/starkffa/textures/font/gui"); os.makedirs(fdir,exist_ok=True)
    prov=[]; table={}
    # chest backgrounds: rows 3..6 x accent (cyan, amber) -> U+E200 + (rows-3)*2 + amber
    for rows in (3,4,5,6):
        for ai,(an,acc) in enumerate((("cyan",CY),("amber",AM))):
            im=gui_bg(acc,rows); n=f"chest{rows}_{an}"; im.save(os.path.join(fdir,n+".png"))
            cp=0xE200+(rows-3)*2+ai; table[n]=hex(cp)
            prov.append({"type":"bitmap","file":f"starkffa:font/gui/{n}.png","ascent":13,"height":im.height,"chars":[chr(cp)]})
    BAN=[("event",AM),("kill",CY),("alert",RD),("streak",AM)]
    for i,(n,acc) in enumerate(BAN):
        im=banner(acc); im.save(os.path.join(fdir,"banner_"+n+".png")); ch=chr(0xE220+i); table["banner_"+n]=hex(0xE220+i)
        prov.append({"type":"bitmap","file":f"starkffa:font/gui/banner_{n}.png","ascent":10,"height":12,"chars":[ch]})
    prov.append({"type":"space","advances":{"":-8,"":-169,"":-1,"":-2,"":-4,"":-16,"":-32,"":-64,"":-128,"":-49}})
    json.dump({"providers":prov},open(os.path.join(pack,"assets/starkffa/font/gui.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=True)
    for lang in ("en_us","en_gb","de_de","de_at","de_ch"):
        ld=os.path.join(pack,"assets/minecraft/lang"); os.makedirs(ld,exist_ok=True)
        json.dump({"container.inventory":""},open(os.path.join(ld,lang+".json"),"w",encoding="utf-8"))
    # preview
    pv=Image.new("RGBA",(176*4+50,222+60),(40,40,48,255)); x=10
    for n in ("chest6_cyan","chest6_amber","chest3_cyan","chest4_amber"):
        pv.alpha_composite(Image.open(os.path.join(fdir,n+".png")),(x,10)); x+=186
    for i,(n,_) in enumerate(BAN): pv.alpha_composite(Image.open(os.path.join(fdir,"banner_"+n+".png")).resize((256,48),Image.NEAREST),(10+i*190,232)) if i<3 else None
    pv.save(os.path.join(os.path.dirname(pack),"gui_preview.png"))
    return table
