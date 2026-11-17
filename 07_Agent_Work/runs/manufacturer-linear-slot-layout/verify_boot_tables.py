import fitz,json
from pathlib import Path
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');p=base/'runs/manufacturer-linear-slot-layout/boot-first-row-four-strip-services';r=json.loads((p/'All Boot Domain Combinations.json').read_text());d=fitz.open(base/'project/adpi-manufacturer-study/linear-slot-source/1900 Boot Performance.pdf');n=0
for key,t in r['tables'].items():
 words=d[t['pdf_page']-1].get_text('words');q=sorted([w for w in words if 310<w[0]<330 and 130<w[1]<690 and w[4].isdigit()],key=lambda w:w[1]);assert len(q)==55
 start={6:5,8:20,10:35,12:45}[t['inlet_inch']]
 for j,row in enumerate(t['rows']):
  anchor=q[start+j]
  for field,lo,hi in [('flow_L_s',310,330),('static_Pa',333,361),('total_Pa',361,385),('T075_m',388,408),('T050_m',408,427),('T025_m',427,450)]:
   hits=[w for w in words if abs(w[1]-anchor[1])<.2 and lo<w[0]<hi and w[4]!='-'];assert len(hits)==1,(key,j,field,hits)
   assert float(hits[0][4])==row[field],(key,j,field,hits,row);n+=1
out=dict(scope='Independent native PDF coordinate verification of4ft BOOT totalflow/static/totalpressure/three throws; no direction/baffle condition inferred',source_sha256=r['source_sha256'],scalar_checks=n,passed=n==720);(p/'Boot Full Table Source Check.json').write_text(json.dumps(out,indent=2));print(out)
