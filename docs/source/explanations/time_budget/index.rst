How the time budget is estimated
================================

:func:`~packingsolver3d.recommend_time_budget` has to answer a question the solver itself does not: how long is worth waiting? In ``ANYTIME`` mode PackingSolver runs until its time limit (:doc:`/explanations/upstream_behaviours/index`), so a limit that is too short returns a truncated pass and one that is too long wastes the user's time. This page explains the model behind the recommendation, the data it was fitted on and its limits. The campaign scripts, the fitted constants and the full tables live in ``experiments/time_budget/`` of the repository.

One formula per algorithm path
------------------------------

Upstream picks its algorithm from the instance shape: number of bins, mean items per bin (largest bin volume over mean item volume) and mean copies per type, with thresholds at 16 and 64. :func:`~packingsolver3d.algorithm_path` replicates that choice and agreed with the labels of every one of the 3140 recorded runs that produced a solution. The model is then one small formula per path, built from what each algorithm does rather than from the data alone:

.. math::

    T(\alpha) = L \,(1 + m(\alpha)) + c(\alpha)

* :math:`L` is the **latency** to the first solution: the cost of one full pass. For ``TSMS`` (tree search over maximal spaces, single-bin ``box`` knapsack with many items) it is block generation plus a first beam pass; for ``SOR`` (single-bin ``boxstacks``) the first sequential-onedimensional-rectangle pass; for ``SSK`` and ``SVC`` (several bins) the first iteration over all bins. It is a power law in the instance size -- items for ``box``, stacks for ``boxstacks`` -- and the number of item types, :math:`L = e^{a}\, \mathrm{size}^{b}\, \mathrm{types}^{c}`, with two algorithm-specific terms: ``TSMS`` adds a constant block-generation step once there are four or more item types (block generation hits its 10000-block cap and costs the same regardless of size), and ``SOR`` multiplies by a constant when the cargo does not fit the bin (the onedimensional stage then has to select items, which is what makes an overfull first pass slow).
* **Growth paths** (``TSMS``, ``TS``, ``SOR``) double their queue between passes, so reaching pass :math:`k` costs :math:`L\,(2^k - 1)`: the time worth waiting after the first solution is a multiple :math:`m(\alpha)` of :math:`L`. **Single-pass paths** (``SSK``, box and boxstacks ``SVC``) are essentially done after the first complete solution -- ``SSK`` usually proves optimality, ``SVC`` stops by itself at two bins or when everything is packed -- so :math:`m = 0` and only a small additive :math:`c(\alpha)` remains.

The coefficients are fitted by least squares in log space with the exponents constrained to be non-negative (a bigger or more heterogeneous instance never gets a shorter budget). The intercept is then shifted to a coverage quantile of the residuals -- 90 % for growth paths, 98 % for single-pass paths where a generous cap costs nothing because the run ends by itself -- which is what makes the recommendation a loose upper bound rather than a median.

What ``alpha`` means
--------------------

For each recorded curve :math:`q(t)` (value at time :math:`t` relative to the value at the end of a 60 s or 150 s run) and each candidate budget :math:`t`, the score

.. math::

    F_\alpha = \frac{(1 + \alpha^2)\, S\, q}{\alpha^2 S + q}, \qquad S = \frac{1}{1 + t / 60\,\mathrm{s}}

combines quality with a speed score whose scale is a minute of waiting, exactly as F-beta combines recall with precision: :math:`\alpha \to \infty` cares only about quality, :math:`\alpha \to 0` only about speed. The maximiser :math:`T^*(\alpha)` of each curve is the budget that instance deserved; :math:`m(\alpha)` is the 80 % quantile of :math:`(T^* - L) / L` over the instances of the path. ``alpha`` therefore enters only through :math:`m` and :math:`c`, tabulated at 0.25, 0.5, 1, 1.5, 2, 3, 4, 6 and 8 and interpolated in :math:`\log\alpha`. ``alpha=4`` is balanced and the default for ``box``; ``alpha=8`` leans towards quality and is the default for ``boxstacks`` (``DEFAULT_ALPHA``): on the container loads of the campaign ``alpha=4`` left 16 % of the single-bin ``boxstacks`` solves below 99 % of the reference, ``alpha=8`` none, at the price of roughly a minute more. Changing the minute in :math:`S` moves the recommendations the same way ``alpha`` does, so it is fixed.

Stall stop
----------

The budget comes with ``stop_when_unimproved_after = max(L, T/2)`` -- never stop in the first half of the budget, never before the expected first solution -- and ``stop_when_unimproved_for = max(2\,\mathrm{s}, (T - L)/2)``: stop once the search has been silent for half its improvement window. Replayed on the recorded curves this ends the median ``TSMS`` solve 20 % earlier at ``alpha=4`` and 20-45 % earlier at ``alpha=8`` for a loss below one point of the share of instances within 1 % of the reference; single-pass paths are unaffected because their runs end by themselves.

