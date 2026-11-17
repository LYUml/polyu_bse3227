"""Compose existing native IFC graph, Graphviz and view-packing adapters."""
from pathlib import Path
import argparse
import copy
import csv
import hashlib
import json
import math
import os
import subprocess

import ifcopenshell
import ezdxf
from bsa import drawing_ifc_graph, drawing_graph, drawing_layout
from bsa.cad_text_layout import text_box
from bsa.three_phase_drawing import DOT_SHA256

parser = argparse.ArgumentParser()
parser.add_argument('--graphviz', required=True)
args = parser.parse_args()
P = Path('C:/Users/lyuml-win/Desktop/polyu_bse3227')
B = P / '07_Agent_Work/runs'
O = B / 'current-source-system-diagrams'
source = B / 'recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path(args.graphviz)) == DOT_SHA256
partition = json.loads((O / 'partition-review.json').read_text(encoding='utf-8'))
assert partition['source_ifc_sha256'] == sha(source)
m = ifcopenshell.open(str(source))
objects = {o.GlobalId: o for o in m.by_type('IfcDistributionElement')}
aliases = {g: f'N{i+1:03d}' for i, g in enumerate(sorted(objects))}
template = json.loads((Path(__file__).parent / 'source-ifc-system-graph.json').read_text(encoding='utf-8'))
flows = {condition: B / f'recentered-logical-supply-network/vav-candidate-station-pressure/{condition}/analysis.json'
         for condition in ['maximum', 'minimum']}
views, key, topologies = [], [], []


def write_exact(path, value):
    text = json.dumps(value, indent=2, allow_nan=False) + '\n'
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8')) == value, path
    else:
        path.write_text(text, encoding='utf-8')


for group in partition['groups']:
    folder = O / 'graph-cache-directional' / group['id']
    folder.mkdir(parents=True, exist_ok=True)
    spec = copy.deepcopy(template)
    spec.update(source='Current source IFC terminal system; schematic topology only',
                ifc=os.path.relpath(source, folder), ifc_sha256=sha(source),
                products=group['products'], marked_products=[group['plenum_guid']])
    graph = spec['graph']
    graph.update(source=spec['source'], notes=[],
                 source_files=[dict(path=os.path.relpath(p, folder), sha256=sha(p)) for p in flows.values()])
    graph['layout'].update(origin=[15, 45], factor=1., node_width_mm=24.,
                           node_height_mm=9., text_height_mm=2., ranksep_mm=4., nodesep_mm=4., rankdir='LR', edge_ports='rank_direction')
    project = folder / 'source.json'
    write_exact(project, spec)
    resolved, topology, _ = drawing_ifc_graph.compose(project, folder)
    assert topology['products'] == 24 and topology['ports'] == 51
    assert len(topology['interfaces']) == 23
    assert len(topology['external_selected_connections']) == 1
    assert len(topology['open_boundary_ports']) == 4
    expected = {(e['from'], e['to'], e['source_port'], e['sink_port']) for e in group['internal_interfaces']}
    assert expected == {(e['from_guid'], e['to_guid'], e['source_port'], e['sink_port']) for e in topology['interfaces']}
    leaves = {r['product_guid']: r for r in group['terminal_leaves']}
    for node in resolved['nodes']:
        guid = node['id']
        label = aliases[guid]
        if guid == group['vav_guid']:
            label = group['id']
        elif guid == group['plenum_guid']:
            label = 'J-' + group['id'].split('-')[1]
        elif guid in leaves:
            row = leaves[guid]
            label = row['label']
        node['label'] = label
        key.append(dict(group=group['id'], diagram_label=label, component_reference=aliases[guid],
                        product_guid=guid, source_name=objects[guid].Name or ''))
    write_exact(folder / 'declared-graph.json', resolved)
    drawing_graph.configuration(folder / 'declared-graph.json')
    write_exact(folder / 'source-topology.json', topology)
    dot = drawing_graph.dot_source(resolved)
    dot_file = folder / 'graph.dot'
    if dot_file.exists():
        assert dot_file.read_text(encoding='utf-8') == dot
    else:
        dot_file.write_text(dot, encoding='utf-8')
    layout_file = folder / 'graphviz.json'
    if not layout_file.exists():
        result = subprocess.run([args.graphviz, '-Tjson', str(dot_file)], capture_output=True, timeout=60)
        (folder / 'graphviz.log').write_bytes(result.stderr)
        assert result.returncode == 0
        layout_file.write_bytes(result.stdout)
    document = drawing_graph.compose(resolved, json.loads(layout_file.read_text(encoding='utf-8')))
    entities = document['entities']
    for guid, row in leaves.items():
        box = next(e for e in entities if e['id'].startswith(f'node:{guid}:box:'))
        center = [(min(p[i] for p in box['points'])+max(p[i] for p in box['points']))/2 for i in range(2)]
        label = next(e for e in entities if e['id'] == f'node:{guid}:label')
        label['insert'][1] += 1.6
        text = f"{row['maximum_flow_L_s']:.0f}/{row['minimum_flow_L_s']:.0f}"
        temp = ezdxf.new().modelspace().add_text(text, dxfattribs={'height': 2.})
        bounds = text_box(temp)
        entities.append(dict(id=f'node:{guid}:flow', kind='text', layer='NOTES',
                             source='Transcribed maximum/minimum L/s from bound calculation cases',
                             classification='secondary_transcription', height=2., rotation=0,
                             text=text, insert=[float(center[0]-(bounds[0]+bounds[2])/2),
                                                float(center[1]-1.6-(bounds[1]+bounds[3])/2)]))
    for e in entities:
        e['id'] = group['id'] + ':' + e['id']
    points = [p for e in entities if e['kind'] == 'polyline' for p in e['points']]
    ymax = max(p[1] for p in points)
    qmax = math.fsum(r['maximum_flow_L_s'] for r in leaves.values())
    qmin = math.fsum(r['minimum_flow_L_s'] for r in leaves.values())
    entities.append(dict(id=group['id'] + ':heading', kind='text', layer='NOTES',
                         source='Transcribed prescribed terminal flows from current bound calculation cases',
                         classification='secondary_transcription', insert=[15, ymax+7], height=2.5,
                         rotation=0, text=f"{group['id']}    {qmax:.0f}/{qmin:.0f} L/s"))
    views.append(dict(id=group['id'], entities=entities))
    topologies.append(topology)
    print('Composed', group['id'], flush=True)

