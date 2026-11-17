"""Fresh source-bound comparison of current geometry against all published panels."""
from pathlib import Path
import csv,json,re,hashlib,math
from pypdf import PdfReader
from shapely.geometry import shape
from bsa.manufacturer_adpi import catalogue,lengths,screen,square_grid_envelope
from bsa.terminal_performance import calculate
from bsa.air_allocation import prepare
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work/project';R=B/'07_Agent_Work/runs/adpi-current-all-panels';R.mkdir(exist_ok=False)
perf=P/'bse3227-terminal-source/Krueger_1400_51400_Performance.pdf';guide=P/'adpi-manufacturer-study/GRD_Engineering.pdf'
curves_path=B/'07_Agent_Work/runs/manufacturer-adpi-native-curves/curves.json';curves=json.loads(curves_path.read_text())
allocation_path=B/'07_Agent_Work/runs/course-refined-report-inputs/allocation.json';allocation=json.loads(allocation_path.read_text())
boundary_path=P/'bse3227-column-row-candidate/office-boundary.geojson';geo=json.loads(boundary_path.read_text());boundary=shape(geo)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(guide)==curves['source_pdf_sha256'];tables={'600x600/'+k:v for k,v in catalogue(perf).items()}
# Same source row layout as the already verified 600-mm page; retain source rows.
small=[]
for line in PdfReader(perf).pages[0].extract_text().splitlines():
    parts=re.sub(r'^(?:(6|8)[\u201d"]|Dia\.)\s+','',line.strip()).split()
    if len(parts)!=25 or any(parts[i]!='-' for i in (5,7,15,17)):continue
    try:q,pt,ps,t=map(float,[parts[i] for i in (11,12,13,18)]);nc=None if parts[9]=='-' else float(parts[9])
    except ValueError:continue
    small.append(dict(flow_L_s=q,total_pressure_Pa=pt,static_pressure_Pa=ps,T025_m=t,NC=nc,NC_qualifier='less than10' if nc is None else 'catalogue row'))
assert len(small)==18 and small[0]['flow_L_s']==19 and small[9]['flow_L_s']==33
tables.update({'300x300/6':small[:9],'300x300/8':small[9:]})
positions=[dict(id=t['id'],center_m=t['center_m']) for t in allocation['terminals']];Ls=lengths(boundary,positions)
current=list(csv.DictReader((B/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv').open(encoding='utf-8-sig')))
assert all(abs(float(r['L_m'])-Ls[r['terminal']][r['direction']])<1e-10 for r in current)
details=[];selection=[]
for terminal in allocation['terminals']:
    options=[]
    for label,table in tables.items():
        failures=[];ratios=[];tests=0
        for condition,loads in [('maximum',[40,60]),('minimum',[20,40])]:
            performance=calculate(table,terminal[condition+'_flow_L_s'])
            if performance['status']!='within_catalogue':failures.append(dict(condition=condition,reason='outside_original_flow_table'));continue
            for direction,L in Ls[terminal['id']].items():
                ratio=performance['T025_m']/L;ratios.append(ratio)
                for load in loads:
                    reading=screen(curves,load,ratio);tests+=1
                    if reading['status']!='paired_curve_threshold_met':failures.append(dict(condition=condition,direction=direction,load_Btuh_ft2=load,**reading))
        result=dict(terminal=terminal['id'],option=label,failed_tests=len(failures),curve_tests=tests,all_source_domain_and_threshold_checks_pass=not failures,failures=failures)
        details.append(result);options.append(result)
    feasible=[x['option'] for x in options if x['all_source_domain_and_threshold_checks_pass']]
    selection.append(dict(terminal=terminal['id'],feasible_options=feasible,minimum_failed_tests=min(x['failed_tests'] for x in options)))
square=square_grid_envelope({k.split('/')[1]:v for k,v in tables.items() if k.startswith('600')},curves,.4,1.2,1006,12)
small_square=square_grid_envelope({k.split('/')[1]:v for k,v in tables.items() if k.startswith('300')},curves,.4,1.2,1006,12)
for row in square['neck_bounds']:row['panel_mm']=600
for row in small_square['neck_bounds']:row['panel_mm']=300
square['neck_bounds'].extend(small_square['neck_bounds'])
summary=dict(scope='Current adopted80-outlet geometry with every published300/600mm Model1400 panel/neck option; paired source-curve diagnostic only,not exact load-interpolated or measured ADPI',
    inputs={str(p.relative_to(B)):sha(p) for p in [perf,guide,curves_path,allocation_path,boundary_path]},
    sensible_load_W_m2=170.1,minimum_load_W_m2=68.04,maximum_paired_loads_Btuh_ft2=[40,60],minimum_paired_loads_Btuh_ft2=[20,40],
    panel_neck_options=len(tables),terminal_option_comparisons=len(details),terminals_with_any_passing_option=sum(bool(r['feasible_options']) for r in selection),
    terminals_without_passing_option=[r['terminal'] for r in selection if not r['feasible_options']],
    curve_test_count=sum(r['curve_tests'] for r in details),geometry_matches_current320_lengths=True,
    regular_square_best_necessary_load_W_m2=max(r['conditional_sensible_W_m2'] for r in square['neck_bounds'] if r['status']=='necessary_bound_only'),
    regular_square_bound_scope=square['scope'],no_global_infeasibility_claim=True,ADPI_verified=False,formal_coursework_package_changed=False,
    next_action='Review actual independent alternative characteristic-length/control assumptions or a major course-basis decision before adopting design changes; do not rerun unchanged layout/neck search.')
for name,value in [('catalogue300-reviewed.json',dict(rows=small,source_sha256=sha(perf),pdf_page=1)),('details.json',details),('selection.json',selection),('regular-square-bound.json',square),('review.json',summary)]:
    (R/name).write_text(json.dumps(value,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='inputs'},indent=2))
