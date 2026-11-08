# HVAC tool review — 2026-11-08

## Adopted

TomLXXVI/python-hvac, MIT, commit `94247560a667905bfbf67e45a58965a58254fce8`.
https://github.com/TomLXXVI/python-hvac

Reviewed `hvac/fluid_flow/conduit/conduit.py` and `cross_section.py`.
The standalone Serghide friction correlation is adapted in
`05_Calculations/scripts/friction.py`; copyright and licence are retained here.
Rectangular equivalent diameter uses the ASHRAE Huebscher expression, and actual
rectangular velocity uses the actual width times height. The implementation is
checked against iterated Colebrook and published ASHRAE Table 13 points.

Full library installation was attempted in this project's isolated venv. Its
Pandas binary could not load under Windows Application Control. No policy was
changed. Only the reviewed, pure mathematical correlation is used. No claim
that the full HVAC package or its other modules passed validation.

## Reviewed but not adopted

JeremySimonneau/hvac-fitting-loss, MIT, commit
`5158848247c35fb0a45b97a60c392829fac6b6d2`.
https://github.com/JeremySimonneau/hvac-fitting-loss

At this commit, `rectangular_duct_loss` passes hydraulic diameter to
`duct_loss`, which calculates velocity using circular area at that diameter.
For Q=1 m3/s and a 1.0 x 0.5 m duct, actual velocity is 2 m/s, whereas this path
uses approximately 2.865 m/s. It is therefore not used for rectangular sizing.
Fitting tables were not independently validated and are not adopted.

akseidel/WpfaksDuctOMatic, MIT: reviewed project metadata and documented features.
Useful desktop ductulator but not needed alongside reproducible CSV calculations.
https://github.com/akseidel/WpfaksDuctOMatic

## CAD

AutoCAD 2027 Core Console opens isolated copies; the native document path is
checked before writes. No live user document is closed or restarted. Source
DXF export is only an inspection intermediate. Native save/reopen and plot
inspection are separate gates.
