Architecture: one extension, values in and out
==============================================

What is compiled
----------------

The repository vendors upstream PackingSolver as a git submodule pinned to a fixed commit (recorded as ``__UPSTREAM_COMMIT__`` in :mod:`packingsolver3d.config.meta`) and never patches it. A top-level ``CMakeLists.txt`` adds that tree with a fixed option set -- HiGHS as the only linear-programming backend, no executables, no upstream tests -- and links the two libraries ``PackingSolver::box`` and ``PackingSolver::boxstacks`` together with a short pybind11 bridge (``packingsolver3d/_core.cpp``) into a single extension module, ``packingsolver3d._core``. Boost, HiGHS and upstream's own solver libraries are statically linked into it; a wheel has no dependency outside the standard library.

What crosses the boundary
-------------------------

The bridge exposes two functions, ``box_solve`` and ``boxstacks_solve``. Each takes plain Python values (dicts and lists produced from an :class:`~packingsolver3d.model.Instance`), builds the upstream instance through upstream's ``InstanceBuilder``, fills an ``OptimizeParameters`` object, releases the GIL, calls upstream's ``optimize()``, and copies the best solution back out as plain values: bins, stacks, placements, upstream's statistics block, the reported bounds, and the captured log. No upstream object outlives the call. Nothing in Python holds a pointer, buffer or reference into solver memory, so the C++ lifetimes never become the caller's problem.

Field names, objective tokens, rotation names and option names are upstream's, verbatim; the bridge parses tokens through upstream's own stream operators rather than re-implementing them. When a key is absent from the payload the corresponding builder setter is not called, so upstream's default applies -- the same default upstream's CSV readers use when a column is missing.

What this implies
-----------------

* **In-process.** The solver runs inside your interpreter. A crash inside upstream ends the process, and the memory budget is upstream's own soft check. When you need containment or a hard limit, run the solve in a worker process (:doc:`/how_to/budgets/index` shows how); the package deliberately does not hide a subprocess layer behind the API.
* **Two validation layers.** Structural checks (empty instance, non-positive extents, ``copies_min`` out of range, defects on unknown bins) and the semantic refusals described in :doc:`/explanations/upstream_behaviours/index` run in Python before the bridge is called; upstream's own ``InstanceBuilder`` checks run inside the bridge and surface as :class:`~packingsolver3d.errors.InvalidInstanceError` carrying upstream's message.
* **Auditable.** Every :class:`~packingsolver3d.result.Result` carries a :class:`~packingsolver3d.result.RunRecord` with the exact options handed to upstream, upstream's captured output, and the wall time. A number published from this package can always be traced back to the call that produced it.
* **Scope is two problem types.** ``rectangle``, ``rectangleguillotine``, ``onedimensional`` and ``irregular`` are not built; the package name says ``3d`` for that reason.
