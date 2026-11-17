import copy,json,math,runpy
from pathlib import Path
import ifcopenshell
from ifcopenshell.util import system
from bsa.duct_transition_quantities import calculate,family_check
from bsa.duct_fitting_data import lookup
G=runpy.run_path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/project/upstream-gap-survey/check_equal_cross_compound_source.py');B=G['B'];R=G['R'];query=G['query'];m=G['m'];basis=json.loads((B/'supported-transition-stages/rectangular-pressure/basis.json').read_text());review=json.loads((R/'review.json').read_text());flows=json.loads((R/'flow-review.json').read_text())['cases'];air=json.loads((B/'supported-transition-stages/rectangular-pressure/maximum/analysis.json').read_text())['air'];rows=[]
for row in review['cases']:
 for folder in row['stage_folders']:
  local=ifcopenshell.open(str(Path(folder)/'transition.ifc'));localfit=local.by_type('IfcDuctFitting')[0];obj=m.by_guid(localfit.GlobalId);ports={p.Name:p for p in system.get_ports(obj)};geo=calculate(obj,'start','end');family='centred_one_plane' if min(geo['quantities']['taper_width_angle_deg'],geo['quantities']['taper_height_angle_deg'])==0 else 'centred_equal_angle_pyramidal';guard=family_check(family,geo);assert guard['pass_check'];t=next(t for t in basis['tables'] if t.get('transition_family')==family and t.get('transition_flow_change')=='contraction');t=copy.deepcopy(t);t['axes']=[dict(quantity='inlet_to_outlet_area_ratio',values=[1.,2.,4.]),dict(quantity='major_taper_angle_deg',values=[30.,45.,60.])];t['coefficients']=[[0.,0.,0.],[.20,.24,.28],[.64,.88,1.1]] if family=='centred_one_plane' else [[0.,0.,0.],[.20,.22,.20],[.64,.88,1.1]];a=geo['inlet_section_m'];b=geo['outlet_section_m'];qs=dict(geo['quantities'],inlet_to_outlet_area_ratio=(a[0]*a[1])/(b[0]*b[1]));checks={}
  for name,case in flows.items():
   r=query(t,qs);q=case['port_flows'][ports['start'].GlobalId]['flow_m3_s'];r.update(local_dynamic_loss_Pa=r['coefficient']*air['density_kg_m3']*(q/(a[0]*a[1]))**2/2,inlet_reference=True);checks[name]=r
  rows.append(dict(product_guid=obj.GlobalId,family=family,family_check=guard,cases=checks))
assert len(rows)==6;(R/'transition-source-review.json').write_text(json.dumps(dict(ifc_sha256=G['report']['ifc_sha256'],native_transition_count=6,source_query_count=12,records=rows,whole_network_pressure_verified=False,design_accepted=False),indent=2));print('12 native transition source queries independently checked')


