"""Conservative native-primitive bounds and literal-shape mesh reuse; project trial."""
import json,hashlib,math
from pathlib import Path
import numpy as np,ifcopenshell.geom
from ifcopenshell.util import placement
from bsa.duct_fitting_chain import value
from bsa.circular_geometry import configure
from bsa.product_alignment import aligned_placement

def matrix(obj):
 w=placement.get_local_placement(obj.ObjectPlacement);aligned_placement(w,np.eye(4),0);return w

def profile_points(p):
 if p.is_a('IfcCircleProfileDef'):
  r=p.Radius;pts=np.array([[-r,-r],[r,-r],[r,r],[-r,r]])
 elif p.is_a('IfcRectangleProfileDef'):
  x,y=p.XDim/2,p.YDim/2;pts=np.array([[-x,-y],[x,-y],[x,y],[-x,y]])
 elif p.is_a('IfcArbitraryClosedProfileDef') and p.OuterCurve.is_a('IfcPolyline'):
  pts=np.asarray([x.Coordinates for x in p.OuterCurve.Points]);assert pts.shape[1]==2
 else:raise ValueError('Unsupported bound profile '+p.is_a())
 if getattr(p,'Position',None):
  f=placement.get_axis2placement(p.Position);pts=pts@f[:2,:2].T+f[:2,-1]
 return pts

def bounds(item,w):
 if item.is_a('IfcMappedItem'):
  transform=placement.get_mappeditem_transformation(item);assert transform is not None and transform.shape==(4,4) and np.isfinite(transform).all();assert np.allclose(transform[3],[0,0,0,1],rtol=0,atol=1e-12)
  results=[bounds(child,w@transform) for child in item.MappingSource.MappedRepresentation.Items];assert results;return np.min([b[0] for b in results],axis=0),np.max([b[1] for b in results],axis=0)
 if item.is_a('IfcBooleanResult'):
  a,b=bounds(item.FirstOperand,w),bounds(item.SecondOperand,w)
  if item.Operator=='UNION':return np.minimum(a[0],b[0]),np.maximum(a[1],b[1])
  if item.Operator in ['DIFFERENCE','INTERSECTION']:return a
  raise ValueError('Unsupported Boolean')
 if item.is_a('IfcExtrudedAreaSolid'):
  f=w@placement.get_axis2placement(item.Position);p=profile_points(item.SweptArea);v=np.column_stack([p,np.zeros(len(p))]);v=np.vstack([v,v+np.array(item.ExtrudedDirection.DirectionRatios)*item.Depth]);v=v@f[:3,:3].T+f[:3,3]
 elif item.is_a('IfcRevolvedAreaSolid'):
  assert tuple(item.Axis.Location.Coordinates)==(0.,0.,0.) and tuple(item.Axis.Axis.DirectionRatios)==(0.,1.,0.);f=w@placement.get_axis2placement(item.Position);p=profile_points(item.SweptArea);lo=p.min(axis=0);hi=p.max(axis=0);angle=float(item.Angle);assert 0<angle<=2*math.pi
  angles=[0.,angle]
  for i in range(3):
   a=math.atan2(-f[i,2],f[i,0]);angles.extend(a+k*math.pi for k in range(-3,5) if 0<=a+k*math.pi<=angle)
  v=np.array([[x*math.cos(a),y,-x*math.sin(a)] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for a in angles]);v=v@f[:3,:3].T+f[:3,3]
 elif item.is_a('IfcAdvancedBrep'):
  points=[]
  def controls(curve):
   if curve.is_a('IfcBSplineCurve'):
    if curve.is_a('IfcRationalBSplineCurveWithKnots'):assert all(x>0 and math.isfinite(x) for x in curve.WeightsData)
    points.extend(p.Coordinates for p in curve.ControlPointsList)
   elif curve.is_a('IfcCircle'):
    f=placement.get_axis2placement(curve.Position);r=curve.Radius;assert r>0;points.extend((f[:3,3]+x*r*f[:3,0]+y*r*f[:3,1]).tolist() for x in [-1,1] for y in [-1,1])
   elif not curve.is_a('IfcLine'):raise ValueError('Unsupported trimmed edge '+curve.is_a())
  for face in item.Outer.CfsFaces:
   surface=face.FaceSurface;face_start=len(points)
   if surface.is_a('IfcBSplineSurface'):
    if surface.is_a('IfcRationalBSplineSurfaceWithKnots'):assert all(x>0 and math.isfinite(x) for row in surface.WeightsData for x in row)
    points.extend(p.Coordinates for row in surface.ControlPointsList for p in row)
   elif not (surface.is_a('IfcPlane') or surface.is_a('IfcCylindricalSurface') or surface.is_a('IfcConicalSurface')):raise ValueError('Unsupported bounded surface '+surface.is_a())
   for bound in face.Bounds:
    loop=bound.Bound
    if loop.is_a('IfcPolyLoop'):points.extend(p.Coordinates for p in loop.Polygon)
    else:
     assert loop.is_a('IfcEdgeLoop')
     for edge in loop.EdgeList:
      e=edge.EdgeElement;assert e.is_a('IfcEdgeCurve');points.extend([e.EdgeStart.VertexGeometry.Coordinates,e.EdgeEnd.VertexGeometry.Coordinates]);controls(e.EdgeGeometry)
   if surface.is_a('IfcCylindricalSurface') or surface.is_a('IfcConicalSurface'):
    f=placement.get_axis2placement(surface.Position);boundary=np.asarray(points[face_start:]);assert len(boundary);z=(boundary-f[:3,3])@f[:3,2];r=surface.Radius
    if surface.is_a('IfcConicalSurface'):r+=max(abs(z.min()),abs(z.max()))*abs(math.tan(surface.SemiAngle))
    assert r>0;points.extend((f[:3,3]+f[:3,2]*h+f[:3,0]*r*x+f[:3,1]*r*y).tolist() for h in [z.min(),z.max()] for x in [-1,1] for y in [-1,1])
  v=np.asarray(points,dtype=float);v=v@w[:3,:3].T+w[:3,3]
 elif item.is_a('IfcFacetedBrep'):
  v=np.array([p.Coordinates for face in item.Outer.CfsFaces for bound in face.Bounds for p in bound.Bound.Polygon]);v=v@w[:3,:3].T+w[:3,3]
 elif item.is_a('IfcTessellatedFaceSet'):
  v=np.asarray(item.Coordinates.CoordList);v=v@w[:3,:3].T+w[:3,3]
 else:raise ValueError('Unsupported bounds item '+item.is_a())
 assert v.ndim==2 and v.shape[1]==3 and np.isfinite(v).all();return v.min(axis=0),v.max(axis=0)

