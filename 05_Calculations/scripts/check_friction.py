"""Independent numerical and published reference checks of adopted correlation."""
import json,math
from pathlib import Path
from friction import serghide,round_friction,rectangular
results=[]
for re in [10000,50000,100000,500000,1000000]:
    for eps in [0.00001,0.0001,0.001,0.01]:
        u=7.0
        for _ in range(100):u=-2*math.log10(eps/3.7+2.51*u/re)
        expected=1/u**2;actual=serghide(re,eps)
        error=abs(actual/expected-1)
        assert error<0.0001
        results.append({'Re':re,'relative_roughness':eps,'relative_error':error})
refs=[]
# ASHRAE 2021 Fundamentals Ch21 Table13, 0.8 Pa/m column; rounded diameters.
for q,d in [(240,270),(470,348),(940,452),(1890,590),(4720,834)]:
    actual=round_friction(q/1000,d/1000,roughness=.00012)
    assert abs(actual/.8-1)<.04,(q,d,actual)
    refs.append({'flow_lps':q,'diameter_mm':d,'reference_Pa_m':.8,'calculated_Pa_m':actual})
assert rectangular(1000,1000,500)['velocity_ms']==2
p=Path(__file__).resolve().parents[2]/'05_Calculations/data/friction_validation.json'
p.write_text(json.dumps({'colebrook_cases':results,'ASHRAE_table13_checks':refs,'rectangular_velocity_check_ms':2.0},indent=2))
print('20 Colebrook comparisons and 5 ASHRAE Table 13 points passed.')
