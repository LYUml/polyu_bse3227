# BSE3227 v06 acceptance evidence

Checked against the original two-page assignment on 09 Nov 2026. User acceptance
is still pending; preparation and verification of the review package are complete.

| Requirement | Evidence |
|---|---|
| Task 1: rule-of-thumb load and total airflow | Report chapters 1-2; course_workshop_basis.json cites lecturer p.1; acceptance_audit_v06.json recomputes load and airflow |
| Task 1: layout, per-outlet flow, L, model, T0.25 and T/L | Native drawing; report chapter 3 and appendices A/C; 80 rows in diffusers_v04.csv; all four L values printed |
| Task 1/2: maximum and 40% checks | 160 catalogue interpolations without extrapolation and 640 directional ratio checks recomputed by audit_acceptance_v06.py; course range 1.0-3.4; applicability qualification on report p.1 |
| Task 3: connected single-line supply layout | 49 native rigid lines and 80 flex lines reconciled to shared data; independent geometric-node flow balance in native_reconciliation_v06.json |
| Task 3: 4-5 outlets/VAV, flex within 5 m | 20 groups of four; all 80 plan lengths plus 0.50 m allowance independently recomputed; maximum 2.607 m also within adopted FSD 4 m limit |
| Task 3: straight runs and distribution branches | Plan shows direct flex routes and straight distribution runs with short VAV take-offs; no duplicate collinear rigid paths; nine source column footprints clear in plan |
| Task 4: each main/branch sized and labelled | 49 native labels matched; all sections in drawing table and report Appendix B; actual rectangular velocity, equivalent circular friction and aspect ratio recomputed |
| Task 4: velocity, friction and aspect limits | Main 10 m/s, branch 8 m/s, friction 0.8 Pa/m, aspect <=4; all sections pass; chosen limits linked to course workshop pp.7-9 |
| Task 4: ASHRAE friction-chart basis | Official chart reproduced in report Appendix D, four graphical cross-checks; correlation also validated against Colebrook and ASHRAE reference points |
| Native AutoCAD 2027 and source preservation | Native reopen/count audit plus coordinate/geometry comparison; all 3894 original model entities preserved; all four original manifest file hashes match |
| Units, scale, layers and actual sample | Sample DWG and sample_cad.py predate full layouts; cached native result (4 6 3) = mm, six polylines/three diffusers, three texts; native v06 INSUNITS=4; plot command 1:100 on A1; PDF scale bar visually reviewed |
| Independent print-quality review | visual_review_v06.json binds inspected drawing/report PDFs to SHA-256; 15 report pages rendered and inspected separately from DWG validation |
| Reproducibility and Git conventions | Shared v04 data, versioned v06 drawing/report scripts, preserved originals, numbered folders and date-prefixed commits; latest package pushed to the requested repository |

## Declared design boundaries

The lecturer's workshop explicitly applies the louvered ratio range to model 1400,
while manufacturer engineering guidance labels it Type 3 circular. The workshop
table band ends at 160 W/m2, below the adopted 170.1 W/m2 sensible allowance.
This package transparently follows the course example; it does not silently claim
an independent manufacturer/ASHRAE comfort certification.

24/12 C room/supply temperatures and 2.7 m ceiling height are assumptions. Eight
upper outlets require ceiling-grid coordination. VAV outlines are schematic, and
beam/headroom clearance and AHU corridor fire-protection details require later
coordination. Full fitting pressure totals and fan selection are outside the brief's
specified supply-section sizing task. The optional marked drawing example could
not be revisited when the Chrome surface became unavailable; no additional
requirements have been invented from it. No email or Canvas submission was sent.
