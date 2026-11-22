# Open-plan Office Air-conditioning Design

BSE3227: HVACR 1

HUANG Celine 24034414D  ·   LUO Qianyu 24114977D  ·   LYU Mingliang 24099296D

RIOBA Ann Muniko 24114901D  ·   XIE Jingxuan 24110957D

## 1. Introduction and design basis

### 1.1 Design objective

The L-shaped office is arranged around the service core, where a variable air volume (VAV) system supplies the open floor and its adjacent section, the wing, through four-way ceiling diffusers. Each VAV box serves four outlets and reduces airflow as the cooling load decreases, making how far the air travels at both peak and minimum flow the key factor in choosing the right diffuser. 

### 1.2 Office layout and design conditions

The supplied plan annotation of 1022 m² is used for the rule-of-thumb load calculation, whereas the interpreted CAD boundary is used to determine diffuser locations and directional lengths. This layout contains 80 diffusers, 20 VAV groups and 47 supply duct sections.

Table 1. Principal design inputs.

| Parameter | Adopted value |
| --- | --- |
| Office load area | 1022 m2, supplied plan |
| Cooling allowance / sensible factor | 189 W/m2 / 0.90, preliminary office allowance |
| Room / supply temperature | 24 °C room; 13 °C supply selected for this design |
| Density / specific heat | 1.20 kg/m3 / 1006 J/(kg K) |
| Minimum airflow | 40% of maximum |
| Diffuser family / neck | 1400/51400 four-cone, 600 x 600 mm / 8 inch |
| Ordinary flexible-connection design cap | 4.00 m; additional routing allowance 0.50 m |
### 1.3 Design operating range

The drawing prefix SD denotes a supply diffuser. At peak load, the office requires 13.09 m³/s of supply air, and at minimum flow, the same outlets supply 5.24 m³/s. Additionally, the facing outlets in the wing determine the peak throw check, while the southward throw at SD-60 determines the minimum flow check, and these locations are examined in Sections 3 and 4.

This ceiling layout serves two different conditions. At full load, the wing outlets receive some of the largest airflows on the floor, allowing their jets to reach the midpoint between neighbouring panels. Conversely, at low load, the room size remains constant, but the air does not reach as far. Therefore, the distance to nearby walls and other outlets also affects performance alongside the floor-wide average flow.

To illustrate the layout mentioned above, the distribution drawing on page 16 shows how the main duct follows the floor plan before connecting to the terminal boxes. The outlet and duct labels on that drawing identify the corresponding data in the schedules, making a single air path clearly visible from the AHU to its four ceiling panels.

## 2. Cooling load and airflow distribution (Task 1)

### 2.1 Preliminary thermal balance

The selected base design uses an office cooling allowance of 189 W/m² and an approximate sensible heat factor of 0.90. Since BEC 2024 [6, p. 85] uses an 11 K room-to-supply temperature difference for calculating the design supply airflow of the reference building, this difference is applied to the office to select a design supply air temperature of 24-11=13 °C. Table 2 uses this selected value to calculate the sensible heat balance.

Table 2. Thermal balance and supply airflow.

| Calculation | Result |
| --- | --- |
| Total cooling = 1022 x 189 | 193.158 kW thermal |
| Sensible cooling = 193.158 x 0.90 | 173.8422 kW thermal |
| Q = sensible W / [density x cp x (24 - 13)] | 13091.316 L/s |
| Minimum supply = 0.40 x maximum | 5236.526 L/s |

At the selected 11 K temperature difference, each cubic metre per second of supply air removes about 13.28 kW of sensible heat. Therefore, the office needs 13.09 m³/s to carry its 173.84 kW sensible load. The remaining cooling duty is latent and is not included in this airflow calculation.

### 2.2 Diffuser distribution and VAV grouping

Larger service areas are assigned a larger share of floor airflow, and the four outlet flows on each box add up to its design airflow (Appendix C).

Each of the 80 diffusers fits inside a distinct ceiling tile within its assigned area, as shown in Figure 3.

The service-cell areas are scaled to the annotated floor area before allocating the sensible cooling load. For SD-77, the allocated area is 15.7843 m², and its peak flow is 13091.316 × 15.7843 / 1022 = 202.19 L/s, with Appendix A listing the resulting different outlet flows.

Dividing the floor total equally gives 163.64 L/s per outlet. While this average works for an estimate, it would not provide enough air for large zones such as SD-77. By scaling airflow by area, SD-77 requires about 38.55 L/s more than the average without changing the total floor airflow. As a result, this difference changes both the terminal-box airflow and the peak throw at this outlet.

### 2.3 Characteristic length

In each of the four discharge directions, the characteristic length is defined as the shorter distance to either the office boundary or the midpoint between opposing outlets, and these four lengths are listed in Appendix B. For the facing pair SD-77 and SD-78, the 3.000 m centre spacing gives L = 1.500 m in the opposing directions, while the same outlet has a separate length north, south and west. Changing the service area changes its airflow and throw, whereas changing the tile position changes these lengths even at the same flow. Appendix A and Appendix B record the two inputs separately.

## 3. Diffuser selection and peak throw (Task 1)

### 3.1 Neck selection on the adopted ceiling grid

The Krueger 1400/51400 four-cone outlet distributes supply air along both ceiling axes. For the 600 mm square panel without a damper, the metric catalogue tables [2] were compared at the same outlet positions and flows. Specifically, for each operating flow, the third horizontal isothermal throw was interpolated between adjacent catalogue rows and divided by the directional length. Peak outlet flows range from 134.22 to 202.19 L/s, and the minimum flows range from 53.69 to 80.88 L/s.

Table 3. Neck comparison using the adopted flows and geometry.

