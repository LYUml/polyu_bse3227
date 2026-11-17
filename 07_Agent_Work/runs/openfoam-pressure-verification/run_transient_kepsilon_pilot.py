from pathlib import Path
import json,hashlib,shutil,re,math,os,subprocess,time
from bsa.openfoam_mesh_review import assess_check_mesh
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');assert Path(os.environ['BSA_PROJECT_ROOT']).resolve()==P.resolve()
B=P/'07_Agent_Work/runs/openfoam-pressure-verification';source=B/'plenum-family-1-local-feature-hex-trial';out=B/'plenum-family-1-transient-kepsilon-pilot'
assert not out.exists();out.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads(Path('docs/evidence/plenum-native-feature-mesh.json').read_text(encoding='utf-8'))
for name,expected in receipt['native_mesh_sha256'].items():assert sha(source/'constant/polyMesh'/name)==expected
(out/'constant').mkdir();shutil.copytree(source/'constant/polyMesh',out/'constant/polyMesh');(out/'system').mkdir();(out/'0').mkdir()
header=lambda name,kind='dictionary':'FoamFile {format ascii;class '+kind+';object '+name+';}\n'
def write(path,text): (out/path).write_text(text,encoding='ascii')
old=B/'actual-family-1-design-flow-cold-upwind'
uold=(old/'0/U').read_text(encoding='utf-8')
flows={}
for name in ['inlet','outlet_0','outlet_1','outlet_2','outlet_3']:
 hit=re.search(r'\b'+name+r'\s*\{[^}]*volumetricFlowRate\s+([0-9.eE+-]+)',uold);assert hit,name
 flows[name]=float(hit.group(1))
assert math.isclose(sum(v for k,v in flows.items() if k!='inlet'),flows['inlet'],rel_tol=1e-13)
geo=json.loads((source/'native-geometry-review.json').read_text())
area=next(p['native_area_m2'] for p in geo['ports'] if p['source_port']=='inlet')
U=flows['inlet']/area;I=.05;Dh=2*.3794*.354/(.3794+.354);length=.07*Dh
k=1.5*(U*I)**2;epsilon=.09**.75*k**1.5/length
u=header('U','volVectorField')+'dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField\n{\nair_wall {type noSlip;}\n'
for name,q in flows.items():
 typ='flowRateInletVelocity' if name=='inlet' else 'flowRateOutletVelocity'
 u+='air_'+name+' {type '+typ+';volumetricFlowRate '+format(q,'.17g')+';value uniform (0 0 0);}\n'
write('0/U',u+'}\n')
p=header('p','volScalarField')+'dimensions [0 2 -2 0 0 0 0];internalField uniform 0;boundaryField {air_wall {type zeroGradient;}\n'
for name in flows:p+='air_'+name+' {type fixedFluxPressure;value uniform 0;}\n'
write('0/p',p+'}\n')
for name,value,dims,wall in [('k',k,'0 2 -2 0 0 0 0','kqRWallFunction'),('epsilon',epsilon,'0 2 -3 0 0 0 0','epsilonWallFunction')]:
 t=header(name,'volScalarField')+'dimensions ['+dims+'];internalField uniform '+format(value,'.17g')+';boundaryField {\nair_wall {type '+wall+';value uniform '+format(value,'.17g')+';}\n'
 for patch in flows:
  if patch=='inlet':t+='air_inlet {type fixedValue;value uniform '+format(value,'.17g')+';}\n'
  else:t+='air_'+patch+' {type inletOutlet;inletValue uniform '+format(value,'.17g')+';value uniform '+format(value,'.17g')+';}\n'
 write('0/'+name,t+'}\n')
