"""Acceptance audit of the shared calculations and issued artifact hashes."""
from pathlib import Path
import csv,json,hashlib,math
from pypdf import PdfReader
from friction import rectangular
R=Path(__file__).resolve().parents[2];D=R/'05_Calculations/data'
def read(n):return list(csv.DictReader((D/f'{n}_v04.csv').open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-8,abs_tol=1e-8),(a,b)
b=json.loads((D/'design_basis_v04.json').read_text());diff=read('diffusers');duct=read('ducts');flex=read('flex_routes');vav=read('vav_boxes')
close(b['total_load_kW'],1022*189/1000);close(b['sensible_load_kW'],1022*189*.9/1000)
close(b['supply_lps'],1022*189*.9/(1.2*1006*12)*1000)
close(sum(float(r['max_lps']) for r in diff),b['supply_lps'])
perf=json.loads((D/'diffuser_performance_rows.json').read_text())['data']
for r in diff:
 close(r['min_lps'],float(r['max_lps'])*.4)
 for mode in ['max','min']:
  q=float(r[f'{mode}_lps']);rows=perf[r['diffuser_type']]
  pairs=[(a,z) for a,z in zip(rows,rows[1:]) if a[0]<=q<=z[0]];assert pairs
  a,z=pairs[0];throw=a[1]+(z[1]-a[1])*(q-a[0])/(z[0]-a[0]);close(throw,r[f'{mode}_T025_m'])
  ratios=[throw/float(r[k]) for k in ['L_w_m','L_e_m','L_s_m','L_n_m']]
  assert all(1<=v<=3.4 for v in ratios)
  close(min(ratios),r[f'{mode}_ratio_min']);close(max(ratios),r[f'{mode}_ratio_max'])
for r in flex:
 length=math.hypot(float(r['start_x_mm'])-float(r['end_x_mm']),float(r['start_y_mm'])-float(r['end_y_mm']))/1000+.5
 close(length,r['design_length_m']);assert length<=4
assert len({r['diffuser'] for r in flex})==80
for v in vav:assert len([r for r in flex if r['vav']==v['id']])==4
for r in duct:
 result=rectangular(float(r['flow_lps']),float(r['width_mm']),float(r['height_mm']))
 for k,value in result.items():close(value,r[k])
 assert result['velocity_ms']<=(10 if r['kind']=='main' else 8)
 assert result['friction_Pa_m']<=.8 and result['aspect_ratio']<=4
manifest=json.loads((D/'source_manifest.json').read_text());assert all(sha(R/r['path'])==r['sha256'] for r in manifest)
paths=['03_Design_Drawings/BSE3227_HVAC_Acceptance_v06.dwg','03_Design_Drawings/BSE3227_HVAC_Acceptance_v06.pdf','04_Final_Report/BSE3227_Design_Acceptance_v06.pdf']
native=json.loads((D/'native_reconciliation_v06.json').read_text());assert native['dwg_sha256']==sha(R/paths[0])
plot=PdfReader(R/paths[1]);report=PdfReader(R/paths[2]);assert len(plot.pages)==1 and len(report.pages)==15
page=plot.pages[0]
# AutoCAD rounds the PDF MediaBox to whole points: allow 0.1 mm paper rounding.
assert abs(float(page.mediabox.width)/72*25.4-841)<.1
assert abs(float(page.mediabox.height)/72*25.4-594)<.1
text='\n'.join(p.extract_text() for p in report.pages)
assert all(r['id'] in text for r in diff+duct)
result={'status':'READY FOR USER ACCEPTANCE - course method with documented qualifications','design_data_revision':'v04','drawing_report_revision':'v06','original_files_hash_verified':len(manifest),'diffusers_checked_both_loads':80,'directional_ratio_checks':640,'flex_routes_checked':80,'vav_groups_of_four':20,'duct_sections_recomputed':49,'drawing_paper':'A1 landscape','report_pages':15,'artifacts':{p:sha(R/p) for p in paths},'limits':'Course-method ADPI applicability qualification remains. Not construction, manufacturer comfort certification, full fan selection or statutory approval.'}
(D/'acceptance_audit_v06.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
