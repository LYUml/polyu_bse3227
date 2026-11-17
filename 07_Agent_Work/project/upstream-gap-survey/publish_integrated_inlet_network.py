"""Deliver consistent current network geometry, inlet datums and scoped pressure."""
import csv,hashlib,html,json,shutil
from pathlib import Path
import numpy as np
import ezdxf,ifcopenshell
from ifcopenshell.util import placement

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');RUN=ROOT/'07_Agent_Work/runs/inlet-integrated-network'
AGENT=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
integration=json.loads((RUN/'integration.json').read_text());caps=json.loads((RUN/'native-cap-review.json').read_text())
flow=json.loads((RUN/'flow-review.json').read_text());raw=json.loads((RUN/'raw-clash/clash.json').read_text())
pressure=json.loads((RUN/'pressure/review.json').read_text());space=json.loads((RUN/'equipment-space/sync-review.json').read_text())
casing=json.loads((RUN/'equipment-space/casing-intersection-review.json').read_text())
native=json.loads((RUN/'drawing/native/native-verification.json').read_text())
projection=json.loads((RUN/'drawing/projection.json').read_text())
IFC=RUN/'Supply Network.ifc';model=ifcopenshell.open(str(IFC))
assert sha(IFC)==integration['ifc_sha256']==caps['ifc_sha256']==pressure['ifc_sha256']==projection['ifc_sha256']
assert raw['inputs'][str(IFC)]==sha(IFC) and raw['intersection_pair_count']==0 and raw['clearance_violation_pair_count']==128
assert space['source_ifc_sha256']==sha(IFC) and sha(RUN/'equipment-space/model.ifc')==space['combined_ifc_sha256']==casing['source_ifc_sha256']
assert native['native_reopen_pass'] and native['plot']['pdf_reference_pass'] and projection['represented_products']==129
doc=ezdxf.readfile(RUN/'drawing/native/native-reopen/source-export.dxf');assert doc.units==6
labels={e.dxf.text:e for e in doc.modelspace() if e.dxftype()=='TEXT' and e.dxf.layer=='BSA_VAV_LABEL'}
assert len(labels)==20;offsets=[]
for row in space['rows']:
    p=model.by_guid(row['source_port_guid']);point=placement.get_local_placement(p.ObjectPlacement)[:3,3]
    assert np.allclose(point,row['inlet_point_m'],atol=1e-9,rtol=0)
    offsets.append(np.array(labels[row['id']].dxf.insert)[:2]-point[:2]-[.15,-.45])
assert np.allclose(offsets,offsets[0],atol=1e-8,rtol=0)
with (RUN/'equipment-space/VAV Inlet Coordinates.csv').open(encoding='utf8',newline='') as f:csvrows=list(csv.reader(f))
assert len(csvrows)==21 and all(len(r)==10 for r in csvrows)
for r,source in zip(csvrows[1:],space['rows']):
    assert r[0]==source['id']
    expected=[*source['inlet_point_m'],source['nominal_diameter_mm'],source['qmax_L_s'],source['qmin_L_s'],*source['shift_m']]
    assert np.allclose(list(map(float,r[1:])),expected,atol=1e-10,rtol=0)
target=ROOT/'03_Design_Drawings/Connection_Layout/Integrated_Inlet_Design';target.mkdir(exist_ok=False)
for source,name in [(IFC,'Supply Network with VAV Inlets.ifc'),(RUN/'equipment-space/model.ifc','Candidate Equipment Spaces.ifc'),
    (RUN/'drawing/native/section.dwg','Supply Network with VAV Inlets.dwg'),(RUN/'drawing/native/sheet.pdf','Supply Network with VAV Inlets.pdf')]:shutil.copyfile(source,target/name)
