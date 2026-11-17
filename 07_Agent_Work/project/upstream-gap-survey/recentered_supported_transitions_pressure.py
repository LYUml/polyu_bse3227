import copy,json,math
from pathlib import Path
import numpy as np,ifcopenshell
from ifcopenshell.util import system
from bsa import source_network_analysis as engine,duct_transition_quantities as transition,duct_elbow_quantities as bend
from bsa.rectangular_tee_profiles import sections
from bsa.duct_fitting_chain import shape_hash
from bsa.duct_fitting_data import prepare,calculate
from bsa.source_pressure_ledger import calculate as ledger
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');RUN=B/'recentered-supported-transition-network';OLD=B/'recentered-transition-stage-candidates';OUT=RUN/'pressure';OUT.mkdir(exist_ok=False)
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'));prior=ifcopenshell.open(str(OLD/'Supply Network.ifc'))
oldcase=json.loads((OLD/'pressure/maximum/analysis.json').read_text());before=json.loads((OLD/'pressure/maximum/fitting-data.json').read_text());canonical={p['port_guid']:[p['width_m'],p['height_m']] for r in before['data_requests'] for p in r['available_reference_ports']}
basis=json.loads((OLD/'pressure/basis.json').read_text());changes=json.loads((RUN/'integration.json').read_text())['changes']
for r in changes:
 first=copy.deepcopy(next(t for t in basis['tables'] if t.get('transition_family')=='centred_one_plane' and t.get('transition_flow_change')=='contraction'));second=copy.deepcopy(next(t for t in basis['tables'] if t.get('transition_family')=='centred_equal_angle_pyramidal'))
 first.update(axes=[dict(quantity='inlet_to_outlet_area_ratio',values=[1.,2.]),dict(quantity='major_taper_angle_deg',values=[30.,45.,60.])],coefficients=[[0.,0.,0.],[.20,.24,.28]],citation_location='Printed19Fitting4-2 contraction1..2,30/45/60degreecolumns;tentativefootnote')
 second.update(axes=[dict(quantity='inlet_to_outlet_area_ratio',values=[1.,2.,4.]),dict(quantity='major_taper_angle_deg',values=[30.,45.,60.])],coefficients=[[0.,0.,0.],[.20,.22,.20],[.64,.88,1.1]],citation_location='Printed20Fitting4-4 contraction area1/2/4,30/45/60degreecolumns;tentativefootnote')
 basis['tables']=[t for t in basis['tables'] if t['product_guid']!=r['original_guid']]
 for table,owner,pin,pout in [(first,r['original_guid'],r['inlet_guid'],r['middleout_guid']),(second,r['second_guid'],r['middlein_guid'],r['outlet_guid'])]:
  table.update(product_guid=owner,inlet_port_guid=pin,outlet_port_guid=pout,reference_port_guid=pin);table['applicability_note']+=';Opt-in two-stage45degreeconstruction;publishedarea4row used where native ratio>2;sourcefriction andclosecouplingunverified.';basis['tables'].append(table)
 for g in [r['middlein_guid'],r['middleout_guid']]:oldcase['port_flows'][g]=copy.deepcopy(oldcase['port_flows'][r['inlet_guid']]);canonical[g]=r['intermediate_section_m']
for t in basis['tables']:
    if t['product_guid'] not in {g for r in changes for g in [r['original_guid'],r['second_guid']]}:assert shape_hash(model.by_guid(t['product_guid']))==shape_hash(prior.by_guid(t['product_guid']))
    t['geometry_sha256']=shape_hash(model.by_guid(t['product_guid']))
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