| Neck | Lowest T/L | Highest T/L | Selection consequence |
| --- | --- | --- | --- |
| 6 inch | 1.2078 | 3.4476 | Peak flow approaches catalogue maximum of 204 L/s. |
| 8 inch | 1.1608 | 3.4 (rounded) | Retains minimum-flow reach with a smaller peak exceedance. |
| 10 inch | 0.9724 | 3.4325 | Falls below 1.0 at minimum flow. |

The 12-, 14- and 15-inch tables begin at 74, 101 and 116 L/s respectively, which is above the lowest required flow. At the highest outlet flow of 202.19 L/s, the 6-inch neck is already close to its last catalogue row (204 L/s). On the other hand, increasing the neck to 10 inches creates a different issue, as its lowest throw ratio decreases to 0.9724 at turndown. Therefore, the selected 8-inch neck keeps the low-flow ratio above 1.0, although the two facing wing outlets still slightly exceed the upper limit at peak flow.

### 3.2 Peak-load check

For SD-77 east and SD-78 west, the catalogue throw lies between 5.1 m at 198 L/s and 5.5 m at 231 L/s, giving T_{0.25}=5.1+(202.189-198)(0.4/33)=5.151 m. Dividing this value by 1.500 m gives a peak ratio of 3.4 to one decimal place, although the unrounded value in Appendix A slightly exceeds the selection limit of 3.4.

Figure 1. Peak throw and opposing-outlet midpoint at SD-77.

On this pair of tiles, the upper ratio corresponds to a catalogue throw of 3.4 × 1.500 = 5.100 m, which shows that the interpolated throw reaches about 51 mm beyond that value. This is a catalogue margin at the midpoint.

## 4. Air distribution at 40% flow (Task 2)

### 4.1 Minimum flow and catalogue interpolation

The VAV minimum for each outlet is set at 40% of its own peak allocation, reducing the total supply to 5236.526 L/s. Although the diffuser size and characteristic lengths remain unchanged, the throw changes with flow. These operating values for every outlet are provided in Appendix A. 

South of SD-60, the minimum supply is 0.40 × 137.76 = 55.104 L/s. The 8-inch catalogue gives throws of 1.5 m and 2.9 m at 33 L/s and 66 L/s, so linear interpolation gives 1.5+(55.104-33)(2.9-1.5)/33 = 2.438 m. With L = 2.100 m, the unrounded ratio is 1.1608, which is the lowest of the minimum-flow directions.

A proportional reduction in airflow does not produce the same percentage drop in throw. At SD-60, the peak flow of 137.76 L/s lies between the 132 and 165 L/s catalogue rows and gives about 4.27 m of throw. However, reducing the airflow to 40% leaves about 57% of this peak throw. Scaling the peak throw directly by 0.40 would give only 1.71 m and would reverse the conclusion for the 2.10 m southward path. Therefore, a second catalogue interpolation is used for every outlet in the minimum condition. 

### 4.2 Interpretation across the operating range

Minimum-flow directional ratios range from 1.1608 to 2.1437 and satisfy the target selection interval. However, the controlling location changes as the VAV boxes throttle. At peak flow, the two wing outlets discharge towards a midpoint only 1.500 m away, whereas at minimum flow, SD-60 still needs to supply 2.100 m to the south. As a result, a smaller low-flow margin is left due to its 2.438 m catalogue throw, in comparison with other directions (Figure 2).

Figure 2. Peak upper and minimum-flow lower directional ratios by diffuser.

The ASHRAE selection table shown in the course design guide applies the 1.0–3.4 interval to a louvered ceiling diffuser for cooling loads between 35 and 160 W/m². Assuming the sensible cooling load is directly proportional to the airflow, the minimum load is 68.04 W/m², whereas the peak load of 170.1 W/m² is above the table range, making the peak comparison serve only as a guide, as stated in Appendix E's separate manufacturer assessment. In practice, the point of interest at low flow is the end of the longer paths, and for SD-60, the catalogue throw is about 0.34 m longer than the southern reference distance. Conversely, at peak load, the concern shifts to the overlapping jets due to the facing outlets in the wing.

## 5. VAV zoning and duct layout (Task 3)

Figure 3. Grid-aligned diffuser arrangement and 20 four-outlet VAV groups.

Each panel occupies a full ceiling tile within its assigned service cell, and each VAV box serves four outlets. The coordinate layout in Figure 3 defines the directional lengths that are listed in Appendix B.

### 5.1 Supply route to the office wing

The supply trunk begins at the air-handling unit and continues through A-01, A-02 and A-03. At the trunk split, D-22 and D-23 carry 1549.78 L/s for both wing boxes. Further downstream, D-24 carries the remaining 766.49 L/s to D-44, the final duct connection to VAV-20. At this box, four flexible branch ducts feed SD-75, SD-76, SD-79 and SD-80, with Appendix C showing their combined minimum flow as 306.6 L/s.

At the VAV-19 branch, the branch duct size decreases from 600 × 400 mm on D-23 to 450 × 300 mm on D-24, since at that point the branch carries airflow only for the four outlets supplied by VAV-20. Meanwhile, the VAV-20 plan connections range from 2.918 to 3.083 m, and adding the 0.50 m routing allowance to the longest flexible duct gives 3.583 m, which remains within both the selected 4 m cap and the 5 m project limit. In addition, clearance should be maintained for the final routing, and fire-resisting barriers should be avoided [1].

Figure 4. Peak airflow at the wing branch point. The remaining branch serves VAV-20.

At the branch, 783.3 L/s leaves the shared duct for VAV-19, while the remaining flow continuing to VAV-20 divides again at the box, where SD-75 and SD-76 each receive 189.46 L/s, SD-79 receives 202.19 L/s and SD-80 receives 185.40 L/s. Overall, the sum of these four outlet flows matches the branch airflow shown on the drawing.

## 6. Main and branch duct sizing (Task 4)

### 6.1 Airflow and available cross-section