t=header('nut','volScalarField')+'dimensions [0 2 -1 0 0 0 0];internalField uniform 0;boundaryField {air_wall {type nutkWallFunction;value uniform 0;}\n'
for patch in flows:t+='air_'+patch+' {type calculated;value uniform 0;}\n'
write('0/nut',t+'}\n')
shutil.copy2(old/'constant/physicalProperties',out/'constant/physicalProperties')
write('constant/momentumTransport',header('momentumTransport')+'simulationType RAS;RAS {model kEpsilon;turbulence on;printCoeffs on;}\n')
write('system/controlDict',header('controlDict')+'application foamRun;solver incompressibleFluid;startFrom startTime;startTime 0;stopAt endTime;endTime 0.005;deltaT 0.00025;writeControl timeStep;writeInterval 20;writeFormat ascii;writePrecision 17;writeCompression off;adjustTimeStep no;runTimeModifiable false;\n')
write('system/fvSchemes',header('fvSchemes')+'''ddtSchemes {default Euler;}
gradSchemes {default Gauss linear;}
divSchemes {default none;div(phi,U) Gauss upwind;div(phi,k) Gauss upwind;div(phi,epsilon) Gauss upwind;div((nuEff*dev2(T(grad(U))))) Gauss linear;}
laplacianSchemes {default Gauss linear corrected;}
interpolationSchemes {default linear;}
snGradSchemes {default corrected;}
wallDist {method meshWave;}
''')
write('system/fvSolution',header('fvSolution')+'''solvers
{
 p {solver GAMG;tolerance 1e-8;relTol 0.01;smoother DICGaussSeidel;}
 pFinal {solver GAMG;tolerance 1e-8;relTol 0;smoother DICGaussSeidel;}
 "(U|k|epsilon)" {solver smoothSolver;smoother symGaussSeidel;tolerance 1e-8;relTol 0.05;}
 "(U|k|epsilon)Final" {solver smoothSolver;smoother symGaussSeidel;tolerance 1e-8;relTol 0;}
}
PIMPLE {nOuterCorrectors 2;nCorrectors 2;nNonOrthogonalCorrectors 1;pRefCell 0;pRefValue 0;momentumPredictor yes;}
''')
policy={'scope':'New source-informed physical-time k-epsilon startup on preserved quality-passed hex mesh; not a continuation/acceptance of failed steady SST studies','native_mesh_sha256':receipt['native_mesh_sha256'],'source_geometry_and_mesh_unchanged':True,'physical_time_seconds':{'deltaT':.00025,'endTime':.005,'steps':20},'nominal_residence_time_s':geo['native_volume_m3']/flows['inlet'],'flow_m3_s':flows,'inlet_area_m2':area,'initial_turbulence_assumptions':{'intensity':I,'length_scale_fraction_Dh':.07,'hydraulic_diameter_m':Dh,'k_m2_s2':k,'epsilon_m2_s3':epsilon},'wall_treatment':'New standard k-epsilon wall-function scenario; no claim of old low-Re yPlus<=1 acceptance or generated layers','scheme':'Euler physical time and upwind convection for startup only; not final high-order design pressure','source_research':{'sha256':'07b071a56db66d494116aca34422059270eb9828df2593691de2ff4d6641be34','pages_actually_rendered_viewed':[20,21],'scope':'DOE2013 report uses standard k-epsilon and documents sustained oscillations; does not validate this mesh or boundary model'},'boundary_assumptions':['Uniform flow-rate inlet, prescribed four outlet flows','Actual developed VAV discharge profile and installation reference planes unverified','Smooth wall-function numerical treatment, not calibrated lined-wall roughness'],'pressure_acceptance_attempted':False,'runtime_budget_seconds':180,'design_accepted':False}
(out/'pilot-inputs.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
env=dict(os.environ);env.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text(encoding='utf-8')));env['OMP_NUM_THREADS']='1'
exe=Path(env['FOAM_APPBIN'])/'foamRun.exe';started=time.monotonic()
with (out/'foamRun.log').open('x',encoding='utf-8') as log:
 result=subprocess.run([str(exe),'-case',str(out),'-solver','incompressibleFluid'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
review={'returncode':result.returncode,'elapsed_seconds':time.monotonic()-started,'source_mesh_unchanged':all(sha(source/'constant/polyMesh'/n)==v for n,v in receipt['native_mesh_sha256'].items()),'copied_mesh_unchanged':all(sha(out/'constant/polyMesh'/n)==v for n,v in receipt['native_mesh_sha256'].items()),'saved_final_time_exists':(out/'0.005/U').exists(),'pressure_adopted':False,'design_accepted':False}
(out/'native-startup-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps(review),flush=True);print((out/'foamRun.log').read_text(encoding='utf-8')[-1800:],flush=True)
