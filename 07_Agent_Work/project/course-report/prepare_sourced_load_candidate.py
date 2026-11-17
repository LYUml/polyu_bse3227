"""Prepare, never adopt, a source-backed alternative to the optional class allowance."""
from pathlib import Path
import copy,json,csv,math,hashlib
from bsa.air_allocation import prepare
from bsa.duct_schedule import run as duct_run
from bsa.manufacturer_adpi import catalogue
from bsa.terminal_performance import calculate
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work';R=P/'runs/course-sourced-load-candidate';R.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=P/'runs/course-refined-report-inputs/allocation.json';old=json.loads(source.read_text())
boundary=P/'project/bse3227-column-row-candidate/office-boundary.geojson';geo=json.loads(boundary.read_text())
hkie=P/'project/adpi-source-review/HKIE Office Cooling Load.pdf';assert sha(hkie)=='ed833d4808a0ad0df67f4d15d555481d98887bb51f068dc4bcbf98cee3d47225'
inputs=copy.deepcopy(old['load']['inputs']);inputs['cooling_allowance'].update(value=150,classification='assumed',source='Design choice: HKIE Transactions8(3),2001,pp58-59,Table3 single-Hong-Kong-office floor benchmark129W/m2; add declared15percent allowance129x1.15=148.35 and round upward to150. Not measured project load,mandatory rule or manufacturer ADPI evidence.')
inputs['sensible_fraction'].update(classification='assumed',source='Retained approximate office SHF0.90 as a design assumption,not an explicit fixed number in the assignment brief.')
terms=[dict(id=t['id'],center_m=t['center_m']) for t in old['terminals']]
cells={t['id']:t['geometry'] for t in old['terminals']}
a=prepare(geo,terms,inputs,.4,service_cells=cells,service_basis='Preserve existing explicit source-bound service cells and interpreted80positions. Only the adopted preliminary cooling allowance changes in this unadopted candidate.')
(R/'allocation.json').write_text(json.dumps(a,indent=2))
project=P/'runs/vav-recenter-friction-compensated/inputs/ducts.json';ducts=json.loads(project.read_text());ducts['basis']+='; unadopted source-backed150W/m2 preliminary alternative,unchanged tree/air properties/source speed/friction/aspect caps and finite candidate dimensions'
(R/'ducts.json').write_text(json.dumps(ducts,indent=2));d=duct_run(R/'ducts.json',R/'schedule',allocation_path=R/'allocation.json',allocation_sha256=sha(R/'allocation.json'))
table=catalogue(P/'project/bse3227-terminal-source/Krueger_1400_51400_Performance.pdf')['6']
rows=list(csv.DictReader((B/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv').open(encoding='utf-8-sig')));by={t['id']:t for t in a['terminals']};result=[]
for row in rows:
    r=copy.deepcopy(row);q=by[r['terminal']][r['case']+'_flow_L_s'];perf=calculate(table,q);assert perf['status']=='within_catalogue'
    r.update(flow_L_s=q,T025_m=perf['T025_m'],ratio=perf['T025_m']/float(r['L_m']));assert 1<=r['ratio']<=3.4;result.append(r)
with (R/'Diffuser Course Ratio Check.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=result[0]);w.writeheader();w.writerows(result)
oldduct=list(csv.DictReader((B/'05_Calculations/Connection Layout Duct Sizing.csv').open()));newduct=list(csv.DictReader((R/'schedule/schedule.csv').open()))
changed=sum((x['Width mm'],x['Height mm'])!=(y['Width mm'],y['Height mm']) for x,y in zip(oldduct,newduct))
assert all(not r['failures'] for r in d['sections'])
summary=dict(scope='Unadopted load/selection candidate for a source-backed coursework decision; original formal package and189W/m2 baseline preserved',
    authority=dict(brief_requires_rule_of_thumb=True,brief_explicitly_fixes_189_or_0_9=False,classroom_189_is_optional_preliminary_reference=True),
    source_pdf_sha256=sha(hkie),source_doi='10.1080/1023697X.2001.10667859',source_url='https://hkie.org.hk/hkietransactions/upload/2019-02-19/An_Evaluation_of_the_Rules_of_Thumb_for_Estimating_Cooling_Load_for_Office_Buildings.pdf',
    source_limits='Single office floor,1999measurements,2001publication; no universal/current-building applicability or statutory authority claimed; source129contains no safety/standby allowance.',
    adopted_candidate_total_W_m2=150,benchmark_total_W_m2=129,declared_design_margin_fraction=.15,rounded_from_W_m2=148.35,sensible_fraction=.9,
    sensible_maximum_W_m2=135,sensible_minimum_W_m2=54,course_table_band_W_m2=[35,160],both_operating_loads_inside_course_table=True,
    total_cooling_kW_thermal=a['load']['total_cooling_kW_thermal'],sensible_cooling_kW_thermal=a['load']['sensible_trial_kW_thermal'],maximum_flow_L_s=a['load']['supply_flow_L_s'],minimum_flow_L_s=.4*a['load']['supply_flow_L_s'],
    terminals=80,vav_groups=20,rigid_sections=47,selected_model='1400/51400',panel_mm=[600,600],neck_inch=6,
    catalogue_ratio_cases=640,catalogue_ratio_range=[min(r['ratio'] for r in result),max(r['ratio'] for r in result)],all640_catalogue_checks_pass=True,
    changed_duct_sizes=changed,all47_source_selected_limits_pass=True,positions_and_group_membership_preserved=True,
    native_KSelect_conditions_required=len({math.floor(r['flow_L_s']*2.118880003289315+.5) for r in result}),
    native_KSelect_verification='pending',native_DWG_candidate='pending',report_candidate='pending',
    manufacturer_Type3_ADPI_accepted=False,physical_ADPI_verified=False,formal_package_replaced=False,user_accepted=False)
(R/'review.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
