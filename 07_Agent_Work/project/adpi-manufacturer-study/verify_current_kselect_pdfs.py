from pathlib import Path
import fitz,json,hashlib,math
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';W=B/'current-course-kselect-all-conditions'
manifest=json.loads((W/'batch-complete.json').read_text());records=[];checks=0
for record in manifest['records']:
 folder=Path(record['folder']);result=json.loads((folder/'result.json').read_text());pdf=folder/'performance.pdf'
 assert result['ok'] and all(result['checks'].values())
 assert hashlib.sha256(pdf.read_bytes()).hexdigest()==record['pdf_sha256']==result['report']['sha256']
 d=fitz.open(pdf);assert len(d)==1;words=d[0].get_text('words')
 def field(y,lo,hi):
  a=[t[4] for t in words if abs(t[1]-y)<.25 and lo<(t[0]+t[2])/2<hi]
  assert len(a)==1,(record['effective_cfm'],y,lo,a)
  return a[0]
 selected={}
 for name,lo,hi in [('airflow_cfm',120,140),('throw_ft',258,282),('nc_reported',365,383),('pressure_in_wc',510,533)]:
  value=float(field(344.4,lo,hi));selected[name]=value
  expected=result['report']['nc_reported'] if name=='nc_reported' else result['report']['selected'][name]
  assert value==expected,(name,value,expected);checks+=1
 anchors=sorted([t for t in words if abs(t[1]-235.7)<.25 and t[0]>150 and t[4].isdigit()],key=lambda t:t[0]);assert len(anchors)==9
 for j,anchor in enumerate(anchors):
  x=(anchor[0]+anchor[2])/2
  for key,y in [('velocity_fpm',217.7),('airflow_cfm',235.7),('throw_ft',253.7),('nc',271.7),('pressure_in_wc',289.7)]:
   value=field(y,x-5,x+5);value=None if value=='-' else float(value)
   assert value==result['report']['table'][key][j],(record['effective_cfm'],j,key,value)
   checks+=1
 assert selected['airflow_cfm']==record['effective_cfm']
 assert math.isclose(selected['throw_ft']*.3048,result['report']['si']['throw_m'],rel_tol=1e-12)
 records.append({'effective_cfm':record['effective_cfm'],'native_selected':selected,'usable_nc':result['report']['selected']['nc'],'pdf_sha256':record['pdf_sha256'],'pdf_native_table_and_selection_match':True})
r={'independent_reader':'PyMuPDF1.26.7 native word bounding boxes; separate from toolkit pypdf parsing','native_reports':len(records),'scalar_checks':checks,'all_native_selected_fields_and9column_tables_match':True,'records':records,'engineering_accepted':False}
(W/'independent-native-report-check.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='records'}))