Each duct section carries the sum of its downstream peak flows, and its width and depth determine the air velocity through v = Q / (WH), where W and H are in metres. The design velocity limits are 10 m/s for main ducts and 8 m/s for branch ducts, combined with a width-to-depth ratio of up to 4:1. In addition, a 600 mm depth cap and a 1.0 Pa/m friction target guide duct selection, while the upper friction is limited at 1.23 Pa/m.

A-01 carries the entire 13.0913 m³/s, and thus, at 10 m/s, the minimum duct area is 1.3091 m². With a 600 mm depth, this requires at least 2.182 m of width, and selecting 2200 × 600 mm gives 9.918 m/s and a 3.67:1 width-to-depth ratio. For the branch serving VAV-20, D-44 carries 0.7665 m³/s through a 450 × 300 mm section, giving 5.678 m/s against its 8 m/s limit.

### 6.2 Straight-duct friction

The drawing provides the equivalent-round Darcy friction gradient at a surface roughness of 0.09 mm. Each section was checked independently in the metric Online Ductulator [5] using the same peak flow and rectangular dimensions, and Appendix D lists both friction results for every section.

Table 4. Fixed-section check against Online Ductulator [5].

| Section | Size (mm) | Online m/s | Online Pa/m | Darcy Pa/m |
| --- | --- | --- | --- | --- |
| A-01 | 2200 × 600 | 9.9 | 0.877 | 0.9023 |
| D-08 | 1350 × 600 | 9.7 | 0.979 | 0.9995 |
| D-44 | 450 × 300 | 5.7 | 0.980 | 0.9990 |

The largest displayed online friction gradient is 0.980 Pa/m at D-24 and D-44, while D-08 governs the Darcy check at 0.9995 Pa/m, and both maximum values remain below 1.23 Pa/m. D-44 explains how important the branch schedule is, as it carries only 0.7665 m³/s, but its smaller cross-section gives a higher online friction gradient than the full-flow trunk A-01. However, since these are straight-section pressure gradients, the duct depth and width must still be checked against beams, insulation and crossing services.

Figure 5. Bare duct cross-sections drawn to a common scale.

A-01 and D-08 both reach the 600 mm depth cap, and their different widths adjust for the drop in airflow downstream. In contrast, D-44 carries much less air and can use a smaller duct depth. On the common trunk, any loss of usable width at a beam or service crossing reduces the area available at the selected depth. Therefore, the 2200 mm width is essential when coordinating the ceiling as well as when calculating velocity.

## 7. Design assessment

### 7.1 Air distribution

The diffuser panel fits the 600 mm ceiling module, and the 8-inch neck maintains adequate throw at the 40% VAV setting. At peak flow, the facing jets from SD-77 and SD-78 have the smallest margin, as their catalogue throw of 5.151 m gives a ratio just above 3.4 at the 1.500 m midpoint. However, at minimum flow the limiting outlet changes to SD-60, where the southward ratio remains above 1.0. These results are derived from the catalogue isothermal throw and the load range outlined in Section 4.

### 7.2 Ductwork and ceiling coordination

The common trunk carries 13.09 m³/s through a 2200 × 600 mm section, and the resulting velocity of 9.918 m/s leaves little margin below the 10 m/s main-duct limit. For the friction check, however, the branch with the largest Darcy friction gradient is D-08, which Table 5 identifies separately from the trunk that sets the maximum velocity.

In addition, while the 600 mm nominal duct depth sets the space required by the bare duct, installation also requires clearance for insulation, flanges and supports where the trunk passes beams or other services. Similarly, the longest flexible connection allows 0.50 m beyond its plan length for routing, which requires a coordinated ceiling section to establish the available clearance and the installed drop.

Table 5. Worst operating cases.

| Quantity | Location | Value | Limit |
| --- | --- | --- | --- |
| Highest speed | A-01–03 | 9.918 m/s | 10 m/s |
| Highest Darcy friction | D-08 | 0.9995 Pa/m | 1.23 Pa/m |
| Peak outlet flow | SD-77 and SD-78 | 202.19 L/s | Table to 297 |
| Lowest ratio | SD-60 south | 1.1608 | 1.0 min |
| Highest ratio | SD-77 and SD-78 | 3.4 (rounded) | 3.4 max |
| Longest conditional flex | VAV-20 | 3.583 m | 4.00 m |
### 7.3 Implications for detailed design

The most critical ceiling locations are the common trunk and the wing outlets, for different reasons. At A-01, the calculated air velocity is already close to the 10 m/s limit, meaning a local reduction in cross-section to clear another service would increase both velocity and friction. Therefore, the coordinated detail should maintain the required area or be checked at the full 13.09 m³/s.

At SD-77 and SD-78, the critical dimension is the spacing between centres, since a change to either tile affects both the facing throw ratio and the distances in the other discharge directions. In addition, the 8-inch selection also depends on the minimum airflow settings at the VAV boxes. For this reason, the individual outlet flows in Appendix A, together with the group totals in Appendix C, serve as the appropriate reference values for balancing.

Furthermore, the straight-duct friction gradients in Table 5 identify where friction loss per metre is greatest. However, selecting the fan would also require the duct lengths and fitting losses along each complete path, together with the pressure drops through the AHU and terminal equipment, as the section with the highest gradient alone does not identify the critical path.

## References

[1] Fire Services Department, Fire Safety Requirements for Mechanical Ventilating Systems, FSD Circular Letter no. 2/2023. Hong Kong: Government of the Hong Kong Special Administrative Region, Jun. 7, 2023, paras. 7.2-7.4. Accessed: Nov. 17, 2026. [Online]. Available: https://www.hkfsd.gov.hk/eng/source/licensing/MECHANICAL_VS_EN_2_2023.pdf

