"""Bind the already-reviewed terminal curve to the current open-plenum paths."""
import csv
import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path

import ifcopenshell
from ifcopenshell.util.system import get_port_element
from bsa.manufacturer_adpi import catalogue
from bsa.source_pressure_ledger import calculate as ledger
from bsa.terminal_pressure_curve import calculate

P = Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
A = Path('C:/Users/lyuml-win/Desktop/building-services-agent')
B = P / '07_Agent_Work/runs'
R = B / 'recentered-logical-supply-network/vav-candidate-station-pressure'
O = B / 'recentered-open-plenum-network/terminal-boundary-pressure'
O.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = P / '07_Agent_Work/project/bse3227-terminal-source/Krueger_1400_51400_Performance.pdf'
assert sha(source) == '073c639219b28068a0c8190a926d493e42a12c0918db464ee8439c55a3994aef'
model = B / 'recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc'
assert sha(model) == 'a26626e4359ca82ca90de33423d46819b66bd78e54f22a0f52e221ff18ce2937'
m = ifcopenshell.open(str(model))
table = catalogue(source)['8']
prior = json.loads((B / 'logical-equipment-network/terminal-square-flow-pressure/review.json').read_text(encoding='utf-8'))
assert prior['pressure_method_sha256'] == sha(A / 'src/bsa/terminal_pressure_curve.py')
assert prior['source_catalogue_reader_sha256'] == sha(A / 'src/bsa/manufacturer_adpi.py')
assert prior['source_performance_pdf_sha256'] == sha(source)
index_path = P / '03_Design_Drawings/Connection_Layout/Current Open Plenum Study/Drawing Component Index.csv'
index = list(csv.DictReader(index_path.open(encoding='utf-8-sig')))
terminal_index = {r['native_port_guid']: r for r in index if r['label'].startswith('SD-')}
assert len(terminal_index) == 80
rows, cases, inputs = [], {}, {}
for condition in ['maximum', 'minimum']:
    files = {n: R / condition / n for n in ['analysis.json', 'fitting-data.json', 'pressure-ledger.json']}
    before = {n: sha(p) for n, p in files.items()}
    c, d, saved = [json.loads(files[n].read_text(encoding='utf-8')) for n in files]
    assert c['source_ifc_sha256'] == sha(model)
    result = ledger(c, d)
    assert result == saved
    own = []
    for path in result['outlet_paths']:
        guid = path['outlet_port_guid']
        port = c['port_flows'][guid]
        owner = get_port_element(m.by_guid(guid)).GlobalId
        assert terminal_index[guid]['product_guid'] == owner
        assert terminal_index[guid]['label'] == port['source_section']
        q = port['flow_m3_s'] * 1000
        value = calculate(table, q)
        lo, hi = next((a, b) for a, b in zip(table, table[1:]) if a['flow_L_s'] <= q <= b['flow_L_s'])
        dec = lambda x: Decimal(str(x))
        fraction = (dec(q)**2-dec(lo['flow_L_s'])**2)/(dec(hi['flow_L_s'])**2-dec(lo['flow_L_s'])**2)
        independent = dec(lo['total_pressure_Pa']) + fraction*(dec(hi['total_pressure_Pa'])-dec(lo['total_pressure_Pa']))
        assert math.isclose(float(independent), value['total_pressure_Pa'], rel_tol=1e-12)
        assert len(path['numerically_unresolved_fitting_paths']) == 2
        row = dict(condition=condition, terminal=port['source_section'], outlet_port_guid=guid,
                   native_endpoint_owner_guid=owner, design_flow_L_s=q,
                   assumed_catalogue_neck_in=8, conditional_terminal_total_pressure_Pa=value['total_pressure_Pa'],
                   represented_straight_partial_Pa=path['known_straight_friction_Pa'],
                   conditional_component_partial_Pa=path['conditional_signed_table_subtotal_Pa'],
                   conditional_budget_with_terminal_Pa=math.fsum([path['known_straight_friction_Pa'], path['conditional_signed_table_subtotal_Pa'], value['total_pressure_Pa']]),
                   remaining_component_gaps=2, complete_pressure_Pa='Unknown', actual_controlled_VAV_loss_Pa='Unknown')
        rows.append(row)
        own.append(row)
    assert len(own) == 80 and len({r['terminal'] for r in own}) == 80
    assert before == {n: sha(p) for n, p in files.items()}
    inputs[condition] = before
    cases[condition] = dict(terminals=80, conditional_terminal_Pt_range_Pa=[min(r['conditional_terminal_total_pressure_Pa'] for r in own), max(r['conditional_terminal_total_pressure_Pa'] for r in own)], remaining_unique_component_gaps=84, complete_pressure_verified=False)
with (O / 'Terminal Boundary Pressure Budget.csv').open('x', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
review = dict(source_ifc_sha256=sha(model), drawing_component_index_sha256=sha(index_path), native_endpoint_and_drawing_index_checks=160, source_performance_pdf_sha256=sha(source), source_locator='PDF2/B1-12 Model1400 nominal8inch 600x600mm panel without damper', previously_reviewed_source_and_method_hashes_match=True, method_sha256=sha(A/'src/bsa/terminal_pressure_curve.py'), input_sha256=inputs, terminal_rows=160, independent_Decimal_pressure_checks=160, cases=cases, source_ledgers_unchanged=True, terminal_Pt_added_once=True, static_or_neck_velocity_pressure_added_again=False, interpolation_basis='Piecewise linear pressure in squared flow; comparison assumption', room_static_reference='Assumed common0Pa gauge; not measured', installed_terminal_and_catalogue_test_plane_correspondence_verified=False, fully_open_VAV_comparison_only=True, actual_controlled_VAV_loss_verified=False, ADPI_verified=False, complete_pressure_verified=False, hydraulic_critical_path=None, fan_duty_Pa=None, design_accepted=False)
(O / 'review.json').write_text(json.dumps(review, indent=2, allow_nan=False)+'\n', encoding='utf-8')
print(json.dumps(review, indent=2))
