from pathlib import Path
import fitz,json,hashlib
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');W=P/'current-course-kselect-all-conditions'
records=json.loads((W/'batch-complete.json').read_text())['records'];checks=0;pins=[]
for r in records:
 folder=Path(r['folder']);pdf=folder/'performance.pdf';before=hashlib.sha256(pdf.read_bytes()).hexdigest();assert before==r['pdf_sha256']
 a=json.loads((folder/'result.json').read_text());w=fitz.open(pdf)[0].get_text('words')
 def field(y,lo,hi):
  vals=[t[4] for t in w if abs(t[1]-y)<.25 and lo<(t[0]+t[2])/2<hi];assert len(vals)==1;return float(vals[0])
 anchors=sorted([t for t in w if abs(t[1]-235.7)<.25 and t[0]>150 and t[4].isdigit()],key=lambda t:t[0]);assert len(anchors)==9
 for j,t in enumerate(anchors):
  x=(t[0]+t[2])/2;assert field(289.7,x-5,x+5)==a['report']['table']['pressure_in_wc'][j];checks+=1
 assert field(344.4,510,533)==a['report']['selected']['pressure_in_wc'];checks+=1
 assert hashlib.sha256(pdf.read_bytes()).hexdigest()==before
 pins.append({'effective_CFM':r['effective_cfm'],'pdf_sha256':before,'result_json_sha256':hashlib.sha256((folder/'result.json').read_bytes()).hexdigest()})
out={'scope':'Fresh independent native-PDF pressure-field check for this pressure comparison; no software re-execution','native_pressure_scalar_checks':checks,'all49_nine_column_pressure_tables_and_selected_pressures_match':True,'native_PDFs_unchanged':True,'source_records':pins}
(P/'current-native-terminal-pressure/native-pressure-source-recheck.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(checks)
