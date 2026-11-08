"""Native AutoLISP overlay on a COPY of the original DWG; preliminary v01."""
import csv,json,shutil
from cad_native import ROOT,CACHE,run,sha
R=ROOT;D=R/'05_Calculations/data';O=(64345.93225182503,15925.58365525945)
def read(name):return list(csv.DictReader((D/name).open(encoding='utf8')))
diff=read('diffusers_v01.csv');boxes=read('vav_boxes_v01.csv');flex=read('flex_routes_v01.csv');ducts=read('ducts_v01.csv')
cmd=[]
def add(expr):cmd.append(expr)
def line(a,b,layer):
    add(f'(entmakex \'((0 . "LINE") (8 . "{layer}") (10 {a[0]+O[0]:.8f} {a[1]+O[1]:.8f} 0) (11 {b[0]+O[0]:.8f} {b[1]+O[1]:.8f} 0)))')
def poly(points,layer):
    add('(entmakex \'((0 . "LWPOLYLINE") (100 . "AcDbEntity") (8 . "'+layer+'") (100 . "AcDbPolyline") (90 . '+str(len(points))+') (70 . 1) '+' '.join(f'(10 {x+O[0]:.8f} {y+O[1]:.8f})' for x,y in points)+'))')
def rect(x,y,w,h,layer):poly([(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)],layer)
def text(x,y,t,layer='M-TEXT',h=220):
    t=t.replace('"','\\"')
    add(f'(entmakex \'((0 . "TEXT") (8 . "{layer}") (10 {x+O[0]:.8f} {y+O[1]:.8f} 0) (40 . {h}) (1 . "{t}") (7 . "Standard")))')

work=R/'05_Calculations/cad/BSE3227_HVAC_v01.dwg'
shutil.copy2(R/'01_Assignment_Brief/Building_Drawings/Project layout.dwg',work)
add('(setvar "TILEMODE" 1)');add('(setvar "BACKGROUNDPLOT" 0)')
for name,col,lw in [('M-SUP-DIFF',5,.3),('M-VAV',6,.3),('M-FLEX',3,.18),('M-DUCT',5,.4),('M-TEXT',7,.18),('M-DUCT-TEXT',5,.18),('M-ORIGINAL-TEXT',7,.18),('M-REVIEW',1,.3)]:
    add(f'(command "_.-LAYER" "_M" "{name}" "_C" "{col}" "{name}" "_LW" "{lw:.2f}" "{name}" "")')
add('(command "_.-LAYER" "_C" "8" "ARCH" "_C" "9" "Ceiling Grid" "")')
for handle in ['8D06','8D08','8D09']:
    add(f'(setq e (handent "{handle}") d (entget e))');add('(entmod (subst (cons 8 "M-ORIGINAL-TEXT") (assoc 8 d) d))')
add('(command "_.-LAYER" "_OFF" "M-ORIGINAL-TEXT" "")')
for r in diff:
    x=float(r['x_mm']);y=float(r['y_mm']);w=600 if r['diffuser_type'].startswith('600') else 300
    rect(x,y,w,w,'M-SUP-DIFF');rect(x,y,w*.5,w*.5,'M-SUP-DIFF')
    text(x-600,y+600,f"{r['id']}  {float(r['max_lps']):.0f} L/s",h=200)
for r in boxes:
    x=float(r['x_mm']);y=float(r['y_mm']);rect(x,y,1000,800,'M-VAV')
    text(x-650,y-750,r['id'],h=220)
for r in flex:
    a=(float(r['start_x_mm']),float(r['start_y_mm']));b=(float(r['end_x_mm']),float(r['end_y_mm']))
    line(a,b,'M-FLEX')
for r in ducts:
    a=(float(r['start_x_mm']),float(r['start_y_mm']));b=(float(r['end_x_mm']),float(r['end_y_mm']))
    line(a,b,'M-DUCT')
    if r['length_m'] and float(r['length_m'])>1.5:
        label=f"{r['id']} {r['width_mm']}x{r['height_mm']}"
        text((a[0]+b[0])/2+150,(a[1]+b[1])/2+200,label,'M-DUCT-TEXT',180)
# AHU and two compartment interfaces, explicitly conditional.
rect(19200,25000,1900,1200,'M-DUCT');text(18100,25900,'AHU SUPPLY',h=250)
rect(19200,23250,1000,200,'M-REVIEW');rect(19200,20760,1000,200,'M-REVIEW')
text(20200,21800,'ENCLOSED CROSSING: REVIEW FIRE STRATEGY','M-REVIEW',170)
notes=[
 'BSE3227 / HVACR 1', 'HVAC REVIEW LAYOUT v01', 'PRELIMINARY - NOT FOR SUBMISSION',
 '40 SUPPLY DIFFUSERS / 10 VAV BOXES', '4 outlets per VAV box',
 'Printed office area: 1022 m2', 'Assumed total load: 120 W/m2',
 'Assumed SHR: 0.75; room/supply 24/12 C', 'Peak supply: 6349.4 L/s', 'Minimum supply: 2539.8 L/s',
 'BLUE: rigid supply duct / diffuser', 'GREEN: flexible connection', 'MAGENTA: VAV (schematic envelope)',
 'All flex routes include 0.50 m allowance.', 'Maximum calculated flex: 3.474 m',
 'Flex limit: 4 m (FSD 2023 cl. 7.2)', 'Assignment limit: 5 m',
 'Duct sizes: width x height, mm', 'Main velocity <= 5.0 m/s', 'Branch velocity <= 4.5 m/s',
 'Straight rigid friction <= 0.8 Pa/m', 'Rectangular aspect ratio <= 4:1',
 'ADPI REVIEW REMAINS OPEN:', '7 outlets fail initial course screen.',
 'Manufacturer pattern classification', 'requires resolution before acceptance.',
 'Ceiling / beam clearances assumed;', 'coordinate before construction.',
 'AHU corridor crossing requires fire', 'enclosure / boundary protection review.',
 'Source architecture retained.', 'See CSVs for all 30 rigid sections.'
]
for i,t in enumerate(notes):text(45900,29900-i*850,t,'M-REVIEW' if i in [2,22,23,24,25] else 'M-TEXT',210 if i>1 else 300)
line((-500,-1800),(55000,-1800),'M-TEXT')
text(0,-2900,'TYPICAL FLOOR / SUPPLY AIR SINGLE-LINE PLAN',h=450)
text(0,-3700,'HV-01    |    A2 1:100    |    2026-11-08    |    DESIGN REVIEW v01',h=250)
line((0,-1000),(5000,-1000),'M-TEXT')
for x in [0,1000,2000,3000,4000,5000]:line((x,-1100),(x,-900),'M-TEXT')
text(0,-700,'0                      5 m',h=200)
add('(command "_.ZOOM" "_E")');add('(command "_.QSAVE")')
pdf=R/'03_Design_Drawings/BSE3227_HVAC_Review_v01.pdf'
if pdf.exists():pdf.unlink()
add(f'(command "_.-PLOT" "_Y" "Model" "DWG To PDF.pc3" "ISO full bleed A2 (594.00 x 420.00 MM)" "_M" "_L" "_N" "_W" "{O[0]-1500},{O[1]-5000}" "{O[0]+56500},{O[1]+33500}" "1:100" "_C" "_Y" "" "_Y" "_A" "{pdf.as_posix()}" "_Y" "_Y")')
add('(command "_.QSAVE")')
run(work,cmd,'review_layout',True)
shutil.copy2(work,R/'03_Design_Drawings/BSE3227_HVAC_Review_v01.dwg')
print('Native review layout saved:',pdf)
