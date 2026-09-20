Solver options
==============

Both ``solve`` functions share the core options; ``box.solve`` adds its algorithm switches, ``boxstacks.solve`` adds the unloading override. Every option maps to a field of upstream's ``OptimizeParameters``; ``None`` leaves upstream's default in place.

Shared options
--------------

.. list-table::
   :header-rows: 1

   * - Keyword
     - Upstream
     - Notes
   * - ``time_limit``
     - ``timer.set_time_limit``
     - seconds; checked at algorithm checkpoints
   * - ``memory_limit``
     - ``memory_limit_megabytes``
     - MiB; upstream's own soft check
   * - ``verbosity_level``
     - ``verbosity_level``
     - default ``0``; the log is captured into ``RunRecord.stdout``
   * - ``optimization_mode``
     - ``optimization_mode``
     - :class:`~packingsolver3d.model.OptimizationMode` token
   * - ``linear_programming_solver``
     - ``linear_programming_solver_name``
     - always set; ``highs`` unless overridden for a custom build
   * - ``stop_when_unimproved_for``
     - an end boolean on ``timer`` (raised by a watchdog thread)
     - seconds without a new incumbent after which the solve stops with ``RunRecord.stop_reason == 'unimproved'``; the clock runs from the start until a first solution exists
   * - ``stop_when_unimproved_after``
     - same watchdog
     - seconds from the start before that stop may fire (default ``0``); needs ``stop_when_unimproved_for``
   * - ``stop_when_unimproved_ratio``
     - same watchdog
     - makes the patience relative: stop once no improvement has arrived for the larger of ``stop_when_unimproved_for`` and this many times the time of the last improvement, and never before a first solution exists; needs ``stop_when_unimproved_for``; :func:`~packingsolver3d.recommend_time_budget` sets it from ``alpha``
   * - ``progress_callback``
     - ``new_solution_callback``
     - called with a :class:`~packingsolver3d.result.ProgressEvent` on every improvement of the incumbent; return ``False`` to stop the solve (``RunRecord.stop_reason == 'callback'``); see :doc:`/how_to/budgets/index`

``box.solve`` switches
----------------------

Each is ``True``, ``False`` or ``None``:

``use_tree_search``, ``use_tree_search_maximal_spaces``, ``use_sequential_single_knapsack``, ``use_sequential_value_correction``, ``use_column_generation``, ``use_dichotomic_search``, ``use_dual_feasible_functions`` -> the identically named ``OptimizeParameters`` fields. With none set, upstream chooses its portfolio from the instance.

``boxstacks.solve`` extras
--------------------------

``unloading_constraint`` -> ``InstanceBuilder::set_unloading_constraint``, overriding :attr:`Instance.unloading_constraint <packingsolver3d.model.Instance.unloading_constraint>` for the call.

What comes back
---------------

``Result.value`` and ``Result.bound`` are read from upstream's output as listed in :doc:`/explanations/statuses/index`; ``Result.statistics`` is upstream's ``Solution`` block verbatim (``NumberOfItems``, ``NumberOfBins``, ``ItemProfit``, ``ItemWeight``, ``BinCost``, ``VolumeLoad``, ``WeightLoad``, ``Waste``, ``XMax``, ``YMax``, ``ZMax``, ``NumberOfStacks``, ``NumberOfUnpackedItems``, ...); ``Result.solve_time`` is upstream's ``Time``; ``Result.run`` is the :class:`~packingsolver3d.result.RunRecord`.
