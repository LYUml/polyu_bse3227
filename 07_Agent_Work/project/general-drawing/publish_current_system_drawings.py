from pathlib import Path
import json,csv,hashlib,shutil
import ifcopenshell,ezdxf
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';W=B/'current-source-system-diagrams'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
part=load(W/'partition-review.json');source=B/'recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc'
assert sha(source)==part['source_ifc_sha256']
m=ifcopenshell.open(source);products={x.GlobalId for x in m.by_type('IfcDistributionElement')}
rows=[]
for f in ['Main System Component Index Reviewed.csv','Terminal System Component Index.csv']:
 with (W/f).open(encoding='utf-8-sig') as h:rows+=list(csv.DictReader(h))
assert len(rows)==598 and {r['product_guid'] for r in rows}==products
assert len({r['component_reference'] for r in rows})==598
specs=[('current-source-main-system-readable-native','Supply Air Main System','MAIN'),('current-source-terminal-systems-01-10-native','Terminal Systems - VAV 01 to 10','01-10'),('current-source-terminal-systems-11-20-native','Terminal Systems - VAV 11 to 20','11-20')]
texts={};artifacts=[]
for folder,title,tag in specs:
 out=B/folder;result=load(out/'drawing/drawing-result.json')
 assert result['native_reopen_pass'] and result['native_audit']['editable_entity_correspondence']
 d=ezdxf.readfile(out/'drawing/reopened/source-export.dxf')
 for e in d.modelspace().query('TEXT'):
  if e.has_xdata('BSA_DRAWING'):
   key=e.get_xdata('BSA_DRAWING')[0].value
   if ':node:' in key or key.startswith('node:') or key.endswith(':heading'):
    assert key not in texts,key
    texts[key]=e.dxf.text
 artifacts.append({'title':title,'run':folder,'native_entities':result['native_audit']['model_entities'],'native_reopen_pass':True,'editable_entity_correspondence':True,'dwg_sha256':sha(out/'drawing/Drawing.dwg'),'pdf_sha256':sha(out/'drawing/Drawing.pdf')})
for r in rows:
 key=('' if r['group']=='MAIN' else r['group']+':')+'node:'+r['product_guid']+':label'
 assert texts[key]==r['diagram_label'],(key,texts[key],r)
cases=[load(B/f'recentered-logical-supply-network/vav-candidate-station-pressure/{c}/analysis.json') for c in ['maximum','minimum']]
for g in part['groups']:
 for leaf in g['terminal_leaves']:
  flows=[c['port_flows'][leaf['port_guid']] for c in cases]
  assert all(f['owner_guid']==leaf['product_guid'] for f in flows)
  expected='/'.join(str(round(f['flow_m3_s']*1000)) for f in flows)
  assert texts[g['id']+':node:'+leaf['product_guid']+':flow']==expected
assert len(m.by_type('IfcRelConnectsPorts'))==597 and len(m.by_type('IfcDistributionPort'))==1275
dest=P/'03_Design_Drawings/Connection_Layout/Current Open Plenum Study/System Diagrams';dest.mkdir(exist_ok=True)
for folder,title,tag in specs:
 for ext in ['dwg','pdf']:shutil.copy2(B/folder/f'drawing/Drawing.{ext}',dest/f'{title}.{ext}')
with (dest/'System Component Index.csv').open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
receipt={'scope':'Same-source editable system topology drawings; separate open-plenum study, not replacement of course baseline','source_ifc_sha256':sha(source),'source_products':598,'source_ports':1275,'source_interfaces':597,'all598_native_visible_labels_match_source_index':True,'all80_native_terminal_maximum_minimum_flow_labels_match_source_cases':True,'flow_basis':'Prescribed preliminary design demand, rounded to nearest L/s on drawings; not measured','artifacts':artifacts,'visual_review':{'reviewer':'Codex host AI','main':'Actual final PDF whole page inspected; no observed clipping or text overlap','terminal':'Final whole pages and representative VAV-01/VAV-11 crops inspected; no observed clipping or text overlap'},'limits':['Schematic links do not prove installed lengths or physical clearance','SD labels identify terminal connection planes, not modeled diffuser bodies','Full pressure, controlled VAV losses, installation and ADPI applicability remain unaccepted'],'design_accepted':False}
(dest/'System Drawing Check.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
(W/'published-system-drawing-review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
