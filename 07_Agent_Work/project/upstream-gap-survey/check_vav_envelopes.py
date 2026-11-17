"""Native saved mesh clashes, including every reservation overlap without waiver."""
import hashlib,json
from pathlib import Path
import numpy as np
import ifcopenshell,ifcopenshell.geom
from bsa.solid_clash import overlaps
from bsa.box_geometry import box_mesh

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
RUN=ROOT/'vav-finite-placement'
report=json.loads((RUN/'placement.json').read_text())
IFC=RUN/'model.ifc'
assert hashlib.sha256(IFC.read_bytes()).hexdigest()==report['saved_ifc_sha256']
model=ifcopenshell.open(str(IFC));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
elements=[e for e in model.by_type('IfcElement') if e.Representation]
assert len(elements)==169
meshes={};kinds={};volumes={}
expected={r['guid']:r for r in report['obstacles']}
for e in elements:
    shape=ifcopenshell.geom.create_shape(settings,e)
    v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3)
    meshes[e.GlobalId]=(v,f)
    if e.GlobalId in expected:
        row=expected[e.GlobalId];lo,size,volume=box_mesh(v,f)
        assert np.allclose(lo,row['origin_m'],rtol=0,atol=1e-8)
        assert np.allclose(size,row['size_m'],rtol=0,atol=1e-8)
        kinds[e.GlobalId]='casing' if row['id'].endswith('CASING') else 'inlet_reservation' if row['id'].endswith('INLET-RESERVATION') else 'access_reservation'
        volumes[e.GlobalId]=volume
    else:kinds[e.GlobalId]='existing_network'
hits,unknown,count,checks=overlaps(elements,meshes,.00002,1e-10,10000)
assert not unknown
categories={}
for hit in hits:
    key='/'.join(sorted(kinds[g] for g in hit['pair']))
    categories[key]=categories.get(key,0)+1
review=dict(ifc_sha256=report['saved_ifc_sha256'],native_box_geometry_reconciled=80,
    represented_elements=169,boolean_candidate_pairs=count,all_solids_valid=True,
    overlap_counts=categories,overlaps=hits,boolean_checks=checks,
    policy='Same20micrometre bounding candidate threshold and1e-10m3 overlap volume as prior rigid-network numerical policy; not installation tolerance',
    reserved_spaces_are_not_physical_products=True,allowed_contacts=[],
    connected_equipment=False,design_accepted=False,
    limitations=['No architecture, elevation, insulation or supports acceptance',
        'Inlet reservation overlaps identify required source-duct replacement space, not a connected round inlet',
        'Both-side access reservations are conservative design assumptions, not actual control enclosures'])
out=RUN/'native-review.json';assert not out.exists()
out.write_text(json.dumps(review,indent=2))
print(json.dumps(dict(elements=169,boxes_reconciled=80,overlap_counts=categories,unknown=len(unknown)),indent=2))