calculations=ROOT/'05_Calculations/Connection_Layout'
coordinate_target=calculations/'Integrated VAV Inlet Coordinates.csv';assert not coordinate_target.exists()
shutil.copyfile(RUN/'equipment-space/VAV Inlet Coordinates.csv',coordinate_target)
summaries={};tables=[]
for condition in ['maximum','minimum']:
    ledger=json.loads((RUN/'pressure'/condition/'pressure-ledger.json').read_text())
    analysis=json.loads((RUN/'pressure'/condition/'analysis.json').read_text())
    assert len(analysis['original_requirement_ids'])==33 and len(analysis['straight_sections'])==65
    assert len(ledger['outlet_paths'])==20 and ledger['numerically_unresolved_fitting_path_count']==52
    rows=[]
    for inlet in space['rows']:
        path=next(p for p in ledger['outlet_paths'] if p['outlet_port_guid']==inlet['source_port_guid'])
        Q=flow['cases'][condition]['port_flows'][inlet['source_port_guid']]['flow_m3_s']*1000
        row=dict(id=inlet['id'],outlet_port_guid=inlet['source_port_guid'],flow_L_s=Q,
            known_straight_Pa=path['known_straight_friction_Pa'],conditional_signed_fitting_Pa=path['conditional_signed_table_subtotal_Pa'],
            missing_fitting_paths=len(path['numerically_unresolved_fitting_paths']),complete_pressure_Pa=None)
        rows.append(row)
    summaries[condition]=dict(**pressure['cases'][condition],rows=rows,critical_path=None,fan_duty_Pa=None)
    body=''.join('<tr>'+''.join('<td>'+html.escape(str(v) if isinstance(v,str) else f'{v:.6f}')+'</td>' for v in [condition,r['id'],r['flow_L_s'],r['known_straight_Pa'],r['conditional_signed_fitting_Pa'],r['missing_fitting_paths']])+'<td>Unknown</td></tr>' for r in rows)
    tables.append('<h2>'+condition.capitalize()+'</h2><table><tr><th>Case</th><th>VAV</th><th>Flow L/s</th><th>Known straight Pa</th><th>Conditional signed fitting Pa</th><th>Missing fitting paths</th><th>Complete pressure</th></tr>'+body+'</table>')
report='''<!doctype html><meta charset="utf-8"><title>Integrated VAV Inlet Pressure Review</title><style>body{font:16px Arial;max-width:1200px;margin:30px auto;line-height:1.5}table{border-collapse:collapse}td,th{padding:7px;border:1px solid #bbb;text-align:right}</style><h1>Integrated VAV Inlet Pressure Review</h1><p>Actual saved mixed-profile network:129bodies,277ports,128connections,one directed tree and20outlets. All128material interfaces and both source-prescribed flow cases are checked. Forty new inlet components are integrated by trimming twenty existing rectangular straights. Source originals are preserved.</p><p>Both cases include65native straight spans and83fitting paths. Thirty-one fitting paths have conditional table values;52lack numerical values, including20new rectangle-to-circle transitions. The original32rigid-network fitting gaps remain. No unknown is converted to zero. Signed partial subtotals are neither lower bounds nor fan duties; parallel paths are never summed.</p><p>Rectangular spans and source queries are freshly calculated on an exact native subgraph of this model. New circular spans use saved bore/length and source-prescribed flows with the existing fluids Darcy engine. Actual full saved port topology reconstructs every path. Reference stations, physical correlation applicability, seams, equipment and boundary-pressure requirements remain unresolved.</p>'''+''.join(tables)+'''<p>Updated equipment inlet coordinate schedule and candidate casing model use these actual outlet datums. Five candidate positions move;these are not verified installed equipment locations. The old flex/discharge schedule remains a separate earlier schematic and does not verify new equipment outlet or plenum connections.</p><p>Actual AutoCAD save/reopen and actual final1:200PDF inspection execute for the horizontal material section at assumed reference z=0. Network intersections0;128unwaived contact-clearance findings remain. A separate check of129network bodies plus20candidate casing envelopes finds no solid intersections;this excludes60nonphysicalreservation proxies and does not establish installed clearance or architecture fit.</p>'''
report_path=calculations/'Integrated VAV Inlet Pressure Review.html';assert not report_path.exists();report_path.write_text(report,encoding='utf8')
assert report.count('<td>')==280 and report.count('Unknown</td>')==40
for condition in summaries.values():
    for row in condition['rows']:
        for key in ['flow_L_s','known_straight_Pa','conditional_signed_fitting_Pa','missing_fitting_paths']:assert f"{row[key]:.6f}" in report
