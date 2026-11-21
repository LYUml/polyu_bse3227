from pathlib import Path
import json,csv,math,sys,shutil,subprocess,re
import numpy as np,ezdxf
from shapely.geometry import shape,LineString,Point,Polygon
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak
from pypdf import PdfReader,PdfWriter
B=Path.cwd(); O=B/'05_Calculations/Grid13'; R=B/'07_Agent_Work/runs'; I=R/'course-refined-report-inputs'; S=B/'00_Submit'; O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def save(name,data):
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
alloc=read(I/'allocation.json')['terminals']; old={t['id']:np.array(t['center_m'])*1000 for t in alloc}
doc=ezdxf.readfile(R/'course-diffuser-native-final/reopened/source-export.dxf'); m=doc.modelspace()
space=shape(read(B/'07_Agent_Work/project/bse3227-column-row-candidate/office-boundary.geojson'))
tiles=[]
for e in m.query('LWPOLYLINE[layer=="Ceiling Grid"]'):
 p=np.array(e.get_points('xy'))
 if e.closed and len(p)==4 and np.allclose(np.ptp(p,axis=0),600) and np.all(np.isclose(p-p.min(0),0)|np.isclose(p-p.min(0),600)) and space.buffer(.00001).covers(Polygon(p/1000)):tiles.append(p.mean(0))
tiles=np.array(tiles);pos={};term=[];rat=[];cat=np.array(read(B/'05_Calculations/data/diffuser_performance_rows.json')['data']['600 panel / 8in neck'])
for t in alloc:
 k=t['id'];cell=shape(t['geometry']); pos[k]=next(tiles[j] for j in np.argsort(np.linalg.norm(tiles-old[k],axis=1)) if cell.covers(Point(tiles[j]/1000)))
assert len(set(tuple(p) for p in pos.values()))==80
gr=rows(I/'VAV Connection Schedule.csv'); vc=read(I/'vav-centres.json');lens={}; flows={}
for t in alloc:
 k=t['id'];x,y=pos[k]/1000;q=t['maximum_flow_L_s']*12/11;flows[k]=q
 term.append(dict(ID=k,X_m=x,Y_m=y,Qmax_Ls=q,Qmin_Ls=q*.4,grid_shift_mm=np.linalg.norm(pos[k]-old[k])))
 for direction,(dx,dy) in dict(east=(1,0),west=(-1,0),north=(0,1),south=(0,-1)).items():
  origin=Point(x,y); ray=LineString([(x,y),(x+dx*100,y+dy*100)]); L=origin.distance(space.boundary.intersection(ray)); ref='boundary'
  for j,p in pos.items():
   a,b=p/1000-[x,y];dist=a*dx+b*dy
   if abs(a*dy-b*dx)<.001 and .001<dist and dist<=L*2+.000001 and space.buffer(.000001).covers(LineString([(x,y),p/1000])) and dist/2<L:L=dist/2;ref=j
  for case,v in [('max',q),('min',q*.4)]:
   assert cat[0,0]<=v<=cat[-1,0];T=np.interp(v,cat[:,0],cat[:,1]);rat.append(dict(ID=k,direction=direction,case=case,Q_Ls=v,L_m=L,reference=ref,T025_m=T,ratio=T/L))
for g in gr:
 ids=g['Diffuser outlets'].split(', ');q=sum(flows[k] for k in ids);ds=[np.linalg.norm(pos[k]/1000-vc[g['VAV']]) for k in ids];lens.update(zip(ids,ds));g.update({'Qmax L/s':f'{q:.1f}','Qmin L/s':f'{.4*q:.1f}','Min plan m':f'{min(ds):.3f}','Max plan m':f'{max(ds):.3f}'})
