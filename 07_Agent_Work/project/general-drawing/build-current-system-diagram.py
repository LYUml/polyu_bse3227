from pathlib import Path
import json,hashlib,subprocess,csv
import numpy as np,ifcopenshell,ifcopenshell.util.system as system
import ezdxf
from ezdxf.math import Bezier4P,Vec2
from bsa.source_network_analysis import prescribed_flows
from bsa.three_phase_drawing import DOT_SHA256
from bsa.cad_text_layout import text_box
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work');S=B/'runs/recentered-constant-height-network';O=B/'runs/current-system-topology-input';O.mkdir(exist_ok=False);dot=Path('C:/Users/lyuml-win/Desktop/building-services-agent/tools/freecad-1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311/bin/dot.exe');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(dot)==DOT_SHA256
pins={str(p):sha(p) for p in [S/'Supply Network.ifc',S/'pressure/maximum/pressure-ledger.json',S/'pressure/maximum/analysis.json']};model=ifcopenshell.open(str(S/'Supply Network.ifc'));ledger=json.loads((S/'pressure/maximum/pressure-ledger.json').read_text());analysis=json.loads((S/'pressure/maximum/analysis.json').read_text());objects=sorted(model.by_type('IfcDistributionElement'),key=lambda o:o.GlobalId);names={o.GlobalId:f'N{i+1:03d}' for i,o in enumerate(objects)};owned={o.GlobalId:[p.GlobalId for p in system.get_ports(o)] for o in objects};directions={p.GlobalId:p.FlowDirection for o in objects for p in system.get_ports(o)};links=[];edges=[]
for rel in model.by_type('IfcRelConnectsPorts'):
 a,b=rel.RelatingPort,rel.RelatedPort
 if a.FlowDirection=='SINK':a,b=b,a
 assert a.FlowDirection=='SOURCE' and b.FlowDirection=='SINK';u=system.get_port_element(a).GlobalId;v=system.get_port_element(b).GlobalId;links.append((a.GlobalId,b.GlobalId));edges.append((u,v,a.GlobalId,b.GlobalId))
assert len(objects)==110 and len(edges)==109
flows=prescribed_flows(owned,directions,links,analysis['port_flows']);bad={r['product_guid'] for p in ledger['outlet_paths'] for r in p['numerically_unresolved_fitting_paths']};assert len(bad)==5
lines=['digraph G {','graph [rankdir=LR,splines=ortho,nodesep=0.18,ranksep=0.16];','node [shape=box,fixedsize=true,width=0.55,height=0.25,fontsize=7];']
for obj in objects:lines.append(f'{names[obj.GlobalId]} [label="{names[obj.GlobalId]}'+('!' if obj.GlobalId in bad else '')+'"];')
for i,(u,v,_,_) in enumerate(edges):lines.append(f'{names[u]} -> {names[v]} [id="e{i}"];')
lines.append('}');(O/'layout.dot').write_text('\n'.join(lines));proc=subprocess.run([str(dot),'-Tjson',str(O/'layout.dot')],capture_output=True,timeout=60);assert proc.returncode==0,proc.stderr;layout=json.loads(proc.stdout);(O/'layout.json').write_bytes(proc.stdout);bounds=[float(x) for x in layout['bb'].split(',')];factor=25.4/72;offset=[15-bounds[0]*factor,50-bounds[1]*factor];assert (bounds[2]-bounds[0])*factor<790 and (bounds[3]-bounds[1])*factor<460
entities=[];byid={o['_gvid']:o['name'] for o in layout['objects']};reverse={v:k for k,v in names.items()}
def pt(p):return [p[i]*factor+offset[i] for i in range(2)]
def add(id,kind,source,layer='TOPOLOGY',**kw):entities.append(dict(id=id,kind=kind,source=source,layer=layer,classification='secondary_transcription',**kw))
seen=set()
for node in layout['objects']:
 name=node['name'];guid=reverse[name];seen.add(guid);source=f'Saved IFC {pins[str(S/"Supply Network.ifc")]}; {guid}';layer='GAPS' if guid in bad else 'TOPOLOGY'
 for i,op in enumerate(node['_draw_']):
  if op['op'] in ['p','P']:add(f'node:{guid}:box:{i}','polyline',source,layer,points=[pt(p) for p in op['points']],closed=True)
 center=pt([float(x) for x in node['pos'].split(',')]);label=name+('!' if guid in bad else '');temp=ezdxf.new();t=temp.modelspace().add_text(label,dxfattribs={'insert':center,'height':2});box=text_box(t);insert=[center[0]-(box[0]+box[2])/2+center[0],center[1]-(box[1]+box[3])/2+center[1]];add(f'node:{guid}:label','text',source,layer,insert=insert,text=label,height=2,rotation=0)
