Tutorial roadmap
================

Use this page when you are new to packingsolver3d and want one small, observable success per step. Tutorials teach a single path each and deliberately stop before every option and every edge case; when your question turns into "how do I set a budget for a hundred instances?" or "what exactly does this field mean upstream?", leave for :doc:`/how_to/index` or :doc:`/reference/index`.

Reading order
-------------

1. :doc:`quick_start/index` -- install the wheel, decide what fits in a carry-on with the ``box`` solver (a knapsack over nineteen pieces), read the result -- status, value, reported bound, placements -- and look at the packing.
2. :doc:`boxstacks/index` -- the same model with stacking rules, weights, an unloading constraint and a semi-trailer truck, solved with the ``boxstacks`` solver.

Where to go next
----------------

* Budgets, algorithm switches and running many instances: :doc:`/how_to/budgets/index`.
* What ``OPTIMAL`` really means here and why a good-looking packing may still be ``FEASIBLE``: :doc:`/explanations/statuses/index`.
* The upstream behaviours you should know before trusting a result: :doc:`/explanations/upstream_behaviours/index`.

.. toctree::
    :maxdepth: 1
    :hidden:

    quick_start/index
    boxstacks/index
