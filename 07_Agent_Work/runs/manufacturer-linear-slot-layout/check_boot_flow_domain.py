import json,re,hashlib
from pathlib import Path
from pypdf import PdfReader
base=Path(r'C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');p=base/'runs/manufacturer-linear-slot-layout/frame-b-clearance-corrected';pdf=base/'project/adpi-manufacturer-study/linear-slot-source/1900 Boot Performance.pdf';reader=PdfReader(pdf);a=json.loads((p/'allocation.json').read_text());d=json.loads((p/'Boot Width Compatible Diagnostic.json').read_text());tables={};results=[]
for t,v in zip(a['terminals'],d['results']):
 key=v['best']['slot_width_inch'];meta=d['tables'][key];page={.5:0,.75:4,1.:8}[float(meta['slot_width_inch'])]+meta['slots']-1
 if key not in tables:
  rows=[]
  for line in reader.pages[page].extract_text().splitlines():
   parts=line.split()
   if len(parts)==23 and parts[0].isdigit() and re.fullmatch(r'0?\.\d+',parts[1]):rows.append(parts)
  assert len(rows)==55,(key,len(rows))
  tables[key]=dict(pdf_page=page+1,inlets={str(inlet):[dict(flow_L_s=float(v[9]),static_Pa=float(v[10]),total_Pa=float(v[11]),T075_m=float(v[12]),T050_m=float(v[14]),T025_m=float(v[16])) for v in rows[start:start+5]] for inlet,start in [(6,5),(8,20),(10,35),(12,45)]})
 coverage=[inlet for inlet,rows in tables[key]['inlets'].items() if rows[0]['flow_L_s']<=t['minimum_flow_L_s']<=t['maximum_flow_L_s']<=rows[-1]['flow_L_s']]
 results.append(dict(id=t['id'],bare_diffuser_choice=key,bare_paired_curve_pass=v['best']['all_checks_pass'],inlets_covering_both_flows=coverage,minimum_flow_L_s=t['minimum_flow_L_s'],maximum_flow_L_s=t['maximum_flow_L_s']))
r=dict(scope='Published BOOT assembly4ft flow-domain screen only; no throw-pattern transfer or pressure adopted',source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),tables=tables,results=results,terminals_with_any_published_inlet_covering_both_flows=sum(bool(t['inlets_covering_both_flows']) for t in results),bare_diffuser_paired_pass=sum(t['bare_paired_curve_pass'] for t in results),assembly_ADPI_accepted=False)
(p/'Boot Assembly Flow Domain Diagnostic.json').write_text(json.dumps(r,indent=2));print('bothflowcovered',r['terminals_with_any_published_inlet_covering_both_flows'],'of63, barepairedpass',r['bare_diffuser_paired_pass'],'tablegroups',len(tables))
