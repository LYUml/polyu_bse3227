from pathlib import Path
import os,json,re,shutil,subprocess,math,hashlib
base=Path(__file__).parent;source=base/'plenum-family-1-constrained-core-topology-merged';case=base/'actual-family-1-four-flow-startup';case.mkdir();[(case/n).mkdir() for n in ['0','constant','system']];shutil.copytree(source/'constant/polyMesh',case/'constant/polyMesh')
cfg=base.parent/'su2-pressure-verification/plenum-native-air-domain/family-1-feedback-study/flow.cfg';text=cfg.read_text()
rho=float(re.search(r'INC_DENSITY_INIT=(.*)',text)[1]);mu=float(re.search(r'MU_CONSTANT=(.*)',text)[1]);speed=abs(float(re.search(r'INC_VELOCITY_INIT=\([^,]+,([^,]+),',text)[1]));nu=mu/rho
mesh=case/'constant/polyMesh'
def body(p):return re.search(r'\n(\d+)\s*\n\(\s*\n(.*?)\n\)',p.read_text(),re.S)[2]
xyz=[tuple(map(float,x.split())) for x in re.findall(r'\(([^()]+)\)',body(mesh/'points'))];faces=[list(map(int,re.findall(r'\d+',x)))[1:] for x in body(mesh/'faces').splitlines()];boundary=(mesh/'boundary').read_text();n,start=map(int,re.search(r'inlet\s*\{[^}]*nFaces\s+(\d+);\s*startFace\s+(\d+);',boundary).groups());area=[]
for face in faces[start:start+n]:
 S=[0.,0.,0.];o=xyz[face[0]]
 for j in range(1,len(face)-1):
  a=[xyz[face[j]][k]-o[k] for k in range(3)];b=[xyz[face[j+1]][k]-o[k] for k in range(3)];cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];S=[x+y*.5 for x,y in zip(S,cross)]
 area.append(S[1])
A=math.fsum(area);assert A>0 and all(abs(xyz[i][1]-19.041159)<1e-10 for f in faces[start:start+n] for i in f)
Q=A*speed;values=re.search(r'MARKER_OUTLET=\(([^)]+)\)',text)[1].split(',');flows={values[i]:float(values[i+1])/rho for i in range(0,6,2)};flows['outlet_3']=Q-math.fsum(flows.values());assert min(flows.values())>0
boundary=re.sub(r'(wall\s*\{\s*type\s+)patch;',r'\1wall;',boundary,count=1);(mesh/'boundary').write_text(boundary)
def header(cls,obj):return f'FoamFile {{format ascii;class {cls};object {obj};}}\n'
k=1.5*(speed*.05)**2;omega=k/(10*nu)
def field(name,cls,dim,internal,patches):
 t=header(cls,name)+f'dimensions [{dim}]; internalField uniform {internal}; boundaryField {{\n'
 for patch,settings in patches.items():t+=patch+' {'+settings+'}\n'
 (case/'0'/name).write_text(t+'}\n')
U={'inlet':f'type fixedValue; value uniform (0 {-speed:.17g} 0);','wall':'type noSlip;'}
U.update({name:f'type flowRateOutletVelocity; volumetricFlowRate {q:.17g}; value uniform (0 0 0);' for name,q in flows.items()});field('U','volVectorField','0 1 -1 0 0 0 0','(0 0 0)',U)
field('p','volScalarField','0 2 -2 0 0 0 0','0',{name:'type zeroGradient;' for name in U})
for name,value,dim,wall in [('k',k,'0 2 -2 0 0 0 0','type fixedValue;value uniform 0;'),('omega',omega,'0 0 -1 0 0 0 0',f'type omegaWallFunction;value uniform {omega:.17g};')]:
 patches={'inlet':f'type fixedValue;value uniform {value:.17g};','wall':wall};patches.update({n:'type zeroGradient;' for n in flows});field(name,'volScalarField',dim,f'{value:.17g}',patches)
field('nut','volScalarField','0 2 -1 0 0 0 0','0',{name:('type nutLowReWallFunction;value uniform 0;' if name=='wall' else 'type calculated;value uniform 0;') for name in U})
(case/'constant/physicalProperties').write_text(header('dictionary','physicalProperties')+f'viscosityModel constant;nu {nu:.17g};\n');(case/'constant/momentumTransport').write_text(header('dictionary','momentumTransport')+'simulationType RAS;RAS {model kOmegaSST;turbulence on;printCoeffs on;}\n')
stock=base/'official-pitzDailySteady';shutil.copy2(stock/'system/fvSchemes',case/'system/fvSchemes');t=(stock/'system/fvSolution').read_text();t=re.sub(r'    residualControl\s*\{[^}]*\}', '',t);t=t.replace('nNonOrthogonalCorrectors 0;','nNonOrthogonalCorrectors 2;\n    pRefCell 0; pRefValue 0;');t=t.replace('relTol          0.1;','relTol          0.1;\n        maxIter 100;');t=t.replace('U               0.9;','U               0.5;').replace('".*"            0.9;','".*"            0.5;');(case/'system/fvSolution').write_text(t)
(case/'system/controlDict').write_text(header('dictionary','controlDict')+'application foamRun;solver incompressibleFluid;startFrom startTime;startTime 0;stopAt endTime;endTime 10;deltaT 1;writeControl timeStep;writeInterval 10;writeFormat ascii;writePrecision 17;runTimeModifiable false;\n')
t=header('dictionary','functions')
for name in ['inlet',*flows]:t+=f'flux_{name} {{type surfaceFieldValue;libs ("libfieldFunctionObjects.dll");regionType patch;name {name};operation sum;fields (phi);writeFields false;writeControl timeStep;writeInterval 1;}}\n'
(case/'system/functions').write_text(t)
r={'scope':'Actual source-family numerical startup trial ONLY, not accepted project pressure','source_cfg_sha256':hashlib.sha256(cfg.read_bytes()).hexdigest(),'source_mesh_case':source.name,'source_mesh_check_failed_categories':3,'density_kg_m3':rho,'dynamic_viscosity_Pa_s':mu,'kinematic_viscosity_m2_s':nu,'inlet_speed_m_s':speed,'native_inlet_area_m2':A,'targets_outward_m3_s':{'inlet':-Q,**flows},'inlet_turbulence_intensity_assumption':.05,'inlet_turbulent_viscosity_ratio_assumption':10,'inlet_k_m2_s2':k,'inlet_omega_s_1':omega,'wall_treatment':'smooth low-Re nut0/k0 with native omegaWallFunction; source NO_WALL_FUNCTION equivalence NOT verified','turbulence_model':'native OpenFOAM kOmegaSST; equivalence to SU2 SST options NOT verified','budget_steps':10,'engineering_accepted':False}
(case/'startup-inputs.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()));e['OMP_NUM_THREADS']='1'
with (case/'foamRun.log').open('x') as f:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/'foamRun.exe'),'-case',str(case)],env=e,stdout=f,stderr=subprocess.STDOUT)
print('foamRun',r.returncode,flush=True);print((case/'foamRun.log').read_text(errors='replace')[-1800:])
