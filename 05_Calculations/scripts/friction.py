"""Reviewed Serghide correlation adapted from python-hvac, MIT.
Source: TomLXXVI/python-hvac, commit 94247560a667905bfbf67e45a58965a58254fce8,
hvac/fluid_flow/conduit/conduit.py, Conduit._serghide.
Copyright (c) 2023 Tom Christiaens. See 06_Tools/python-hvac-LICENSE.md.
Only the pure mathematical function is reused; no claim of full-package validation.
"""
import math

def serghide(reynolds, relative_roughness):
    if reynolds <= 0: return 0.0
    a=-2*math.log10(relative_roughness/3.7+12/reynolds)
    b=-2*math.log10(relative_roughness/3.7+2.51*a/reynolds)
    c=-2*math.log10(relative_roughness/3.7+2.51*b/reynolds)
    return (a-(b-a)**2/(c-2*b+a))**-2

def round_friction(q_m3s, diameter_m, rho=1.204, mu=1.81e-5, roughness=0.00009):
    v=q_m3s/(math.pi*diameter_m**2/4)
    re=rho*v*diameter_m/mu
    f=serghide(re,roughness/diameter_m)
    return f*rho*v*v/(2*diameter_m)

def rectangular(q_lps,w_mm,h_mm):
    w,h=w_mm/1000,h_mm/1000
    de=1.30*(w*h)**0.625/(w+h)**0.25
    return {'velocity_ms':q_lps/1000/(w*h), 'equivalent_diameter_mm':de*1000,
            'friction_Pa_m':round_friction(q_lps/1000,de), 'aspect_ratio':max(w,h)/min(w,h)}

def select(q_lps, velocity_limit=5.0, friction_limit=0.8):
    candidates=[]
    for h in range(200,1050,50):
        for w in range(h,min(4*h,2200)+1,50):
            r=rectangular(q_lps,w,h)
            if r['velocity_ms']<=velocity_limit and r['friction_Pa_m']<=friction_limit:
                candidates.append((w*h,abs(w/h-2),w,h,r))
    _,_,w,h,r=min(candidates)
    return {'width_mm':w,'height_mm':h,**r}
