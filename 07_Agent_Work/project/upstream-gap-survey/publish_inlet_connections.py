"""Publish checked local inlet assemblies and exact upstream editable CAD sources."""
import hashlib,html,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');BASE=ROOT/'07_Agent_Work/runs/rect-round-cadquery'
RUN=BASE/'analytic-inlet-assemblies';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=json.loads((RUN/'author-review.json').read_text());caps=json.loads((RUN/'independent-review.json').read_text())
review=json.loads((RUN/'assembly-review.json').read_text());plot=json.loads((RUN/'drawing-sections/native/native-verification.json').read_text())
common=json.loads((BASE/'kernel-common-validated/kernel-review.json').read_text())
old=json.loads((BASE/'kernel-csg/kernel-review.json').read_text())
assert sha(RUN/'VAV Inlet Assemblies.ifc')==native['ifc_sha256']==caps['ifc_sha256']==review['ifc_sha256']
for a,b in zip(common['results'],old['results']):assert a['id']==b['id'] and a['brep_sha256']==b['brep_sha256'] and a['STEP_reimport_units_pass']
agent=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
assert sha(agent/'src/bsa/cadquery_rect_round.py')==common['worker_sha256']
assert plot['native_reopen_pass'] and plot['plot']['pdf_reference_pass']
target=ROOT/'03_Design_Drawings/Connection_Layout/VAV_Inlet_Connections';target.mkdir(exist_ok=False)
for source,name in [(RUN/'VAV Inlet Assemblies.ifc','VAV Inlet Connections.ifc'),
    (RUN/'drawing-sections/native/section.dwg','VAV Inlet Connections.dwg'),
    (RUN/'drawing-sections/native/sheet.pdf','VAV Inlet Connections.pdf')]:shutil.copyfile(source,target/name)
step_dir=target/'STEP';step_dir.mkdir()
for row in common['results']:
    source=BASE/'kernel-common-validated'/(row['id']+'.step')
    assert sha(source)==row['artifacts'][source.name];shutil.copyfile(source,step_dir/source.name)
rows=[]
for case in native['cases']:
    r=next(x for x in review['rows'] if x['id']==case['id'])
    rows.append(dict(id=case['id'],source_section_guid=case['source_section_guid'],
        transition_guid=case['guid'],round_lead_guid=case['round_guid'],
        width_m=case['width_m'],height_m=case['height_m'],diameter_m=case['diameter_m'],
        transition_total_m=case['start_length_m']+case['taper_length_m']+case['end_length_m'],
        round_length_m=r['saved_round_length_m'],proposed_VAV_shift_m=case['length_budget']['downstream_shift_m'],
        retained_rectangular_m=case['length_budget']['retained_rectangular_straight_m'],
        proposed_inlet_point_m=case['length_budget']['proposed_inlet_point_m'],
        maximum=r['calculations']['maximum'],minimum=r['calculations']['minimum'],
        full_pressure_Pa=None,existing_network_revised=False))
summary=dict(native_bodies=40,transitions=20,round_leads=20,owned_ports=80,local_links=20,
    schema_express_pass=True,all_native_caps_and_walls_pass=True,
    maximum_circle_chord_error_m=max(x['circular_chord_error_m'] for x in caps['cases']),
    raw_intersection_pairs=0,raw_clearance_violation_pairs=20,contact_waivers=0,
    common_CadQuery_worker_actual_cases=20,common_worker_sha256=common['worker_sha256'],
    common_STEP_units_reimport_pass=True,common_BRep_hashes_match_project_prototype=True,
    independent_nominal_boundary_frames_verified=True,
    CAD_versions=common['versions'],new_dependency_lock_sha256=sha(agent/'adapters/cadquery/requirements.lock'),
    OCP_binary_sha256=sha(agent/'tools/cadquery-runtime/Lib/site-packages/OCP/OCP.cp312-win_amd64.pyd'),
    native_DWG_reopen_pass=True,native_DWG_entity_count=plot['checks']['model_entity_count'],
    actual_PDF_visually_inspected=True,PDF_review='Five actual saved-native longitudinal material section families represent20cases; labels/notes/reference show no observed clipping or overlap',
    drawing_representative_native_GUIDs=10,drawing_is_whole_network_plan=False,
    reference_expected_mm=plot['plot']['reference_expected_mm'],reference_measured_mm=plot['plot']['reference_measured_mm'],
    shifted_candidate_units={r['id']:r['proposed_VAV_shift_m'] for r in rows if r['proposed_VAV_shift_m']>0},
    maximum_round_straight_friction_range_Pa=[min(r['maximum']['straight_friction_Pa'] for r in rows),max(r['maximum']['straight_friction_Pa'] for r in rows)],
    assumptions=['0.3m taper and50mm end collars; no product or prescribed angle acceptance',
        '0.8mm section-plane-offset wall, not constant sheet-normal thickness',
        '80mm minimum retained rectangle is internal construction policy',
        'Nominal circular bore and inherited chart roughness/fluid properties',
        'Proposed VAV inlet datum and reference elevation remain assumptions'],
    network_merged=False,full_pressure_verified=False,installation_verified=False,design_accepted=False,
    deliverable_sha256={str(p.relative_to(target)).replace('\\','/'):sha(p) for p in target.rglob('*') if p.is_file()})
