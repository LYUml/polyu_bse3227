# BSE3227 HVAC mini-design

## Current acceptance package — v06

Prepared for user acceptance against the four tasks in the assignment brief.

- Editable AutoCAD drawing: [BSE3227_HVAC_Acceptance_v06.dwg](03_Design_Drawings/BSE3227_HVAC_Acceptance_v06.dwg)
- A1 landscape plan, 1:100: [drawing PDF](03_Design_Drawings/BSE3227_HVAC_Acceptance_v06.pdf)
- 15-page English report: [report PDF](04_Final_Report/BSE3227_Design_Acceptance_v06.pdf)
- [Requirement-by-requirement evidence](04_Final_Report/ACCEPTANCE_CHECKLIST.md)

80 diffusers; 20 VAV boxes with four outlets each; 49 rigid duct sections.
Course allowance 189 W/m2, SHF 0.9, printed area 1022 m2; total cooling
193.158 kW; maximum/minimum supply 12000.4/4800.1 L/s. Maximum calculated
flex length 2.607 m. Both flow conditions pass the adopted course ratio screen.

The report explicitly records the difference between the lecturer's model-1400
example and manufacturer pattern classification, and the table's load-band limit.
Results are course-method checks, not independently certified ADPI. Room/supply
temperatures and ceiling height are declared assumptions. Ceiling-grid coordination,
beam levels and corridor fire protection remain design coordination notes; the
assignment supply layout does not constitute a construction package or fan selection.

## Reproduction and evidence

Shared engineering data is `05_Calculations/data/*_v04.csv` and
`design_basis_v04.json`. v05/v06 change drawing annotations and report content,
not engineering values. With Python dependencies and AutoCAD 2027 installed:

```powershell
.venv/Scripts/python.exe 05_Calculations/scripts/build_design_v04.py
.venv/Scripts/python.exe 05_Calculations/scripts/draw_acceptance_v06.py
.venv/Scripts/python.exe 05_Calculations/scripts/reconcile_native_v06.py
.venv/Scripts/python.exe 05_Calculations/scripts/verify_acceptance_v06.py
.venv/Scripts/python.exe 05_Calculations/scripts/build_report_v06.py
.venv/Scripts/python.exe 05_Calculations/scripts/audit_acceptance_v06.py
```

Native geometry reconciliation, source hashes, calculation audit and dated visual
review evidence are in `05_Calculations/data/*v06.json`. Rerender and visually
review PDFs after any regeneration; successful commands do not prove print quality.

## Repository conventions

Originals: `01_Assignment_Brief`; references and exact source register:
`02_References`; drawings: `03_Design_Drawings`; report: `04_Final_Report`;
versioned calculations/CAD copies: `05_Calculations`; reviewed tool licences:
`06_Tools`. Date-prefixed Git commits follow the BSE3124 project convention.
Original files remain unchanged. Earlier v01-v05 deliverables are retained history,
not the current package. In particular, the provisional 120 W/m2 basis is superseded.
