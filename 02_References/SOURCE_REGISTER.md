# Design reference register

## Controlling course evidence found after v02

Canvas Week 8 contains the previously missing workshop notes. The local course
folder was incomplete; earlier statements about missing numeric criteria apply
only to the brief/local inventory, not the full course.

`Space air diffusion design and air duct sizing.pdf`, Canvas file 320901:
https://canvas.polyu.edu.hk/courses/5076/files/320901?module_item_id=124516

- Page 1: office rule-of-thumb cooling allowance 189 W/m2 and office sensible
  heat factor approximately 0.9. These supersede the assumed 120 W/m2 / 0.75.
- Page 4: typical directional-outlet flow 50-150 L/s; check both design and
  minimum flow, with 40% given as an example.
- Page 5: explicitly applies T0.25/L=1.0-3.4 to Krueger 1400, 6-inch neck,
  93 L/s, L=2.4 m, T0.25=3.5 m. This is the adopted course method. The table
  image cites ASHRAE Fundamentals 2005. Record, rather than conceal, the
  manufacturer-pattern discrepancy and 35-160 W/m2 table-band limitation.
- Page 7: office low-pressure supply maximum velocities 10 m/s main and 8 m/s
  branch; recommended low-velocity pressure gradient 0.65-1.23 Pa/m.
- Page 9: supplied ASHRAE 2013 friction chart, density 1.20 kg/m3 and roughness
  0.09 mm.

Verified through Canvas preview text and visual inspection of the ADPI example
and table. Download failed; no local original-file hash is claimed. Structured
transcription: `05_Calculations/data/course_workshop_basis.json`.
v01/v02 calculations and drawings must be recalculated before final release.

Downloaded/reviewed 2026-11-08. Assignment requirements take precedence for
course scope; official regulatory constraints are recorded separately.

| Source | Exact locator | Application |
|---|---|---|
| Assignment brief | pp. 1–2, tasks 1–4 | VAV system; 40% minimum flow; 4–5 outlets per box; flex <=5 m; duct velocity/friction and preferred aspect ratio <=4 |
| Original DWG/Layout PDF | Office label; model geometry | Given 1022 m2 for loads; INSUNITS=4; 45,000 x 30,000 mm external footprint |
| Krueger 2012 performance data | B1-11 and B1-12, metric columns, notes | No-damper horizontal isothermal throws; third value is T0.25. Do not extrapolate below tabulated flow |
| Krueger air distribution engineering | a1-10/11; Type 3 chart | Defines L; specifically describes model 1400 as circular-pattern. This is a material classification issue, not ignored |
| Krueger reference charts | B1-10, footer | Model-specific 80% ADPI charts are at 20 Btuh/ft2; not a universal high-load guarantee |
| ASHRAE Applications 2015 | Ch. 57, Tables 3–4 | Historical louvered category 35–160 W/m2; T0.25/L 1.0–3.4 for ADPI>80. Used as an explicitly provisional course screen pending model-pattern resolution |
| ASHRAE Applications 2019 | Ch. 58, Tables 5–6A and qualifications | Updated low-load guidance, 25/50 W/m2; do not extrapolate to 90 W/m2 maximum load |
| Liu, Clark & Novoselac (2017), supplied paper | Energy and Buildings 134, 271–284; abstract, methods, selection tables | Tests at 25/50 W/m2; does not specify this assignment's load or temperature inputs |
| ASHRAE Fundamentals 2021 | Ch. 21, Figure 9, Eq. 25, Tables 12–13 | Standard-air friction-chart basis, rectangular equivalent diameter, velocity guidance and independent reference points |
| EMSD BEC 2024 | Table 6.4 (printed p.23); 6.7.2–6.7.5; 6.10.6.1–2; 6.11.1/Table 6.11c | Room design condition cross-check; VAV fan power; static-pressure reset; insulation. Fan power compliance cannot be proven without complete fan/system data |
| FSD Circular 2/2023 | Section 3 introduction; 7.1–7.2 (printed pp.10–11); 9.2 (p.13) | Fire-compartment penetration protection; tested flexible duct; normal flex limit 4 m; protect services crossing protected areas |

