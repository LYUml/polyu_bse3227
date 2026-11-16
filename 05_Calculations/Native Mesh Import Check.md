# Native mesh import check

The existing main and two plenum meshes import through isolated native OpenFOAM 12 without remeshing. Seventeen-digit coordinate output prevents rounding from collapsing thin wall-layer cells. All source points are preserved exactly. No system MPI or file associations were changed.

All three high-precision meshes retain three failed native quality-check categories: aspect ratio, cell determinant and face interpolation weight. Positive volumes and completed import are insufficient to accept pressure calculations. No new pressure result is supplied. The companion JSON records actual checks and source hashes; this is verification evidence, not a course requirement or final design acceptance.