summary=dict(network_bodies=129,ports=277,links=128,boundaries=21,connected_directed_tree=True,
    trimmed_rectangular_segments=20,original_requirement_ids_retained=33,native_rectangular_cap_matches=108,native_circular_cap_matches=20,
    source_flows_reconciled_at_all277ports=True,maximum_m3_s=flow['cases']['maximum']['inlet_m3_s'],minimum_m3_s=flow['cases']['minimum']['inlet_m3_s'],
    raw_network_intersections=0,raw_network_clearance_violations=128,contact_waivers=0,
    candidate_casings=20,candidate_casings_moved=5,casing_plus_network_intersections=0,
    nonphysical_reservation_proxies_excluded_from149body_casing_intersection_check=60,
    both_cases=dict(straight_spans=65,fitting_paths=83,conditional_values=31,numerical_gaps=52),
    native_DWG_reopened=True,native_DWG_entities=native['checks']['model_entity_count'],all129native_GUIDs_in_section=True,
    actual_PDF_visually_inspected=True,PDF_review='Actual horizontal material sections;20inlet labels, title/notes/reference show no observed clipping or overlap',
    print_reference_expected_mm=native['plot']['reference_expected_mm'],print_reference_measured_mm=native['plot']['reference_measured_mm'],
    native20CADlabel_datum_checks_pass=True,coordinate_CSV200cells_reconciled=True,pressure_HTML280cells_reconciled=True,
    scope='Integrated rigid mixed-profile network to proposed equipment inlet boundaries; VAV internal/discharge/plenum/flex, actual installation and full pressure unresolved',
    pressure_budget_complete=False,full_pressure_verified=False,installation_verified=False,design_accepted=False,
    deliverable_sha256={p.name:sha(p) for p in target.iterdir() if p.is_file()})
check=calculations/'Integrated_Inlet_Network_Check.json';assert not check.exists()
check.write_text(json.dumps(dict(**summary,coordinates=space['rows'],pressure=summaries),indent=2))
(RUN/'delivery-review.json').write_text(json.dumps(summary,indent=2))
(AGENT/'docs/evidence/integrated-inlet-network.json').write_text(json.dumps(summary,indent=2))
(target/'Review scope.md').write_text('''# Integrated inlet design study

The saved network has129actual bodies,277ports and128links in one source-directed
tree,with one inlet and twenty proposed equipment-inlet boundaries. Twenty
rectangular source straights are trimmed and forty checked inlet components are
integrated. Source geometry and previous design studies remain preserved.

The candidate equipment-space model adds20casing and60nonphysicalreservation
proxies;five casing positions are updated to the actual new inlet datums.
129network records remain byte-identical in that appended coordination model.
Inlet reservations now use actual saved round outside diameter; insulation and
installed clearances are not inferred. Casing location/datum/control handedness
and gauge/reference elevation remain assumptions. These are unselected products.

Native schema,108rectangular/20circular material interfaces,actual graph and both
277port flow cases verify. Raw network clash finds0intersections and128unwaived
contact findings. A separate149body network/casing intersection check excludes
60nonphysicalreservations and finds0solid intersections;no installation pass follows.

Actual native DWG save/reopen and inspected horizontal material-section PDF
represent all129network bodies and20inlet labels. Candidate casings/reservations
are in the separate IFC,not asserted to appear in the129body drawing.
The coordinate CSV matches saved inlet datums and native CAD label translation.

Fresh maximum/minimum calculations include65straight spans and83fitting paths:
31conditional table values,52numerical gaps. This includes20new transitions with
unknown loss;the original32gaps remain. Complete pressure,fan duty and critical
path stay unknown. No signed partial sum is called a lower bound or fan duty.

Actual VAV internal/collar/discharge connections,distribution plenum,flex routes,
controls/acoustics,architectural clearance and load/ADPI/final submission review
remain incomplete. Earlier flex and equipment-space studies are different
scenarios;their acceptance is not carried onto these changed inlet datums.
''',encoding='utf8')
print(json.dumps(dict(delivered_network_bodies=129,updated_casings=20,pressure_cases=2,numerical_gaps=52,full_pressure_verified=False)))
