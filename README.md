# BSE3227 HVAC mini-design

Work in progress. Sources: 01_Assignment_Brief; references: 02_References; drawings: 03_Design_Drawings; report: 04_Final_Report; shared data and scripts: 05_Calculations; tools: 06_Tools.

No design acceptance claimed until native DWG and visual PDF checks are complete.

## Latest review artifacts

Current course-basis revision is **v04**: 80 diffusers, 20 four-outlet VAV
boxes, 49 rigid sections, maximum supply 12000.4 L/s and minimum 4800.1 L/s.
The v04 DWG/PDF are in `03_Design_Drawings`; the matching 12-page report is
`04_Final_Report/BSE3227_Design_Review_v04.pdf`. Both airflow conditions pass
the explicitly adopted workshop ratio screen. Manufacturer/table applicability
qualifications remain recorded, not converted into a general compliance claim.
Native counts and flow reconciliation are in `native_review_v04.json`.
v04 fixes an overlapping upper branch, clears the nine identified column
footprints in plan, and includes original friction-chart cross-check evidence.
Detailed native geometry/annotation reconciliation and final package issue
remain outstanding. v01-v03 are superseded history.

- `03_Design_Drawings/BSE3227_HVAC_Review_v02.dwg` and `.pdf`: native A1 review drawing, 30 section IDs and duct schedule; corrected ADPI warning.
- `04_Final_Report/BSE3227_Design_Review_v01.pdf`: six-chapter English calculation review.
- `05_Calculations/data/native_review_v02.json`: native reopen/count audit, airflow reconciliation and unchanged original-source hashes.

The drawing still uses v01 airflow and geometry and is now superseded in design
basis by newly located Canvas Week 8 workshop guidance: 189 W/m2 total cooling,
office sensible heat factor about 0.9, and the explicit course 1400 example
using T0.25/L = 1.0-3.4. See `course_workshop_basis.json` for page locators,
source URLs and technical qualifications. A full recalculation and revised
layout are required; v01/v02 are not submission drawings.