notes = [
    'TERMINAL SYSTEMS - 20 source VAV groups / 80 outlets; 480 actual distribution products',
    'Box labels: source equipment/outlet IDs or Nxxx component references; see Component Index.',
    'Below terminal IDs: maximum/minimum L/s, rounded to nearest 1 L/s; calculation assumptions apply.',
    'Bold J boxes: pressure data unresolved. Schematic lengths are not installed duct lengths.',
    'Complete pressure, physical installation and ADPI remain unverified. Main network is separate.',
]
legend = [dict(id=f'legend:{i}', kind='text', layer='NOTES', source='Drawing scope and bound calculation cases',
               classification='secondary_transcription', insert=[0, i*5], height=2.5, rotation=0, text=text)
          for i, text in enumerate(reversed(notes))]
views.append(dict(id='Legend', entities=legend))
sheet = copy.deepcopy(template['graph']['sheet'])
sheet.update(title='SUPPLY AIR TERMINAL SYSTEMS', number='BSE3227-S-02')
layout = dict(schema='bsa.drawing-layout/1', source='Same current source IFC and prescribed maximum/minimum calculation cases',
              units='mm', layers=template['graph']['layers'], blocks={}, sheet=sheet,
              content_window=[15, 40, 812, 550], gap_mm=8., views=views)
document, packing = drawing_layout.compose(layout)
out = Path(__file__).parent / 'current-terminal-systems-directed.json'
write_exact(out, layout)
write_exact(O / 'prepared-terminal-document-directed.json', document)
write_exact(O / 'prepared-terminal-packing-directed.json', packing)
with (O / 'Terminal System Component Index.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(key[0])); writer.writeheader(); writer.writerows(key)
write_exact(O / 'terminal-preflight-directed.json', dict(source_ifc_sha256=sha(source),
            input_sha256=sha(out), graphviz_sha256=DOT_SHA256, groups=20, products=480,
            native_internal_interfaces=460, native_external_main_connections=20, terminal_leaves=80,
            all_native_source_topologies_reconciled=True, views_packed=21,
            source_geometry_changed=False, native_CAD_executed=False, design_accepted=False))
print('Prepared all20 native source groups /480products /80outlets; no native CAD claim', flush=True)