for edge in layout['edges']:
 i=int(edge['id'][1:]);u,v,a,b=edges[i];assert byid[edge['tail']]==names[u] and byid[edge['head']]==names[v];source=f'Saved IFC directed ports {a} > {b}'
 for group in ['_draw_','_hdraw_']:
  for j,op in enumerate(edge.get(group,[])):
   if op['op'] in ['b','B']:
    points=[pt(p) for p in op['points']];assert (len(points)-1)%3==0
    for k in range(0,len(points)-1,3):
     flat=list(Bezier4P([Vec2(p) for p in points[k:k+4]]).flattening(.01))
     for n,(x,y) in enumerate(zip(flat,flat[1:])):
      if x.distance(y)>1e-8:add(f'edge:{i}:{group}:{j}:{k}:{n}','line',source,start=list(x)[:2],end=list(y)[:2])
   elif op['op'] in ['p','P']:add(f'edge:{i}:{group}:{j}','polyline',source,points=[pt(p) for p in op['points']],closed=True)
assert seen==set(names)
notes=['110 source bodies / 109 directed interfaces / 20 rigid outlet boundaries','! marks5products with11numerically unresolved fitting paths; remaining losses conditional','Topology only: line lengths are schematic; complete pressure and fan duty remain unknown']
for i,text in enumerate(notes):add(f'note-{i}','text','Source IFC and current maximum-flow pressure ledger; software review scope','NOTES',insert=[15,545-i*6],text=text,height=3,rotation=0)
spec=dict(schema='bsa.drawing-document/1',source='Actual current source IFC directed topology; no installation scale or pressure acceptance',units='mm',layers={'TOPOLOGY':dict(color=7,lineweight=18),'GAPS':dict(color=1,lineweight=50),'NOTES':dict(color=7,lineweight=18)},blocks={},entities=entities,sheet=dict(paper='A1',window=[0,0,827,574],scale=1,title='SUPPLY NETWORK SYSTEM SCHEMATIC',number='BSE3227-CS-03',reference_length=50));(B/'project/general-drawing/current-system-diagram.json').write_text(json.dumps(spec,indent=2)+'\n')
with (O/'Component Key.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['diagram_id','ifc_guid','source_name','numeric_fitting_gap','inherited_inlet_flow_m3_s'])
 for obj in objects:w.writerow([names[obj.GlobalId],obj.GlobalId,obj.Name,obj.GlobalId in bad,next(flows[p] for p in owned[obj.GlobalId] if directions[p]=='SINK')])
assert all(sha(Path(p))==h for p,h in pins.items());(O/'topology-review.json').write_text(json.dumps(dict(source_sha256={Path(p).name:h for p,h in pins.items()},graphviz_sha256=sha(dot),nodes=names,interfaces=[dict(from_guid=u,to_guid=v,source_port=a,sink_port=b) for u,v,a,b in edges],flow_ports_reconciled=len(flows),unresolved_product_guids=sorted(bad),numeric_fitting_gaps=11,layout_size_mm=[(bounds[2]-bounds[0])*factor,(bounds[3]-bounds[1])*factor],design_accepted=False),indent=2));print('110node/109edge actual topology prepared')
