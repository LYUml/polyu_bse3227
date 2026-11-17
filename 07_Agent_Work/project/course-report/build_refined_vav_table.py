import json,csv,math,hashlib
from pathlib import Path
import ezdxf
from bsa.vav_schedule import rows_from,author,cells,HEADERS
from bsa.duct_sheet_native import run
from bsa.native_cad import DEFAULT_EXE
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');I=B/'07_Agent_Work/runs/course-refined-report-inputs'
R=B/'07_Agent_Work/runs/course-refined-vav-table';R.mkdir(exist_ok=False)
a=json.loads((I/'allocation.json').read_text());t={x['id']:x for x in a['terminals']};centres=json.loads((I/'vav-centres.json').read_text());groups=list(csv.DictReader((I/'VAV Connection Schedule.csv').open()))
review=dict(groups=[])
for g in groups:
    members=g['Diffuser outlets'].split(', ');review['groups'].append(dict(id=g['VAV'],outlet_count=4,maximum_flow_L_s=sum(t[k]['maximum_flow_L_s'] for k in members),routes=[dict(terminal=k,plan_length_m=math.dist(t[k]['center_m'],centres[g['VAV']])) for k in members]))
rows=rows_from(review,a);dxf=R/'VAV Connection Schedule.dxf';labels,ref=author(rows,dxf)
settings=dict(source_sha256=hashlib.sha256(dxf.read_bytes()).hexdigest(),layers=['BSA_VAV_TABLE'],sheet=dict(source='Generated native-coordinate connection table; 100 mm print reference',window_drawing_units=[0,0,290,200],scale_denominator=1,reference_handle=ref,pdf_tolerance_mm=.2))
(R/'native-settings.json').write_text(json.dumps(settings,indent=2));native=run(dxf,R/'native-settings.json',R/'native',DEFAULT_EXE)
(R/'rows.json').write_text(json.dumps(rows,indent=2));(R/'review.json').write_text(json.dumps(native,indent=2));print(json.dumps(native))
