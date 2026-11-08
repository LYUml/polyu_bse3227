"""Three actual office diffusers; test native save/reopen and plotted legibility."""
from pathlib import Path
import shutil, json
from cad_native import ROOT,CACHE,run,sha

O=(64345.93225182503,15925.58365525945)
def pt(x,y):return f'({O[0]+x:.8f} {O[1]+y:.8f} 0.0)'
def poly(points,layer):
    return '(entmakex \'((0 . "LWPOLYLINE") (100 . "AcDbEntity") (8 . "'+layer+'") (100 . "AcDbPolyline") (90 . '+str(len(points))+') (70 . 1) '+ ' '.join(f'(10 {O[0]+x:.8f} {O[1]+y:.8f})' for x,y in points)+'))'
work=ROOT/'05_Calculations/cad/BSE3227_Sample_v01.dwg'
shutil.copy2(ROOT/'01_Assignment_Brief/Building_Drawings/Project layout.dwg',work)
cmd=['(setvar "TILEMODE" 1)','(setvar "BACKGROUNDPLOT" 0)',
     '(command "_.-LAYER" "_M" "M-SUP-DIFF" "_C" "4" "M-SUP-DIFF" "_LW" "0.30" "M-SUP-DIFF" "")',
     '(command "_.-LAYER" "_M" "M-TEXT" "_C" "7" "M-TEXT" "")',
     '(command "_.-LAYER" "_C" "8" "ARCH" "_C" "9" "Ceiling Grid" "")']
for i,x in enumerate([2880,8280,13680],1):
    y=2970
    cmd += [poly([(x-300,y-300),(x+300,y-300),(x+300,y+300),(x-300,y+300)],'M-SUP-DIFF'),
            poly([(x-160,y-160),(x+160,y-160),(x+160,y+160),(x-160,y+160)],'M-SUP-DIFF')]
    cmd.append(f'(entmakex \'((0 . "TEXT") (8 . "M-TEXT") (10 {O[0]+x-300:.8f} {O[1]+y+500:.8f} 0) (40 . 250) (1 . "SD-{i:02} / SAMPLE") (7 . "Standard")))')
cmd+=['(command "_.ZOOM" "_E")','(command "_.QSAVE")']
pdf=CACHE/'three_diffuser_sample.pdf'
if pdf.exists():pdf.unlink()
cmd += [f'(command "_.-PLOT" "_Y" "Model" "DWG To PDF.pc3" "ISO full bleed A3 (420.00 x 297.00 MM)" "_M" "_L" "_N" "_W" "{O[0]},{O[1]}" "{O[0]+17000},{O[1]+11000}" "1:50" "_C" "_Y" "" "_Y" "_A" "{pdf.as_posix()}" "_N" "_Y")']
run(work,cmd,'sample_build',True)
out=CACHE/'sample_reopen.txt'
run(work,[f'(setq f (open "{out.as_posix()}" "w"))','(prin1 (list (getvar "INSUNITS") (sslength (ssget "_X" \'((8 . "M-SUP-DIFF")))) (sslength (ssget "_X" \'((8 . "M-TEXT"))))) f)','(close f)'],'sample_reopen')
print(out.read_text());print(pdf, pdf.exists())