Stopping policies compared
--------------------------

The budget is a *policy*, not just a number: a time limit, an earliest stop and a patience. Three ways of stopping were replayed on every recorded curve (``experiments/time_budget/policy_compare.py``), also with the machine two times slower or two times faster than assumed while the policy keeps its parameters in seconds:

* **A, time limit only** -- the formula's ``time_limit`` and nothing else.
* **B, stagnation only** -- a fixed patience of 3, 5 or 10 s from the start of the solve, cap 600 s; **B_L** the same but never before the predicted first solution :math:`L`.
* **C, the combination shipped here** -- ``time_limit`` as the cap, ``after = max(L, T/2)``, ``patience = max(2 s, (T - L)/2)``.

.. list-table:: Share of solves ending below 99 % of the reference / share ending with no solution / median time used (idle-machine seconds)
   :header-rows: 1
   :widths: 26 14 20 20 20

   * - path (instances)
     - policy
     - speed as assumed
     - machine 2x slower
     - machine 2x faster
   * - box TSMS (1653)
     - A, alpha 4
     - 4.5 % / 0.2 % / 5.2 s
     - 13.9 % / 0.2 % / 5.2 s
     - 1.8 % / 0 % / 5.2 s
   * -
     - B, 5 s
     - 1.9 % / 0.7 % / 8.9 s
     - 5.0 % / 0.8 % / 10.2 s
     - 0.8 % / 0.5 % / 8.3 s
   * -
     - C, alpha 4
     - 6.0 % / 0.2 % / 4.3 s
     - 18.1 % / 4.4 % / 4.8 s
     - 2.5 % / 0.2 % / 4.0 s
   * -
     - C, alpha 8
     - 1.9 % / 0.2 % / 10.3 s
     - 4.3 % / 0.2 % / 11.2 s
     - 0.7 % / 0 % / 9.9 s
   * - boxstacks SOR, container loads (49)
     - A, alpha 4
     - 16.3 % / 0 % / 25 s
     - 28.6 % / 0 % / 25 s
     - 6.1 % / 0 % / 18 s
   * -
     - B, 5 s
     - 36.7 % / 20.4 % / 7.8 s
     - 46.9 % / 30.6 % / 6.6 s
     - --
   * -
     - B_L, 10 s
     - 22.4 % / 8.2 % / 17 s
     - 28.6 % / 12.2 % / 19 s
     - --
   * -
     - C, alpha 8
     - 0 % / 0 % / 67 s
     - 6.1 % / 0 % / 68 s
     - 0 % / 0 % / 39 s
   * - box SSK, several bins (55)
     - B, 5 s
     - 30.9 % / 25.5 % / 2.3 s
     - --
     - --
   * -
     - B_L, A or C
     - 3.6-7.3 % / 1.8-3.6 % / 2.3 s
     - 18.2 % / 10.9 % / 4.6 s
     - 5.5 % / 1.8 % / 1.1 s
   * - boxstacks SVC, several bins (32)
     - B, 10 s
     - 78 % / 78 % / 10 s
     - --
     - --
   * -
     - B_L, A or C
     - 3.1 % / 3.1 % / 35 s
     - 34.4 % / 34.4 % / 57 s
     - 0 % / 0 % / 17 s

What the replay shows:

* A bare stagnation stop is not a substitute for a budget. It is the most speed-robust policy on ``TSMS`` (first solution within a second or two) but it stops before any solution exists on every slow-first-solution path: 20-45 % of the single-bin ``boxstacks`` loads, 25-36 % of the multi-bin ``box`` loads and 78-100 % of the multi-bin ``boxstacks`` loads end with nothing. The earliest-stop guard needs the latency model, which is why ``stop_when_unimproved_after`` exists and why it is filled from :math:`L`.
* A fixed patience also fights the algorithms: the queue-doubling paths space their improvements further and further apart, so a constant patience always cuts some level; the loss is what the remaining levels would have added (20-27 % of the ``SOR`` loads stay below 99 % with 10 s of patience). The patience has to scale with the improvement window, which is what ``(T - L)/2`` does.
* A bare time limit is predictable (it is the progress-bar scale) and accurate where the model is, but it truncates when the machine is slower than assumed (``TSMS``: 4.5 % to 13.9 % below 99 %) and wastes time when it is faster (half of the ``alpha=8`` solves run to the limit on a machine twice as fast).
* The combination C is the shortest at equal quality when the speed is right and ends early by itself on a fast machine. Its weakness is that ``after`` and ``patience`` are absolute seconds: two times slower than assumed, ``alpha=4`` stops 4.4 % of the ``TSMS`` solves before their first solution. ``alpha=8`` tolerates that error much better, and calibrating ``speed`` removes it.
* A patience relative to the *observed* first-solution time (``kappa`` times it, implemented by a ``progress_callback`` that returns ``False``) is even more speed-robust on ``TSMS`` (4.4 % below 99 % on a machine twice as slow with ``kappa=4``, against 18 % for C at ``alpha=4``) but weaker on ``SOR``, whose first pass is cheap relative to its later levels. It is an optional second trigger for a calling application, not a replacement.

