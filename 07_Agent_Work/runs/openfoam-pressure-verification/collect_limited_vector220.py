from pathlib import Path
import ctypes,json,hashlib,os,subprocess,sys
root=Path('C:/Users/lyuml-win/Desktop/building-services-agent')
b=Path(__file__).parent;c=b/'actual-family-1-resolution-limited-vector'
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.restype=ctypes.c_void_p
k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
k.CloseHandle.argtypes=[ctypes.c_void_p]
h=k.OpenProcess(0x100000,False,28444)
if h:
 try:
  result=k.WaitForSingleObject(h,1800000)
  assert result==0,('solver wait incomplete',result)
 finally:k.CloseHandle(h)
assert (c/'foamRun-to220.log').read_text(encoding='utf-8').rstrip().endswith('End')
assert (c/'220/U').exists()
subprocess.run([sys.executable,str(b/'review_native_limited_vector220.py')],check=True,stdout=subprocess.DEVNULL)
os.environ['BSA_PROJECT_ROOT']=str(b.parents[2])
from bsa.openfoam_history import review_project
rel=c.relative_to(b.parents[2]).as_posix()
r=review_project(rel+'/native-history-to220.json',rel+'/window220-review.json')
fields=['U','p','Pt','k','omega','nut']
def hashes():return {n:hashlib.sha256((c/'220'/n).read_bytes()).hexdigest() for n in fields}
before=hashes()
e=dict(os.environ);e.update(json.loads((root/'tools/bluecfd-evaluation/isolated-environment.json').read_text(encoding='utf-8')));e['OMP_NUM_THREADS']='1'
with (c/'yPlus-step220.log').open('x',encoding='utf-8') as log:
 out=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamPostProcess.exe'),'-case',str(c),'-solver','incompressibleFluid','-time','220','-func','yPlus'],env=e,stdout=log,stderr=subprocess.STDOUT)
assert out.returncode==0
assert before==hashes()
rows=[s.split() for s in (c/'postProcessing/yPlus/220/yPlus.dat').read_text(encoding='utf-8').splitlines() if s.strip() and not s.startswith('#')]
assert len(rows)==1 and float(rows[0][0])==220 and rows[0][1]=='wall'
v=list(map(float,rows[0][2:]));assert len(v)==3
report={'returncode':0,'six_original_fields_unchanged':True,'field_sha256':before,'yPlus':dict(zip(['minimum','maximum','average'],v)),'yPlus_target':1,'yPlus_target_pass':v[1]<=1,'engineering_accepted':False}
with (c/'yPlus-step220-review.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,allow_nan=False)
print(json.dumps({'window':r['window_iterations'],'numerical_window_pass':r['numerical_window_pass'],'pressure_relative_ranges':{n:x['relative_range'] for n,x in r['pressures'].items()},'yPlus':report['yPlus'],'engineering_accepted':False}),flush=True)
