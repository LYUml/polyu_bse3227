# BSE3227 HVAC mini-design

Work in progress. Sources: 01_Assignment_Brief; references: 02_References; drawings: 03_Design_Drawings; report: 04_Final_Report; shared data and scripts: 05_Calculations; tools: 06_Tools.

No design acceptance claimed until native DWG and visual PDF checks are complete.

## Latest review artifacts

Current drawing revision is **v05**, using the unchanged v04 calculation data:
80 diffusers, 20 four-outlet VAV boxes, 49 rigid sections, maximum supply
12000.4 L/s and minimum 4800.1 L/s. v05 moves the four lower upper-zone
outlet annotations away from the horizontal duct and adjusts upper labels.
The current report remains `04_Final_Report/BSE3227_Design_Review_v04.pdf`;
its outstanding-native-reconciliation statement is superseded by the audits below.

`native_reconciliation_v05.json` records actual AutoCAD 2027 reopen/export
comparison of all duct/flex endpoints, diffuser/VAV geometry, 49 section labels,
independent geometric-node flow balance and all 3894 original model entities.
The v05 upper-zone PDF detail was visually inspected after native plotting.
v04 column clearance and friction-chart evidence still applies to unchanged geometry.
Course-method ADPI qualifications remain; final report/package issue is outstanding.
The optional marked-example browser review could not continue on 09 Nov because
the previously available Chrome surface was unavailable. No new course requirements
are inferred from that inaccessible example.

### Historical artifacts (superseded)

- `03_Design_Drawings/BSE3227_HVAC_Review_v02.dwg` and `.pdf`: native A1 review drawing, 30 section IDs and duct schedule; corrected ADPI warning.
- `04_Final_Report/BSE3227_Design_Review_v01.pdf`: six-chapter English calculation review.
- `05_Calculations/data/native_review_v02.json`: native reopen/count audit, airflow reconciliation and unchanged original-source hashes.

The drawing still uses v01 airflow and geometry and is now superseded in design
basis by newly located Canvas Week 8 workshop guidance: 189 W/m2 total cooling,
office sensible heat factor about 0.9, and the explicit course 1400 example
using T0.25/L = 1.0-3.4. See `course_workshop_basis.json` for page locators,
source URLs and technical qualifications. A full recalculation and revised
layout are required; v01/v02 are not submission drawings.
