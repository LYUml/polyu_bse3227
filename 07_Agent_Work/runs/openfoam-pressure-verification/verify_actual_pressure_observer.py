from pathlib import Path
import re,json,math
from array import array
case=Path(__file__).parent/'actual-family-1-design-flow-upwind';fields={n:(case/'11'/n).read_text() for n in ['p','U','phi','Pt']}
assert re.search(r'dimensions\s+\[1 -1 -2 0 0 0 0\]',fields['Pt'])
boundary=(case/'constant/polyMesh/boundary').read_text()
def patch(t,name):
 m=re.search(r'\b'+name+r'\s*\{',t);begin=m.end();i=begin;d=1
 while d:
  if t[i]=='{':d+=1
  if t[i]=='}':d-=1
  i+=1
 return t[begin:i-1]
def values(t,n,vector=False):
 m=re.search(r'value\s+uniform\s+(\([^)]*\)|[^;]+);',t)
 if m:return [tuple(map(float,m[1].strip('()').split())) if vector else float(m[1])]*n
 m=re.search(r'value\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\n\)',t,re.S);assert m and int(m[1])==n
 return [tuple(map(float,x.split())) for x in re.findall(r'\(([^()]+)\)',m[2])] if vector else list(map(float,m[2].split()))
pinternal=list(map(float,re.search(r'internalField\s+nonuniform\s+List<scalar>\s+\d+\s*\((.*?)\n\)',fields['p'],re.S)[1].split()))
owner=array('i',map(int,re.search(r'\n\d+\s*\n\(\s*\n(.*?)\n\)',(case/'constant/polyMesh/owner').read_text(),re.S)[1].split()))
r={'scope':'Saved step11 observer algebra only, unconverged actual startup','ports':{},'pressure_accepted':False,'field_Pt_dimensions':[1,-1,-2,0,0,0,0]}
for name in ['inlet','outlet_0','outlet_1','outlet_2','outlet_3']:
 b=patch(boundary,name);n=int(re.search(r'nFaces\s+(\d+);',b)[1]);start=int(re.search(r'startFace\s+(\d+);',b)[1]);pb=patch(fields['p'],name);assert 'zeroGradient' in pb;p=[pinternal[owner[i]] for i in range(start,start+n)];u=values(patch(fields['U'],name),n,True);phi=values(patch(fields['phi'],name),n);Pt=values(patch(fields['Pt'],name),n)
 calc=[1.2*(x+.5*math.fsum(a*a for a in v)) for x,v in zip(p,u)];error=max(abs(x-y) for x,y in zip(calc,Pt));independent=math.fsum(f*v for f,v in zip(phi,calc))/math.fsum(phi)
 lines=(case/f'postProcessing/pressure_{name}/10/surfaceFieldValue.dat').read_text().splitlines();rows={int(float(x.split()[0])):float(x.split()[1]) for x in lines if x.strip() and not x.startswith('#')};native=rows[11];assert error<1e-8 and abs(native-independent)<1e-8,(name,error,native,independent)
 r['ports'][name]={'faces':n,'maximum_face_formula_error_Pa':error,'native_weighted_average_Pa':native,'independent_signed_phi_weighted_average_Pa':independent,'average_absolute_difference_Pa':abs(native-independent),'maximum_face_speed_m_s':max(math.sqrt(math.fsum(a*a for a in v)) for v in u),'negative_face_flux_count':sum(f<0 for f in phi),'positive_face_flux_count':sum(f>0 for f in phi)}
(case/'pressure-observer-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
