"""Verify changed candidate fields, preserve main engineering, then publish the appendix."""
from pathlib import Path
import csv,json,hashlib,math,re,shutil
from decimal import Decimal
import ezdxf
from shapely.geometry import shape
from pypdf import PdfReader,PdfWriter
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';R=P/'runs/course-sourced-load-candidate';O=P/'runs/course-report-supplementary-load'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());csvrows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig')))
review=read(O/'review.json');assert review['all16_main_pages_pixel_identical']
main=B/'03_Design_Drawings/Connection_Layout/Supply Air Distribution.dwg';mainplot=main.with_suffix('.pdf');maincalc=B/'05_Calculations/Connection Layout Duct Sizing.csv'
protected={str(p.relative_to(B)):sha(p) for p in [main,mainplot,maincalc,B/'05_Calculations/Connection_Layout/VAV Connection Schedule.csv',B/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv']}
assert sha(main)=='02d7911d791bb94f47c39981f6663c088a29a1c1273bc2a92f32a7165fe4bc60'
allocation=read(R/'allocation.json');terms={t['id']:t for t in allocation['terminals']};old=read(P/'runs/course-refined-report-inputs/allocation.json')
assert len(terms)==80 and all(t['center_m']==terms[t['id']]['center_m'] and abs(t['allocated_load_area_m2']-terms[t['id']]['allocated_load_area_m2'])<1e-12 and shape(t['geometry']).equals(shape(terms[t['id']]['geometry'])) for t in old['terminals'])
assert abs(sum(t['maximum_flow_L_s'] for t in terms.values())-9524.10536779324)<1e-8
assert all(abs(t['minimum_flow_L_s']-.4*t['maximum_flow_L_s'])<1e-12 for t in terms.values())
duct=csvrows(R/'schedule-corridor/schedule.csv');original={v['Section']:v for v in csvrows(maincalc)}
doc=ezdxf.readfile(R/'native/reopened/source-export.dxf');texts=[e for e in doc.modelspace().query('TEXT') if e.dxf.layer=='BSA_SCHEDULE']
for row in duct:
 tag=next(e for e in texts if e.dxf.text==row['Section']);cells=sorted([e for e in texts if abs(e.dxf.insert.y-tag.dxf.insert.y)<1e-8],key=lambda e:e.dxf.insert.x)
 expected=[row['Section'],f"{float(row['Flow L/s']):.1f}",f"{float(row['Width mm']):.0f} x {float(row['Height mm']):.0f}",f"{float(row['Velocity m/s']):.2f}",f"{float(row['Friction Pa/m']):.3f}"]
 assert [e.dxf.text for e in cells]==expected
 assert all(float(row[k])<=float(original[row['Section']][k]) for k in ['Width mm','Height mm'])
 assert abs(float(row['Flow L/s'])/1000/(float(row['Width mm'])*float(row['Height mm'])/1e6)-float(row['Velocity m/s']))<1e-10
 assert not row['Failed criteria']
vav=read(R/'vav/rows.json');table=ezdxf.readfile(R/'vav/native/reopened/source-export.dxf');tt=[e for e in table.modelspace().query('TEXT') if e.dxf.layer=='BSA_VAV_TABLE']
for g in vav:
 assert len(g['terminals'])==4
 assert abs(sum(terms[k]['maximum_flow_L_s'] for k in g['terminals'])-g['maximum_flow_L_s'])<1e-10
 tag=next(e for e in tt if e.dxf.text==g['id']);cells=sorted([e for e in tt if abs(e.dxf.insert.y-tag.dxf.insert.y)<1e-8],key=lambda e:e.dxf.insert.x)
 assert [e.dxf.text for e in cells]==[g['id'],', '.join(g['terminals']),f"{g['maximum_flow_L_s']:.1f}",f"{g['minimum_flow_L_s']:.1f}",f"{g['minimum_plan_length_m']:.3f}",f"{g['maximum_plan_length_m']:.3f}",'4']
for file,throw,ratio in [('Diffuser Course Ratio Check.csv','T025_m','ratio'),('Native K-Select Ratio Check.csv','native_T025_m','native_ratio')]:
 rows=csvrows(R/file);assert len(rows)==640
 for row in rows:
  v=Decimal(row[throw])/Decimal(row['L_m']);assert abs(float(v)-float(row[ratio]))<1e-12 and 1<=v<=Decimal('3.4')
p=PdfReader(O/'BSE3227 HVAC Mini-Design.pdf');assert len(p.pages)==18
ids=[f'SD-{i:02}' for i in range(1,81)]
for pages in [[8,9],[10,11]]:assert re.findall(r'SD-\d{2}','\n'.join(p.pages[i].extract_text() for i in pages))==ids
assert re.findall(r'VAV-\d{2}',p.pages[12].extract_text())==[f'VAV-{i:02}' for i in range(1,21)]
assert re.findall(r'[AD]-\d{2}','\n'.join(p.pages[i].extract_text() for i in [13,14]))==[r['Section'] for r in csvrows(maincalc)]
assert re.findall(r'\[(\d+)\]',p.pages[7].extract_text())==list('123456')
assert re.findall(r'\[(\d+)\]',p.pages[17].extract_text())==['8','7','8']
assert all('PolyU' not in p.pages[i].extract_text() for i in [7,17])
review.update(visual_review='Actual pages17/18 rendered and inspected; typography, diagram and references legible without clipping',candidate_native_duct_fields=235,candidate_native_vav_fields=140,candidate_decimal_ratio_checks=1280,main_appendix_identities_preserved=True,main_engineering_files_sha256=protected,main_engineering_files_unchanged=True,coursework_ready_for_user_review=True)
# Preserve originals privately before updating only the report and delivery manifests.
archive=O/'previous-published';archive.mkdir(exist_ok=False)
formal=B/'04_Final_Report/Connection_Layout/BSE3227 HVAC Mini-Design.pdf';anon=B/'04_Final_Report/Public_Snapshot/BSE3227 HVAC Mini-Design.pdf'
for name,path in [('Identified Report.pdf',formal),('Anonymous Report.pdf',anon)]:shutil.copy2(path,archive/name)
w=PdfWriter();w.append(anon);w.append(O/'Supplementary Load Comparison.pdf')
with (O/'Anonymous Report.pdf').open('wb') as f:w.write(f)
shutil.copy2(O/'BSE3227 HVAC Mini-Design.pdf',formal);shutil.copy2(O/'Anonymous Report.pdf',anon)
supp=B/'05_Calculations/Supplementary_Load_Study';supp.mkdir(exist_ok=False)
for source,name in [(R/'Diffuser Course Ratio Check.csv','Diffuser Course Ratio Check.csv'),(R/'Native K-Select Ratio Check.csv','Native K-Select Ratio Check.csv'),(R/'Native K-Select Check.json','Native K-Select Check.json'),(R/'Online Ductulator Check.csv','Online Ductulator Check.csv'),(R/'Online Ductulator Check.json','Online Ductulator Check.json'),(R/'schedule-corridor/schedule.csv','Duct Sizing.csv'),(R/'native/Revised Drawing.dwg','Supplementary Layout.dwg'),(R/'native/Revised Drawing.pdf','Supplementary Layout.pdf'),(R/'vav/native/Supply Air Distribution.dwg','Supplementary VAV Schedule.dwg'),(R/'vav/native/Supply Air Distribution.pdf','Supplementary VAV Schedule.pdf')]:shutil.copy2(source,supp/name)
review.update(anonymous_report_sha256=sha(anon),formal_report_path=str(formal.relative_to(B)).replace('\\','/'),report_sha256=sha(formal),alternative_drawings_location=str(supp.relative_to(B)).replace('\\','/'),user_direction='Keep coursework main design; own-method alternatives only in appendix',regulatory_limits='Ordinary flex design budget3.373m<4m conditional on0.5m allowance; installed/fire-boundary/whole-system compliance not certified')
(supp/'README.md').write_text('# Supplementary load study\n\nUnadopted 150 W/m2 / 6-inch-neck comparison supporting Appendix E only.\nThe main coursework remains 189 W/m2 / 8-inch neck at 03_Design_Drawings/Connection_Layout.\nDo not mix these schedules or drawings with the main submission.\nSource: Lao and Deng, HKIE Transactions8(3),58-59,2001, DOI10.1080/1023697X.2001.10667859;129W/m2 whole-floor benchmark plus declared15% margin, rounded to150. Single historical office study; not measured project load or statutory sizing.\nNative drawings saved/reopened and actual plots visually inspected. No physical ADPI or manufacturer Type3 acceptance.\n')
assert protected=={name:sha(B/name) for name in protected}
(O/'review.json').write_text(json.dumps(review,indent=2));(supp/'Delivery Check.json').write_text(json.dumps(review,indent=2))
for name in ['Coursework Delivery Check.json','Final Course Consistency Check.json']:
 path=B/'05_Calculations/Connection_Layout'/name
 if path.exists():
  d=read(path);d.update(report_pages=18,report_sha256=sha(formal),anonymous_public_report_sha256=sha(anon),supplementary_appendix='Appendix E; unadopted150W/m2/6inch comparison only; main189W/m2 course design unchanged',reference_count=8,coursework_user_accepted=False)
  path.write_text(json.dumps(d,indent=2))
print(json.dumps(dict(pages=18,main_unchanged=True,native_fields=375,ratio_checks=1280,report_sha256=sha(formal)),indent=2))
