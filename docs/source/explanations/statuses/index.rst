Statuses, values and bounds
===========================

Every :class:`~packingsolver3d.result.Result` reports three separate things, and the package refuses to blur them:

* ``value`` -- the objective value of the packing the solver returned. This is what was **achieved**.
* ``bound`` -- the bound upstream reported for the requested objective (``BinPackingBound``, ``KnapsackBound``, ...). This is what was **proved**.
* ``status`` -- the verdict, derived from the two above and from upstream's feasibility flags.

The four statuses
-----------------

.. list-table::
   :header-rows: 1

   * - Status
     - Meaning
   * - ``OPTIMAL``
     - A packing exists and its ``value`` meets the ``bound`` upstream reported for this objective (equal for minimisation objectives once the bound is reached; profit at least the bound for knapsack). Proven, not guessed.
   * - ``FEASIBLE``
     - A packing exists but either no bound was reported for this objective or the value does not meet it. A heuristic incumbent, however good it looks, stays here.
   * - ``NO_SOLUTION``
     - Upstream returned no packing (no bins, or no items placed).
   * - ``INFEASIBLE``
     - Upstream set ``IsProvenInfeasible``.

For the ``FEASIBILITY`` objective the rule is different by nature: the result is ``OPTIMAL`` when every item is packed and ``FEASIBLE`` otherwise.

Which objectives carry a bound
------------------------------

.. list-table::
   :header-rows: 1

   * - Objective
     - ``value`` read from
     - ``bound`` read from
     - Sense
   * - ``BIN_PACKING``
     - ``NumberOfBins``
     - ``BinPackingBound``
     - minimise
   * - ``VARIABLE_SIZED_BIN_PACKING``
     - ``BinCost``
     - ``VariableSizedBinPackingBound``
     - minimise
   * - ``KNAPSACK``
     - ``ItemProfit``
     - ``KnapsackBound``
     - maximise
   * - ``OPEN_DIMENSION_X`` / ``_Y`` / ``_Z``
     - ``XMax`` / ``YMax`` / ``ZMax``
     - ``OpenDimension?Bound`` (``box`` only; ``boxstacks`` reports none)
     - minimise
   * - every other objective (``DEFAULT``, ``BIN_PACKING_WITH_LEFTOVERS``, ...)
     - --
     - none
     - never ``OPTIMAL``

Why this matters
----------------

Upstream's own ``is_proven_optimal()`` applies the same comparison, so the package does not invent a stricter notion; it only refuses to call a result optimal when upstream did not prove it. When you report numbers from a campaign, keep the two columns: "best found" and "best bound". The gap between them is the honest statement of what the run established, and it is what a reader needs to compare against another solver.
