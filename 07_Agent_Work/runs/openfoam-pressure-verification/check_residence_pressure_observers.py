from pathlib import Path
import re,json,math,hashlib,sys
import numpy as np
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/openfoam-pressure-verification');c=B/'plenum-family-1-initialized-residence';time=sys.argv[1] if len(sys.argv)>1 else '0.005'
def block(text,name):
 m=re.search(r'\b'+re.escape(name)+r'\s*\{',text[text.index('boundaryField'):]);assert m
 offset=text.index('boundaryField');start=offset+m.end();level=1
 for i in range(start,len(text)):
  level+=(text[i]=='{')-(text[i]=='}')
  if level==0:return text[start:i]
 raise ValueError('Unclosed patch')
def patch(field,name,count):
 t=block((c/time/field).read_text(),name)
 m=re.search(r'\bvalue\s+nonuniform\s+List<(scalar|vector)>\s+(\d+)\s*\((.*?)\n\)\s*;',t,re.S)
 if m:
  assert int(m[2])==count
  a=np.fromstring(m[3].replace('(',' ').replace(')',' '),sep=' ')
  return a.reshape((count,3)) if m[1]=='vector' else a
 m=re.search(r'\bvalue\s+uniform\s+([^;]+);',t);assert m
 a=np.fromstring(m[1].replace('(',' ').replace(')',' '),sep=' ')
 return np.tile(a,(count,1)) if field=='U' else np.full(count,a[0])
results={}
for name in ('inlet','outlet_0','outlet_1','outlet_2','outlet_3'):
 path=list((c/'postProcessing'/('pressure_'+name)).rglob('surfaceFieldValue.dat'));assert len(path)==1
 txt=path[0].read_text();count=int(re.search(r'# Faces\s*:\s*(\d+)',txt)[1]);rows=[l.split() for l in txt.splitlines() if l.strip() and not l.startswith('#')];matched=[r for r in rows if float(r[0])==float(time)];assert len(matched)==1;native=float(matched[0][1])
 p=patch('p','air_'+name,count);u=patch('U','air_'+name,count);phi=patch('phi','air_'+name,count);pt=1.2*(p+.5*np.sum(u*u,axis=1));expected=math.fsum(phi*pt)/math.fsum(phi)
 assert math.isclose(expected,native,rel_tol=1e-12,abs_tol=1e-11),(name,expected,native)
 results[name]={'faces':count,'reconstructed_Pa':expected,'native_Pa':native,'absolute_difference_Pa':abs(expected-native),'signed_flux_sum_m3_s':math.fsum(phi)}
r={'scope':'Independent saved-field reconstruction of five native total-pressure observers at specified saved time only; not pressure/design acceptance','time_s':float(time),'assumed_density_kg_m3':1.2,'formula':'sum(phi*rho*(p_kinematic+0.5*mag(U)^2))/sum(phi)','all5_observers_match':True,'fields_sha256':{n:hashlib.sha256((c/time/n).read_bytes()).hexdigest() for n in ('p','U','phi')},'results':results,'pressure_adopted':False};(c/('pressure-observer-check-'+time+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