check=ROOT/'05_Calculations/Connection_Layout/VAV_Inlet_Connection_Check.json';assert not check.exists()
check.write_text(json.dumps(dict(**summary,air=review['air'],source_ifc_sha256=native['source_ifc_sha256'],rows=rows),indent=2))
body=''.join('<tr>'+''.join('<td>'+html.escape(str(v) if isinstance(v,str) else f'{v:.6f}')+'</td>' for v in [r['id'],r['diameter_m']*1000,r['transition_total_m'],r['round_length_m'],r['proposed_VAV_shift_m'],r['retained_rectangular_m'],r['maximum']['straight_friction_Pa'],r['minimum']['straight_friction_Pa']])+'<td>Unknown</td></tr>' for r in rows)
report='''<!doctype html><meta charset="utf-8"><title>VAV Inlet Connection Review</title><style>body{font:16px Arial;max-width:1200px;margin:30px auto;line-height:1.5}table{border-collapse:collapse}th,td{padding:7px;border:1px solid #bbb;text-align:right}</style><h1>VAV Inlet Connection Review</h1><p>Twenty actual saved local assemblies: finite rectangle-to-circle transition plus3D round straight. The earlier equipment-space and rigid network studies remain separate. Existing rectangular ducts have not yet been shortened/reconnected.</p><p>Upstream CadQuery2.6.1/OCP7.8.1.1.post1 generates exact ruled loft solids. IFC stores analytic outer/inner operands and Boolean walls;40native bodies,80ports and20local links are checked. No source curve approximation or tolerance widening is used to accept the rejected16-sided generator. Editable STEP sources declare mm and have been reimported to verify their actual units.</p><p>Lengths0.3m taper,50mm collars,0.8mm section offset and80mm retained rectangle are declared design assumptions. Proposed equipment shifts are not adopted installation positions. Round Darcy friction uses inherited air conditions and roughness; transition, seam, product collar, plenum and other losses remain unknown. No complete-pressure or fan-duty claim follows.</p><table><tr><th>VAV</th><th>Nominal bore mm</th><th>Transition total m</th><th>Round3D m</th><th>Proposed shift m</th><th>Prospective retained rectangle m</th><th>Max round friction Pa</th><th>Min round friction Pa</th><th>Complete local pressure</th></tr>'''+body+'''</table><p>Raw40geometry clash:0intersections,20unwaived contact clearance findings. These numerical checks do not establish installation clearance. Control/acoustic choice, actual product collar/seals, source-duct replacements and whole-network pressure remain unresolved. Manufacturer installation recommendation: Krueger single-duct IOM PDF6 Step2A recommends3D upstream straight; this is not a newly invented regulatory clause.</p>'''
html_path=check.with_name('VAV Inlet Connection Review.html');assert not html_path.exists();html_path.write_text(report,encoding='utf8')
assert report.count('<td>')==180 and report.count('Unknown</td>')==20
for r in rows:assert f"{r['maximum']['straight_friction_Pa']:.6f}" in report and f"{r['minimum']['straight_friction_Pa']:.6f}" in report
(RUN/'delivery-review.json').write_text(json.dumps(summary,indent=2))
(agent/'docs/evidence/vav-inlet-connections.json').write_text(json.dumps(summary,indent=2))
(target/'Review scope.md').write_text('''# VAV inlet connection study

These are twenty source-bound local inlet assemblies, not an adopted whole
network revision or installation design. IFC contains forty actual hollow
bodies/eighty owned ports/twenty local connections. Five representative native
longitudinal material sections cover all twenty cases in the actual DWG/PDF.
STEP contains exact local transition CAD shapes in mm; IFC uses metres and
proposed world placements. STEP coordinates are not global building coordinates.

CadQuery2.6.1/OCP7.8.1.1.post1 creates ruled outer/inner lofts. The successful
IFC route reuses native Boolean difference; exact coincident vertex records
share entity identity without changing any coordinates. Saved schema, closed
walls, cap areas/radii/corners/frames and round3D lengths are checked. The
standalone common CAD worker has also reimported all20STEP files for units.

The0.3m taper,50mm collars,0.8mm section-offset wall and80mm rectangular remainder
are explicit design assumptions, not product/fabrication or code acceptance.
Five proposed inlet points move0.11–0.43m downstream to meet this local length
budget; equipment envelopes and source ducts have not yet been revised to match.
Nominal duct/collar fits, seal construction, controls, acoustics, architecture,
installed elevation, plenum/flex and full pressure remain unresolved.

Maximum round-straight friction is1.14–2.07Pa per group under inherited air and
roughness assumptions. Unknown transition/joint losses remain unknown. Raw
geometry gives0intersections and20unwaived connection clearance findings.
Actual AutoCAD save/reopen and actual final1:10PDF review execute. No preview,
local check or source-matched component is called a completed system design.
''',encoding='utf8')
print(json.dumps(dict(delivered_bodies=40,editable_STEP_files=20,HTML_rows=20,native_DWG_reopened=True,network_merged=False)))
