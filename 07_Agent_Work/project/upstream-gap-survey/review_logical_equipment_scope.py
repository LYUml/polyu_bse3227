import json,hashlib,copy
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.geom
from ifcopenshell.util import placement
from bsa.duct_fitting_chain import value
from bsa.source_pressure_ledger import calculate
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'logical-equipment-network';oldp=B/'three-dimensional-outlet-candidate/Shared Supply and Outlet Connections.ifc';newp=R/'Supply Air Logical Network.ifc';old=ifcopenshell.open(str(oldp));m=ifcopenshell.open(str(newp));integration=json.loads((R/'integration.json').read_text());settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);ids={r[k] for r in integration['records'] for k in ['vav_guid','plenum_guid']}
for obj in m.by_type('IfcElement'):
 prev=old.by_guid(obj.GlobalId);assert value(obj.Representation)==value(prev.Representation) and np.array_equal(placement.get_local_placement(obj.ObjectPlacement),placement.get_local_placement(prev.ObjectPlacement))
for g in ids:
 shapes=[ifcopenshell.geom.create_shape(settings,f.by_guid(g)) for f in [old,m]];assert np.array_equal(shapes[0].geometry.verts,shapes[1].geometry.verts) and np.array_equal(shapes[0].geometry.faces,shapes[1].geometry.faces)
(R/'geometry-handoff.json').write_text(json.dumps(dict(source_ifc_sha256=hashlib.sha256(oldp.read_bytes()).hexdigest(),ifc_sha256=hashlib.sha256(newp.read_bytes()).hexdigest(),all664native_geometry_definitions_and_world_placements_unchanged=True,native_reclassified_equipment_meshes_checked=40,physical_scope_GUIDs_preserved=604,previous_collision_scope_preserved=True,previous_collision_check='Three_Dimensional_Outlet_Check.json explicit shared-geometry chain',new120connections_are_logical_only=True,physical_cap_verification=False,design_accepted=False),indent=2));print('40reclassified nativeequipment meshesmatch;all664geometry definitions/placementsunchanged',flush=True)
O=R/'pressure-classified';O.mkdir(exist_ok=False);report=json.loads((R/'pressure-reviewed/review.json').read_text());classcounts={}
for c in ['maximum','minimum']:
 folder=O/c;folder.mkdir();case=json.loads((R/'pressure-reviewed'/c/'analysis.json').read_text());data=json.loads((R/'pressure-reviewed'/c/'fitting-data.json').read_text());counts={}
 for request in data['data_requests']:
  if request['recorded_table_result'] is not None:continue
  obj=m.by_guid(request['product_guid'])
  if obj.is_a('IfcAirTerminalBox'):kind='VAV_device';evidence=['Selected LMHS configuration and sourced total-pressure loss or explicitly defined static/reference stations','Selected liner/control/discharge configuration and minimum operating pressure feasibility','Collar/slip-drive insertion and joint sealing;publishedminimumstatic is not automatically whole device loss']
  elif obj.PredefinedType=='BEND':kind='outlet_bend';evidence=['Applicable selected-material correlation at actual native minor/90degree angle andR/D1.5','Reference velocity and local-versus-wall-friction convention','Adjacent-fitting interaction and installed product correspondence;diameter/angle are already read from native geometry']
  elif obj.Name.endswith('-J-PLENUM'):kind='J_plenum_path';evidence=['Selected Jattenuator1-to4 unequal-flow pressure performance with source-defined stations','Actual liner/baffles/net collar bores and flow split applicability','Do not substitute outside dimensions or an isolated generic tee coefficient']
  else:kind='compound_main_path';evidence=request['required_evidence']
  request.update(required_evidence=evidence,engineering_gap_class=kind);counts[kind]=counts.get(kind,0)+1
 assert counts==dict(compound_main_path=4,outlet_bend=160,VAV_device=20,J_plenum_path=80) or counts==dict(outlet_bend=160,compound_main_path=4,VAV_device=20,J_plenum_path=80);data['source_analysis']=str(folder);ledger=calculate(case,data);assert ledger['numerically_unresolved_fitting_path_count']==264 and len(ledger['outlet_paths'])==80
 for name,obj in [('analysis.json',case),('fitting-data.json',data),('pressure-ledger.json',ledger)]:(folder/name).write_text(json.dumps(obj,indent=2))
 classcounts[c]=counts
report['gap_classes']=classcounts;report['physical_airway_continuity_verified']=False;(O/'review.json').write_text(json.dumps(report,indent=2));print(classcounts)
