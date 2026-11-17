from pathlib import Path
import re,json,hashlib
import numpy as np
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');s=B/'plenum-family-1-initialized-residence/constant/polyMesh';c=B/'plenum-family-1-outlet-extension-trial';m=c/'constant/polyMesh'
def body(path):
 t=path.read_text();mt=re.search(r'\n(\d+)\s*\n\(',t);assert mt;return int(mt[1]),t[mt.end():t.rfind(')')]
def read(mesh):
 n,t=body(mesh/'points');pts=np.fromstring(t.replace('(',' ').replace(')',' '),sep=' ').reshape((-1,3));assert len(pts)==n
 n,t=body(mesh/'faces');faces=[tuple(map(int,x[1].split())) for x in re.findall(r'(\d+)\(([^()]*)\)',t)];assert len(faces)==n
 own=np.fromstring(body(mesh/'owner')[1],sep=' ',dtype=int);nei=np.fromstring(body(mesh/'neighbour')[1],sep=' ',dtype=int);return pts,faces,own,nei
sp,sf,so,sn=read(s);p,f,o,n=read(m);assert np.array_equal(p[:len(sp)],sp)
lookup={tuple(sorted(v)):i for i,v in enumerate(f) if max(v)<len(sp)};assert len(lookup)==len(sf)
ids=np.array([lookup[tuple(sorted(v))] for v in sf]);assert len(set(ids))==len(sf)
assert np.array_equal(o[ids],so);assert np.array_equal(n[ids[:len(sn)]],sn)
oldcells=int(max(so.max(),sn.max()))+1;newcells=int(max(o.max(),n.max()))+1;assert oldcells==142480 and newcells==190880
boundary=(s/'boundary').read_text();stations={};zones=[]
for j in range(4):
 match=re.search(r'air_outlet_'+str(j)+r'\s*\{(.*?)\}',boundary,re.S);count=int(re.search(r'nFaces\s+(\d+)',match[1])[1]);start=int(re.search(r'startFace\s+(\d+)',match[1])[1]);newids=ids[start:start+count];assert (newids<len(n)).all() and (o[newids]<oldcells).all() and (n[newids]>=oldcells).all()
 assert all(f[int(k)]==sf[start+i] for i,k in enumerate(newids))
 stations[str(j)]={'faces':count,'now_internal':True,'original_face_coordinates_and_orientation_preserved':True,'new_face_labels':newids.tolist()}
 zones.append('original_outlet_'+str(j)+' {type faceZone;faceLabels List<label> '+str(count)+'('+ ' '.join(map(str,newids))+');flipMap List<bool> '+str(count)+'('+ ' '.join(['false']*count)+');}')
(m/'faceZones').write_text('FoamFile {format ascii;class regIOobject;object faceZones;}\n4\n(\n'+'\n'.join(zones)+'\n)\n')
(c/'original-pressure-stations.json').write_text(json.dumps(stations,indent=2))
r={'scope':'Computational outlet extension topology verification; not actual installation or pressure acceptance','original_cells':oldcells,'extended_cells':newcells,'added_cells':newcells-oldcells,'original_point_count':len(sp),'original_face_count':len(sf),'all_original_points_exactly_preserved':True,'all_original_faces_unique_and_preserved':True,'all_original_face_owner_cells_preserved':True,'all_original_internal_neighbours_preserved':True,'original_outlet_faces_preserved_as_internal_stations':{k:{a:b for a,b in v.items() if a!='new_face_labels'} for k,v in stations.items()},'computational_extension_m':.25,'layers':25,'native_full_mesh_quality_pass':'Mesh OK.' in (c/'checkMesh.log').read_text(),'faceZones_sha256':hashlib.sha256((m/'faceZones').read_bytes()).hexdigest(),'pressure_adopted':False,'design_accepted':False};(c/'extension-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
