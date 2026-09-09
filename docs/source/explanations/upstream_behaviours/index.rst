Upstream behaviours you should know
===================================

packingsolver3d is a faithful binding: it does what upstream PackingSolver does at the pinned commit, and it does not paper over upstream's choices. The behaviours below were found while building the package, each is backed by the upstream source location or a reproducible observation, and each says what the package does about it. If you rely on one of them, check this page again after the submodule moves.

The LP backend is fixed to HiGHS
--------------------------------

*Upstream.* ``OptimizeParameters::linear_programming_solver_name`` defaults to ``CLP``; the factory that resolves the name is a chain of ``#if <backend>_FOUND`` guards ending in a bare ``throw`` ("no linear programming solver found"). The bundled build compiles HiGHS only. Small instances never reach column generation and hide the problem.

*Package.* Every call sets the solver name to HiGHS; ``linear_programming_solver`` exists as an override only for custom builds.

``copies_min`` defaults to "all copies"
---------------------------------------

*Upstream.* ``InstanceBuilder::build`` resolves an item type's ``copies_min == -1`` to ``copies`` for every objective except knapsack, where it becomes ``0``. An explicit ``copies_min = 0`` therefore makes bin packing return zero bins as the true optimum.

*Package.* :attr:`ItemType.copies_min <packingsolver3d.model.ItemType.copies_min>` is ``None`` by default and then left to upstream. Set it only when you mean "at least this many copies".

``boxstacks`` groups stacks without comparing footprints
--------------------------------------------------------

*Upstream.* ``tree_search.cpp`` buckets item types by ``(group_id, stackability_id)`` alone; ``SolutionBuilder::add_item`` later throws when an item's footprint does not match the stack it was put in. Both ids default to ``0``, so two item shapes in a plain instance already trigger it.

*Package.* :func:`packingsolver3d.boxstacks.validate` raises :class:`~packingsolver3d.errors.StackSemanticsError` when two item types share a bucket but have no footprint in common over their allowed rotations. Give differently shaped items different ``stackability_id`` values.

``boxstacks`` keeps items upright
---------------------------------

*Upstream.* The sequential one-dimensional / rectangle phase only ever picks ``XYZ`` or ``YXZ`` (``sequential_onedimensional_rectangle.cpp``), and the tree search takes heights from ``z(Rotation::XYZ)``. An item type allowing only side rotations ends in ``SolutionBuilder::add_item`` throwing "forbidden rotation".

*Package.* :func:`packingsolver3d.boxstacks.validate` raises :class:`~packingsolver3d.errors.UnsupportedFeatureError` for item types whose ``rotations`` include neither ``XYZ`` nor ``YXZ``. The ``box`` solver places all six rotations.

``boxstacks`` accepts defects but places stacks over them
---------------------------------------------------------

*Observation.* At the pinned commit, instances with a floor :class:`~packingsolver3d.model.Defect` in a corner, in the interior, or spanning the full bin width all produced stacks overlapping the defect; upstream's certificate lists the defect, its search treats it as an insertion anchor, and no overlap check rejects the placement. This is upstream behaviour, not a translation error: the package's tests only assert that such instances are accepted.

*Package.* ``defects`` are forwarded faithfully. Do not rely on them being avoided until upstream changes; the docstring of :func:`packingsolver3d.boxstacks.solve` repeats this.

The ``box`` model has no stacking, defects or unloading
-------------------------------------------------------

*Upstream.* The ``box`` solver knows bins, items, rotations and weight capacity. Its readers ignore unknown columns without a diagnostic.

*Package.* :func:`packingsolver3d.box.validate` raises :class:`~packingsolver3d.errors.UnsupportedFeatureError` when an instance carries stacking fields, defects or an unloading constraint, instead of solving a different problem in silence. Use :func:`packingsolver3d.boxstacks.solve` for those.

Limits are upstream's, and the solver runs in-process
-----------------------------------------------------

*Upstream.* ``time_limit`` feeds upstream's timer, checked at algorithm checkpoints; ``memory_limit`` feeds ``memory_limit_megabytes``, compared against the resident size at checkpoints.

*Package.* Both are forwarded as-is. There is no wall-clock kill and no hard address-space limit, and a crash inside upstream ends the interpreter. :doc:`/how_to/budgets/index` shows the worker-process pattern that restores hard limits and crash containment when you need them.

Item profit and bin cost default to geometry
--------------------------------------------

*Upstream.* An unset item profit becomes ``x * y * z``; an unset bin cost becomes ``x * y`` -- an area, not a volume.

*Package.* Both fields are ``None`` by default and left to upstream. Pass an explicit ``cost`` whenever bin types differ in height and you optimise ``VARIABLE_SIZED_BIN_PACKING``.

Anytime runs are not reproducible run to run
--------------------------------------------

*Upstream.* The default ``ANYTIME`` mode uses threads and wall-clock checkpoints; the incumbent at the time limit can differ between runs. The reported bound does not depend on timing.

*Package.* Use ``OptimizationMode.NOT_ANYTIME_DETERMINISTIC`` (or ``NOT_ANYTIME_SEQUENTIAL``, which upstream's own tests use) when two runs must agree, and always record ``result.run.options``.
