"""Rebuild original UI illustrations (optional authoring dependency: Pillow).
Runtime uses only the committed PNGs; no downloaded artwork or product photos.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'scenes'
OUT.mkdir(exist_ok=True)
BLUE, INK, LIME, PAPER, PEACH = '#1549df', '#142244', '#dffa75', '#fffdf5', '#ffb797'
SCALE = 2
font_path = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'

def layer():
    im = Image.new('RGBA', (840, 600))
    return im, ImageDraw.Draw(im)

def xy(box): return tuple(round(v*SCALE) for v in box)
def rect(d, box, fill, r=0, outline=None, width=2):
    d.rounded_rectangle(xy(box), radius=r*SCALE, fill=fill, outline=outline, width=width*SCALE)
def line(d, pts, fill=INK, width=2): d.line(xy(pts), fill=fill, width=width*SCALE, joint='curve')
def circle(d, box, fill, outline=None, width=2): d.ellipse(xy(box), fill=fill, outline=outline, width=width*SCALE)
def poly(d, pts, fill, outline=None): d.polygon(xy(pts), fill=fill, outline=outline, width=2*SCALE)
def text(d, p, s, size=12, fill=INK):
    d.text(xy(p), s, fill=fill, font=ImageFont.truetype(font_path, size*SCALE))
def star(d,x,y,c=LIME):
    poly(d,[x,y-17,x+5,y-5,x+17,y,x+5,y+5,x,y+17,x-5,y+5,x-17,y,x-5,y-5],c)
def book(d,x,y,w=75,h=105,c=PEACH):
    rect(d,[x,y,x+w,y+h],c,5,INK);line(d,[x+12,y,x+12,y+h]);rect(d,[x+22,y+22,x+w-10,y+27],PAPER,2)
    line(d,[x+22,y+42,x+w-12,y+42]);line(d,[x+22,y+52,x+w-22,y+52])
def note(d,x,y,w=130,h=105,c=PAPER):
    rect(d,[x+6,y+7,x+w+6,y+h+7],'#0c36b4',5)
    rect(d,[x,y,x+w,y+h],c,5,INK)
    for j in range(3):line(d,[x+18,y+40+j*15,x+w-18-(j%2)*22,y+40+j*15],'#a8b5cc')
def heart(d,x,y,sz=40):
    circle(d,[x-sz,y-sz*.6,x,y+sz*.4],PEACH,INK)
    circle(d,[x,y-sz*.6,x+sz,y+sz*.4],PEACH,INK)
    poly(d,[x-sz+2,y+sz*.05,x+sz-2,y+sz*.05,x,y+sz],PEACH)
    line(d,[x-sz+2,y+sz*.05,x,y+sz,x+sz-2,y+sz*.05])
def lamp(d,x,y):
    circle(d,[x-45,y+89,x+45,y+104],PAPER,INK)
    line(d,[x,y+92,x,y+20,x+30,y-5],PAPER,7)
    poly(d,[x+2,y-35,x+55,y-35,x+72,y+1,x-15,y+1],LIME,INK)

def draw(kind):
    base,d = layer(); front,f = layer()
    circle(d,[80,18,348,286],None,'#4974e6',1)
    line(d,[22,270,399,270],'#7797ed',1)
    star(d,370,42);circle(d,[34,79,46,91],PEACH)
    if kind in ('login','home'):
        rect(d,[40,192,375,207],PAPER,5,INK);line(d,[65,208,65,270],PAPER,5);line(d,[348,208,348,270],PAPER,5)
        book(d,69,97);book(d,151,120,62,72,LIME);lamp(d,285,90)
        poly(f,[244,92,332,92,365,188,214,188],'#fff3a449')
        star(f,221,49,PEACH);text(d,[54,229],'A LITTLE LESS WASTE.',12,PAPER)
    elif kind=='account':
        rect(d,[67,46,335,235],'#1038b8',14);rect(d,[55,32,323,221],PAPER,14,INK)
        rect(d,[55,32,323,69],LIME,12);text(d,[73,45],'CAMPUS ID / 09',13)
        circle(d,[77,92,159,174],PEACH,INK);circle(d,[103,108,133,138],INK);rect(d,[95,142,142,168],INK,16)
        text(d,[179,101],'HELLO,',25);text(d,[179,136],'NEIGHBOUR.',12)
        line(d,[77,196,298,196],'#b3c2d3');rect(f,[247,191,343,241],LIME,24,INK);text(f,[264,207],'SAY HI!',14)
    elif kind=='publish':
        rect(d,[72,70,319,250],PAPER,10,INK);rect(d,[90,88,302,207],'#edf1ff',4)
        book(d,155,100,75,97,LIME);text(d,[99,224],'READY FOR A NEW STORY',12)
        rect(f,[276,40,355,119],PEACH,18,INK);line(f,[316,61,316,98],INK,4);line(f,[297,80,335,80],INK,4)
        star(f,50,185)
    elif kind=='mine':
        rect(d,[44,30,365,263],'#103bb6',10,PAPER);rect(d,[46,142,364,155],PAPER,3);rect(d,[46,248,364,261],PAPER,3)
        book(d,70,52,58,88,PEACH);book(d,139,70,52,70,LIME);lamp(d,275,38)
        rect(d,[83,185,208,238],PEACH,5,INK);line(d,[83,199,208,199]);rect(d,[244,189,322,237],LIME,6,INK)
        rect(f,[170,129,244,166],LIME,3,INK);text(f,[185,140],'OPEN',15)
    elif kind=='favorites':
        rect(d,[51,35,348,262],'#1038b8',12);rect(d,[42,27,339,254],'#f6dcb4',12,INK)
        note(d,65,66,114,143);book(d,91,88,60,81,LIME);text(d,[81,185],'SAVED.',12)
        note(d,195,101,114,126);lamp(d,245,110)
        rect(d,[91,52,152,73],'#ffb797',3);rect(d,[216,87,281,108],LIME,3)
        heart(f,286,55,29);star(f,51,231,PAPER)
    elif kind=='messages':
        note(d,55,45,213,128);circle(d,[77,62,108,93],PEACH,INK)
        rect(d,[121,66,239,78],LIME,6);line(d,[78,115,222,115]);line(d,[78,137,190,137])
        poly(d,[115,173,115,196,144,173],PAPER,INK)
        rect(f,[171,176,365,245],LIME,19,INK);poly(f,[323,245,346,262,346,243],LIME)
        for x in (211,253,295):circle(f,[x,203,x+13,216],INK)
    elif kind=='intentions':
        rect(d,[47,48,361,252],PAPER,10,INK)
        for x in (137,247):line(d,[x,49,x,251],'#c1cdde',1)
        line(d,[77,199,127,199,168,96,227,96,279,172,325,172],BLUE,4)
        for x,y,n in [(77,199,'1'),(190,96,'2'),(325,172,'3')]:
            circle(d,[x-16,y-16,x+16,y+16],LIME,INK);text(d,[x-4,y-7],n,13)
        text(d,[65,65],'MEET / CHECK / PASS ON',10)
        circle(f,[271,101,319,149],PEACH,INK);poly(f,[277,137,295,166,313,137],PEACH);circle(f,[287,117,303,133],PAPER)
    elif kind=='logs':
        rect(d,[81,28,331,268],PAPER,9,INK);rect(d,[81,28,331,69],LIME,9,INK)
        for x in (114,167,220,273):rect(d,[x,19,x+8,43],PEACH,4,INK)
        for i in range(3):
            circle(d,[104,94+i*48,124,114+i*48],BLUE);line(d,[140,102+i*48,289,102+i*48],'#9cabca',3)
        circle(f,[274,201,356,283],PEACH,INK);line(f,[315,216,315,242,337,250],INK,4)
    base.save(OUT/f'{kind}-base.png');front.save(OUT/f'{kind}-float.png')

for name in ('home','login','account','publish','mine','favorites','messages','intentions','logs'):
    draw(name)
print('Wrote 9 original layered scenes to', OUT)
