import tempfile,subprocess,shutil,csv,json,re,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import ezdxf
B=Path.cwd();S=B/'00_Submit';o=Path(tempfile.mkdtemp());old=B/'04_Final_Report/Connection_Layout/BSE3227 HVAC Mini-Design.pdf';new=S/'BSE3227_Group7_report.pdf'
def pdf(p):return subprocess.check_output(['pdftotext','-layout','-enc','UTF-8',str(p),'-']).decode().split('\f')[:-1]
a,b=pdf(old),pdf(new);assert len(a)==18 and len(b)==17
def rr(n):return list(csv.DictReader((S/'Calculations'/n).open()))
def check(page,k,expected):
 lines=[l.split() for l in b[page-1].splitlines() if l.strip().split()[:1]==[k]];assert lines==[[k]+expected],(k,lines,expected)
def dwg(name):
 p=o/(name+'.dwg');shutil.copy2(S/'Drawings'/p.name,p);target=o/(name+'.dxf');sc=o/'export.scr';sc.write_text('(setvar "FILEDIA" 0)\n(command "_.DXFOUT" "'+target.as_posix()+'" "16")\n_.QUIT\n_N\n');subprocess.run([r'C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe','/i',str(p),'/s',str(sc)],stdout=subprocess.DEVNULL,timeout=90);return ezdxf.readfile(target).modelspace()
def cells(m,layer,k):
 ts=list(m.query(f'TEXT[layer=="{layer}"]'));e=next(z for z in ts if z.dxf.text==k);return [z.dxf.text for z in sorted([z for z in ts if abs(z.dxf.insert.y-e.dxf.insert.y)<1e-6],key=lambda z:z.dxf.insert.x)]
m=dwg('Supply Air Distribution');v=dwg('VAV Connection Schedule')
online={r['ID']:r['Online_Pa_m'] for r in rr('Online Ductulator Check.csv')}
for i,r in enumerate(rr('Duct Sizing.csv')):
 k=r['ID'];q,w,h,u,f,lim=map(float,[r[x] for x in ['Q_Ls','W_mm','H_mm','V_ms','Calc_Pa_m','Vlimit_ms']]); check(14+(i>=24),k,[f'{q:.2f}',str(int(w)),chr(215),str(int(h)),f'{u:.3f}',str(lim),f'{f:.4f}',online[k],f'{w/h:.2f}']);assert cells(m,'BSA_SCHEDULE',k)==[k,f'{q:.1f}',f'{w:.0f} x {h:.0f}',f'{u:.2f}',f'{f:.3f}']
for r in rr('VAV Connection Schedule.csv'):
 k=r['VAV'];assert cells(v,'BSA_VAV_TABLE',k)==list(r.values());check(13,k,r['Diffuser outlets'].split()+[r['Qmax L/s'],r['Qmin L/s'],r['Min plan m']+'-'+r['Max plan m']])
rat=rr('Diffuser Course Ratio Check.csv')
for i,t in enumerate(rr('Grid locations.csv')):
 k=t['ID'];rs=[r for r in rat if r['ID']==k];assert len(rs)==8
 check(9+i//40,k,[f"{float(t[x]):.2f}" for x in ['Qmax_Ls','Qmin_Ls']]+[f'{fn(float(r[x]) for r in rs):.3f}' for x in ['T025_m'] for fn in (max,min)]+[f"{fn(float(r['ratio']) for r in rs):.4f}" for fn in (max,min)])
 check(11+i//40,k,[f"{float(next(r['L_m'] for r in rs if r['direction']==d)):.4f}" for d in ['west','east','south','north']])
sheet=Image.new('RGB',(6*180,6*250),'white')
for j,p in enumerate((old,new)):
 subprocess.run(['pdftoppm','-scale-to','240','-png',str(p),str(o/f'p{j}')],check=True)
 for i,z in enumerate(sorted(o.glob(f'p{j}-*.png'))):sheet.paste(Image.open(z),(i%3*360+j*180,i//3*250))
subprocess.run(['pdftoppm','-scale-to','240','-png','-singlefile',str(S/'Drawings/Supply Air Distribution.pdf'),str(o/'drawing')],check=True)
assert ImageChops.difference(Image.open(o/'drawing.png'),Image.open(o/'p1-16.png')).getbbox() is None
out=B/'05_Calculations/Grid13/Page comparison.png';sheet.save(out);print('Verified 17 pages; A/B/C/D and native schedules; embedded plot.',out)