sys.path.insert(0,str(B/'05_Calculations/scripts'));from friction import rectangular
duct=[]
for r in rows(B/'05_Calculations/Connection_Layout/Online Ductulator Check.csv'):
 q=float(r['Flow L/s'])*12/11;lim=float(r['Velocity limit m/s']);cand=[]
 for h in range(250,601,50):
  for w in range(h,4*h+1,50):
   z=rectangular(q,w,h)
   if z['velocity_ms']<=lim and z['friction_Pa_m']<=1:cand.append((w*h,w/h,w,h,z))
 _,_,w,h,z=min(cand);duct.append(dict(ID=r['Section'],Q_Ls=q,W_mm=w,H_mm=h,V_ms=z['velocity_ms'],Calc_Pa_m=z['friction_Pa_m'],Vlimit_ms=lim))
save('Duct Sizing.csv',duct);save('VAV Connection Schedule.csv',gr);save('Diffuser Course Ratio Check.csv',rat);save('Grid locations.csv',term)
def edit_table(space,layer,values):
 tx=list(space.query(f'TEXT[layer=="{layer}"]'))
 for k,vals in values.items():
  tag=next(e for e in tx if e.dxf.text==k); cells=sorted((e for e in tx if abs(e.dxf.insert.y-tag.dxf.insert.y)<1e-7),key=lambda e:e.dxf.insert.x);assert len(vals)==len(cells)
  for e,v in zip(cells,vals):e.dxf.text=v
edit_table(m,'BSA_SCHEDULE',{r['ID']:[r['ID'],f"{r['Q_Ls']:.1f}",f"{r['W_mm']} x {r['H_mm']}",f"{r['V_ms']:.2f}",f"{r['Calc_Pa_m']:.3f}"] for r in duct})
for e in m.query('TEXT[layer=="BSA_SCHEDULE"]'):
 if e.dxf.text=='Pa/m':e.dxf.text='Calc Pa/m'
for e in m.query('TEXT[layer=="BSA_NOTES"]'):
 if 'Flex design' in e.dxf.text:e.dxf.text=f"24/13 C; max XY + 0.50 m = {max(lens.values())+.5:.3f} m."
for e in m.query('LWPOLYLINE[layer=="BSA_DIFFUSER"]'):
 p=np.array(e.get_points('xy')).mean(0);k=min(old,key=lambda k:np.linalg.norm(old[k]-p));assert np.linalg.norm(old[k]-p)<.001;e.translate(*(pos[k]-old[k]),0)
for e in m.query('LINE[layer=="BSA_FLEX"]'):
 for attr in ['start','end']:
  p=np.array(e.dxf.get(attr))[:2];k=min(old,key=lambda k:np.linalg.norm(old[k]-p))
  if np.linalg.norm(old[k]-p)<.001:e.dxf.set(attr,(*pos[k],0));break
 else:raise ValueError('unmatched flex')
for e in m.query('TEXT[layer=="BSA_LABEL"]'):
 if e.dxf.text in old:e.translate(*(pos[e.dxf.text]-old[e.dxf.text]),0)
vdoc=ezdxf.readfile(R/'course-refined-vav-table/native/reopened/source-export.dxf');edit_table(vdoc.modelspace(),'BSA_VAV_TABLE',{g['VAV']:list(g.values()) for g in gr})
for d,name,template in [(doc,'Supply Air Distribution',R/'course-diffuser-native-final/Supply Air Distribution.scr'),(vdoc,'VAV Connection Schedule',R/'course-refined-vav-table/native/Supply Air Distribution.scr')]:
 base=O/name; base.with_suffix('.dwg').unlink(missing_ok=True);base.with_suffix('.pdf').unlink(missing_ok=True);d.saveas(base.with_suffix('.dxf'))
 for stage,script,ext in [('save',R/'course-refined-vav-table/native/save.scr','.dxf'),('plot',template,'.dwg')]:
  s=re.sub(r'C:/[^"]+/Supply Air Distribution(?=\.(?:pdf|dwg|dxf))',base.as_posix(),script.read_text());sc=O/(name+stage+'.scr');sc.write_text(s);exe=r'C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe'
  subprocess.run([exe,'/i',str(base.with_suffix(ext)),'/s',str(sc)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90);assert base.with_suffix('.dwg' if stage=='save' else '.pdf').exists()


subprocess.run([sys.executable, str(O/'restored.py')], check=True)

