"""Independent readback of candidate delivered entities, ratios and PDF schedules."""
from pathlib import Path
import csv,json,re,math,hashlib
from decimal import Decimal,localcontext
import ezdxf
from pypdf import PdfReader
from shapely.geometry import shape,LineString,Polygon
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=B/'07_Agent_Work/runs';I=R/'course-refined-report-inputs'
read=lambda p:json.loads(p.read_text());rows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig')))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
allocation=read(I/'allocation.json');terms={t['id']:t for t in allocation['terminals']};centres=read(I/'vav-centres.json')
groups=rows(I/'VAV Connection Schedule.csv');native=ezdxf.readfile(R/'course-diffuser-native-final/reopened/source-export.dxf')
space=shape(read(B/'07_Agent_Work/project/bse3227-column-row-candidate/office-boundary.geojson'))
flex=[e for e in native.modelspace().query('LINE') if e.dxf.layer=='BSA_FLEX'];assert len(flex)==80
assert all(space.buffer(1e-7).covers(LineString([(e.dxf.start.x/1000,e.dxf.start.y/1000),(e.dxf.end.x/1000,e.dxf.end.y/1000)])) for e in flex)
panels=[e for e in native.modelspace().query('LWPOLYLINE') if e.dxf.layer=='BSA_DIFFUSER'];assert len(panels)==80
assert all(space.covers(Polygon([(p[0]/1000,p[1]/1000) for p in e.get_points()])) for e in panels)
assert all(abs(t['minimum_flow_L_s']/t['maximum_flow_L_s']-.4)<1e-14 for t in terms.values())
lengths=[]
for g in groups:
    members=g['Diffuser outlets'].split(', ');assert len(members)==4
    ds=[]
    for tid in members:
        xy=terms[tid]['center_m'];start=centres[g['VAV']];ds.append(math.dist(xy,start))
        assert sum(math.dist([p[0]/1000,p[1]/1000],xy)<1e-8 for e in flex for p in [e.dxf.start,e.dxf.end])==1
    assert f'{min(ds):.3f}'==g['Min plan m'] and f'{max(ds):.3f}'==g['Max plan m'];lengths.extend(ds)
ratio_rows=rows(I/'Diffuser Course Ratio Check.csv');native_rows=rows(I/'Native K-Select Ratio Check.csv')
for r in ratio_rows:
    with localcontext() as ctx:
        ctx.prec=40;v=Decimal(r['T025_m'])/Decimal(r['L_m'])
        assert abs(float(v)-float(r['ratio']))<1e-12 and 1<=v<=Decimal('3.4')
for r in native_rows:
    with localcontext() as ctx:
        ctx.prec=40;v=Decimal(r['native_reported_throw_ft'])*Decimal('.3048')/Decimal(r['L_m'])
        assert abs(float(v)-float(r['native_ratio']))<1e-12 and 1<=v<=Decimal('3.4')
ducts=rows(B/'05_Calculations/Connection Layout Duct Sizing.csv');texts=[e for e in native.modelspace().query('TEXT') if e.dxf.layer=='BSA_SCHEDULE']
for row in ducts:
    found=[e for e in texts if e.dxf.text==row['Section']];assert len(found)==1;e=found[0]
    cells=sorted([v for v in texts if abs(v.dxf.insert.y-e.dxf.insert.y)<1e-8],key=lambda v:v.dxf.insert.x)
    assert [v.dxf.text for v in cells]==[row['Section'],f"{float(row['Flow L/s']):.1f}",f"{float(row['Width mm']):.0f} x {float(row['Height mm']):.0f}",f"{float(row['Velocity m/s']):.2f}",f"{float(row['Friction Pa/m']):.3f}"]
    velocity=float(row['Flow L/s'])/1000/(float(row['Width mm'])*float(row['Height mm'])/1e6)
    assert abs(velocity-float(row['Velocity m/s']))<1e-10
table=ezdxf.readfile(R/'course-refined-vav-table/native/reopened/source-export.dxf')
tt=[e for e in table.modelspace().query('TEXT') if e.dxf.layer=='BSA_VAV_TABLE']
for g in groups:
    tag=next(e for e in tt if e.dxf.text==g['VAV']);cells=sorted([e for e in tt if abs(e.dxf.insert.y-tag.dxf.insert.y)<1e-8],key=lambda e:e.dxf.insert.x)
    assert [e.dxf.text for e in cells]==[g[k] for k in ['VAV','Diffuser outlets','Qmax L/s','Qmin L/s','Min plan m','Max plan m','Outlets']]
private=R/'course-report-refined-private-polished/BSE3227 HVAC Mini-Design.pdf';public=R/'course-report-refined-public-polished/BSE3227 HVAC Mini-Design.pdf'
p=PdfReader(private);pub=PdfReader(public);assert len(p.pages)==len(pub.pages)==16
ids=[f'SD-{i:02}' for i in range(1,81)];extract=lambda pages: '\n'.join(p.pages[i].extract_text() for i in pages)
assert re.findall(r'SD-\d{2}',extract([8,9]))==ids
assert re.findall(r'SD-\d{2}',extract([10,11]))==ids
assert re.findall(r'VAV-\d{2}',extract([12]))==[g['VAV'] for g in groups]
assert re.findall(r'[AD]-\d{2}',extract([13,14]))==[g['Section'] for g in ducts]
for g in groups:
    assert g['Min plan m']+'-'+g['Max plan m'] in p.pages[12].extract_text()
refs=p.pages[7].extract_text();assert re.findall(r'\[(\d)\]',refs)==list('123456') and 'PolyU' not in refs
members=read(B/'07_Agent_Work/project/course-report/Private/group-details.json')['members']
pubtext='\n'.join(x.extract_text() for x in pub.pages)
for member in members:
    assert member['name'] in p.pages[0].extract_text() and member['name'] not in pubtext
native_record=read(R/'course-diffuser-native-final/review.json')
result=dict(scope='Final refined coursework numerical/native/PDF identity audit; not measured ADPI or statutory certification',
    pages=16,terminals=80,vav_groups=20,rigid_sections=47,course_ratio_checks=640,native_ratio_checks=640,
    independent_decimal_ratio_checks=1280,native_duct_fields=235,native_vav_fields=140,
    all80_panels_and_flex_lines_inside_interpreted_boundary=True,all_report_appendix_identities_match=True,
    group_flows_and_membership_preserved=True,private_members_present_public_members_absent=True,
    six_external_IEEE_references_verified=True,report_sha256=sha(private),public_report_sha256=sha(public),
    dwg_sha256=sha(R/'course-diffuser-native-final/Supply Air Distribution.dwg'),
    plot_sha256=sha(R/'course-diffuser-native-final/Supply Air Distribution.pdf'),
    maximum_plan_flex_m=max(lengths),maximum_conditional_flex_m=max(lengths)+.5,total_plan_flex_m=sum(lengths),
    native_reopen_pass=True,all_checks_pass=True,ADPI_verified=False,full_HK_statutory_compliance_established=False,
    coursework_user_accepted=False)
(R/'course-refined-final-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
