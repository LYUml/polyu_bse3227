import json,math,hashlib
from decimal import Decimal as D
from pathlib import Path
import ifcopenshell
from bsa.duct_fitting_data import lookup
from bsa.duct_fitting_chain import value
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'equal-cross-compound-core-candidate';m=ifcopenshell.open(str(R/'Supply Network.ifc'));o=m.by_guid('3tK$ugPAvIAAusb9mKjQEp');local=ifcopenshell.open(str(R/'core/junction.ifc'));assert value(o.Representation.Representations[0].Items[0])==value(local.by_type('IfcDuctFitting')[0].Representation.Representations[0].Items[0]);spec=json.loads((R/'core.json').read_text());assert all(s['width_m']==1.35 and s['height_m']==.9 for s in spec['stations']);bs={b['id']:b for b in spec['branches']};assert bs['D-02']['width_m']==bs['D-05']['width_m']==.6 and all(b['height_m']==.9 for b in bs.values())
branch=dict(axes=[dict(quantity='area',values=[.3,.4,.5]),dict(quantity='flow',values=[.1,.2])],coefficients=[[1.1,1.4],[.99,1.1],[.97,1.]])
main=dict(axes=[dict(quantity='velocity',values=[.6,.8,1.])],coefficients=[.06,.02,0.])
pdf=B.parent/'project/full-network-transition-study/ashrae2021.pdf';assert hashlib.sha256(pdf.read_bytes()).hexdigest()=='746121b31696fd23cc11a39fd83d7be9ba3fec9bf0d81caa3b5e1ce6235abfbb';(R/'private-junction-source-slice.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),branch=branch,main=main,citation='2021 PHVAC9 supplement printed38/39 Fitting5-23 and47/48 Fitting5-35 diverging;actual primary diagrams reviewed'),indent=2))
def query(t,qs):
 r=lookup(t,qs);assert r['status']=='calculated';total=D(0)
 for idx in r['support_indexes']:
  term=D(str(t['coefficients'][idx[0]][idx[1]] if len(idx)==2 else t['coefficients'][idx[0]]))
  for j,a in enumerate(t['axes']):
   n=idx[j];vals=a['values'];q=qs[a['quantity']];lo=max(v for v in vals if v<=q);hi=min(v for v in vals if v>=q)
   if hi!=lo:term*= (D(str(hi))-D(str(q)))/(D(str(hi))-D(str(lo))) if vals[n]==lo else (D(str(q))-D(str(lo)))/(D(str(hi))-D(str(lo)))
  total+=term
 assert math.isclose(float(total),r['coefficient'],rel_tol=1e-12);return dict(quantities=qs,coefficient=r['coefficient'],independent_decimal_match=True)
flow=json.loads((B/'compound-source-feasibility/review.json').read_text())['cases'];records={}
for name,c in flow.items():
 q=c['external_flows_m3_s'];mid=c['after_upper_takeoff_m3_s'];qs=[('upper_branch',branch,dict(area=.5/1.35,flow=q['D-22']/q['upper'])),('upper_main',main,dict(velocity=mid/q['upper'])),('lower_main',main,dict(velocity=q['lower']/mid)),('lower_left',branch,dict(area=.6/1.35,flow=q['D-02']/mid)),('lower_right',branch,dict(area=.6/1.35,flow=q['D-05']/mid))];rows={k:query(t,p) for k,t,p in qs};records[name]=rows
report=dict(ifc_sha256=hashlib.sha256((R/'Supply Network.ifc').read_bytes()).hexdigest(),native_core_matches_checked_local_body=True,source_family_geometry=dict(constant_main_area=True,branch_height_equals_main=True,lower_opposed_branch_areas_equal=True,deflection_deg=90),cases=records,source_query_count=10,scope='Separated component correlation screening on actual constant core, not a pressure-accepted compound fitting. Only69.416mm clear between apertures;source stations and close-coupled interaction unresolved.',source_pressure_ledger_integrated=False,full_pressure_accepted=False,design_accepted=False);(R/'junction-source-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
