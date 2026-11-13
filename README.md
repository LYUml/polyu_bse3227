# BSE3227 HVAC mini-design

## Current agent design study

- Editable drawing: [Supply Air Distribution.dwg](03_Design_Drawings/Agent_Study/Supply%20Air%20Distribution.dwg)
- Reviewed plot: [Supply Air Distribution.pdf](03_Design_Drawings/Agent_Study/Supply%20Air%20Distribution.pdf)
- Calculation and review report: [HVAC System Design.pdf](04_Final_Report/Agent_Study/HVAC%20System%20Design.pdf)
- Source-linked aggregate evidence: [AGENT_REVIEW.json](05_Calculations/AGENT_REVIEW.json)

The general Building Services Agent executed this study in the coursework
workspace. Five calculation/drawing tasks pass,including native DWG save and
independent reopening. Six package stages complete without execution errors.
Saved drawing correspondence covers80diffusers,20VAVgroups and47rigid sections.
The24-page report retains all33source requirements and six unresolved inputs.

**Full engineering acceptance is pending.** ADPI applicability remains pending:
actual room sensible load,characteristic lengths and installation conditions are
unverified,and the preliminary trial load is outside the selected classroom
criterion's source range. Planar flexible-line lengths do not establish installed
lengths or regulatory acceptance. Geometry/scale,source connections,routing and
sizing applicability remain under review. The report distinguishes thermal kW
from electrical demand;successful execution is not design certification.

## Workspace and source records

General source/skills/tests live in the separate
[building-services-agent repository](https://github.com/LYUml/building-services-agent).
Coursework inputs,configurations,runs and local evidence live in07_Agent_Work.
That directory and the detailed local agent_checks are intentionally excluded
from this public repository. Canvas export archives,classroom originals,student
lists and local runtime logs are not included in this new snapshot.

Local replay requires those source files,a reviewed configuration and the pinned
agent/runtime dependencies;the public clone alone does not bundle every course
source. Select the coursework root explicitly with BSA_PROJECT_ROOT. New runs
must use new output directories and recheck sources,geometry,actual plots and
engineering acceptance. Do not repair stale hashes to clear changed inputs.

Original files and prior tracked outputs remain preserved as historical context.
Their acceptance statements are not transferred to this current study. Use the
clean filenames linked above for the current review;internal run/revision history
stays in local provenance and Git history.

## Current-method replay verification

The current general agent has rerun the same interpreted project after a
source-preserving tool update. All 33 requirements and six unresolved inputs
remain. Native DWG reopening and visual inspection of all 24 report pages and
the A1 drawing were repeated. Report and drawing page content matches the
previously reviewed outputs, so the linked deliverable files remain unchanged.
The aggregate review records the new tool commit and local evidence hashes;
original creation provenance is preserved. This confirms repeatability, while
ADPI, physical applicability and full engineering acceptance remain pending.

## AutoCAD source intake checkpoint

The original source drawing now passes native export followed by a pinned upstream
DXF backend inspection. Entity handles/types/layer assignments reconcile across
3,894 model-space entities, 16 layers and three actual layouts; source bytes are
preserved. Header units report millimetres. Independent building dimensions,
physical scale, nested geometry and paper-space/plot interpretation remain pending.
See [source inspection aggregate](05_Calculations/AutoCAD_Source_Inspection.json).
This checkpoint is source intake; engineering design/release reviews remain separate.

## Source-backed AutoCAD writer replay

A pinned open-source backend now independently writes the recalculated 47-section
duct schedule and flow arrows. Native DWG reopening and scoped A1 visual inspection
execute; all 33 requirements and six unresolved inputs remain. The resulting PDF
page content matches the current public sheet, so existing deliverables are retained.
See [replay aggregate](05_Calculations/AutoCAD_Schedule_Replay.json). This is a
repeatability/provider comparison, with full engineering acceptance still pending.

The general agent's shared AutoCAD command has also executed a fresh source-backed
47-section DXF replay and independent verification. This command trial does not
repeat native DWG or visual acceptance; those retain their preceding evidence.
See [shared-entry aggregate](05_Calculations/AutoCAD_Shared_Entry.json).

## Inherited task-chain writer replay

A fresh complete 16-task plan now selects the pinned upstream sheet writer while
retaining original sources, all 33 requirements and six unresolved inputs. Five
scoped executable stages pass through native DWG reopening and A1 plot review;
eleven regulatory/manual tasks remain pending. The whole-plan command correctly
returns an incomplete result. Public drawing page content remains unchanged.
See [task-chain replay aggregate](05_Calculations/AutoCAD_Workflow_Replay.json).

A subsequent source-plan-bound replay verifies the declared writer against the
original plan, closing a reproduced recorded-writer bypass. All original
requirements and gaps remain; this check did not repeat native/visual acceptance.
See [source-plan verification](05_Calculations/AutoCAD_Source_Plan_Verification.json).

## Related evidence for complete requirements

Five original load/minimum-flow/schedule requirements now expose related existing
calculation and drawing artifacts alongside their unchanged primary review. All
33 source requirements, full quotes and six input gaps remain. The common source
inventory, fresh task-chain replay and delivery-context verification execute;
all five primary reviews remain pending. Native/visual acceptance was not repeated.
See [supporting evidence aggregate](05_Calculations/Supporting_Requirement_Evidence.json).

## Integrated upstream-writer package

The complete interpreted HVAC package now replays with the pinned upstream writer
and related requirement evidence. Native DWG reopening, source-tree paths,
junction/terminal/ADPI reviews and the 24-page report execute without stage errors.
All report pages and the A1 sheet were actually inspected. Both PDFs retain the
same page content as existing delivery files; those files remain unchanged.
All 33 requirements and six unresolved inputs remain. Complete pressure/fan duty,
physical installation, ADPI applicability and full acceptance remain pending.
See [integrated replay aggregate](05_Calculations/Integrated_HVAC_Replay.json).

## AI-client HVAC package execution

A real local MCP client now prepares the source-pinned configuration, runs the
complete existing HVAC package, audits 49 artifacts and retrieves report/drawing
page images. Native DWG reopening and 24-page report production execute without
stage errors. All 33 requirements and six unresolved inputs remain, and status
stays review_required. This protocol trial inspects report first/last pages and
full A1 only; previous complete visual review retains its own evidence. Public
deliverable files are preserved because PDF page content matches.
See [MCP package aggregate](05_Calculations/MCP_HVAC_Project.json).
