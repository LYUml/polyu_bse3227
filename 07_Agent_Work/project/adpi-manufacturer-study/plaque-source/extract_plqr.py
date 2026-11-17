from pathlib import Path
import json,re
from pypdf import PdfReader
from bsa.terminal_performance import calculate
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');S=P/'07_Agent_Work/project/adpi-manufacturer-study/plaque-source';B=P/'07_Agent_Work/runs';t=PdfReader(S/'PLQ 5PLQ PLQR MiniCatalog.pdf').pages[14].extract_text();rows=[]
for line in t.splitlines():
 parts=re.sub(r'^(?:(6|8|10|12|14|15)[\u201d"]|Dia\.)\s+','',line.strip()).split()
 if len(parts)!=25 or any(parts[i]!='-' for i in (5,7,15,17)):continue
 try:q,ps,pt,t75,t50,t25=map(float,[parts[i] for i in (11,12,13,14,16,18)])
 except ValueError:continue
 rows.append({'flow_L_s':q,'static_pressure_Pa':ps,'total_pressure_Pa':pt,'T075_m':t75,'T050_m':t50,'T025_m':t25,'NC':None if parts[9]=='-' else float(parts[9]),'NC_qualifier':'less than10' if parts[9]=='-' else 'catalogue value'})
assert len(rows)==54;tables={str(neck):rows[i*9:(i+1)*9] for i,neck in enumerate((6,8,10,12,14,15))};assert [x[0]['flow_L_s'] for x in tables.values()]==[19,33,51,74,101,116]
import csv,hashlib
source=P/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv';course=list(csv.DictReader(source.open()));assert len(course)==640;evaluations=[]
terminal_flows={}
for row in course:terminal_flows.setdefault(row['terminal'],set()).add(float(row['flow_L_s']))
allowed={tid:[neck for neck,table in tables.items() if table[0]['flow_L_s']<=min(qs) and max(qs)<=table[-1]['flow_L_s']] for tid,qs in terminal_flows.items()};assert len(allowed)==80 and all(allowed.values())
selected={tid:necks[0] for tid,necks in allowed.items()}
for row in course:
 q=float(row['flow_L_s']);L=float(row['L_m']);neck=selected[row['terminal']];v=calculate(tables[neck],q);assert v['status']=='within_catalogue'
 evaluations.append({'terminal':row['terminal'],'candidate_neck_inch':int(neck),'condition':row['case'],'direction':row['direction'],'flow_L_s':q,'T025_m':v['T025_m'],'planar_diagnostic_L_m':L,'ratio':v['T025_m']/L})
assert len(evaluations)==640
out=B/'manufacturer-plqr-source';out.mkdir(exist_ok=True);(out/'source-tables.json').write_text(json.dumps(tables,indent=2));(out/'current-layout-diagnostic.json').write_text(json.dumps({'source_course_csv_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'product':'PLQR24x24 no damper; per-terminal smallest neck covering both published flow domains, diagnostic choice only','available_necks_by_terminal':allowed,'candidate_necks_by_terminal':selected,'pattern':'Manufacturer expanding square discharge pattern; Type9 correspondence still requires explicit applicability review','rows':evaluations,'all160_operating_flows_within_published_domain':True,'ADPI_curves_applied':False,'ADPI_verified':False,'design_adopted':False},indent=2));print(json.dumps({'source_rows':len(rows),'operating_conditions':160,'diagnostic_direction_cases':len(evaluations),'ratio_min':min(x['ratio'] for x in evaluations),'ratio_max':max(x['ratio'] for x in evaluations),'all_flows_covered':True,'neck_counts':{n:list(selected.values()).count(n) for n in set(selected.values())},'ADPI_verified':False}))
