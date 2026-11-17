from pathlib import Path
import re,json,math,hashlib
import numpy as np
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');c=B/'plenum-family-1-initialized-residence';time='0.25'
helper=(B/'check_residence_pressure_observers.py').read_text();exec(helper[helper.index('def block'):helper.index('results={}')])
m=c/'constant/polyMesh'
def body(path):
 t=path.read_text();mt=re.search(r'\n(\d+)\s*\n\(',t);assert mt;return int(mt[1]),t[mt.end():t.rfind(')')]
n,t=body(m/'points');points=np.fromstring(t.replace('(',' ').replace(')',' '),sep=' ').reshape((-1,3));assert len(points)==n
n,t=body(m/'faces');faces=re.findall(r'(\d+)\(([^()]*)\)',t);assert len(faces)==n
n,t=body(m/'owner');owner=np.fromstring(t,sep=' ',dtype=int);assert len(owner)==n
ut=(c/time/'U').read_text();um=re.search(r'internalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\((.*?)\n\)\s*;',ut,re.S);assert um and int(um[1])==142480
internalU=np.fromstring(um[2].replace('(',' ').replace(')',' '),sep=' ').reshape((-1,3))
boundary=(m/'boundary').read_text();results={}
for name in ('inlet','outlet_0','outlet_1','outlet_2','outlet_3'):
 match=re.search(r'air_'+name+r'\s*\{(.*?)\}',boundary,re.S);count=int(re.search(r'nFaces\s+(\d+)',match[1])[1]);start=int(re.search(r'startFace\s+(\d+)',match[1])[1]);vectors=[]
 for expected,indices in faces[start:start+count]:
  ids=np.fromstring(indices,sep=' ',dtype=int);assert len(ids)==int(expected);pts=points[ids];vectors.append(.5*np.cross(pts,np.roll(pts,-1,axis=0)).sum(axis=0))
 sf=np.array(vectors);areas=np.linalg.norm(sf,axis=1);normals=sf/areas[:,None];phi=patch('phi','air_'+name,count);u=patch('U','air_'+name,count);p=patch('p','air_'+name,count)*1.2;un=np.sum(u*normals,axis=1);forward=(-1 if name=='inlet' else 1);flow=np.sum(phi);area=np.sum(areas);bulk=flow/area
 txt=list((c/'postProcessing'/('pressure_'+name)).rglob('surfaceFieldValue.dat'))[0].read_text();nativearea=float(re.search(r'# Area\s*:\s*([^\s]+)',txt)[1]);assert math.isclose(area,nativearea,rel_tol=1e-10)
 reverse=phi*forward<0;reverseflow=float(np.abs(phi[reverse]).sum());forwardflow=float(np.abs(phi[~reverse]).sum());pt=p+.6*np.sum(u*u,axis=1)
 adjacent_normal=np.sum(internalU[owner[start:start+count]]*normals,axis=1);adj_reverse=adjacent_normal*forward<0
 results[name]={'adjacent_internal_reverse_face_count':int(adj_reverse.sum()),'adjacent_internal_reverse_area_fraction':float(areas[adj_reverse].sum()/area),'adjacent_internal_min_normal_velocity_m_s':float(adjacent_normal.min()),'adjacent_internal_max_normal_velocity_m_s':float(adjacent_normal.max()),'faces':count,'area_m2':float(area),'native_area_matches':True,'bulk_normal_velocity_m_s':float(bulk),'normal_velocity_min_m_s':float(un.min()),'normal_velocity_max_m_s':float(un.max()),'area_weighted_normal_velocity_CV':float(np.sqrt(np.sum(areas*(un-bulk)**2)/area)/abs(bulk)),'reverse_flow_face_count':int(reverse.sum()),'reverse_to_forward_volume_flux_ratio':reverseflow/forwardflow,'static_pressure_range_Pa':float(np.ptp(p)),'total_pressure_range_Pa':float(np.ptp(pt)),'flow_weighted_total_pressure_Pa':float(np.sum(phi*pt)/flow),'phi_vs_velocity_face_flux_max_abs_m3_s':float(np.max(np.abs(phi-np.sum(u*sf,axis=1))))}
r={'scope':'Saved0.25s imposed-port profile diagnostics; no developed-flow/domain-independence acceptance','numpy_version':np.__version__,'source_fields_sha256':{n:hashlib.sha256((c/time/n).read_bytes()).hexdigest() for n in ('U','p','phi')},'ports':results,'boundary_condition_source':'https://cpp.openfoam.org/v12/flowRateOutletVelocityFvPatchVectorField_8C_source.html','outlet_reverse_normal_velocity_clamped_by_native_BC':True,'zero_boundary_reverse_flow_does_not_prove_no_recirculation':True,'prescribed_flow_boundary_conditions':True,'actual_VAV_inlet_profile_known':False,'pressure_adopted':False};(c/'port-profile-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
