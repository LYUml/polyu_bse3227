import fitz,json
from pathlib import Path
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');out=base/'runs/manufacturer-linear-slot-layout/boundary-corrected';r=json.loads((out/'slot-count-selection.json').read_text());doc=fitz.open(base/'project/adpi-manufacturer-study/linear-slot-source/1900 Supply Performance.pdf');n=0
for width,table in r['tables'].items():
 words=doc[table['pdf_page']-1].get_text('words'); shifted=table['pdf_page'] in (1,7); qlo,qhi=(280,300) if shifted else (260,280);anchors=sorted([w for w in words if qlo<w[0]<qhi and w[4].isdigit()],key=lambda w:w[1])
 # first five horizontal rows are one-slot; next five are two-slot.
 assert len(anchors)>=10
 for row,anchor in zip(table['rows'],anchors[(table['slots']-1)*5:table['slots']*5]):
  ranges=[('flow_L_s_m',qlo,qhi),('static_Pa',305,335),('T075_m',403,422),('T050_m',422,441),('T025_m',441,465)] if shifted else [('flow_L_s_m',260,280),('static_Pa',285,315),('T075_m',383,400),('T050_m',401,422),('T025_m',423,447)]
  for key,lo,hi in ranges:
   hits=[w for w in words if abs(w[1]-anchor[1])<.06 and lo<w[0]<hi and w[4]!='-'];assert len(hits)==1,(width,key,hits)
   assert float(hits[0][4])==row[key],(width,key,hits,row);n+=1
check=dict(scope='Independent native word-coordinate check, four widths, published even slot counts, two-way horizontal, metric q/Ps/three throws',scalar_checks=n,passed=n==350,source_sha256=r['performance_source_sha256'])
(out/'slot-count-source-verification.json').write_text(json.dumps(check,indent=2));print(check)
print('flow gaps',[(v['id'],v['best']) for v in r['results'] if v['best']['out_of_table_flow_cases']])