Guidance for a calling application
----------------------------------

What each field of :class:`~packingsolver3d.TimeBudget` is for, written for a desktop tool such as Stowly whose settings hold one "maximum time" and, since the stagnation stop exists, a "stop after N seconds without improvement":

* ``time_limit`` is the *maximum time* setting and the full scale of a time-driven progress bar. Expect the solve to end before it: it is a coverage quantile, not a median.
* ``stop_when_unimproved_for`` and ``stop_when_unimproved_after`` are the *stop-when-stalled* settings; fill both from the budget rather than letting the user pick one number, because the second protects the slow-first-solution paths and the first must scale with the algorithm. A ``RunRecord.stop_reason`` of ``'unimproved'`` is the normal, good outcome and worth showing as "finished early: N s without improvement".
* ``alpha`` is the only dial worth exposing, as a coarse choice (faster / balanced / thorough mapping to 2 / 4 / 8) rather than a number; keep the solver-dependent default (``box`` 4, ``boxstacks`` 8).
* ``speed`` should be calibrated, not typed: after each solve compute ``budget.typical_latency * budget.speed / observed_first_solution_time`` from the first :class:`~packingsolver3d.ProgressEvent` (the median prediction, not the covered ``latency``), smooth it over runs (an exponential average with a weight of about 0.3 on the newest value is enough) and persist it per machine. Before any calibration exists, prefer ``alpha=8`` or a ``speed`` below 1: the replay shows the combination degrades gracefully when the machine is faster than assumed and badly when it is slower.
* ``path``, ``latency`` and ``improvement`` are explanations: "expected first solution in about L s", and a warning when ``path == 'SVC'`` on ``boxstacks`` (several bins) or when ``time_limit`` sits at the 600 s cap, because those are the shapes the pinned upstream handles slowly.
* Optional second trigger: a ``progress_callback`` that returns ``False`` once no improvement has arrived for ``kappa`` (about 4) times the observed first-solution time, for ``box`` only; it shortens ``TSMS`` solves further and is robust to machine speed by construction. Keep the budget's own stall stop as the first trigger.

The data
--------

3158 solves in ``ANYTIME`` mode with :doc:`progress events </how_to/budgets/index>` recorded, one per instance: upstream's ``box`` knapsack families bischoff1995 (700), davies1999 (900), egeblad2009 (60) and loh1992 (15), ivancic1989 as multi-bin bin packing (47), a stratified sample of 1240 ROADEF 2022 single-truck ``boxstacks`` instances, 160 synthetic container loads (20' and 40' containers, 2 to 40 item types, 0.6 to 2.0 bin volumes of cargo, knapsack and bin packing, both solvers) and the 40' demo container in three variants, three repeats each. Reference runs lasted 60 s (upstream families) or 150 s (container loads). The ROADEF instances are small (41 items median) and finish in well under a second; they are evaluated but not fitted, so that they do not swamp the ``boxstacks`` paths. Times were measured with thirteen solves sharing a sixteen-core machine and rescaled by an idle-machine calibration on 80 of the instances; the reference machine and the upstream commit are recorded in ``packingsolver3d._time_budget_constants.REFERENCE``.

Limits
------

* The model knows the algorithm, not the geometry. Two instances with the same size, type count and fill can differ several-fold in latency (the log residuals have a standard deviation of 0.4 to 1.1 depending on the path); the coverage quantile absorbs that by over-estimating.
* ``boxstacks`` with several bins is slow by construction at the pinned commit: ``SVC`` solves every bin with a full fixed-queue pass before it reports anything, and 17 of 40 synthetic bin-packing loads found no solution within 150 s. The recommendation for that path is that latency at the 98 % quantile, capped at 600 s; treat a recommendation at the cap as "this instance shape is beyond what the multi-bin ``boxstacks`` path handles quickly".
* Very small instances (``TS`` on a few dozen items) get a constant of a few seconds: their first solution is instantaneous and every further second buys tenths of a percent.
* ``alpha=8`` deliberately spends minutes on overfull containers because their curves keep improving for minutes; if that is too long for an interactive tool, use ``alpha=4`` (the ``box`` default) or ``alpha=6`` for ``boxstacks`` and keep the stall stop.
