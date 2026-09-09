Replay upstream's test instances
================================

Use this page when you want to check that this package reproduces what upstream PackingSolver produces, or when your instances are stored in upstream's CSV format.

What the repository already does
--------------------------------

``test/testfile/upstream/`` holds verbatim copies of the instances upstream's own unit tests solve -- seven for ``box`` (knapsack, open-dimension-x and variable-sized bin packing cases) and three for ``boxstacks`` (variable-sized bin packing and two semi-trailer truck axle-weight cases). ``test/test_upstream_cases.py`` replays each of them with the parameters the upstream gtest uses and compares the result to upstream's ``solution.csv`` by the quantity upstream's ``Solution::operator<`` compares for that objective: profit for knapsack, cost for variable-sized bin packing, ``x_max`` for open dimension x, number of bins for bin packing.

One case needs a note. Upstream's test for the semi-trailer knapsack instance drives a sub-algorithm (``sequential_onedimensional_rectangle``) directly, and its reference solution is empty; the public entry point here is ``optimize()``, which packs two of the three items. The repository therefore compares that case against the certificate upstream's own ``packingsolver_boxstacks`` executable writes for ``optimize()`` on the same files (``solution_optimize.csv``, provenance in ``SOURCE.md``).

Reading upstream CSV instances
------------------------------

Upstream instances are three CSV files: ``items.csv``, ``bins.csv`` and ``parameters.csv``. The test module contains a small reader (``load_case``) that maps upstream's columns onto :class:`~packingsolver3d.model.ItemType` and :class:`~packingsolver3d.model.BinType`; it is not part of the public API yet, but the mapping is short and documented in :doc:`/reference/model_fields/index`:

* ``X, Y, Z, COPIES, COPIES_MIN, PROFIT, WEIGHT`` map one to one; an absent column or an empty cell means "leave the field ``None``" so upstream's default applies, exactly as upstream's reader treats an absent column.
* ``ROTATION_XYZ ... ROTATION_ZXY`` columns with value ``1`` become the ``rotations`` list; if no rotation column exists, leave ``rotations=None``.
* ``GROUP_ID, STACKABILITY_ID, NESTING_HEIGHT, MAXIMUM_STACKABILITY, MAXIMUM_WEIGHT_ABOVE`` are the item stacking fields; ``MAXIMUM_WEIGHT, MAXIMUM_STACK_DENSITY`` the bin ones.
* ``IS_SEMI_TRAILER_TRUCK=1`` plus the ``TRACTOR_WEIGHT ... MIDDLE_AXLE_MAXIMUM_WEIGHT`` columns become a :class:`~packingsolver3d.model.SemiTrailerTruck`.
* ``parameters.csv`` rows ``objective`` and ``unloading-constraint`` are the :class:`~packingsolver3d.model.Objective` and :class:`~packingsolver3d.model.UnloadingConstraint` tokens.

Comparing with upstream's executable
------------------------------------

Because the package calls the same ``optimize()`` upstream's command line calls, an instance solved here and with ``packingsolver_box`` built from the same commit with ``--linear-programming-solver highs`` and the same time limit should reach the same objective value in deterministic modes. Anytime runs depend on timing and may differ in the incumbent, never in the reported bound.
