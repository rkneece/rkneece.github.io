"""Reproducible RES01 concept elevation; source-authored dimensional diagram."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
W,H=1728,1560
BG='#faf8f3'; INK='#293d43'; TEAL='#32838b'; LINE='#afa99d'; WHITE='#fffdf7'
img=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(img)
def font(size,bold=False):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size)
def text(x,y,s,size=22,fill=INK,bold=False,anchor=None):d.text((x,y),s,font=font(size,bold),fill=fill,anchor=anchor)
def box(xy,fill,outline=LINE,width=2):d.rectangle(xy,fill=fill,outline=outline,width=width)
def line(xy,fill=LINE,width=2):d.line(xy,fill=fill,width=width)
def dim(x1,x2,y,label,size=23,fill=TEAL):
 line((x1,y,x2,y),fill);line((x1-6,y+7,x1+6,y-7),fill);line((x2-6,y+7,x2+6,y-7),fill)
 b=d.textbbox((0,0),label,font=font(size,True)); tw=b[2]-b[0];d.rectangle(((x1+x2-tw)/2-12,y-19,(x1+x2+tw)/2+12,y+19),fill=BG);text((x1+x2)/2,y,label,size,fill,True,'mm')
text(86,50,'43 CEDAR  /  FIREPLACE ALCOVE',36,bold=True)
text(86,101,'Measured concept elevation • 75-inch TV • October 26, 2026',23)
text(1642,61,'CONCEPT 01 / REV D',20,TEAL,True,'ra')
for x in (317,605,1123,1411):line((x,220 if x not in (317,1411) else 166,x,308),'#ccd0ca',1)
dim(317,1411,178,'152″ TOTAL — FIELD MEASURED',26,INK)
dim(317,605,250,'40″ PROPOSED',21);dim(605,1123,250,'72″ PROPOSED',21);dim(1123,1411,250,'40″ PROPOSED',21)
box((317,307,1411,960),'#f0ede5',width=1)
for x in range(328,1411,33):line((x,308,x,959),'#dedbd2',1)
box((628,307,1099,571),'#152124',outline='#152124');box((636,315,1091,563),'#263237',outline='#202c31',width=3)
text(864,409,'75″ TV',37,'#f9f7ee',True,'ma');text(864,457,'≈65.4″ W × 36.8″ H',23,'#cbd2d0',False,'ma')
# 24 x 48-inch unit targets, drawn at 7.2 px/in. House-standard square-edge casing:
# 3.75-inch side legs and a 5-inch head; flat butt joints; identical on both sides.
for center in (461,1267):
 x=center-86
 box((x-27,435,x+173+27,471),WHITE)
 box((x-27,471,x,817),WHITE);box((x+173,471,x+200,817),WHITE)
 box((x,471,x+173,817),'#c9deda',outline='#9db8b2',width=3)
 for y in range(480,812,13):line((x+9,y,x+165,y),'#dfebe6',1)
 box((x-27,817,x+200,830),WHITE)
 box((x+4,588,x+169,684),'#e8f0eb',outline='#e8f0eb')
 text(center,600,'24″ W × 48″ H',20,bold=True,anchor='ma');text(center,635,'UNIT TARGET',16,anchor='ma');text(center,662,'CATALOG SIZE TBD',14,anchor='ma')
# Matching benches: exactly TWO side-by-side Shaker drawers on EACH side.
for x in (321,1127):
 box((x,831,x+280,853),'#d8d0bc');box((x,854,x+280,960),'#f8f5ed')
 for a,b in ((x+8,x+136),(x+144,x+272)):
  box((a,862,b,941),WHITE)
  box((a+9,872,b-9,931),'#f0ede5',outline='#c8c1b4',width=2)
  cx=(a+b)/2;box((cx-9,896,cx+9,900),'#45504d',outline='#45504d',width=1)
# Mantel, recessed brick and fireplace retain the prior measured concept arrangement.
box((605,591,1123,604),WHITE);box((611,604,1117,621),WHITE)
box((615,621,1113,674),WHITE)
box((664,675,1064,960),'#b18b6e',outline='#d1c1aa')
for y in range(677,960,24):
 line((665,y,1064,y),'#d8c8ae',3)
 for x in range(674+(31 if ((y-677)//24)%2 else 0),1064,62):line((x,y,x,y+23),'#d8c8ae',2)
box((615,675,664,923),WHITE);box((1064,675,1113,923),WHITE)
box((610,922,671,960),WHITE);box((1058,922,1118,960),WHITE)
box((680,757,1048,943),'#252823',outline='#494337',width=7);box((694,772,1034,930),'#302e29',outline='#302e29')
for x in range(734,1004,38):d.polygon([(x,911),(x+14,863),(x+29,911)],fill='#ca9057')
box((605,961,1123,980),'#b9b9ac');line((288,982,1441,982),'#77847e',2)
line((267,831,267,961),TEAL);line((259,831,275,831),TEAL);line((259,961,275,961),TEAL)
line((275,831,313,831),'#c5d1ca',1);text(246,871,'18″',23,TEAL,True,'ra');text(246,904,'PROP.',16,TEAL,False,'ra')
line((86,1039,1642,1039),'#c8cfc7',2)
text(86,1064,'DESIGN DIMENSIONS',23,bold=True)
for y,s in [(1103,'• Side bays: 40″ each; center bay: 72″ overall.'),(1140,'• Window units: approximately 24″ W × 48″ H.'),(1177,'• Bench seat: 18″ above floor, including cushion.'),(1214,'• Max two Shaker drawers per side; interior sizes TBD.')]:text(86,y,s,22)
text(960,1064,'WINDOW CASING / FINAL COORDINATION',22,bold=True)
for y,s in [(1103,'Square-edge Craftsman casing, matching rest of house:'),(1140,'3½–4″ legs; 5″ head; flat butt joints, no profiles.'),(1177,'TV / mantel heights, fireplace model and clearances,'),(1214,'Window size / opening, sill height and bench depth TBD.')]:text(960,y,s,19)
box((86,1264,1642,1392),'#e8f0eb',outline=TEAL,width=2)
text(114,1279,'TV MOUNT / BEFORE DRYWALL',23,TEAL,True)
text(114,1318,'TV supported by MantelMount inside the stud cavity.',24)
text(114,1354,'Add a receptacle and install the mount before drywall.',24)
text(86,1418,'Only the 152″ total width is field confirmed. Proposed dimensions are for design review, not construction.',20,'#687c7c')
text(86,1453,'Width proportions drawn to scale. Vertical placement is illustrative; ceiling and roof geometry are intentionally omitted.',18,'#687c7c')
text(86,1510,'Retained vertical T&G: entire fireplace / south wall and both alcoves • Swiss Coffee 75% • eggshell',21)
img.save(ROOT/'43_Cedar_Fireplace_Measured_Concept.png',optimize=True)
print(ROOT/'43_Cedar_Fireplace_Measured_Concept.png')