[2] Krueger, “1400, 51400, M1400, M51400 published performance data,” 2012, p. B1-12. Accessed: Nov. 17, 2026. [Online]. Available: https://www.krueger-hvac.com/file/3118/1400_51400_M1400_M51400_PublishedPerformanceData.pdf

[3] Krueger, “K-Select selection software.” Accessed: Nov. 17, 2026. [Online]. Available: https://www.krueger-hvac.com/public/software/k-select

[4] Krueger, “Air distribution engineering,” 2012, pp. a1-9-a1-11. Accessed: Nov. 17, 2026. [Online]. Available: https://www.krueger-hvac.com/file/9261/GRD_Engineering.pdf

[5] Ductulator.com, “Ductulator (Metric).” Accessed: Nov. 17, 2026. [Online]. Available: https://ductulator.com/metric/

[6] Electrical and Mechanical Services Department, Code of Practice for Energy Efficiency of Building Services Installation, 2024 ed. Hong Kong: Government of the Hong Kong Special Administrative Region, 2024, sec. 6. Accessed: Nov. 17, 2026. [Online]. Available: https://www.emsd.gov.hk/beeo/en/pee/BEC_2024_ENG.pdf

## Appendix A. Diffuser operating schedule

Table A1. Original-catalogue flows, throws and directional ratio extremes.

| Outlet | Qmax L/s | Qmin L/s | Tmax m | Tmin m | Upper T/L | Lower T/L |
| --- | --- | --- | --- | --- | --- | --- |
| SD-01 | 144.23 | 57.69 | 4.348 | 2.547 | 2.7347 | 1.2131 |
| SD-02 | 161.26 | 64.50 | 4.555 | 2.837 | 2.8646 | 1.5759 |
| SD-03 | 161.26 | 64.50 | 4.555 | 2.837 | 2.8646 | 1.5759 |
| SD-04 | 153.79 | 61.52 | 4.464 | 2.710 | 2.8077 | 1.5055 |
| SD-05 | 155.23 | 62.09 | 4.482 | 2.734 | 2.8186 | 1.3020 |
| SD-06 | 161.26 | 64.50 | 4.555 | 2.837 | 2.8646 | 1.3507 |
| SD-07 | 161.26 | 64.50 | 4.555 | 2.837 | 2.8646 | 1.5759 |
| SD-08 | 171.51 | 68.60 | 4.699 | 2.955 | 2.9551 | 1.2313 |
| SD-09 | 167.54 | 67.02 | 4.638 | 2.922 | 3.0923 | 1.2173 |
| SD-10 | 151.25 | 60.50 | 4.433 | 2.667 | 2.9556 | 1.4815 |
| SD-11 | 151.25 | 60.50 | 4.433 | 2.667 | 2.7883 | 1.4815 |
| SD-12 | 134.22 | 53.69 | 4.227 | 2.378 | 2.6584 | 1.3209 |
| SD-13 | 161.26 | 64.50 | 4.555 | 2.837 | 2.5304 | 1.3507 |
| SD-14 | 161.26 | 64.50 | 4.555 | 2.837 | 2.5304 | 1.5759 |
| SD-15 | 161.26 | 64.50 | 4.555 | 2.837 | 2.5304 | 1.5759 |
| SD-16 | 161.26 | 64.50 | 4.555 | 2.837 | 2.5304 | 1.5759 |
| SD-17 | 161.26 | 64.50 | 4.555 | 2.837 | 2.5304 | 1.3507 |
| SD-18 | 161.26 | 64.50 | 4.555 | 2.837 | 2.5304 | 1.3507 |
| SD-19 | 161.26 | 64.50 | 4.555 | 2.837 | 2.5304 | 1.5759 |
| SD-20 | 178.77 | 71.51 | 4.809 | 3.017 | 2.6715 | 1.2570 |
| SD-21 | 173.77 | 69.51 | 4.733 | 2.974 | 3.1552 | 1.2393 |
| SD-22 | 151.25 | 60.50 | 4.433 | 2.667 | 2.9556 | 1.4815 |
| SD-23 | 151.25 | 60.50 | 4.433 | 2.667 | 2.4630 | 1.4815 |
| SD-24 | 151.25 | 60.50 | 4.433 | 2.667 | 2.5479 | 1.4815 |
| SD-25 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.3507 |
| SD-26 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.5759 |
| SD-27 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.5759 |
| SD-28 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.5759 |
| SD-29 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.3507 |
| SD-30 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.3507 |
| SD-31 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.5759 |
| SD-32 | 178.77 | 71.51 | 4.809 | 3.017 | 3.2058 | 1.2570 |
| SD-33 | 173.77 | 69.51 | 4.733 | 2.974 | 3.1552 | 1.2393 |
| SD-34 | 151.25 | 60.50 | 4.433 | 2.667 | 2.9556 | 1.4815 |
| SD-35 | 151.25 | 60.50 | 4.433 | 2.667 | 2.9556 | 1.4815 |
| SD-36 | 151.25 | 60.50 | 4.433 | 2.667 | 2.9556 | 1.4815 |
| SD-37 | 176.06 | 70.43 | 4.768 | 2.994 | 3.1784 | 1.4256 |
| SD-38 | 176.06 | 70.43 | 4.768 | 2.994 | 3.1784 | 1.4257 |
| SD-39 | 176.06 | 70.43 | 4.768 | 2.994 | 3.1784 | 1.4257 |
| SD-40 | 176.06 | 70.43 | 4.768 | 2.994 | 3.1784 | 1.4257 |
## Appendix A. Diffuser operating schedule (continued)

Table A1. Original-catalogue flows, throws and directional ratio extremes.

