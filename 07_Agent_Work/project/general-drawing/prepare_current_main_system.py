from pathlib import Path
import json,copy,os,csv,hashlib
import ifcopenshell
from bsa import drawing_ifc_graph,drawing_graph
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';O=B/'current-source-system-diagrams';F=O/'main-source';F.mkdir(exist_ok=False)
source=B/'recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc';m=ifcopenshell.open(str(source));main=ifcopenshell.open(str(B/'recentered-cross-network/Supply Network.ifc'));selected=sorted(o.GlobalId for o in main.by_type('IfcDistributionElement'));aliases={g:f'N{i+1:03d}' for i,g in enumerate(sorted(o.GlobalId for o in m.by_type('IfcDistributionElement')))};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();part=json.loads((O/'partition-review.json').read_text(encoding='utf-8'));feeds={g['upstream_main_product_guid']:g['id'].split('-')[1] for g in part['groups']};assert len(feeds)==20
spec=json.loads((Path(__file__).parent/'source-ifc-system-graph.json').read_text(encoding='utf-8'));spec.update(source='Current same-model native main port topology; schematic only',ifc=os.path.relpath(source,F),ifc_sha256=sha(source),products=selected)
s=spec['graph'];s['source']=spec['source'];s['notes']=[];s['layout'].update(origin=[25,65],nodesep_mm=7.4);s['sheet'].update(title='SUPPLY AIR MAIN SYSTEM',number='BSE3227-S-01')
paths=[B/f'recentered-logical-supply-network/vav-candidate-station-pressure/{v}/analysis.json' for v in ['maximum','minimum']];s['source_files']=[dict(path=os.path.relpath(p,F),sha256=sha(p)) for p in paths];project=F/'source.json';project.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8');graph,topo,_=drawing_ifc_graph.compose(project,F);assert topo['products']==118 and len(topo['interfaces'])==117 and len(topo['external_selected_connections'])==20 and len(topo['open_boundary_ports'])==1
key=[]
for node in graph['nodes']:
 g=node['id'];label=aliases[g]+('>'+feeds[g] if g in feeds else '')+('!' if g in spec['marked_products'] else '');node['label']=label;key.append(dict(group='MAIN',diagram_label=label,component_reference=aliases[g],product_guid=g,source_name=m.by_guid(g).Name or ''))
notes=['Nxxx>nn feeds VAV-nn on S02/S03; Nxxx is the source component reference.',
       '! marks the compound main junction: 4 numerical loss paths unresolved; other losses conditional.',
       'SD labels on S02/S03 identify terminal connection planes, not modeled diffuser geometry.',
       'Schematic lengths are not installed duct lengths. Full pressure, installation and ADPI unverified.']
graph['notes']=[dict(id=f'note-{i}',kind='text',layer='NOTES',source='Current source model topology and conditional pressure scope',classification='secondary_transcription',insert=[15,545-i*6],text=text,height=3.,rotation=0) for i,text in enumerate(notes)]
out=Path(__file__).parent/'current-main-system.json';graph['source_files']=[dict(path=os.path.relpath((F/r['path']).resolve(),out.parent),sha256=r['sha256']) for r in graph['source_files']];out.write_text(json.dumps(graph,indent=2)+'\n',encoding='utf-8');drawing_graph.configuration(out)
(O/'main-topology-review.json').write_text(json.dumps(topo,indent=2)+'\n',encoding='utf-8')
with (O/'Main System Component Index.csv').open('x',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(key[0]));w.writeheader();w.writerows(key)
print('Prepared current118main products/117interfaces/20source feeder references')
