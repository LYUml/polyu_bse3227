from pathlib import Path
import re,json,math,hashlib,itertools
case=Path(__file__).parent/'actual-family-1-resolution-limited-gradient'
r={'scope':'Saved20 limited-gradient startup native fields and residual diagnostics only','field_time':20,'engineering_accepted':False,'fields':{}}
for name in ['U','p','Pt','k','omega','nut']:
 path=case/'20'/name;data=path.read_bytes();text=data.decode();m=re.search(r'internalField\s+nonuniform\s+List<(\w+)>\s+(\d+)\s*\(',text);assert m;count=int(m[2]);assert count==684730
 if m[1]=='vector':
  rows=itertools.islice(re.finditer(r'\(([^()]+)\)',text[m.end():]),count);vals=[math.sqrt(math.fsum(float(v)**2 for v in a[1].split())) for a in rows]
 else:
  body=text[m.end():text.index(')',m.end())];vals=list(map(float,body.split()))
 assert len(vals)==count and all(math.isfinite(v) for v in vals)
 r['fields'][name]={'native_cell_values':count,'minimum':min(vals),'maximum':max(vals),'sha256':hashlib.sha256(data).hexdigest()}
 if name in ['k','omega','nut']:assert min(vals)>=0
 if name=='p':assert re.search(r'dimensions\s+\[0 2 -2 0 0 0 0\]',text)
 if name=='Pt':assert re.search(r'dimensions\s+\[1 -1 -2 0 0 0 0\]',text)
log=(case/'foamRun-startup20.log').read_text();assert log.rstrip().endswith('End');blocks=re.split(r'^Time = ([0-9.]+)s\s*$',log,flags=re.M);initial={};terminal={}
for i in range(1,len(blocks),2):
 step=int(float(blocks[i]))
 if 1<=step<=20:
  for field,val in re.findall(r'Solving for (\w+), Initial residual = ([^,]+)',blocks[i+1]):initial.setdefault(field,[]).append(float(val));terminal[field]=float(val)
r['initial_residual_ranges_startup20']={name:{'minimum':min(values),'maximum':max(values),'terminal':terminal[name]} for name,values in initial.items()};r['negative_k_bounding_events']=len(re.findall(r'^bounding k,',log,re.M));r['residual_acceptance_target_not_defined_by_this_review']=True
(case/'saved20-field-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