| Outlet | Qmax L/s | Qmin L/s | Tmax m | Tmin m | Upper T/L | Lower T/L |
| --- | --- | --- | --- | --- | --- | --- |
| SD-41 | 176.06 | 70.43 | 4.768 | 2.994 | 3.1784 | 1.4257 |
| SD-42 | 176.06 | 70.43 | 4.768 | 2.994 | 3.1784 | 1.4257 |
| SD-43 | 176.06 | 70.43 | 4.768 | 2.994 | 3.1784 | 1.4257 |
| SD-44 | 195.18 | 78.07 | 5.057 | 3.156 | 3.3715 | 1.3150 |
| SD-45 | 189.72 | 75.89 | 4.975 | 3.110 | 3.3164 | 1.2957 |
| SD-46 | 165.14 | 66.06 | 4.602 | 2.901 | 3.0681 | 1.3815 |
| SD-47 | 165.14 | 66.06 | 4.602 | 2.901 | 3.0681 | 1.3815 |
| SD-48 | 165.14 | 66.06 | 4.602 | 2.901 | 3.0681 | 1.3815 |
| SD-49 | 147.77 | 59.11 | 4.391 | 2.608 | 2.9274 | 1.2417 |
| SD-50 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.3507 |
| SD-51 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.3507 |
| SD-52 | 152.37 | 60.95 | 4.447 | 2.686 | 2.9646 | 1.2789 |
| SD-53 | 154.08 | 61.63 | 4.468 | 2.715 | 2.9785 | 1.2927 |
| SD-54 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.3507 |
| SD-55 | 161.26 | 64.50 | 4.555 | 2.837 | 3.0365 | 1.3507 |
| SD-56 | 170.12 | 68.05 | 4.678 | 2.943 | 3.1184 | 1.2264 |
| SD-57 | 166.35 | 66.54 | 4.620 | 2.911 | 3.0803 | 1.2131 |
| SD-58 | 151.25 | 60.50 | 4.433 | 2.667 | 2.9556 | 1.2699 |
| SD-59 | 151.25 | 60.50 | 4.433 | 2.667 | 2.9556 | 1.2699 |
| SD-60 | 137.76 | 55.10 | 4.270 | 2.438 | 2.8465 | 1.1608 |
| SD-61 | 146.46 | 58.58 | 4.375 | 2.585 | 2.9168 | 1.2311 |
| SD-62 | 146.46 | 58.58 | 4.375 | 2.585 | 2.9168 | 1.4363 |
| SD-63 | 146.46 | 58.58 | 4.375 | 2.585 | 2.9168 | 1.4363 |
| SD-64 | 146.46 | 58.58 | 4.375 | 2.585 | 2.9168 | 1.4363 |
| SD-65 | 146.46 | 58.58 | 4.375 | 2.585 | 2.9168 | 1.2311 |
| SD-66 | 146.46 | 58.58 | 4.375 | 2.585 | 2.9168 | 1.2311 |
| SD-67 | 146.46 | 58.58 | 4.375 | 2.585 | 2.9168 | 1.4363 |
| SD-68 | 162.36 | 64.95 | 4.568 | 2.855 | 3.0454 | 1.1897 |
| SD-69 | 170.55 | 68.22 | 4.684 | 2.947 | 3.1228 | 1.2280 |
| SD-70 | 150.10 | 60.04 | 4.419 | 2.647 | 2.9463 | 1.4707 |
| SD-71 | 150.10 | 60.04 | 4.419 | 2.647 | 2.9463 | 1.4707 |
| SD-72 | 150.10 | 60.04 | 4.419 | 2.647 | 2.9463 | 1.4707 |
| SD-73 | 189.46 | 75.78 | 4.971 | 3.107 | 3.3137 | 1.2948 |
| SD-74 | 189.46 | 75.78 | 4.971 | 3.107 | 3.3137 | 1.2948 |
| SD-75 | 189.46 | 75.78 | 4.971 | 3.107 | 2.7614 | 1.2948 |
| SD-76 | 189.46 | 75.78 | 4.971 | 3.107 | 2.8566 | 1.2948 |
| SD-77 | 202.19 | 80.88 | 5.151 | 3.216 | 3.4339 | 1.3398 |
| SD-78 | 202.19 | 80.88 | 5.151 | 3.216 | 3.4339 | 1.3398 |
| SD-79 | 202.19 | 80.88 | 5.151 | 3.216 | 2.8615 | 1.3398 |
| SD-80 | 185.40 | 74.16 | 4.909 | 3.073 | 2.8213 | 1.2804 |
## Appendix B. Characteristic lengths

Table B1. Plan-direction lengths in metres.

