# STARK DARK: GUI backgrounds + title banners, imported by build_pack.py
import os, json
from PIL import Image, ImageDraw
SL0=(13,16,22); SL1=(22,27,36); SL2=(33,40,52); SL3=(52,62,78); CY=(63,224,255); AM=(255,181,71); RD=(255,77,94); WH=(232,238,245)
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def gui_bg(accent, rows=6):
    W,H=176, 17+rows*18+97+8   # 222 for 6 rows
    H=114+rows*18
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([0,0,W-1,H-1],radius=5,fill=SL1+(255,),outline=SL3+(255,))
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
def kitb_bg():
    """Kit builder (6 rows): kit rows 0-2 plain, row 3 = hotbar (cyan, digits 1-9), row 4 = upgrades (amber),
    row 5 = controls (back/templates/clear/help, PRICE amber, SAVE cyan, SAVE+EQUIP amber glow, gaps at 50/52),
    side bars mark the zones, "PALETTE" label above the player inventory."""
    import pix5
    rows = 6; W, H = 176, 114 + rows * 18
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=5, fill=SL1 + (255,), outline=SL3 + (255,))
    for x in range(6, W - 6):
        t = abs((x - W / 2) / (W / 2 - 6)); c = lerp(CY, SL2, t ** 1.6)
        im.putpixel((x, 15), c + (255,))
    def slot(x, y, fill=SL0, outline=SL2, mark=CY, glow=None):
        if glow:
            d.rectangle([x - 2, y - 2, x + 17, y + 17], outline=glow + (110,))
        d.rectangle([x - 1, y - 1, x + 16, y + 16], fill=fill + (255,), outline=outline + (255,))
        im.putpixel((x - 1, y - 1), mark + (160,))
    # kit rows 0-2
    for r in range(3):
        for c in range(9): slot(8 + c * 18, 18 + r * 18)
    # row 3: hotbar
    y3 = 18 + 3 * 18
    for c in range(9):
        x = 8 + c * 18
        slot(x, y3, fill=lerp(SL0, CY, 0.10), outline=lerp(SL2, CY, 0.55))
        pix5.draw(im, x + 1, y3 + 1, str(c + 1), lerp(SL3, CY, 0.75) + (200,))
    # row 4: upgrades
    y4 = 18 + 4 * 18
    for c in range(9): slot(8 + c * 18, y4, fill=lerp(SL0, AM, 0.10), outline=lerp(SL2, AM, 0.55), mark=AM)
    # row 5: controls
    y5 = 18 + 5 * 18
    for c in range(4): slot(8 + c * 18, y5)
    slot(8 + 4 * 18, y5, fill=lerp(SL0, AM, 0.14), outline=AM, mark=AM)                    # price
    slot(8 + 6 * 18, y5, fill=lerp(SL0, CY, 0.14), outline=CY)                              # save
    slot(8 + 8 * 18, y5, fill=lerp(SL0, AM, 0.20), outline=AM, mark=AM, glow=AM)           # save + equip
    # zone bars (left + right margin)
    for (y0, y1, col) in [(17, 70, SL3), (71, 88, CY), (89, 106, AM), (107, 124, SL3)]:
        for y in range(y0 + 1, y1):
            for x in (2, 3, W - 4, W - 3): im.putpixel((x, y), col + (255,))
    # palette label + divider line
    py = 18 + rows * 18 + 13
    ly = py - 9
    end = pix5.draw(im, 8, ly, "PALETTE", lerp(SL3, CY, 0.7) + (255,))
    for x in range(end + 3, W - 14): im.putpixel((x, ly + 2), lerp(SL3, CY, 0.22) + (255,))
    pix5.draw(im, W - 12, ly, "^", lerp(SL3, CY, 0.7) + (255,))
    pix5.draw(im, W - 12, ly + 3, "^", lerp(SL3, CY, 0.4) + (255,))
    for r in range(3):
        for c in range(9): slot(8 + c * 18, py + r * 18)
    for c in range(9): slot(8 + c * 18, py + 58)
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
    # dedicated kit builder background (6 rows) -> U+E208
    im=kitb_bg(); im.save(os.path.join(fdir,"kitb6.png")); table["kitb6"]=hex(0xE208)
    prov.append({"type":"bitmap","file":"starkffa:font/gui/kitb6.png","ascent":13,"height":im.height,"chars":[chr(0xE208)]})
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
    for n in ("chest6_cyan","kitb6","chest3_cyan","chest4_amber"):
        pv.alpha_composite(Image.open(os.path.join(fdir,n+".png")),(x,10)); x+=186
    for i,(n,_) in enumerate(BAN): pv.alpha_composite(Image.open(os.path.join(fdir,"banner_"+n+".png")).resize((256,48),Image.NEAREST),(10+i*190,232)) if i<3 else None
    pv.save(os.path.join(os.path.dirname(pack),"gui_preview.png"))
    return table