## Official download URLs

- https://www.krueger-hvac.com/file/3118/1400_51400_M1400_M51400_PublishedPerformanceData.pdf
- https://www.krueger-hvac.com/file/9261/GRD_Engineering.pdf
- https://www.krueger-hvac.com/file/6765/1400FR_ReferenceChart.pdf
- https://handbook.ashrae.org/Handbooks/A15/SI/a15_ch57/a15_ch57_si.aspx
- https://handbook.ashrae.org/Handbooks/A19/SI/A19_Ch58/a19_ch58_si.aspx
- https://handbook.ashrae.org/Handbooks/F21/SI/F21_Ch21/F21_Ch21_si.aspx
- https://www.emsd.gov.hk/beeo/en/pee/BEC_2024_ENG.pdf
- https://www.hkfsd.gov.hk/eng/source/licensing/MECHANICAL_VS_EN_2_2023.pdf

The adopted 120 W/m2 total rule-of-thumb allowance, SHR 0.75, supply temperature
12 C, ceiling 2.7 m, velocity limits 5/4.5 m/s and rigid friction limit 0.8 Pa/m
are preliminary design choices, not invented course instructions or statutory
requirements. Revise if better course or building information becomes available.

Do not confuse the BEC water-pipe friction provision (6.9) with an air-duct limit.
The fan-power limit and sensor set-point are not a duct Pa/m specification.

## Subsequent model-classification correction

The generic louvered ADPI screen in v01 is retired as an acceptance test.
Krueger Engineering a1-11 identifies 1400 as Type 3 circular-pattern. ASHRAE
2015 Ch57 Table 3 gives the circular characteristic length as distance to the
closest wall or intersecting jet. The independent audit is reproduced by
`05_Calculations/scripts/audit_adpi.py`. All 40 current maximum-flow ratios lie
outside both the 60 W/m2 (0.7–1.3) and 125 W/m2 (0.5–1.5) circular table ranges.
These are diagnostic comparisons, not a manufactured prediction at the
assumed 90 W/m2. Neither the initial seven louvered-screen failures nor the
remaining apparent passes establish model-specific ADPI acceptance.

The 2019 round-diffuser ranges at 25 and 50 W/m2 are recorded separately for
the 36 W/m2 minimum case; no exact ADPI percentage is inferred between rows.
The preliminary drawing remains unsuitable for submission until this design
issue is resolved.

## Additional primary-source research, 2026-11-08

- CIBSE Hong Kong, Francis Yik, *Fundamentals, Design & Control of ACMV*:
  https://cibse.org.hk/image/catalog/PDF/ACMV-Fundamentals-Guide-Book-by-Francis-Yik.pdf
  Downloaded as `CIBSE_HK_ACMV_Fundamentals_Yik.pdf`. Table 3.12, printed p.110,
  provides typical Hong Kong office indoor design and internal-gain ranges.
  These inputs are not a whole-building W/m2 cooling allowance and do not
  establish the assignment's intended load. Envelope and ventilation loads
  cannot be silently omitted or counted as room sensible loads.
- Krueger, Dan Int-Hout, *ADPI, Comfort and LEED*, April 2010:
  https://www.krueger-hvac.com/files/white%20papers/white_paper_adpi_comfort_leed.pdf
  Downloaded as `Krueger_ADPI_Comfort_LEED.pdf`. Pages 4-6 discuss graphical
  selection envelopes and include a 1400 example. This is historical engineering
  guidance, not evidence of current LEED or regulatory compliance.
- Local 2026/27 teaching scheme lists a Week 8 mini-design workshop (21/23
  October). No workshop file appears in the current local course inventory.
  The assignment explicitly requests rule-of-thumb cooling load but does not
  state a numeric allowance. Available extracted lecture/tutorial text has
  not yielded an assignment-specific allowance; some PDF font extraction
  warnings prevent claiming a complete visual review of every course page.