| Outlet | West | East | South | North |
| --- | --- | --- | --- | --- |
| SD-01 | 2.1000 | 1.8000 | 1.5900 | 1.8000 |
| SD-02 | 1.8000 | 1.8000 | 1.5900 | 1.8000 |
| SD-03 | 1.8000 | 1.8000 | 1.5900 | 1.8000 |
| SD-04 | 1.8000 | 1.8000 | 1.5900 | 1.8000 |
| SD-05 | 1.8000 | 2.1000 | 1.5900 | 1.8000 |
| SD-06 | 2.1000 | 1.8000 | 1.5900 | 1.8000 |
| SD-07 | 1.8000 | 1.8000 | 1.5900 | 1.8000 |
| SD-08 | 1.8000 | 2.4000 | 1.5900 | 1.8000 |
| SD-09 | 2.4000 | 1.5000 | 1.5900 | 1.8000 |
| SD-10 | 1.5000 | 1.8000 | 1.5900 | 1.8000 |
| SD-11 | 1.8000 | 1.8000 | 1.5900 | 1.8000 |
| SD-12 | 1.8000 | 1.7400 | 1.5900 | 1.8000 |
| SD-13 | 2.1000 | 1.8000 | 1.8000 | 1.8000 |
| SD-14 | 1.8000 | 1.8000 | 1.8000 | 1.8000 |
| SD-15 | 1.8000 | 1.8000 | 1.8000 | 1.8000 |
| SD-16 | 1.8000 | 1.8000 | 1.8000 | 1.8000 |
| SD-17 | 1.8000 | 2.1000 | 1.8000 | 1.8000 |
| SD-18 | 2.1000 | 1.8000 | 1.8000 | 1.8000 |
| SD-19 | 1.8000 | 1.8000 | 1.8000 | 1.8000 |
| SD-20 | 1.8000 | 2.4000 | 1.8000 | 1.8000 |
| SD-21 | 2.4000 | 1.5000 | 1.8000 | 1.8000 |
| SD-22 | 1.5000 | 1.8000 | 1.8000 | 1.8000 |
| SD-23 | 1.8000 | 1.8000 | 1.8000 | 1.8000 |
| SD-24 | 1.8000 | 1.7400 | 1.8000 | 1.8000 |
| SD-25 | 2.1000 | 1.8000 | 1.8000 | 1.5000 |
| SD-26 | 1.8000 | 1.8000 | 1.8000 | 1.5000 |
| SD-27 | 1.8000 | 1.8000 | 1.8000 | 1.5000 |
| SD-28 | 1.8000 | 1.8000 | 1.8000 | 1.5000 |
| SD-29 | 1.8000 | 2.1000 | 1.8000 | 1.5000 |
| SD-30 | 2.1000 | 1.8000 | 1.8000 | 1.5000 |
| SD-31 | 1.8000 | 1.8000 | 1.8000 | 1.5000 |
| SD-32 | 1.8000 | 2.4000 | 1.8000 | 1.5000 |
| SD-33 | 2.4000 | 1.5000 | 1.8000 | 1.5000 |
| SD-34 | 1.5000 | 1.8000 | 1.8000 | 1.5000 |
| SD-35 | 1.8000 | 1.8000 | 1.8000 | 1.5000 |
| SD-36 | 1.8000 | 1.7400 | 1.8000 | 1.5000 |
| SD-37 | 2.1000 | 1.8000 | 1.5000 | 2.1000 |
| SD-38 | 1.8000 | 1.8000 | 1.5000 | 2.1000 |
| SD-39 | 1.8000 | 1.8000 | 1.5000 | 2.1000 |
| SD-40 | 1.8000 | 1.8000 | 1.5000 | 2.1000 |
## Appendix B. Characteristic lengths (continued)

Table B1. Plan-direction lengths in metres.

| Outlet | West | East | South | North |
| --- | --- | --- | --- | --- |
| SD-41 | 1.8000 | 2.1000 | 1.5000 | 2.1000 |
| SD-42 | 2.1000 | 1.8000 | 1.5000 | 2.1000 |
| SD-43 | 1.8000 | 1.8000 | 1.5000 | 2.1000 |
| SD-44 | 1.8000 | 2.4000 | 1.5000 | 2.1000 |
| SD-45 | 2.4000 | 1.5000 | 1.5000 | 2.1000 |
| SD-46 | 1.5000 | 1.8000 | 1.5000 | 2.1000 |
| SD-47 | 1.8000 | 1.8000 | 1.5000 | 2.1000 |
| SD-48 | 1.8000 | 1.7400 | 1.5000 | 2.1000 |
| SD-49 | 2.1000 | 1.8000 | 2.1000 | 1.5000 |
| SD-50 | 1.8000 | 1.8000 | 2.1000 | 1.5000 |
| SD-51 | 1.8000 | 1.8000 | 2.1000 | 1.5000 |
| SD-52 | 1.8000 | 1.8000 | 2.1000 | 1.5000 |
| SD-53 | 1.8000 | 2.1000 | 2.1000 | 1.5000 |
| SD-54 | 2.1000 | 1.8000 | 2.1000 | 1.5000 |
| SD-55 | 1.8000 | 1.8000 | 2.1000 | 1.5000 |
| SD-56 | 1.8000 | 2.4000 | 2.1000 | 1.5000 |
| SD-57 | 2.4000 | 1.5000 | 2.1000 | 1.5000 |
| SD-58 | 1.5000 | 1.8000 | 2.1000 | 1.5000 |
| SD-59 | 1.8000 | 1.8000 | 2.1000 | 1.5000 |
| SD-60 | 1.8000 | 1.7400 | 2.1000 | 1.5000 |
| SD-61 | 2.1000 | 1.8000 | 1.5000 | 1.5000 |
| SD-62 | 1.8000 | 1.8000 | 1.5000 | 1.5000 |
| SD-63 | 1.8000 | 1.8000 | 1.5000 | 1.5000 |
| SD-64 | 1.8000 | 1.8000 | 1.5000 | 1.5000 |
| SD-65 | 1.8000 | 2.1000 | 1.5000 | 1.5000 |
| SD-66 | 2.1000 | 1.8000 | 1.5000 | 1.5000 |
| SD-67 | 1.8000 | 1.8000 | 1.5000 | 1.5000 |
| SD-68 | 1.8000 | 2.4000 | 1.5000 | 1.5000 |
| SD-69 | 2.4000 | 1.5000 | 1.5000 | 1.8000 |
| SD-70 | 1.5000 | 1.8000 | 1.5000 | 1.8000 |
| SD-71 | 1.8000 | 1.8000 | 1.5000 | 1.8000 |
| SD-72 | 1.8000 | 1.7400 | 1.5000 | 1.8000 |
| SD-73 | 2.0167 | 1.5000 | 1.8000 | 2.4000 |
| SD-74 | 1.5000 | 1.8000 | 1.8000 | 2.4000 |
| SD-75 | 1.8000 | 1.8000 | 1.8000 | 2.4000 |
| SD-76 | 1.8000 | 1.7400 | 1.8000 | 2.4000 |
| SD-77 | 2.0167 | 1.5000 | 2.4000 | 2.2300 |
| SD-78 | 1.5000 | 1.8000 | 2.4000 | 2.2300 |
| SD-79 | 1.8000 | 1.8000 | 2.4000 | 2.2300 |
| SD-80 | 1.8000 | 1.7400 | 2.4000 | 2.2300 |
## Appendix C. VAV grouping and connections

