# BSE3227 · HVAC handover

[Design report (PDF, 17 pages)](BSE3227_Group7_report.pdf) · [Editable LaTeX package](BSE3227_LaTeX.zip) · [Project index](../README.md)

The submitted design uses a 24 °C room temperature and 13 °C supply air, with 80 diffusers, 20 VAV groups and 47 rigid duct sections. Appendix E describes the manufacturer assessment.

## Drawings

| Sheet | AutoCAD source | Plotted sheet |
| --- | --- | --- |
| Supply air distribution | [Edit DWG](Drawings/Supply%20Air%20Distribution.dwg) | [View PDF](Drawings/Supply%20Air%20Distribution.pdf) |
| VAV connection schedule | [Edit DWG](Drawings/VAV%20Connection%20Schedule.dwg) | [View PDF](Drawings/VAV%20Connection%20Schedule.pdf) |

## Calculation tables

- [Diffuser coordinates and airflows](Calculations/Grid%20locations.csv)
- [Directional throw and characteristic lengths](Calculations/Diffuser%20Course%20Ratio%20Check.csv)
- [VAV connections and group airflows](Calculations/VAV%20Connection%20Schedule.csv)
- [Duct sizes, velocities and friction](Calculations/Duct%20Sizing.csv)

- [Online Ductulator results by section](Calculations/Online%20Ductulator%20Check.csv)

## Updating the package

Edit the DWG for the affected sheet and export its PDF. For changes to dimensions, locations or airflows, update the corresponding calculation rows and report figures. The supply air plan appears on page 16. Edit the [LaTeX sections](../04_Final_Report/LaTeX/sections/) and follow the [build instructions](../04_Final_Report/LaTeX/README.md).