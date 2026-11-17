"""Reconcile and publish the same recentered network's native and pressure artifacts."""
import hashlib
import html
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import shutil
import ifcopenshell
from bsa.duct_fitting_chain import shape_hash

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
AGENT=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
WORK=ROOT/'07_Agent_Work';RUN=WORK/'runs/recentered-network-integrated'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=json.loads((RUN/'drawing/native/native-verification.json').read_text())
geometry=json.loads((RUN/'independent-native-review.json').read_text())
raw=json.loads((RUN/'raw-clash/clash.json').read_text())
projection=json.loads((RUN/'drawing/projection.json').read_text())
assert native['native_reopen_pass'] and native['checks']['model_entity_count']==112
assert raw['intersection_pair_count']==0 and raw['clearance_violation_pair_count']==88
assert geometry['native_material_cap_pairs_matched']==88 and sha(RUN/'Supply Network.ifc')==geometry['ifc_sha256']==projection['ifc_sha256']
assert len(projection['component_contour_counts'])==89 and all(projection['component_contour_counts'].values())
assert sha(RUN/'drawing/native/sheet.pdf')==native['plot']['pdf_sha256']
local=json.loads((WORK/'runs/recentered-local-fittings/review.json').read_text())
point=json.loads((WORK/'runs/recentered-local-fittings/independent-review.json').read_text())
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'))
gains={}
for row in local['cases']:
    folder=WORK/'runs/recentered-local-fittings'/row['node']
    for path in [folder/'tee/unequal-tee.ifc',*[folder/r['arm']/'transition.ifc' for r in row['main_transitions']]]:
        obj=ifcopenshell.open(str(path)).by_type('IfcDuctFitting')[0]
        assert shape_hash(obj)==shape_hash(model.by_guid(obj.GlobalId))
    if row['node'] in ['TAP-VAV-04','TAP-VAV-10','TAP-VAV-16']:
        child=ifcopenshell.open(str(folder/row['main_transitions'][0]['arm']/'transition.ifc')).by_type('IfcDuctFitting')[0]
        gains[child.GlobalId]=next(p for p in point['independent_source_queries'] if p['node']==row['node'])
old=json.loads((WORK/'runs/reduced-branch-network-reviewed/one-plane-source-extension-reviewed/maximum/fitting-data.json').read_text())
key=lambda x:tuple(x[k] for k in ['product_guid','inlet_port_guid','outlet_port_guid'])
old_values={key(x):x for x in old['table_results']}
parts=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Coordinated Network Pressure Review</title><style>body{font:15px/1.5 Arial;max-width:1100px;margin:30px auto;padding:20px;color:#24343d}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #ccd6dd;padding:7px}th{background:#eaf1f5}</style><h1>Coordinated Network Pressure Review</h1><p>This saved rigid network now follows the optimized Connection Layout node positions, three compensated sections and source-prescribed flows. Six tee/main-transition groups and three elbows are updated; all45retained straight endpoints/profiles are reconciled. Original designs and earlier network studies are preserved.</p><p>89bodies,197ports,88connections and20outlet paths form one directed tree. All88native material interfaces match, and21boundaryframes match the selected source. Raw unchanged numerical policy finds zero solid intersections but88clearance violations at connected interfaces, with no waivers. Installation clearances remain unverified.</p><p>Both maximum and given40percent minimum cases have63fitting paths:31conditional values and32numerical gaps. Three transitions newly match source families; two previously populated transitions lose equal-angle applicability after the actual size change and remain null. This is a net reduction of one numerical gap, not proof of lower full pressure. No unknown value becomes zero.</p>']
expected=[];case_summaries={};added=[];lost=[]
for name,title in [('maximum','Maximum design flow'),('minimum','Given forty-percent minimum design flow')]:
    folder=RUN/'pressure'/name
    case=json.loads((folder/'analysis.json').read_text());loss=json.loads((folder/'fitting-data.json').read_text());ledger=json.loads((folder/'pressure-ledger.json').read_text())
    assert loss['calculated_table_paths']==31 and ledger['numerically_unresolved_fitting_path_count']==32
    for row in loss['table_results']:
        if row['product_guid'] in gains:
            p=gains[row['product_guid']];field='maximum_conditional_local_loss_Pa' if name=='maximum' else 'minimum_given40percent_conditional_local_loss_Pa'
            assert math.isclose(row['coefficient'],p['independently_recomputed_coefficient'],rel_tol=1e-12)
            assert math.isclose(row['signed_tabulated_contribution_Pa'],p[field],rel_tol=1e-12)
    if name=='maximum':
        fresh={key(x):x for x in loss['table_results']}
        added=[k for k,x in fresh.items() if x['coefficient'] is not None and old_values.get(k,{}).get('coefficient') is None]
        lost=[k for k,x in old_values.items() if x['coefficient'] is not None and fresh.get(k,{}).get('coefficient') is None]
        assert len(added)==3 and len(lost)==2
        assert all(fresh[k]['reason']=='declared transition family not met' for k in lost)
    parts.append('<h2>'+title+'</h2><p>Straight friction and signed conditional source subtotals are shown separately. They are neither fan duties nor assured pressure bounds. Parallel outlet paths must not be summed.</p><table><tr>'+''.join('<th>'+x+'</th>' for x in ['Outlet section','Flow L/s','Known straight Pa','Conditional signed subtotal Pa','Unknown fitting paths','Complete pressure'])+'</tr>')
    for row in ledger['outlet_paths']:
        port=case['port_flows'][row['outlet_port_guid']]
        values=[port['source_section'],f"{port['flow_m3_s']*1000:.3f}",f"{row['known_straight_friction_Pa']:.4f}",f"{row['conditional_signed_table_subtotal_Pa']:.4f}",str(len(row['numerically_unresolved_fitting_paths'])),'Unknown']
        expected.extend(values);parts.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in values)+'</tr>')
    parts.append('</table>')
    case_summaries[name]=dict(conditional_values=31,numerical_gaps=32,outlets=20)