Group flows are rounded display values. Connection lengths are straight XY geometry, not installed flexible lengths.

Table C1. Four-outlet VAV groups.

| VAV | Diffuser outlets | Qmax L/s | Qmin L/s | XY range m |
| --- | --- | --- | --- | --- |
| VAV-01 | SD-01, SD-02, SD-13, SD-14 | 628.0 | 251.2 | 2.403-2.693 |
| VAV-02 | SD-03, SD-04, SD-15, SD-16 | 637.6 | 255.0 | 2.486-2.606 |
| VAV-03 | SD-05, SD-06, SD-17, SD-18 | 639.0 | 255.6 | 2.750-2.782 |
| VAV-04 | SD-07, SD-08, SD-19, SD-20 | 672.8 | 269.1 | 2.486-2.606 |
| VAV-05 | SD-09, SD-10, SD-21, SD-22 | 643.8 | 257.5 | 2.306-2.380 |
| VAV-06 | SD-11, SD-12, SD-23, SD-24 | 588.0 | 235.2 | 2.492-2.599 |
| VAV-07 | SD-25, SD-26, SD-37, SD-38 | 674.6 | 269.9 | 2.177-2.511 |
| VAV-08 | SD-27, SD-28, SD-39, SD-40 | 674.6 | 269.9 | 2.268-2.418 |
| VAV-09 | SD-29, SD-30, SD-41, SD-42 | 674.6 | 269.9 | 2.555-2.607 |
| VAV-10 | SD-31, SD-32, SD-43, SD-44 | 711.3 | 284.5 | 2.268-2.418 |
| VAV-11 | SD-33, SD-34, SD-45, SD-46 | 679.9 | 272.0 | 2.070-2.173 |
| VAV-12 | SD-35, SD-36, SD-47, SD-48 | 632.8 | 253.1 | 2.275-2.411 |
| VAV-13 | SD-49, SD-50, SD-61, SD-62 | 601.9 | 240.8 | 2.140-2.547 |
| VAV-14 | SD-51, SD-52, SD-63, SD-64 | 606.5 | 242.6 | 2.232-2.454 |
| VAV-15 | SD-53, SD-54, SD-65, SD-66 | 608.3 | 243.3 | 2.523-2.641 |
| VAV-16 | SD-55, SD-56, SD-67, SD-68 | 640.2 | 256.1 | 2.232-2.454 |
| VAV-17 | SD-57, SD-58, SD-69, SD-70 | 638.3 | 255.3 | 2.031-2.213 |
| VAV-18 | SD-59, SD-60, SD-71, SD-72 | 589.2 | 235.7 | 2.239-2.448 |
| VAV-19 | SD-73, SD-74, SD-77, SD-78 | 783.3 | 313.3 | 2.761-2.900 |
| VAV-20 | SD-75, SD-76, SD-79, SD-80 | 766.5 | 306.6 | 2.918-3.083 |
## Appendix D. Supply duct sizing

Table D1. Adopted rectangular sections and calculated friction.

| Section | Flow L/s | Size mm x mm | Speed m/s | Limit m/s | Calc Pa/m | Online Pa/m | W:H |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-01 | 13091.32 | 2200 × 600 | 9.918 | 10.0 | 0.9023 | 0.877 | 3.67 |
| A-02 | 13091.32 | 2200 × 600 | 9.918 | 10.0 | 0.9023 | 0.877 | 3.67 |
| A-03 | 13091.32 | 2200 × 600 | 9.918 | 10.0 | 0.9023 | 0.877 | 3.67 |
| D-01 | 11541.53 | 1950 × 600 | 9.865 | 10.0 | 0.9207 | 0.897 | 3.25 |
| D-02 | 1816.76 | 600 × 450 | 6.729 | 8.0 | 0.8901 | 0.877 | 1.33 |
| D-03 | 1208.49 | 550 × 350 | 6.278 | 8.0 | 0.9773 | 0.963 | 1.57 |
| D-04 | 601.94 | 400 × 300 | 5.016 | 8.0 | 0.8423 | 0.830 | 1.33 |
| D-05 | 1867.69 | 600 × 450 | 6.917 | 8.0 | 0.9374 | 0.924 | 1.33 |
| D-06 | 1227.49 | 500 × 400 | 6.137 | 8.0 | 0.8941 | 0.881 | 1.25 |
| D-07 | 589.22 | 450 × 250 | 5.238 | 8.0 | 0.9874 | 0.974 | 1.80 |
| D-08 | 7857.08 | 1350 × 600 | 9.700 | 10.0 | 0.9995 | 0.979 | 2.25 |
| D-09 | 2023.94 | 650 × 450 | 6.919 | 8.0 | 0.9009 | 0.887 | 1.44 |
| D-10 | 1349.29 | 600 × 350 | 6.425 | 8.0 | 0.9809 | 0.966 | 1.71 |
| D-11 | 674.65 | 350 × 350 | 5.507 | 8.0 | 0.9766 | 0.960 | 1.00 |
| D-12 | 2023.94 | 650 × 450 | 6.919 | 8.0 | 0.9009 | 0.887 | 1.44 |
| D-13 | 1312.66 | 450 × 450 | 6.482 | 8.0 | 0.9752 | 0.961 | 1.00 |
| D-14 | 632.78 | 400 × 300 | 5.273 | 8.0 | 0.9240 | 0.910 | 1.33 |
| D-15 | 3809.20 | 850 × 550 | 8.148 | 10.0 | 0.9313 | 0.916 | 1.55 |
| D-16 | 1904.60 | 600 × 450 | 7.054 | 8.0 | 0.9724 | 0.958 | 1.33 |
| D-17 | 1265.59 | 500 × 400 | 6.328 | 8.0 | 0.9466 | 0.933 | 1.25 |
| D-18 | 628.01 | 400 × 300 | 5.233 | 8.0 | 0.9111 | 0.897 | 1.33 |
| D-19 | 1904.60 | 600 × 450 | 7.054 | 8.0 | 0.9724 | 0.958 | 1.33 |
| D-20 | 1231.80 | 500 × 400 | 6.159 | 8.0 | 0.9000 | 0.887 | 1.25 |
| D-21 | 587.98 | 450 × 250 | 5.227 | 8.0 | 0.9836 | 0.970 | 1.80 |
## Appendix D. Supply duct sizing (continued)

