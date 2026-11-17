import copy,json,math
from pathlib import Path
import numpy as np,ifcopenshell
from ifcopenshell.util import system
from bsa import source_network_analysis as engine,duct_transition_quantities as transition,duct_elbow_quantities as bend
from bsa.rectangular_tee_profiles import sections
from bsa.rectangular_cross_profiles import sections as cross_sections
from bsa.duct_fitting_chain import shape_hash
from bsa.duct_fitting_data import prepare,calculate
from bsa.source_pressure_ledger import calculate as ledger
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');RUN=B/'recentered-constant-height-network';OLD=B/'recentered-supported-transition-network';OUT=RUN/'pressure';OUT.mkdir(exist_ok=False)
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'));prior=ifcopenshell.open(str(OLD/'Supply Network.ifc'))
oldcase=json.loads((OLD/'pressure/maximum/analysis.json').read_text());before=json.loads((OLD/'pressure/maximum/fitting-data.json').read_text());canonical={p['port_guid']:[p['width_m'],p['height_m']] for r in before['data_requests'] for p in r['available_reference_ports']}
basis=json.loads((OLD/'pressure/basis.json').read_text());changes=json.loads((RUN/'integration.json').read_text())['cases']
for r in changes:
 template=copy.deepcopy(next(t for t in basis['tables'] if t.get('transition_family')=='centred_one_plane' and t.get('transition_flow_change')=='contraction'))
 template.update(product_guid=r['transition_guid'],inlet_port_guid=r['transition_inlet_guid'],outlet_port_guid=r['transition_outlet_guid'],reference_port_guid=r['transition_inlet_guid'],citation_location='Printed19,Fitting4-2 contraction area1..2;unambiguous15/45 and matching repeated30columns;tentativecontractionfootnote',applicability_note='Centred one-plane height contraction after constant-height tee;short-body interaction and whole friction/product applicability unverified.',axes=[dict(quantity='inlet_to_outlet_area_ratio',values=[1.,2.]),dict(quantity='major_taper_angle_deg',values=[15.,30.,45.])],coefficients=[[0.,0.,0.],[.20,.20,.24]])
 basis['tables']=[t for t in basis['tables'] if t['product_guid']!=r['tee_guid']];basis['tables'].append(template)
 for guid in [r['transition_inlet_guid'],r['transition_outlet_guid']]:oldcase['port_flows'][guid]=copy.deepcopy(oldcase['port_flows'][r['branch_port_guid']])
 obj=model.by_guid(r['tee_guid']);sizes=sections(obj);owned=system.get_ports(obj);common=next(p for p in owned if p.FlowDirection=='SINK');assert common.Name!='branch'
 for out in owned:
  if out.FlowDirection!='SOURCE':continue
  table=copy.deepcopy(template);table.pop('transition_flow_change',None);table.pop('transition_family',None);branch=out.Name=='branch'
  table.update(product_guid=obj.GlobalId,inlet_port_guid=common.GlobalId,outlet_port_guid=out.GlobalId,reference_port_guid=common.GlobalId,citation_location='Printed38main/39theta90branch,Fitting5-23 constant-height tee',applicability_note='Literal native tee Hb=Hc and unchanged main area;branch Ab/Ac=Wb/Wc exactly under verified height equality,so width ratio is the algebraically cancelled source area parameter. No boundary snapping/clamping. Common inlet reference;products/bodyfriction/interaction unverified.',axes=[dict(quantity='outlet_to_inlet_width_ratio',values=[.5,.6,.7,.8]),dict(quantity='outlet_to_inlet_flow_ratio',values=[.3,.4,.5,.6])] if branch else [dict(quantity='outlet_to_inlet_velocity_ratio',values=[.1,.2,.3,.4,.5,.6,.8,1.])],coefficients=[[1.1,1.2,1.4,1.5],[1.,1.1,1.1,1.2],[.95,.98,1.,1.1],[.92,.93,.94,.95]] if branch else [.32,.26,.20,.14,.10,.06,.02,0.],conditions=[dict(quantity='deflection_deg',minimum=90. if branch else 0.,maximum=90. if branch else 0.),dict(quantity='outlet_to_inlet_height_ratio',minimum=1.,maximum=1.)])
  basis['tables'].append(table)
for t in basis['tables']:
    if t['product_guid'] not in {g for r in changes for g in [r['tee_guid'],r['transition_guid']]}:assert shape_hash(model.by_guid(t['product_guid']))==shape_hash(prior.by_guid(t['product_guid']))
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
        elif obj.Name=='RECTANGULAR-CROSS':dims=cross_sections(obj)
        elif obj.Name=='RECTANGULAR-BULLHEAD-TEE':dims=sections(obj,bullhead_area_sum=True)
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