parts.append('<h2>Scope</h2><p>Source:2021 ASHRAE Principles of HVAC Ninth Edition fitting supplement; original tentative contraction-data, reference-velocity and geometry-family conditions remain. Published applicability, internal fitting friction/stations, adjacent fitting/joint interaction, actual VAV/flexible-duct/terminal/equipment losses, boundary pressures and balancing remain unresolved. Clear internal nominal-size interpretation, gauge and reference elevation remain study assumptions. All33source requirements remain; full fan duty, actual thermal/ADPI, installed coordination and final engineering acceptance are not established. The native1:200drawing is a rigid-network overview with editable GUID-linked contours, not an installation sheet.</p></html>')
report=''.join(parts)
class Cells(HTMLParser):
    def __init__(self):super().__init__();self.on=False;self.values=[]
    def handle_starttag(self,t,a):
        if t=='td':self.on=True;self.values.append('')
    def handle_data(self,s):
        if self.on:self.values[-1]+=s
    def handle_endtag(self,t):
        if t=='td':self.on=False
parsed=Cells();parsed.feed(report);assert parsed.values==expected and len(expected)==240
dest=ROOT/'03_Design_Drawings/Connection_Layout'
outputs=[]
for src,name in [(RUN/'Supply Network.ifc','Supply Network Coordination.ifc'),(RUN/'drawing/native/section.dwg','Supply Network Coordination.dwg'),(RUN/'drawing/native/sheet.pdf','Supply Network Coordination.pdf')]:
    target=dest/name;assert not target.exists();shutil.copyfile(src,target);outputs.append(target)
calc=ROOT/'05_Calculations/Connection_Layout';report_file=calc/'Coordinated Network Pressure Review.html';assert not report_file.exists();report_file.write_text(report,encoding='utf-8');outputs.append(report_file)
summary=dict(**geometry,network_integrated=True,maximum=case_summaries['maximum'],minimum=case_summaries['minimum'],
    newly_supported_transition_paths=3,previous_transition_values_now_family_rejected=2,net_numerical_gap_reduction=1,
    raw_intersection_pairs=0,raw_clearance_violation_pairs=88,raw_contact_waivers=0,
    native_DWG_reopen_pass=True,native_entity_count=112,all89native_guids_in_drawing=True,
    plot_scale_denominator=200,plot_reference_expected_mm=50.,plot_reference_measured_mm=native['plot']['reference_measured_mm'],
    actual_PDF_page_visually_inspected=True,report_cells_reconciled=240,
    local_source_query_Decimal_checks_match=True,
    scope='Executed recentered rigid network and source-prescribed-flow pressure study; installed hardware, complete pressure and final design acceptance remain unresolved')
summary['deliverable_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in outputs}
(RUN/'delivery-review.json').write_text(json.dumps(summary,indent=2))
(calc/'Coordinated_Network_Check.json').write_text(json.dumps(summary,indent=2))
(AGENT/'docs/evidence/recentered-network.json').write_text(json.dumps(summary,indent=2))
with (dest/'Review scope.md').open('a',encoding='utf-8') as f:f.write('\n\nSupply Network Coordination IFC/DWG/PDF now rebases the finite rigid network\nto this recentered layout and three compensated sizes.89bodies/197ports/\n88links,all88materialcapinterfaces and21sourceboundaryframes match.\nActual native112entityDWGreopen and1:200PDF inspected;10mreference49.995667mm.\nMaximum/minimum31conditional fitting values and32numerical gaps; fullpressure\nunknown. Raw89validgeometry/zero intersections/88clearanceviolations, no waivers.\nSee the matching calculation report in05_Calculations/Connection_Layout.\nEarlier Network_Study is preserved as a different historical scenario.\nInstalled hardware,physicalclearance,flexlength,ADPI and final acceptance remain\nunresolved; this coordination overview is not an installation drawing.\n')
print(json.dumps({k:summary[k] for k in ['network_integrated','maximum','minimum','net_numerical_gap_reduction','raw_intersection_pairs','raw_clearance_violation_pairs','report_cells_reconciled']},indent=2))