Table D1. Adopted rectangular sections and calculated friction.

| Section | Flow L/s | Size mm x mm | Speed m/s | Limit m/s | Calc Pa/m | Online Pa/m | W:H |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D-22 | 1549.78 | 600 × 400 | 6.457 | 8.0 | 0.8961 | 0.883 | 1.50 |
| D-23 | 1549.78 | 600 × 400 | 6.457 | 8.0 | 0.8961 | 0.883 | 1.50 |
| D-24 | 766.49 | 450 × 300 | 5.678 | 8.0 | 0.9990 | 0.980 | 1.50 |
| D-25 | 628.01 | 400 × 300 | 5.233 | 8.0 | 0.9111 | 0.897 | 1.33 |
| D-26 | 637.58 | 400 × 300 | 5.313 | 8.0 | 0.9370 | 0.922 | 1.33 |
| D-27 | 639.02 | 400 × 300 | 5.325 | 8.0 | 0.9409 | 0.926 | 1.33 |
| D-28 | 672.80 | 350 × 350 | 5.492 | 8.0 | 0.9716 | 0.955 | 1.00 |
| D-29 | 643.82 | 400 × 300 | 5.365 | 8.0 | 0.9541 | 0.939 | 1.33 |
| D-30 | 587.98 | 450 × 250 | 5.227 | 8.0 | 0.9836 | 0.970 | 1.80 |
| D-31 | 674.65 | 350 × 350 | 5.507 | 8.0 | 0.9766 | 0.960 | 1.00 |
| D-32 | 674.65 | 350 × 350 | 5.507 | 8.0 | 0.9766 | 0.960 | 1.00 |
| D-33 | 674.65 | 350 × 350 | 5.507 | 8.0 | 0.9766 | 0.960 | 1.00 |
| D-34 | 711.28 | 450 × 300 | 5.269 | 8.0 | 0.8695 | 0.855 | 1.50 |
| D-35 | 679.88 | 350 × 350 | 5.550 | 8.0 | 0.9907 | 0.974 | 1.00 |
| D-36 | 632.78 | 400 × 300 | 5.273 | 8.0 | 0.9240 | 0.910 | 1.33 |
| D-37 | 601.94 | 400 × 300 | 5.016 | 8.0 | 0.8423 | 0.830 | 1.33 |
| D-38 | 606.55 | 400 × 300 | 5.055 | 8.0 | 0.8542 | 0.842 | 1.33 |
| D-39 | 608.26 | 400 × 300 | 5.069 | 8.0 | 0.8587 | 0.846 | 1.33 |
| D-40 | 640.21 | 400 × 300 | 5.335 | 8.0 | 0.9442 | 0.929 | 1.33 |
| D-41 | 638.26 | 400 × 300 | 5.319 | 8.0 | 0.9389 | 0.924 | 1.33 |
| D-42 | 589.22 | 450 × 250 | 5.238 | 8.0 | 0.9874 | 0.974 | 1.80 |
| D-43 | 783.29 | 400 × 350 | 5.595 | 8.0 | 0.9298 | 0.911 | 1.14 |
| D-44 | 766.49 | 450 × 300 | 5.678 | 8.0 | 0.9990 | 0.980 | 1.50 |
## Supply air distribution drawing

[View the full-size drawing](Drawings/Supply%20Air%20Distribution.pdf)

## Appendix E. Manufacturer air-distribution assessment

### E.1 Application to the specified diffuser

The main design uses eighty Krueger 1400/51400 ceiling diffusers. Appendix A reports catalogue throw divided by the corresponding plan length. The manufacturer assessment examines the Type 3 circular-pattern curves in Krueger Air Distribution Engineering [4]. Each curve relates throw ratio to predicted ADPI for a specified sensible load.

Table E1. Manufacturer curve selection for the adopted load assumptions.

| Condition | Sensible load | Published curves |
| --- | --- | --- |
| Maximum flow | 170.10 W/m2 | 40 and 60 Btu/(h ft2) |
| 40% flow | 68.04 W/m2 | 20 and 40 Btu/(h ft2) |

The paired-curve method compares each directional ratio with both bounding load curves. A point beyond the published domain has no supported reading. Sections 3 and 4 use the louvered-diffuser selection interval. Confirming an ADPI value from the manufacturer curves would require a supported reading at each operating point.

### E.2 Linear-slot system

The separate manufacturer-based system uses 63 Krueger Model 1900 linear-slot outlets. Its selection uses the Type 4 slot curves and the throw data for the selected slot configuration. The characteristic length runs in plan from the slot to the boundary or the midpoint between opposing outlets. Each outlet is checked at maximum and minimum flow.

The two systems use different outlets, layouts and throw curves. Drawings and schedules in Appendices A through D apply to the 80-outlet system. Applying the slot selection at 24/13 °C requires outlet-specific flows and a fresh curve check; the existing slot study does not establish performance at that operating point.

Manufacturer source: Krueger, 1900 Supply Published Performance Data, pp. 1, 4, 7 and 10. Air-distribution curves: reference [4].

