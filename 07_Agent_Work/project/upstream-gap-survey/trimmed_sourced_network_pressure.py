"""Fresh native profile and conditional pressure queries on recentered saved network."""
import copy
import json
import math
from pathlib import Path
import ifcopenshell
import numpy as np
from ifcopenshell.util import system
from bsa import source_network_analysis as engine,duct_transition_quantities as transition,duct_elbow_quantities as bend
from bsa.rectangular_tee_profiles import sections
from bsa.duct_fitting_chain import shape_hash
from bsa.duct_fitting_data import prepare,calculate
from bsa.source_pressure_ledger import calculate as ledger

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
RUN=ROOT/'runs/sourced-inlet-network';OLD=ROOT/'runs/reduced-branch-network-reviewed'
OUT=RUN/'pressure-trimmed-rectangle-reviewed';OUT.mkdir(exist_ok=False)
model=ifcopenshell.open(str(RUN/'trimmed-source.ifc'));prior=ifcopenshell.open(str(OLD/'Supply Network.ifc'))
oldcase=json.loads((OLD/'analysis.json').read_text())
before=json.loads((OLD/'one-plane-source-extension-reviewed/maximum/fitting-data.json').read_text())
canonical={p['port_guid']:[p['width_m'],p['height_m']] for x in before['data_requests'] for p in x['available_reference_ports']}
basis=json.loads((OLD/'one-plane-source-extension-reviewed/basis.json').read_text())
for t in basis['tables']:
    assert t['geometry_sha256']==shape_hash(prior.by_guid(t['product_guid']))
    t['geometry_sha256']=shape_hash(model.by_guid(t['product_guid']))
    t['applicability_note']+='; Re-evaluated against fresh recentered native geometry and source flow, not carried-over numerical acceptance.'
local=json.loads((ROOT/'runs/recentered-local-fittings/review.json').read_text())
for case in local['cases']:
    if case['node'] not in ['TAP-VAV-04','TAP-VAV-10','TAP-VAV-16']:continue
    arm=case['main_transitions'][0]['arm'];native=ifcopenshell.open(str(ROOT/'runs/recentered-local-fittings'/case['node']/arm/'transition.ifc'));obj=native.by_type('IfcDuctFitting')[0]
    assert not any(t['product_guid']==obj.GlobalId for t in basis['tables'])
    family='centred_one_plane' if case['node']=='TAP-VAV-10' else 'centred_equal_angle_pyramidal'
    t=copy.deepcopy(next(t for t in basis['tables'] if t.get('transition_family')==family))
    owned=system.get_ports(model.by_guid(obj.GlobalId));pin=next(p for p in owned if p.FlowDirection=='SINK');pout=next(p for p in owned if p.FlowDirection=='SOURCE')
    t.update(product_guid=obj.GlobalId,geometry_sha256=shape_hash(model.by_guid(obj.GlobalId)),inlet_port_guid=pin.GlobalId,outlet_port_guid=pout.GlobalId,reference_port_guid=pin.GlobalId)
    if family=='centred_one_plane':
        t['axes'][1]['values']=[15.,30.,45.];t['coefficients']=[[0.,0.,0.],[.20,.20,.24]]
        t['citation_location']+='; reviewed15degree contraction column'
    basis['tables'].append(t)
path=OUT/'basis.json';path.write_text(json.dumps(basis,indent=2));prepared,pins=prepare(path)
summary={}
for name,factor in [('maximum',1.),('minimum',.4)]:
    bindings={g:{k:r[k] for k in ['source_section','source_node','flow_m3_s','classification']} for g,r in oldcase['port_flows'].items()}
    for row in bindings.values():row['flow_m3_s']*=factor
    case=engine.calculate(model,bindings,oldcase['air']);case.update(air=oldcase['air'],original_requirement_ids=oldcase['original_requirement_ids'])
    for obj in model.by_type('IfcDistributionElement'):
        ports=system.get_ports(obj);dims={}
        if obj.is_a('IfcDuctSegment'):
            p=obj.Representation.Representations[0].Items[0].SweptArea
            dims={port.GlobalId:[p.XDim-2*p.WallThickness,p.YDim-2*p.WallThickness] for port in ports}
        elif obj.PredefinedType=='JUNCTION' and obj.Name=='RECTANGULAR-TEE':dims=sections(obj)
        elif obj.PredefinedType in ['TRANSITION','BEND']:
            pin=next(p for p in ports if p.FlowDirection=='SINK');pout=next(p for p in ports if p.FlowDirection=='SOURCE')
            if obj.PredefinedType=='TRANSITION':geo=transition.calculate(obj,pin.Name,pout.Name);key='transition_geometry'
            else:geo=bend.calculate(obj,pin.Name,pout.Name,bindings[pin.GlobalId]['flow_m3_s'],case['air']);key='elbow_geometry'
            next(x for x in case['products'] if x['guid']==obj.GlobalId)[key]=geo
            dims={pin.GlobalId:geo['inlet_section_m'],pout.GlobalId:geo['outlet_section_m'] if 'outlet_section_m' in geo else geo['inlet_section_m']}
        else:
            assert shape_hash(obj)==shape_hash(prior.by_guid(obj.GlobalId))
            dims={p.GlobalId:canonical[p.GlobalId] for p in ports}
        for guid,(w,h) in dims.items():
            row=case['port_flows'][guid];assert np.allclose([w,h],[row['width_m'],row['height_m']],atol=1e-8,rtol=0)
            v=row['flow_m3_s']/(w*h);row.update(width_m=w,height_m=h,actual_velocity_m_s=v,actual_velocity_pressure_Pa=case['air']['density_kg_m3']*v*v/2)
    result=calculate(model,case,prepared);result['original_requirement_ids']=case['original_requirement_ids'];pressure=ledger(case,result)
    folder=OUT/name;folder.mkdir()
    for filename,data in [('analysis.json',case),('fitting-data.json',result),('pressure-ledger.json',pressure)]:
        (folder/filename).write_text(json.dumps(data,indent=2))
    summary[name]=dict(conditional_values=result['calculated_table_paths'],numerical_gaps=pressure['numerically_unresolved_fitting_path_count'],fitting_paths=result['unique_fitting_paths'],outlets=20,inlet_flow_m3_s=case['boundary_inlet_flow_m3_s'])
(OUT/'review.json').write_text(json.dumps(dict(cases=summary,network_integrated=True,full_pressure_verified=False,design_accepted=False),indent=2))
print(json.dumps(summary,indent=2))
