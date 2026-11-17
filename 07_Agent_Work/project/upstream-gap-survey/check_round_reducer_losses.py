import json,math,hashlib
from pathlib import Path
from decimal import Decimal as D
import ifcopenshell
from bsa.round_reducer_quantities import calculate
from bsa.duct_fitting_data import lookup
import bsa.round_reducer_quantities as reader
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');P=B/'j-outlet-reducer-candidate-verified';O=B/'round-reducer-loss-review';O.mkdir(exist_ok=False)
m=ifcopenshell.open(str(P/'Candidate Round Reducers.ifc'));reducers=json.loads((P/'review.json').read_text());routes=json.loads((B/'j-outlet-8in-routed-plan-labelled/review.json').read_text());bind={r['outlet']:r for r in routes['routes']}
# Private4-1 slice: visual source19/table first ratio1/2rows,10/15/20degreecolumns.
table=dict(axes=[dict(quantity='inlet_to_outlet_area_ratio',values=[1.,2.]),dict(quantity='included_angle_deg',values=[10.,15.,20.])],coefficients=[[0.,0.,0.],[.20,.20,.20]])
records=[]
for r in reducers['records']:
 obj=m.by_guid(r['product_guid']);branch=bind[r['plenum_outlet_id']]
 for condition in ['maximum','minimum']:
  q=branch['pressure'][condition]['flow_m3_s'];geo=calculate(obj,q,1.2);result=lookup(table,geo);assert result['status']=='calculated'
  independent=(D(str(geo['inlet_to_outlet_area_ratio']))-D(1))*D('.20');assert abs(result['coefficient']-float(independent))<1e-14
  vp=geo['inlet_velocity_pressure_Pa'];records.append(dict(vav=r['vav'],terminal=branch['terminal'],product_guid=obj.GlobalId,condition=condition,flow_m3_s=q,native_quantities=geo,coefficient=result['coefficient'],conditional_reducer_loss_Pa=result['coefficient']*vp,total_pressure_Pa=None))
assert len(records)==160
proof=dict(ifc_sha256=hashlib.sha256((P/'Candidate Round Reducers.ifc').read_bytes()).hexdigest(),native_reader_sha256=hashlib.sha256(Path(reader.__file__).read_bytes()).hexdigest(),source_document_sha256=hashlib.sha256((B.parent/'project/full-network-transition-study/ashrae2021.pdf').read_bytes()).hexdigest(),source_url='https://xp20.ashrae.org/SupplementalFiles/PHVAC9/Fitting_Loss_Coefficients.pdf',source_locator='2021 Online Supplemental Material Accompanying Principles of HVAC,9th Edition;printed19,Fitting4-1 round transition,contraction Ao/A1>1;Idelchik et al1986 Diagrams5-2/5-22',source_slice_visually_reviewed=True,query_count=160,independent_Decimal_coefficients_match=True,source_reference='Large inlet Ao/Vo,not small outlet',coefficient_range=[min(r['coefficient'] for r in records),max(r['coefficient'] for r in records)],maximum_flow_loss_range_Pa=[min(r['conditional_reducer_loss_Pa'] for r in records if r['condition']=='maximum'),max(r['conditional_reducer_loss_Pa'] for r in records if r['condition']=='maximum')],records=records,physical_applicability_verified=False,full_pressure_verified=False,design_accepted=False)
(O/'review.json').write_text(json.dumps(proof,indent=2));(O/'private-source-slice.json').write_text(json.dumps(table,indent=2));print(json.dumps({k:v for k,v in proof.items() if k!='records'}))
