from pathlib import Path
import json,csv,hashlib
import ifcopenshell,ifcopenshell.util.system as S,ezdxf
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');B=P/'07_Agent_Work/runs';W=B/'current-source-system-diagrams';D=P/'03_Design_Drawings/Connection_Layout/Current Open Plenum Study/System Diagrams'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
m=ifcopenshell.open(B/'recentered-open-plenum-network/Supply Air Open Plenum Reviewed.ifc')
native=set()
for r in m.by_type('IfcRelConnectsPorts'):
 a,b=r.RelatingPort,r.RelatedPort
 if a.FlowDirection=='SINK':a,b=b,a
 assert a.FlowDirection=='SOURCE' and b.FlowDirection=='SINK'
 native.add((a.GlobalId,b.GlobalId))
main=load(W/'main-topology-review.json');seen={(e['source_port'],e['sink_port']) for e in main['interfaces']}
cases=[load(B/f'recentered-logical-supply-network/vav-candidate-station-pressure/{c}/analysis.json') for c in ['maximum','minimum']]
text={}
for tag in ['01-10','11-20']:
 f=ezdxf.readfile(B/f'current-source-terminal-systems-{tag}-native/drawing/reopened/source-export.dxf')
 for e in f.modelspace().query('TEXT'):
  if e.has_xdata('BSA_DRAWING'):text[e.get_xdata('BSA_DRAWING')[0].value]=e.dxf.text
rows=[]
for i,g in enumerate(load(W/'partition-review.json')['groups'],1):
 t=load(W/f"graph-cache-spaced/{g['id']}/source-topology.json")
 for e in t['interfaces']:
  pair=(e['source_port'],e['sink_port']);assert pair not in seen;seen.add(pair)
 assert len(t['external_selected_connections'])==1
 x=t['external_selected_connections'][0];pair=(x['peer_port'],x['selected_port'])
 assert pair not in seen;seen.add(pair)
 assert S.get_port_element(m.by_guid(pair[0])).GlobalId==g['upstream_main_product_guid']
 assert S.get_port_element(m.by_guid(pair[1])).GlobalId==g['entry_product_guid']
 inv=[a for a in main['external_selected_connections'] if a['selected_port']==pair[0] and a['peer_port']==pair[1]]
 assert len(inv)==1
 flows=[c['port_flows'][pair[1]]['flow_m3_s']*1000 for c in cases]
 assert text[g['id']+':heading']==g['id']+'    '+('/'.join(str(round(q)) for q in flows))+' L/s'
 rows.append(dict(main_label=f'OUT{i:02}',terminal_group=g['id'],terminal_sheet='BSE3227-S-02' if i<=10 else 'BSE3227-S-03',source_product_guid=g['upstream_main_product_guid'],source_port_guid=pair[0],sink_product_guid=g['entry_product_guid'],sink_port_guid=pair[1],maximum_flow_L_s=flows[0],minimum_flow_L_s=flows[1]))
assert len(native)==597 and seen==native
with (D/'System Connections.csv').open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
check=load(D/'System Drawing Check.json')
check['connection_review']={'all597_directed_source_interfaces_partitioned_exactly_once':True,'main_internal_interfaces':117,'terminal_internal_interfaces':460,'cross_sheet_connections':20,'all20_cross_sheet_port_owners_directions_and_inverse_records_match':True,'all20_native_group_flow_headings_match_source_cases':True,'connection_csv_sha256':hashlib.sha256((D/'System Connections.csv').read_bytes()).hexdigest(),'scope':'Native IFC topology and saved drawing group flow text; not pressure or physical port acceptance'}
(D/'System Drawing Check.json').write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')
Path('docs/evidence/current-system-drawings.json').write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')
print(check['connection_review'])
