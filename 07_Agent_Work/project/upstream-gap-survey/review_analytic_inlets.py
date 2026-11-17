"""Independent saved IFC wall, port, cap area/radius and source-frame review."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom as geom
from ifcopenshell.util import placement,system
from bsa.solid_clash import from_mesh

RUN=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/rect-round-cadquery/analytic-inlet-assemblies')
report=json.loads((RUN/'author-review.json').read_text());path=RUN/'VAV Inlet Assemblies.ifc'
assert hashlib.sha256(path.read_bytes()).hexdigest()==report['ifc_sha256']
model=ifcopenshell.open(str(path));settings=geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
from bsa.circular_geometry import configure
configure(settings)
checks=[]
for row in report['cases']:
    obj=model.by_guid(row['guid']);frame=placement.get_local_placement(obj.ObjectPlacement)
    assert np.allclose(frame,row['frame'],rtol=0,atol=1e-9)
    ports={p.Name:p for p in system.get_ports(obj)};assert set(ports)=={'rectangle','circle'}
    for name,p in ports.items():
        assert p.GlobalId==row['ports'][name]['guid']
        assert np.allclose(placement.get_local_placement(p.ObjectPlacement),row['ports'][name]['frame'],rtol=0,atol=1e-9)
    shape=geom.create_shape(settings,obj)
    vertices=np.array(shape.geometry.verts).reshape(-1,3);faces=np.array(shape.geometry.faces).reshape(-1,3)
    solid=from_mesh((vertices,faces));volume=solid.volume()
    expected=next(r['volume_m3'] for r in report['profiles'] if r['profile']==row['profile'])
    assert math.isclose(volume,expected,rel_tol=.002,abs_tol=1e-12)
    local=(vertices-frame[:3,3])@frame[:3,:3]
    z0=-row['start_length_m'];z1=row['taper_length_m']+row['end_length_m'];t=row['section_offset_m']
    ring0=local[abs(local[:,2]-z0)<1e-8];ring1=local[abs(local[:,2]-z1)<1e-8]
    assert len(ring0)>=8 and len(ring1)>32
    w,h,r=row['width_m'],row['height_m'],row['diameter_m']/2
    for half in [(w/2+t,h/2+t),(w/2,h/2)]:
        for sx in [-1,1]:
            for sy in [-1,1]:assert np.min(np.linalg.norm(ring0[:,:2]-[sx*half[0],sy*half[1]],axis=1))<1e-8
    radius=np.linalg.norm(ring1[:,:2],axis=1)
    assert np.all(np.minimum(abs(radius-r),abs(radius-r-t))<1e-8)
    inner=ring1[abs(radius-r)<1e-8];angles=np.sort(np.unique(np.arctan2(inner[:,1],inner[:,0])))
    gap=np.diff(np.r_[angles,angles[0]+2*math.pi]);sag=r*(1-math.cos(max(gap)/2));assert sag<=.00002
    areas=[]
    for z,expected_area in [(z0,(w+2*t)*(h+2*t)-w*h),(z1,math.pi*((r+t)**2-r**2))]:
        cap=local[faces[np.all(abs(local[faces][:,:,2]-z)<1e-8,axis=1)]]
        area=float(np.linalg.norm(np.cross(cap[:,1]-cap[:,0],cap[:,2]-cap[:,0]),axis=1).sum()/2)
        assert math.isclose(area,expected_area,rel_tol=.002,abs_tol=1e-10),(row['id'],area,expected_area)
        areas.append(area)
    checks.append(dict(id=row['id'],native_closed_positive_wall=True,
        native_volume_m3=volume,rectangle_cap_inner_outer_corners_match=True,
        circular_cap_inner_outer_radii_match=True,cap_annulus_areas_m2=areas,
        circular_chord_error_m=sag,source_placement_and_owned_ports_match=True,
        prospective_rectangular_remainder_m=row['length_budget']['retained_rectangular_straight_m'],
        proposed_VAV_shift_m=row['length_budget']['downstream_shift_m']))
out=RUN/'independent-review.json';assert not out.exists()
out.write_text(json.dumps(dict(ifc_sha256=report['ifc_sha256'],cases=checks,
    actual_native_fittings=20,owned_ports=40,source_cap_accuracy_budget_m=.00002,
    full_pressure_verified=False,network_merged=False,installation_verified=False,
    scope='Saved finite local transition bodies/caps/ports only; real product collar seals, gauges, round leads and existing duct revisions unresolved'),indent=2))
print(json.dumps(dict(native_fittings=20,owned_ports=40,all_native_caps_and_walls_pass=True,
    maximum_circle_chord_error_m=max(r['circular_chord_error_m'] for r in checks))))
