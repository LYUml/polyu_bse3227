import json,re,hashlib
from pathlib import Path
from pypdf import PdfReader
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');p=base/'runs/manufacturer-linear-slot-layout/frame-b-clearance-corrected';pdf=base/'project/adpi-manufacturer-study/linear-slot-source/1900 Boot Performance.pdf';reader=PdfReader(pdf);a=json.loads((p/'allocation.json').read_text());tables={}
for width,startpage in [(.5,0),(.75,4),(1.,8)]:
 for slots in [2,4]:
  page=startpage+slots-1;rows=[]
  for line in reader.pages[page].extract_text().splitlines():
   v=line.split()
   if len(v)==23 and v[0].isdigit() and re.fullmatch(r'0?\.\d+',v[1]):rows.append(v)
  assert len(rows)==55
  for inlet,start in [(6,5),(8,20),(10,35),(12,45)]:
   key=f'{width}inch-{slots}slots-{inlet}inlet';tables[key]=dict(slot_width_inch=width,slots=slots,inlet_inch=inlet,pdf_page=page+1,rows=[dict(flow_L_s=float(v[9]),static_Pa=float(v[10]),total_Pa=float(v[11]),T075_m=float(v[12]),T050_m=float(v[14]),T025_m=float(v[16])) for v in rows[start:start+5]])
results=[]
for t in a['terminals']:
 options=[key for key,table in tables.items() if table['rows'][0]['flow_L_s']<=t['minimum_flow_L_s']<=t['maximum_flow_L_s']<=table['rows'][-1]['flow_L_s']]
 results.append(dict(id=t['id'],minimum_flow_L_s=t['minimum_flow_L_s'],maximum_flow_L_s=t['maximum_flow_L_s'],source_domain_eligible=options))
r=dict(scope='All published even-slot BOOT4ft domains only, no bare-diffuser throw/pressure substitution',source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),tables=tables,results=results,covered_terminals=sum(bool(t['source_domain_eligible']) for t in results),assembly_design_accepted=False);(p/'All Boot Domain Combinations.json').write_text(json.dumps(r,indent=2));print('covered',r['covered_terminals'],'of63');print('uncovered',[(t['id'],round(t['minimum_flow_L_s'],2),round(t['maximum_flow_L_s'],2)) for t in results if not t['source_domain_eligible']])
