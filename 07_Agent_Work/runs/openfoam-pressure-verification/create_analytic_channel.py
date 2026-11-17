from pathlib import Path
import os,json,subprocess,re,shutil
base=Path(__file__).parent;case=base/'analytic-laminar-channel';case.mkdir();[(case/n).mkdir() for n in ['0','constant','system']]
stock=base/'official-pitzDailySteady'
def header(cls,obj):return f'FoamFile {{format ascii;class {cls};object {obj};}}\n'
(case/'system/blockMeshDict').write_text(header('dictionary','blockMeshDict')+"""
convertToMeters 1;
vertices ((0 0 0)(1 0 0)(1 .1 0)(0 .1 0)(0 0 .01)(1 0 .01)(1 .1 .01)(0 .1 .01));
blocks (hex (0 1 2 3 4 5 6 7) (48 32 1) simpleGrading (1 1 1));
edges ();
boundary
(
inlet {type patch; faces ((0 4 7 3));}
outlet {type patch; faces ((1 2 6 5));}
wall {type wall; faces ((0 1 5 4)(3 7 6 2));}
frontAndBack {type empty; faces ((0 3 2 1)(4 5 6 7));}
);
mergePatchPairs ();
""")
(case/'system/controlDict').write_text(header('dictionary','controlDict')+"""
application foamRun; solver incompressibleFluid;
startFrom startTime; startTime 0; stopAt endTime; endTime 1000; deltaT 1;
writeControl timeStep; writeInterval 1000; writeFormat ascii; writePrecision 17;
runTimeModifiable false;
""")
shutil.copy2(stock/'system/fvSchemes',case/'system/fvSchemes')
t=(stock/'system/fvSolution').read_text();t=re.sub(r'    residualControl\s*\{[^}]*\}', '', t);t=t.replace('tolerance       1e-06;','tolerance       1e-12;').replace('tolerance       1e-05;','tolerance       1e-12;');(case/'system/fvSolution').write_text(t)
(case/'constant/momentumTransport').write_text(header('dictionary','momentumTransport')+'simulationType laminar;\n')
(case/'constant/physicalProperties').write_text(header('dictionary','physicalProperties')+'viscosityModel constant; nu .01;\n')
e=dict(os.environ);e.update(json.loads(Path('tools/bluecfd-evaluation/isolated-environment.json').read_text()))
def run(cmd,args=[]):
 with (case/(cmd+'.log')).open('x') as f:r=subprocess.run([str(Path(e['FOAM_APPBIN'])/(cmd+'.exe')),'-case',str(case),*args],env=e,stdout=f,stderr=subprocess.STDOUT)
 print(cmd,r.returncode,flush=True);assert r.returncode==0
run('blockMesh');run('checkMesh',['-allTopology','-allGeometry'])
def body(p):return re.search(r'\n(\d+)\s*\n\(\s*\n(.*?)\n\)',p.read_text(),re.S)[2]
xyz=[tuple(map(float,x.split())) for x in re.findall(r'\(([^()]+)\)',body(case/'constant/polyMesh/points'))];faces=[list(map(int,re.findall(r'\d+',x)))[1:] for x in body(case/'constant/polyMesh/faces').splitlines()]
t=(case/'constant/polyMesh/boundary').read_text();n,start=map(int,re.search(r'inlet\s*\{[^}]*nFaces\s+(\d+);\s*startFace\s+(\d+);',t).groups());assert n==32
profile=[]
for face in faces[start:start+n]:
 y=sum(xyz[i][1] for i in face)/len(face);profile.append(6*y/.1*(1-y/.1))
u=header('volVectorField','U')+'dimensions [0 1 -1 0 0 0 0]; internalField uniform (1 0 0); boundaryField {\n'
u+='inlet {type fixedValue; value nonuniform List<vector> '+str(n)+'\n(\n'+'\n'.join(f'({v:.17g} 0 0)' for v in profile)+'\n); }\n'
u+='outlet {type zeroGradient;} wall {type noSlip;} frontAndBack {type empty;} }\n';(case/'0/U').write_text(u)
(case/'0/p').write_text(header('volScalarField','p')+'dimensions [0 2 -2 0 0 0 0]; internalField uniform 0; boundaryField {inlet {type zeroGradient;} outlet {type fixedValue;value uniform 0;} wall {type zeroGradient;} frontAndBack {type empty;}}\n')
(case/'benchmark-inputs.json').write_text(json.dumps({'scope':'Synthetic analytic benchmark, not project air properties','length_m':1,'height_m':.1,'depth_m':.01,'nx':48,'ny':32,'mean_velocity_m_s':1,'kinematic_viscosity_m2_s':.01,'density_for_pressure_conversion_kg_m3':1.2,'expected_kinematic_pressure_slope':-12,'expected_pressure_slope_Pa_m':-14.4,'profile':'6 Umean y/H (1-y/H), sampled at inlet face centres','verification_relative_target':.01},indent=2)+'\n')
run('foamRun')
