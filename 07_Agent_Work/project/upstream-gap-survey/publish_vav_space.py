"""Publish source-bound finite placement and revised inlet candidates."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
BASE=ROOT/'07_Agent_Work/runs';RUN=BASE/'vav-finite-placement'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
revision=json.loads((BASE/'vav-manufacturer-capacity/inlet-revision.json').read_text())
audit=json.loads((RUN/'native-review.json').read_text())
placement=json.loads((RUN/'placement.json').read_text())
native=json.loads((RUN/'drawing-final/native/native-verification.json').read_text())
projection=json.loads((RUN/'drawing-final/projection.json').read_text())
assert sha(RUN/'model.ifc')==audit['ifc_sha256']==projection['ifc_sha256']
assert native['native_reopen_pass'] and native['plot']['pdf_reference_pass']
assert audit['overlap_counts']=={'existing_network/inlet_reservation':20}
assert placement['original_entities_unchanged']
assert projection['component_count']==169 and len(projection['contours_per_guid'])==169
target=ROOT/'03_Design_Drawings/Connection_Layout/VAV_Equipment_Space'
target.mkdir(exist_ok=False)
for source,name in [(RUN/'model.ifc','VAV Equipment Space.ifc'),
    (RUN/'drawing-final/native/section.dwg','VAV Equipment Space.dwg'),
    (RUN/'drawing-final/native/sheet.pdf','VAV Equipment Space.pdf')]:shutil.copyfile(source,target/name)
summary=dict(groups=20,casing_envelopes=20,inlet_reservations=20,both_side_access_reservations=40,
    original89network_entities_unchanged=True,native_box_reconciliation=80,
    casing_network_overlap_pairs=0,all_overlap_categories=audit['overlap_counts'],
    contact_waivers=0,candidate_inlet_counts={str(s):sum(r['revised_candidate_size_in']==s for r in revision['rows']) for s in [12,14]},
    nominal_inlet_duct_maximum_velocity_range_m_s=[min(r['maximum_duct_velocity_m_s'] for r in revision['rows']),max(r['maximum_duct_velocity_m_s'] for r in revision['rows'])],
    collar_over8m_s_groups=[r['id'] for r in revision['rows'] if r['maximum_collar_velocity_m_s']>8],
    collar_velocity_note='Course branch-duct target applies to proposed nominal inlet duct; no manufacturer internal-collar velocity limit claimed',
    native_reopen_pass=True,native_entity_count=native['checks']['model_entity_count'],
    all169native_GUIDs_projected=True,actual_PDF_visually_inspected=True,
    actual_PDF_review='Final rendered monochrome plot has bold casing outlines and dashed reservations; title/legend/notes/reference not visibly clipped or overlapping',
    reference_expected_mm=native['plot']['reference_expected_mm'],reference_measured_mm=native['plot']['reference_measured_mm'],
    source_catalogue_sha256=revision['catalogue_sha256'],source_IOM_sha256=revision['installation_manual_sha256'],
    assumptions=['Original abstract VAV node is proposed inlet collar entrance centre',
        'Inherited centreline z=0, not installed elevation',
        'Both-side access reservation includes conservative casing-length and height coverage; control handedness unselected'],
    upstream_rectangular_duct_replacements_required=20,connected_equipment=False,
    full_pressure_verified=False,installation_verified=False,design_accepted=False,
    deliverable_sha256={p.name:sha(p) for p in target.iterdir() if p.is_file()})
check=ROOT/'05_Calculations/Connection_Layout/VAV_Equipment_Space_Check.json'
assert not check.exists();check.write_text(json.dumps(dict(**summary,rows=revision['rows']),indent=2))
(RUN/'delivery-review.json').write_text(json.dumps(summary,indent=2))
agent=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
(agent/'docs/evidence/vav-equipment-space.json').write_text(json.dumps(summary,indent=2))
(target/'Review scope.md').write_text('''# VAV equipment space study

Finite manufacturer casing envelopes and reserved inlet/access spaces are
located on the coordinated rigid network. These are equipment candidates,
not connected installed products. Original abstract VAV points are assumed
to be inlet-collar entrance centres; reference elevation remains assumed.

Applying the course8m/s branch target to proposed nominal circular inlet ducts
changes the smallest combined capacity/control/velocity candidates to seven
size12 and thirteen size14. The earlier capacity-only study is preserved.
Catalogue collars are undersized; VAV01/12 collar velocities exceed8m/s,
which is retained separately and is not a manufacturer-limit failure claim.

Manufacturer source: Krueger LMHS MiniCatalog printed A2-4/A2-7/A2-26;
single-duct IOM PDF3 service access and PDF6 Step2A. Recommended inlet straight
length is3D and control access18in. Both-side reservations are conservative
host design assumptions pending control handedness and exact submittal.

All80saved native boxes reconcile. No casing intersects the represented
network, but all20inlet reservations overlap existing rectangular ducts:
replacement transitions and round straight sections are still required.
No overlap is waived. Architecture, elevation, insulation, supports,
clearance, distribution plenums, flex, acoustics and full pressure are pending.

Actual AutoCAD save/reopen and final1:200PDF visual review execute. Solid/bold
casing outlines and dashed reservations distinguish physical candidates from
reserved spaces in the monochrome plot. The model adds no new MEP ports;
the original89body197port88link pressure network remains unchanged.
''',encoding='utf8')
print(json.dumps(dict(candidate_counts=summary['candidate_inlet_counts'],delivered=list(summary['deliverable_sha256']),design_accepted=False),indent=2))
