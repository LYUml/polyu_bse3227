# Supply air connection layout study

This drawing moves ten VAV symbols and associated taps to the centres of their
unchanged four-diffuser groups. Three existing candidate duct sections are
increased from 500 x 350 to 550 x 350 mm to compensate longer trunk segments.
The source allocation and all eighty diffuser positions remain unchanged.

Planar flexible connections shorten in total; no rigid bend is added. Native
AutoCAD reopening, print reference and actual PDF visual review executed.
Twenty untrimmed straight-friction path estimates do not increase under the
same numerical assumptions. This excludes flexible ducts, fittings and equipment.

This is a standalone revised single-line scenario. Original Agent_Study drawings,
report, VAV table, IFC network and pressure ledgers describe the earlier geometry;
they remain preserved and must not be treated as outputs of this revision.

Installed geometry/elevation/slack, hardware, obstacle completeness, chart-method
applicability, room loads, ADPI and full project/code acceptance remain pending.
See 05_Calculations/VAV_Layout_Improvement_Check.json and Connection Layout Duct Sizing.csv.


The matching VAV Connection Schedule now uses this same recentered native
layout:20groups/80terminals,10updatedgroupconnectionlengths,unchanged prescribed
maximum/minimum flows and membership. Saved/reopened DWG185entities,140native
cells and80rawplanconnections independently reconcile. Actual A4PDF inspected;
100mmreference measured100.033667mm. Companion CSV/check are under
05_Calculations/Connection_Layout. These are straight XY lower-bound lengths,
not installed flex lengths or selected hardware. Full pressure and ADPI remain
unresolved; do not combine with the separate earlier network-study geometry.


Supply Network Coordination IFC/DWG/PDF now rebases the finite rigid network
to this recentered layout and three compensated sizes.89bodies/197ports/
88links,all88materialcapinterfaces and21sourceboundaryframes match.
Actual native112entityDWGreopen and1:200PDF inspected;10mreference49.995667mm.
Maximum/minimum31conditional fitting values and32numerical gaps; fullpressure
unknown. Raw89validgeometry/zero intersections/88clearanceviolations, no waivers.
See the matching calculation report in05_Calculations/Connection_Layout.
Earlier Network_Study is preserved as a different historical scenario.
Installed hardware,physicalclearance,flexlength,ADPI and final acceptance remain
unresolved; this coordination overview is not an installation drawing.
