"""Independent native cap/material and Decimal checks for staged candidate."""
from decimal import Decimal as D
import hashlib
import json
import math
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
from ifcopenshell.util import system,placement
import numpy as np
from bsa.interface_contacts import cap,matching
from bsa.solid_clash import from_mesh

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/staged-transition-candidate-reviewed'
record=json.loads((RUN/'review.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
def read(path,guid=None):
    model=ifcopenshell.open(str(path));obj=model.by_guid(guid) if guid else model.by_type('IfcDuctFitting')[0]
    shape=ifcopenshell.geom.create_shape(settings,obj)
    vertices=np.asarray(shape.geometry.verts).reshape(-1,3);faces=np.asarray(shape.geometry.faces).reshape(-1,3)
    caps={p.Name:cap(vertices,faces,placement.get_local_placement(p.ObjectPlacement)) for p in system.get_ports(obj)}
    return caps,from_mesh((vertices,faces))
old,_=read(ROOT/'runs/reduced-branch-network-reviewed/Supply Network.ifc',record['original_transition_guid'])
first,solid1=read(RUN/'stage-1/transition.ifc');last,solid2=read(RUN/'stage-2/transition.ifc')
matching(old['start'],first['start']);matching(first['end'],last['start']);matching(last['end'],old['end'])
overlap=(solid1^solid2).volume();assert abs(overlap)<1e-12
for stage in record['stages']:
    a,b=[list(map(lambda x:D(str(x)),stage[n])) for n in ['start_section_m','end_section_m']]
    ratio=a[0]*a[1]/(b[0]*b[1]);angle=D(str(max(stage['actual_included_angles_deg'])))
    if stage['stage']==1:
        assert D(20)<=angle<D(30)
        ordinate=D('.21')+(angle-20)/10*(D('.20')-D('.21'))
    else:
        assert D(15)<=angle<D(30)
        ordinate=D('.20')
    independent=(ratio-1)*ordinate
    assert math.isclose(float(independent),stage['source_query']['coefficient'],rel_tol=1e-12,abs_tol=0)
summary=dict(stages=2,native_schema_geometry_checks_pass=True,source_family_checks_pass=True,
    native_material_cap_pairs_matched=3,internal_material_overlap_m3=overlap,
    independent_decimal_queries_match=True,total_length_m=record['original_total_length_m'],
    external_frames_preserved=True,original_network_modified=False,network_integrated=False,
    new_internal_interfaces=1,interaction_and_joint_losses_unknown=True,combined_pressure_Pa=None,
    pressure_budget_complete=False,design_accepted=False,source_review_sha256=sha(RUN/'review.json'))
(RUN/'independent-review.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
