import json,math,hashlib,subprocess,sys,csv,importlib.metadata
from pathlib import Path
import fitz
A=Path('C:/Users/lyuml-win/Desktop/building-services-agent');B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'three-dimensional-outlet-candidate';O=R/'manufacturer-friction-source-reviewed';O.mkdir(exist_ok=False);pdf=R/'Friction Loss Charts.pdf';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lock=json.loads((A/'adapters/pdf2plot/lock.json').read_text());helper=A/'tools/pdf2plot-99a8ee1/pdf2plot_helper.py';assert sha(helper)==lock['files']['pdf2plot_helper.py'] and importlib.metadata.version('PyMuPDF')=='1.26.7'
doc=fitz.open(pdf);page=doc[1];paths=page.get_drawings();box=paths[31]['rect'];left,top,right,bottom=list(box);assert paths[31]['items'][0][0]=='qu';stroke=paths[36];assert len(stroke['items'])==1 and stroke['items'][0][0]=='l' and stroke['width']==1.;points=[list(p) for p in stroke['items'][0][1:]];assert points==[[98.70999908447266,289.6679992675781],[218.44400024414062,221.7559814453125]];assert any(w[4]=='8”' and 90<w[0]<92 and 289<w[1]<290 for w in page.get_text('words'))
raw=dict(canvas=dict(height=page.rect.height),paths=[dict(id=0,points=[dict(x=x,y=page.rect.height-y) for x,y in points])]);(O/'native-paths.json').write_text(json.dumps(raw));args=[sys.executable,'-X','utf8',str(helper),'export',str(O/'native-paths.json'),'--x-left',f'@{left}:0.01','--x-right',f'@{right}:0.1','--y-bottom',f'@{bottom}:30','--y-top',f'@{top}:5000','--x-log','--y-log','--data','0','--output',str(O/'calibrated.csv')];proc=subprocess.run(args,capture_output=True,text=True,encoding="utf-8");(O/'export.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0;cal=list(csv.DictReader((O/'calibrated.csv').open()));assert len(cal)==2
native=[]
for (x,y),row in zip(points,cal):
 actual=[.01*10**((x-left)/(right-left)),30*math.exp((bottom-y)/(bottom-top)*math.log(5000/30))];assert all(math.isclose(v,float(row[k]),rel_tol=6e-6) for k,v in zip(['x','y'],actual));native.append(actual)
# Held-out native grid lines are independent of the two source curve points.
checks=[]
for index,q in [(7,1000.),(12,500.),(24,300.)]:
 y=paths[index]['items'][0][1].y;pred=bottom-(bottom-top)*math.log(q/30)/math.log(5000/30);checks.append(dict(axis='flow',value=q,residual_pdf_points=abs(y-pred)))
for index,p in [(17,.03),(19,.05)]:
 x=paths[index]['items'][0][1].x;pred=left+(right-left)*math.log10(p/.01);checks.append(dict(axis='pressure',value=p,residual_pdf_points=abs(x-pred)))
assert max(c['residual_pdf_points'] for c in checks)<1.
qlo,qhi=[r[1] for r in native];plo,phi=[r[0] for r in native];rows=[];model=json.loads((R/'review.json').read_text())
for route in model['records']:
 straight=math.fsum(p['length_m'] for p in route['pieces'] if p['kind']=='straight')
 for condition,flow in route['source_flows'].items():
  q=flow['flow_m3_s']/0.0004719474432;inside=qlo<=q<=qhi
  p=None if not inside else math.exp(math.log(plo)+(math.log(q)-math.log(qlo))*(math.log(phi)-math.log(plo))/(math.log(qhi)-math.log(qlo)));pa_m=None if p is None else p*249.08891/3.048
  rows.append(dict(terminal=route['terminal'],vav=route['vav'],condition=condition,flow_CFM=q,status='bounded_source_curve' if inside else 'outside_visible_source_fragment',manufacturer_inH2O_per10ft=p,manufacturer_straight_Pa_m=pa_m,native_straight_length_m=straight,manufacturer_straight_only_Pa=None if pa_m is None else pa_m*straight,bend_pressure_Pa=None,complete_branch_pressure_Pa=None))
result=dict(source_pdf_sha256=sha(pdf),source_url='https://www.flexmasterusa.com/Portals/2/pg/files/sdp/Acc/Friction_Loss_Charts.pdf',pdf_page=2,printed_page=19,diameter_in=8,source_pressure_axis_unit='inH2O per10ft,NOTper100ft',curve_identity='Visually inspected8in straight-run TripleLock line,nativepath36 right-of-label fragment only',support_flow_CFM=[qlo,qhi],native_grid_checks=checks,source_stroke_pdf_points=1.,upstream_helper_sha256=sha(helper),upstream_commit=lock.get('commit'),calibration_points_independently_reconciled=True,rows=rows,counts={c:dict(supported=sum(r['condition']==c and r['status']=='bounded_source_curve' for r in rows),unsupported=sum(r['condition']==c and r['status']!='bounded_source_curve' for r in rows)) for c in ['maximum','minimum']},bend_chart_applicability='Radius/equivalent-length chart lacks explicit angle basis;no90degree or partial-angle correction adopted',product_selected=False,physical_geometry_is_smooth_proxy=True,pressure_budget_complete=False,design_accepted=False);(O/'review.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ['support_flow_CFM','counts','source_pdf_sha256']}))


