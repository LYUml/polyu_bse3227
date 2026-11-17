import json
from pathlib import Path
import ifcopenshell,numpy as np
from outlet_native_batches import body,bounds,matrix,key
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/three-dimensional-outlet-candidate');m=ifcopenshell.open(str(R/'Supply and Three Dimensional Outlet Candidate.ifc'));r=json.loads((R/'review.json').read_text());cache=R/'bounded-native-review/mesh-cache'
for route in r['records']:
 for p in route['pieces']:
  o=m.by_guid(p['guid']);f=cache/(key(o)+'.npz')
  if not f.exists():continue
  d=np.load(f);w=matrix(o);v=d['v']@w[:3,:3].T+w[:3,3];lo,hi=bounds(body(o),w)
  if np.any(v.min(axis=0)<lo-1e-8) or np.any(v.max(axis=0)>hi+1e-8):print(p['guid'],p['kind'],body(o),w.tolist(),'vmin',v.min(axis=0).tolist(),'lo',lo.tolist(),'vmax',v.max(axis=0).tolist(),'hi',hi.tolist());raise SystemExit()
