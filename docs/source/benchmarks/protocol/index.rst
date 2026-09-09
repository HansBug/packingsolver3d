Protocol and caveats
====================

This page states exactly how the numbers in :doc:`../leaderboards/index` were produced, so that a reader can decide how far to trust them and can regenerate them.

Budgets and machine
-------------------

* **packingsolver3d** was called through :func:`packingsolver3d.box.solve` with ``time_limit=10.0`` and ``memory_limit=1024`` and otherwise default options (anytime mode, every upstream sub-algorithm enabled). Upstream ``box`` uses several threads on knapsack instances; nothing was done to pin it to one core.
* **Third-party libraries** ran with the same 10 s budget where they accept one (the U-Nesting metaheuristics); the greedy libraries finish in well under a second and were not repeated.
* **Reference codes** ran at their own budgets: the CP-SAT model for 20 s on one thread with 4 GiB, the Martello-Pisinger-Vigo code for 1 s on one thread. They are marked "reference" in the tables and are there to certify optima, not to compete.
* One run per case. Upstream's anytime mode is not reproducible to the last node, so a re-run can differ in the cases that are not proven optimal.
* Machine: Intel Core i7-11700, 16 hardware threads, Linux 6.8, CPython 3.10; packingsolver3d built from the upstream commit pinned in ``packingsolver3d.config.meta``.

Every solution is re-checked
----------------------------

No participant's own objective value is used. Every solution, ours included, is stored as placements (item type, bin, position, extents) and ``tools/make_benchmarks.py`` recomputes the objective from the placements and the instance file after checking, with a tolerance of one millionth, that

* every box lies inside its bin,
* no two boxes in the same bin overlap,
* no item type is placed more often than it has copies,
* the extents of every box are a rotation of its item type, and the *exact* orientation where the variant fixes it,
* all items are placed when the objective is to minimise bins.

A solution that fails any check is shown as ``invalid`` and the participant's total for that benchmark becomes ``n/a`` with the count of valid cases. This is how the four U-Nesting metaheuristics lose their THPACK9 total: on seven to nine of the 47 instances their placements stick out of the container.

Bounds, stars, totals and gaps
------------------------------

* The **Theoretical bound** row gives, per case, the best available bound: for the knapsack family the smallest valid upper bound (the CP-SAT proof where it exists, PackingSolver's reported bound otherwise), for the bin packing families the largest valid lower bound (the volume bound, PackingSolver's reported bound, and for the Martello-Pisinger-Vigo class the generator's construction).
* A value followed by ``*`` equals that bound, so it is a **proven optimum** for that case. The star is only given to participants that solved the same problem variant; a relaxed row cannot earn it.
* **Total** is the sum over all cases: profit for the knapsack family (higher is better), bins for the bin packing families (lower is better). Rows are sorted by total; rows with any missing or invalid case sort last.
* **Bound (gap)** repeats the bound total and gives the distance to it: a percentage for profit, a bin count for bins. ``0`` means every case reached the bound.

Problem variants
----------------

Two of the three families fix the orientation of every item. py3dbp, jerry800416/3D-bin-packing and gedex/bp3d cannot be told to keep an orientation; they rotate freely and therefore solve a **relaxed** problem on those families. Their rows are marked "rotation relaxed", their values may legitimately exceed the fixed-pose bound, and they never receive a star there. On the THPACK9 family every orientation is allowed for everybody, so no row is relaxed. The U-Nesting strategies and the reference codes honour the fixed pose.

How the third-party libraries were driven
-----------------------------------------

The greedy Python and Go libraries are bin-loading heuristics with no notion of a knapsack objective. On the knapsack family they were given the single container and the item list in two orders (largest first and as listed) and the better valid packing was kept; the profit is then the sum over the items they managed to place. On the bin packing families they were given one candidate bin per item and the number of bins actually used was counted. The U-Nesting strategies expose a single-container API; bins were filled one after another, each call receiving the items left over from the previous one, with the strategy's own time budget per call. The Martello-Pisinger-Vigo code was run with the generator's default general-packing parameters and reports a lower and an upper bound; the CP-SAT reference is an exact model of the fixed-pose knapsack whose ``OPTIMAL`` status is the proof used in the bound row.

Caveats
-------

* **Scope, not quality of engineering.** py3dbp, its Go and fork variants and U-Nesting's greedy strategies are designed to load a container in milliseconds with simple rules; PackingSolver is an anytime optimisation solver that spends its whole budget. The tables measure what each returns under the stated budget on these instances, nothing more.
* **Small, constraint-free instances.** No weights, stability, stacking or unloading constraints are used; several of the libraries support such constraints and PackingSolver's ``box`` solver does not.
* **Single run, single machine.** Metaheuristics and upstream's anytime search vary between runs; the proven-optimal cells are stable, the others may move by a few units.
* **Threads.** PackingSolver used several cores on the knapsack cases while the other libraries ran on one. On the 30-item class-9 replicates and on 31 THPACK9 instances its solves finished in about one second with a closed proof, so the difference does not explain the gap there; on the larger cases it used the full 10 s like the metaheuristics.
* **Third-party data ships with the docs.** The third-party placements live in ``tools/benchmarks/third_party.json`` with library version, algorithm label and budget per entry. They were produced by the maintainers with each library's public release or commit through thin adapters that are not part of this repository; what *is* reproducible from this repository is the independent re-validation of every stored placement and every number derived from it.
