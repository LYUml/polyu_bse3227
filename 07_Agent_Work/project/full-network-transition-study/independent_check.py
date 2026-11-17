import bisect, hashlib, json, math
from pathlib import Path
from pypdf import PdfReader
root=Path(__file__).resolve().parents[2]
basis=Path(__file__).with_name('basis.json')
record=root/'runs/full-network-transition-fitting-data/fitting-data.json'
d=json.loads(record.read_text()); tables=json.loads(basis.read_text())['tables']
text=PdfReader(basis.with_name('ashrae2021.pdf')).pages[19].extract_text(extraction_mode='layout').split('4-4',1)[1]
line=next(line for line in text.splitlines() if line.split() and line.split()[0]=='2')
values=[float(v) for v in line.split()[1:]]
assert len(values)==10
# Independently extracted row2; row1 zeros visually checked on saved source page.
angles=[20.,30.,45.]; row=[values[i] for i in (2,3,4)]
checked=[]
for t in tables:
 if t.get('transition_family')!='centred_equal_angle_pyramidal':continue
 result=next(v for v in d['table_results'] if (v['product_guid'],v['inlet_port_guid'],v['outlet_port_guid'])==(t['product_guid'],t['inlet_port_guid'],t['outlet_port_guid']))
 req=next(v for v in d['data_requests'] if (v['product_guid'],v['inlet_port_guid'],v['outlet_port_guid'])==(t['product_guid'],t['inlet_port_guid'],t['outlet_port_guid']))
 g=req['transition_geometry']; wi,hi=g['inlet_section_m'];wo,ho=g['outlet_section_m'];length=g['quantities']['taper_length_m']
 walls=[math.degrees(2*math.atan(abs(b-a)/(2*length))) for a,b in ((wi,wo),(hi,ho))]
 assert abs(walls[0]-walls[1])<=1e-6
 rho=json.loads((Path(d['source_analysis'])/'analysis.json').read_text())['air']['density_kg_m3']; vp=rho*(req['inlet']['flow_m3_s']/(wi*hi))**2/2
 assert math.isclose(vp,req['inlet']['actual_velocity_pressure_Pa'],rel_tol=1e-12,abs_tol=1e-12)
 angle=max(walls); ratio=wi*hi/(wo*ho); j=min(1,max(0,bisect.bisect_right(angles,angle)-1)); fraction=(angle-angles[j])/(angles[j+1]-angles[j]); expected=(row[j]+fraction*(row[j+1]-row[j]))*(ratio-1.)
 assert math.isclose(expected,result['coefficient'],rel_tol=1e-12,abs_tol=1e-12)
 assert t['reference_port_guid']==t['inlet_port_guid']==result['reference_port_guid']
 assert math.isclose(result['signed_tabulated_contribution_Pa'],expected*vp,rel_tol=1e-12,abs_tol=1e-12)
 assert not result['physical_applicability_verified']
 checked.append(dict(product_guid=t['product_guid'],coefficient_agreement=True,reference_inlet_verified=True,independent_wall_angle_area_query=True))
assert len(checked)==8 and d['calculated_table_paths']==31 and not d['pressure_budget_complete'] and d['critical_path'] is None
out=dict(checked=checked,all_agree=True,source_record_sha256=hashlib.sha256(record.read_bytes()).hexdigest(),basis_sha256=hashlib.sha256(basis.read_bytes()).hexdigest(),source_pdf_sha256=hashlib.sha256(basis.with_name('ashrae2021.pdf').read_bytes()).hexdigest(),design_accepted=False)
Path(__file__).with_name('independent-check.json').write_text(json.dumps(out,indent=2));print('8 independent native angle/area/inlet-reference controls agree; complete pressure remains pending')
