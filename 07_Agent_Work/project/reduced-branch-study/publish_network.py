"""Prepare clean study deliverables without publishing protected source tables."""
import hashlib
import html
import json
from pathlib import Path
import shutil
from collections import Counter

ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/'07_Agent_Work/runs/reduced-branch-network-reviewed'
AGENT=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
case=json.loads((RUN/'analysis.json').read_text());minimum=json.loads((RUN/'minimum-flow/analysis.json').read_text())
maximum_ledger=json.loads((RUN/'reynolds-source-extension/maximum/pressure-ledger.json').read_text())
minimum_ledger=json.loads((RUN/'reynolds-source-extension/minimum/pressure-ledger.json').read_text())
native=json.loads((RUN/'drawing/native/native-verification.json').read_text())
audit=json.loads((RUN/'independent-review.json').read_text())
reynolds=json.loads((RUN/'reynolds-source-extension/review.json').read_text())
clash=json.loads((RUN/'raw-clash/clash.json').read_text())
assert audit['native_material_cap_pairs_matched']==88
assert reynolds['cases']['maximum']==reynolds['cases']['minimum']==dict(finite_paths=29,numerical_gaps=34,outlets=20)
assert native['native_reopen_pass'] and native['checks']['model_entity_count']==112
assert clash['intersection_pair_count']==0 and clash['clearance_violation_pair_count']==88
dest=ROOT/'03_Design_Drawings/Network_Study';dest.mkdir(parents=True,exist_ok=False)
for source,name in [(RUN/'Supply Network.ifc','Supply Network Study.ifc'),(RUN/'drawing/native/section.dwg','Supply Network Study.dwg'),(RUN/'drawing/native/sheet.pdf','Supply Network Study.pdf')]:
    shutil.copyfile(source,dest/name)
parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><title>Supply Network Pressure Review</title><style>body{font:16px/1.5 Arial;max-width:1100px;margin:30px auto;padding:20px;color:#24343d}table{border-collapse:collapse;width:100%;margin:20px 0}th,td{border:1px solid #ccd6dd;padding:8px;text-align:left}th{background:#eaf1f5}.pending{background:#fff0d2;padding:18px}h1{line-height:1.2}</style><h1>Supply Network Pressure Review</h1><p class="pending">Separate engineering study; full pressure and fan duty remain unknown. This is not a merged design with the relocated VAV Connection Layout scenario. Original course sources and designs are preserved.</p><p>Thirteen enlarged branch-plus-taper arrangements are replaced by reduced-branch sharp tees while retaining external end planes, original outlet demands and the source requirement inventory. The saved rigid model contains89bodies,197ports,88connections and20outlet paths. All88native material cap pairs match. The same unwaived numerical policy finds zero solid intersections and88clearance violations at connected interfaces; this does not establish installation clearance.</p><p>Both maximum and given40percent minimum flow conserve at every port and product. There are63fitting paths:29with conditional source values and34without. The original model had76paths,31conditional values and45gaps. Removing13tapers removes3previously populated values and10unknowns; one revised branch obtains a new bounded source value. Neither component reduction nor missing-data reduction proves a lower complete pressure.</p><p>At minimum flow, elbow Reynolds numbers and source corrections are recalculated. One previously plateau-only binding now uses the same publisher printed12 correction row for lower Reynolds numbers. Independent Decimal arithmetic agrees; maximum-flow values are unchanged. No bounds are extrapolated.</p>''']
for title,ledger,flows in [('Maximum design flow',maximum_ledger,case),('Given forty-percent minimum design flow',minimum_ledger,minimum)]:
    parts.append('<h2>'+title+'</h2><p>Conditional signed source subtotals are separate from native straight friction. They are neither lower bounds nor fan duties. Parallel paths must not be summed.</p><table><tr><th>Outlet source section</th><th>Flow L/s</th><th>Known straight Pa</th><th>Conditional signed subtotal Pa</th><th>Unknown fitting paths</th><th>Complete pressure</th></tr>')
    for row in ledger['outlet_paths']:
        port=flows['port_flows'][row['outlet_port_guid']]
        values=[port['source_section'],f"{port['flow_m3_s']*1000:.3f}",f"{row['known_straight_friction_Pa']:.4f}",f"{row['conditional_signed_table_subtotal_Pa']:.4f}",len(row['numerically_unresolved_fitting_paths']),'Unknown']
        parts.append('<tr>'+''.join('<td>'+html.escape(str(value))+'</td>' for value in values)+'</tr>')
    parts.append('</table>')
parts.append('<h2>Source and scope</h2><p>2021 ASHRAE Principles of HVAC Ninth Edition online fitting supplement, source-pinned native geometry and the original brief minimum40percent turndown. Published applicability, whole-fitting friction/stations, adjacent fitting and joint interaction, flexible ducts, terminals/equipment and boundary pressures remain unresolved. Nominal dimensions as clear internal sizes, elevation and gauge remain declared study assumptions. Actual room load, ADPI, physical installation and complete engineering acceptance are not established. All33source requirements and six project input gaps remain.</p><p>The DWG/PDF is a1:200rigid-network overview, not an installation drawing. Source IFC GUIDs are retained in editable CAD entities; full private source and numerical provenance stay in the selected workspace.</p></html>')
(ROOT/'05_Calculations/Supply Network Pressure Review.html').write_text(''.join(parts),encoding='utf-8')
(dest/'Review scope.md').write_text('''# Supply Network Study

Separate source-linked rigid-network revision:13reduced-branch tees replace
13enlarged-branch/taper arrangements while preserving original external ends
and prescribed design flows.89bodies,197ports,88connections,20outlets.
Native IFC schema/geometry/port replay and all88material cap matches pass.
Same raw policy:zero intersections,88clearance violations; no waivers.
Maximum and40percent minimum cases each retain34unknown fitting paths.
Full pressure,fan duty,installation/architecture,equipment,load/ADPI and
complete engineering acceptance remain unresolved.

Actual AutoCAD save/reopen verifies112entities; all89native product IDs are
present in linked contours. Actual A4at1:200PDF visually inspected;10m
reference expected50mm,measured49.995667mm. No observed title/geometry/reference
overlap or clipping. This is a rigid-network overview,not an installation sheet.

This is based on the earlier compound-network source scenario. It is not a
merge with Connection_Layout and its VAV relocations/size changes. Do not
combine scenarios as an accepted design. Original course sources and parent
network remain unchanged. See the separate Supply Network Pressure Review.
''',encoding='utf-8')
visual=dict(pdf_sha256=sha(dest/'Supply Network Study.pdf'),actual_pdf_page_inspected=True,
    observation='Actual A4at1:200page: readable headings/notes and separated rigid contours/reference; no observed clipping or overlaps. No per-component tag or installation-detail acceptance.',engineering_accepted=False)
(RUN/'drawing/visual-review.json').write_text(json.dumps(visual,indent=2))
summary=dict(revised_tees=13,removed_separate_tapers=13,bodies=89,ports=197,links=88,outlets=20,source_requirements=33,native_cap_pairs_matched=88,
    unchanged_retained_straights=45,maximum_flow_continuity_pass=True,minimum_flow_continuity_pass=True,maximum_fitting_paths=63,
    maximum_conditional_values=29,maximum_numeric_gaps=34,minimum_conditional_values=29,minimum_numeric_gaps=34,original_numeric_gaps=45,
    old_finite_values_retained=28,removed_finite_transition_values=3,new_supported_branch_values=1,lower_Re_source_extension_independently_verified=True,
    original_maximum_elbow_result_unchanged=True,raw_geometry_coverage=True,raw_intersection_pairs=0,raw_clearance_violation_pairs=88,
    native_dwg_reopen_pass=True,native_dwg_entities=112,all89native_guids_in_contours=True,plot_scale=200,reference_expected_mm=50.,
    reference_measured_mm=native['plot']['reference_measured_mm'],actual_pdf_visual_review_pass=True,original_network_modified=False,
    pressure_budget_complete=False,design_accepted=False,common_mcp_producer_registered=False,
    scope='Executed project-scoped composition of existing engines; separate source scenario, not unified coursework or installation acceptance',
    revision_sha256=sha(RUN/'revision.json'),independent_review_sha256=sha(RUN/'independent-review.json'),reynolds_review_sha256=sha(RUN/'reynolds-source-extension/review.json'))
(AGENT/'docs/evidence/reduced-branch-network.json').write_text(json.dumps(summary,indent=2))
(ROOT/'05_Calculations/Supply_Network_Study_Check.json').write_text(json.dumps(summary,indent=2))
print('Delivered:',dest)
print('Remaining gaps:',Counter(x['predefined_type'] for x in maximum_ledger['missing_evidence_by_outlet_coverage']))