def body(obj):
 reps=[r for r in obj.Representation.Representations if r.RepresentationIdentifier=='Body'];assert len(reps)==1 and len(reps[0].Items)==1;return reps[0].Items[0]

def key(obj):return hashlib.sha256(json.dumps(value(body(obj)),sort_keys=True,separators=(',',':')).encode()).hexdigest()

class Cache:
 def __init__(self,folder):
  self.folder=Path(folder);self.folder.mkdir(exist_ok=False);self.settings=ifcopenshell.geom.settings();self.settings.set(self.settings.USE_WORLD_COORDS,True);configure(self.settings);self.metadata={};self.last=None;self.actual_native_calls=0
 def local(self,obj):
  h=key(obj)
  if self.last is not None and self.last[0]==h:return self.last[1:]
  path=self.folder/(h+'.npz')
  if not path.exists():
   shape=ifcopenshell.geom.create_shape(self.settings,obj);w=matrix(obj);v=(np.asarray(shape.geometry.verts).reshape(-1,3)-w[:3,3])@w[:3,:3];f=np.asarray(shape.geometry.faces,dtype=np.int32).reshape(-1,3);np.savez_compressed(path,v=v,f=f);self.metadata[h]=dict(sample_guid=obj.GlobalId,npz_sha256=hashlib.sha256(path.read_bytes()).hexdigest());self.actual_native_calls+=1
  else:
   with np.load(path) as data:v,f=data['v'],data['f']
  self.last=(h,v,f);return v,f
 def world(self,obj):
  v,f=self.local(obj);w=matrix(obj);return v@w[:3,:3].T+w[:3,3],f

