# Plenum air domains

These closed air volumes come from the existing supply-air candidate IFC. They are analysis geometry, not duct material or a completed pressure design.

Two geometric families cover 7 and 13 existing plenums. Each native air volume and all five candidate port areas reconcile; air/material intersection has zero volume. Individual outlet flow fractions vary and cannot be replaced by equal quarters. Geometry reuse alone does not establish reusable loss coefficients.

Metal thickness, lining, outside-envelope interpretation and omitted balancing blades retain the candidate assumptions recorded in the check. Manufacturer internals, inlet profile, actual joints and pressure acceptance remain unresolved. No mesh or solver result is delivered in this folder.

## Mesh preparation follow-up

The separate Plenum Mesh Boundary Check.json records two actual layered meshes and final source-bound boundary checks. Each had 1496 internal wall marker faces removed without changing volume connectivity or coordinates. Five port planes and exterior orientation pass independent checks. Large meshes remain private. This extends the earlier geometry-only check; pressure, grid independence and manufacturer internal correspondence remain unaccepted. No missing pressure values were filled.
