"""Prepare a fresh source-consistent illustrated report without publishing it."""
import csv,json,copy,math
from pathlib import Path
import ezdxf
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');P=B/'07_Agent_Work/project/course-report'
R=B/'07_Agent_Work/runs/course-refined-report-inputs';R.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
fixed=read(B/'07_Agent_Work/runs/course-diffuser-fixed-service-checked/review.json')
native_dir=B/'07_Agent_Work/runs/course-diffuser-native-final';native=read(native_dir/'review.json')
assert native['native_reopen_pass'] and native['preserved_records']==4885
allocation=read(B/'07_Agent_Work/runs/vav-recenter-design-reviewed/delivery/allocation/allocation.json')
for t in allocation['terminals']:
    if t['id'] in fixed['changes']:t['center_m']=fixed['changes'][t['id']]
allocation['geometry_basis']+='; retain explicit source service cells and their assigned loads after150mm within-cell centre displacement'
(R/'allocation.json').write_text(json.dumps(allocation,indent=2))
terms={t['id']:t for t in allocation['terminals']}
candidate=read(B/'07_Agent_Work/runs/course-diffuser-position-screen/axis1_-0.15.json')
lengths={(r['terminal'],r['direction']):r['screened_length_m'] for r in candidate['cases']}
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def write(name,data):
    with (R/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)
ratios=rows(B/'05_Calculations/Connection_Layout/Diffuser Course Ratio Check.csv')
for row in ratios:
    row['L_m']=lengths[row['terminal'],row['direction']];row['ratio']=float(row['T025_m'])/row['L_m']
assert all(1<=r['ratio']<=3.4 for r in ratios)
write('Diffuser Course Ratio Check.csv',ratios)
native_rows=rows(B/'07_Agent_Work/runs/course-diffuser-fixed-service-checked/Native K-Select Candidate Ratios.csv')
for row in native_rows:row['original_catalogue_ratio']=float(row['original_catalogue_T025_m'])/float(row['L_m'])
write('Native K-Select Ratio Check.csv',native_rows)
d=ezdxf.readfile(native_dir/'reopened/source-export.dxf')
groups=rows(B/'05_Calculations/Connection_Layout/VAV Connection Schedule.csv');centres={}
for group in groups:
    tids=group['Diffuser outlets'].split(', ');endpoints=[terms[k]['center_m'] for k in tids];matches=[]
    for e in d.modelspace().query('CIRCLE'):
        if e.dxf.layer!='BSA_VAV':continue
        xy=[e.dxf.center.x/1000,e.dxf.center.y/1000]
        count=sum(any((math.dist([l.dxf.start.x/1000,l.dxf.start.y/1000],xy)<1e-8 and math.dist([l.dxf.end.x/1000,l.dxf.end.y/1000],p)<1e-8) or (math.dist([l.dxf.end.x/1000,l.dxf.end.y/1000],xy)<1e-8 and math.dist([l.dxf.start.x/1000,l.dxf.start.y/1000],p)<1e-8) for l in d.modelspace().query('LINE') if l.dxf.layer=='BSA_FLEX') for p in endpoints)
        if count==4:matches.append(xy)
    assert len(matches)==1;centres[group['VAV']]=matches[0]
    distance=[math.dist(p,matches[0]) for p in endpoints];group['Min plan m']=f'{min(distance):.3f}';group['Max plan m']=f'{max(distance):.3f}'
