import json,hashlib
from pathlib import Path
import fitz
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
out=base/'runs/manufacturer-linear-slot-layout'
pdf=base/'project/adpi-manufacturer-study/linear-slot-source/1900 Supply Performance.pdf'
c=json.loads((out/'first-candidate.json').read_text())
words=fitz.open(pdf)[9].get_text('words')
checks=[]
for row,y in zip(c['source_rows'],[198.54258,208.98258,219.42258,229.86258,240.30258]):
 for key,lo,hi in [('flow_L_s_m',260,280),('static_Pa',285,315),('T075_m',383,400),('T050_m',404,420),('T025_m',423,444)]:
  hits=[w for w in words if abs(w[1]-y)<.06 and lo<w[0]<hi and w[4] != '-']
  assert len(hits)==1,(key,y,hits)
  value=float(hits[0][4]);assert value==row[key],(key,value,row[key])
  checks.append(dict(field=key,source_y=y,value=value,matched=True))
r=dict(scope='Independent native PDF word-coordinate check of metric two-way horizontal two-slot performance; NC not checked here',source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),pdf_page=10,scalar_checks=checks,passed=len(checks)==25,design_accepted=False)
(out/'independent-performance-check.json').write_text(json.dumps(r,indent=2))
print(json.dumps(dict(passed=r['passed'],scalar_checks=len(checks),out_of_boundary=[v['id'] for v in c['results'] if not v['segment_inside']],fresh_allocation_check=c.get('fresh_allocation_check'))))

