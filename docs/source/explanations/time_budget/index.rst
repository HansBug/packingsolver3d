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

combines quality with a speed score whose scale is a minute of waiting, exactly as F-beta combines recall with precision: :math:`\alpha \to \infty` cares only about quality, :math:`\alpha \to 0` only about speed. The maximiser :math:`T^*(\alpha)` of each curve is the budget that instance deserved; :math:`m(\alpha)` is the 80 % quantile of :math:`(T^* - L) / L` over the instances of the path. ``alpha`` therefore enters only through :math:`m` and :math:`c`, tabulated at 0.25, 0.5, 1, 1.5, 2, 3, 4, 6 and 8 and interpolated in :math:`\log\alpha`. ``alpha=4`` is the balanced default; ``alpha=8`` is the quality-leaning setting. Changing the minute in :math:`S` moves the recommendations the same way ``alpha`` does, so it is fixed.

Stall stop
----------

The budget comes with ``stop_when_unimproved_after = max(L, T/2)`` -- never stop in the first half of the budget, never before the expected first solution -- and ``stop_when_unimproved_for = max(2\,\mathrm{s}, (T - L)/2)``: stop once the search has been silent for half its improvement window. Replayed on the recorded curves this ends the median ``TSMS`` solve 20 % earlier at ``alpha=4`` and 20-45 % earlier at ``alpha=8`` for a loss below one point of the share of instances within 1 % of the reference; single-pass paths are unaffected because their runs end by themselves.

The data
--------

3158 solves in ``ANYTIME`` mode with :doc:`progress events </how_to/budgets/index>` recorded, one per instance: upstream's ``box`` knapsack families bischoff1995 (700), davies1999 (900), egeblad2009 (60) and loh1992 (15), ivancic1989 as multi-bin bin packing (47), a stratified sample of 1240 ROADEF 2022 single-truck ``boxstacks`` instances, 160 synthetic container loads (20' and 40' containers, 2 to 40 item types, 0.6 to 2.0 bin volumes of cargo, knapsack and bin packing, both solvers) and the 40' demo container in three variants, three repeats each. Reference runs lasted 60 s (upstream families) or 150 s (container loads). The ROADEF instances are small (41 items median) and finish in well under a second; they are evaluated but not fitted, so that they do not swamp the ``boxstacks`` paths. Times were measured with thirteen solves sharing a sixteen-core machine and rescaled by an idle-machine calibration on 80 of the instances; the reference machine and the upstream commit are recorded in ``packingsolver3d._time_budget_constants.REFERENCE``.

Limits
------

* The model knows the algorithm, not the geometry. Two instances with the same size, type count and fill can differ several-fold in latency (the log residuals have a standard deviation of 0.4 to 1.1 depending on the path); the coverage quantile absorbs that by over-estimating.
* ``boxstacks`` with several bins is slow by construction at the pinned commit: ``SVC`` solves every bin with a full fixed-queue pass before it reports anything, and 17 of 40 synthetic bin-packing loads found no solution within 150 s. The recommendation for that path is that latency at the 98 % quantile, capped at 600 s; treat a recommendation at the cap as "this instance shape is beyond what the multi-bin ``boxstacks`` path handles quickly".
* Very small instances (``TS`` on a few dozen items) get a constant of a few seconds: their first solution is instantaneous and every further second buys tenths of a percent.
* ``alpha=8`` deliberately spends minutes on overfull containers because their curves keep improving for minutes; if that is too long for an interactive tool, use ``alpha=4`` and the stall stop.