write('VAV Connection Schedule.csv',groups);(R/'vav-centres.json').write_text(json.dumps(centres))
s=(P/'build_course_report_members_references.py').read_text()
s=s.replace("course-report-citations-public' if PUBLIC else '07_Agent_Work/runs/course-report-citations-private", "course-report-refined-public' if PUBLIC else '07_Agent_Work/runs/course-report-refined-private")
start=s.index('kselect=json.loads(');end=s.index('\ndef read(k):',start)
replacement='''I=B/'07_Agent_Work/runs/course-refined-report-inputs'
N=B/'07_Agent_Work/runs/course-diffuser-native-final'
for key,name in [('ratios','Diffuser Course Ratio Check.csv'),('vav','VAV Connection Schedule.csv'),('kselect_ratios','Native K-Select Ratio Check.csv'),('allocation','allocation.json')]:paths[key]=I/name
paths['plan']=N/'Supply Air Distribution.pdf';paths['original_dwg']=N/'Supply Air Distribution.dwg';paths['native_check']=N/'review.json'
paths['position_review']=B/'07_Agent_Work/runs/course-diffuser-fixed-service-checked/review.json'
kselect=json.loads(paths['kselect_check'].read_text());native_check=json.loads(paths['native_check'].read_text());assert native_check['native_reopen_pass']
previous=B/'04_Final_Report/Connection_Layout/BSE3227 HVAC Mini-Design.pdf';shutil.copy2(previous,R/'Previous Coursework Report.pdf')
hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
'''
s=s[:start]+replacement+s[end:]
catalogue_range=[min(r['ratio'] for r in ratios),max(r['ratio'] for r in ratios)]
s=s.replace('1.1098-3.2245',f'{catalogue_range[0]:.4f}-{catalogue_range[1]:.4f}').replace('1.2066-3.2797','1.2117-3.1122')
s=s.replace("sub('2.3 Flexible connection design')", "p('Twelve diffusers are displaced 150 mm south within their original explicit service areas. Service-area loads, all terminal flows, VAV membership and rigid section sizes remain unchanged; Figure 2 identifies the adjusted row.')\nsub('2.3 Flexible connection design')")
insert="""
page('3.4 Air distribution layout and local refinement')
from hvac_illustrations import overview,critical_detail
fixed=json.loads(paths['position_review'].read_text())
centres=json.loads((I/'vav-centres.json').read_text())
story.append(overview(W,allocation,vav,centres,fixed['changes']))
p('Figure 2. Source-coordinate diffuser arrangement, schematic VAV grouping and adjusted row.',caption)
p('A finite comparison considered 50, 100 and 150 mm shifts of the controlling source row or column. The selected 150 mm southward row adjustment preserves all assigned service-area loads and moves no diffuser outside its original service cell. No new rigid bend, VAV group or diffuser type is introduced.')
table('Table 4. Native-throw geometric check before and after the selected adjustment.',['Quantity','Before','Adopted'],[['Minimum directional ratio','1.2066','1.2117'],['Maximum directional ratio','3.2797','3.1122'],['Margin below upper ratio limit','3.54%','8.46%'],['Cases within adopted interval','640/640','640/640'],['Total planar flexible length','197.894 m','199.024 m'],['Maximum conditional flexible length','3.373 m','3.373 m']],[1.8,1,1])
p('The upper-bound margin increases by 4.92 percentage points. The tradeoff is 1.130 m more total planar flexible connection (0.57%); the maximum connection budget remains unchanged. These are geometric selection margins, not an increase in ADPI percentage or a complete pressure comparison.',small)
page('3.5 Critical diffuser and worked calculation')
position=json.loads((B/'07_Agent_Work/runs/course-diffuser-position-screen/axis1_-0.15.json').read_text())
critical=fixed['critical_maximum'];geometry_case=next(c for c in position['cases'] if c['terminal']==critical['terminal'] and c['direction']==critical['direction'])
story.append(critical_detail(W,allocation,geometry_case,critical))
p('Figure 3. SD-56 northward characteristic length and tabulated isothermal throw.',caption)
p('SD-56 receives 155.9466 L/s at maximum flow and 62.3786 L/s at minimum flow. Its northward L increases from 1.3940 to 1.4690 m. At the unchanged native input of 330 CFM (155.7427 L/s), the reported 15.0 ft throw gives T<sub>0.25</sub> = 15.0 x 0.3048 = 4.5720 m. Hence T<sub>0.25</sub>/L = 4.5720/1.469042 = 3.1122, compared with 3.2797 before the adjustment [3].')
p('The original metric-table interpolation is retained separately: T<sub>0.25</sub> = 4.4903 m at the prescribed maximum flow, giving 4.4903/1.469042 = 3.0566 [2]. The native and catalogue values use different flow rounding and reported performance; they are not presented as identical.')
p('The minimum-flow limiting point after adjustment is SD-08 eastward: native T<sub>0.25</sub> = 2.7432 m and L = 2.263959 m give a ratio of 1.2117. All other directions and both operating flows are checked in the schedules; improving SD-56 alone would not establish a whole-layout pass.')
sub('Worked duct-sizing check')
example=next(r for r in duct if r['Section']=='D-11')
flow=float(example['Flow L/s']);wmm=float(example['Width mm']);hmm=float(example['Height mm']);velocity=flow/1000/(wmm*hmm/1e6)
p(f'D-11 carries {flow:.3f} L/s through {wmm:.0f} x {hmm:.0f} mm. Area = {wmm/1000:.3f} x {hmm/1000:.3f} = {wmm*hmm/1e6:.4f} m<super>2</super>; velocity = {flow/1000:.6f}/{wmm*hmm/1e6:.4f} = {velocity:.3f} m/s, below its adopted 8 m/s branch limit. The aspect ratio is {max(wmm,hmm)/min(wmm,hmm):.2f}; calculated friction is '+example['Friction Pa/m']+' Pa/m, below 1.23 Pa/m. These checks do not include fitting or equipment losses.')
"""
s=s.replace("page('4. Duct sizing and Hong Kong design provisions')",insert+"\npage('4. Duct sizing and Hong Kong design provisions')")
(P/'build_refined_illustrated_report.py').write_text(s)
print(json.dumps(dict(catalogue_ratio_range=catalogue_range,prepared_inputs=str(R),groups_checked=len(groups))))
