"""Explicit 1.25-width inlet elbow candidate; original interfaces preserved."""
import json,hashlib,math
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api
from ifcopenshell.util import placement,system,element
from bsa.rectangular_tee_transitions import relative_placement
from bsa.duct_elbow_quantities import calculate
from bsa.duct_fitting_chain import shape_hash
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');S=B/'recentered-cross-network';O=B/'recentered-inlet-radius-network';O.mkdir(exist_ok=False)
m=ifcopenshell.open(str(S/'Supply Network.ifc'));old=ifcopenshell.open(str(S/'Supply Network.ifc'));g='1GS8rKBADM7RZvHhbL6Ep3';obj=m.by_guid(g);ps=system.get_ports(obj);frames={p.GlobalId:placement.get_local_placement(p.ObjectPlacement) for p in ps};world=placement.get_local_placement(obj.ObjectPlacement);delta=.3375
shift=sum((f[:3,2] for f in frames.values()),np.zeros(3))*delta;world[:3,3]+=shift
bodyrep=next(r for r in obj.Representation.Representations if r.RepresentationIdentifier=='Body');body=element.copy_deep(m,bodyrep.Items[0]);bodyrep.Items=[body];body.SweptArea.Position.Location.Coordinates=(1.6875,0.)
axisrep=next(r for r in obj.Representation.Representations if r.RepresentationIdentifier=='Axis');axis=element.copy_deep(m,axisrep.Items[0]);axisrep.Items=[axis];axis.Points.CoordList=[tuple(float(x*1.25) for x in row) for row in axis.Points.CoordList]
obj.ObjectPlacement=relative_placement(m,world,None);changes=[]
for p in ps:
 f=frames[p.GlobalId].copy();f[:3,3]+=f[:3,2]*delta;p.ObjectPlacement=relative_placement(m,np.linalg.inv(world)@f,obj.ObjectPlacement)
 rel=(*p.ConnectedTo,*p.ConnectedFrom)[0];peer=rel.RelatedPort if rel.RelatingPort==p else rel.RelatingPort;straight=system.get_port_element(peer);assert straight.is_a('IfcDuctSegment');sf=placement.get_local_placement(straight.ObjectPlacement);ends={q.GlobalId:placement.get_local_placement(q.ObjectPlacement) for q in system.get_ports(straight)};ends[peer.GlobalId][:3,3]=f[:3,3];coords=[float((v[:3,3]-sf[:3,3])@sf[:3,2]) for v in ends.values()];depth=max(coords)-min(coords);assert depth>.08;rep=straight.Representation.Representations[0];solid=element.copy_deep(m,rep.Items[0]);rep.Items=[solid];before=solid.Depth;solid.Depth=depth;sf[:3,3]+=sf[:3,2]*min(coords);straight.ObjectPlacement=relative_placement(m,sf,None)
 for q in system.get_ports(straight):q.ObjectPlacement=relative_placement(m,np.linalg.inv(sf)@ends[q.GlobalId],straight.ObjectPlacement)
 changes.append(dict(guid=straight.GlobalId,old_length_m=before,new_length_m=depth))
pset=element.get_psets(obj).get('BSA_DesignInputs',{});api.run('pset.edit_pset',m,pset=m.by_id(pset['id']),properties=dict(CenterlineRadius_m=1.6875,RadiusBasis='Host design target 1.25 clear radial width; candidate only'))
path=O/'Supply Network.ifc';m.write(str(path));m=ifcopenshell.open(str(path));a=json.loads((S/'pressure/maximum/analysis.json').read_text());geo=calculate(m.by_guid(g),'in','out',12.000372763419484,a['air']);assert math.isclose(geo['quantities']['bend_centerline_radius_m'],1.6875)
changed={g,*[r['guid'] for r in changes]};unchanged=[o for o in m.by_type('IfcDistributionElement') if o.GlobalId not in changed];assert len(unchanged)==115 and all(shape_hash(o)==shape_hash(old.by_guid(o.GlobalId)) for o in unchanged)
openports=[p for p in m.by_type('IfcDistributionPort') if not p.ConnectedTo and not p.ConnectedFrom];assert len(openports)==21 and all(np.allclose(placement.get_local_placement(p.ObjectPlacement),placement.get_local_placement(old.by_guid(p.GlobalId).ObjectPlacement),atol=1e-9,rtol=0) for p in openports)
record=dict(source_ifc_sha256=hashlib.sha256((S/'Supply Network.ifc').read_bytes()).hexdigest(),ifc_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),radius_before_m=1.35,radius_after_m=1.6875,classification='design_target',basis='Explicit finite radius choice within source table; no manufacturer/installation acceptance',changed_straights=changes,unchanged_product_shapes=115,external_frames_unchanged=21,native_bend_quantities=geo,design_accepted=False)
(O/'integration.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
