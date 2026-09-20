Budgets, algorithm switches and batch runs
==========================================

Use this page when you run the solver on instances that do not finish instantly: a research campaign, a benchmark, a service with a response-time target.

Time budget
-----------

.. code-block:: python

   result = box.solve(instance, time_limit=35.0)

``time_limit`` (seconds) is handed to upstream's timer. The search phases check it at their own checkpoints, so a run can overshoot by the length of one checkpoint interval; measure ``result.run.wall_time`` if the exact figure matters. Without a limit upstream runs its whole schedule, which on a hard instance means a very long time.

Memory budget
-------------

.. code-block:: python

   result = box.solve(instance, time_limit=35.0, memory_limit=4096)

``memory_limit`` (MiB) is upstream's own ``memory_limit_megabytes``: the solver compares its resident size against it at checkpoints and stops growing. It is a soft limit -- nothing outside the solver enforces it. The section on isolation below shows how to add a hard one.

Optimisation modes
------------------

:class:`~packingsolver3d.model.OptimizationMode` selects upstream's schedule:

* ``ANYTIME`` (default) improves the incumbent until the limit;
* ``NOT_ANYTIME`` and ``NOT_ANYTIME_DETERMINISTIC`` run a fixed schedule, the latter reproducibly;
* ``NOT_ANYTIME_SEQUENTIAL`` is the fixed schedule with the sequential mode passed down to every sub-solver; upstream's own unit tests use it.

.. code-block:: python

   from packingsolver3d import OptimizationMode
   result = box.solve(instance, time_limit=35.0,
                      optimization_mode=OptimizationMode.NOT_ANYTIME_DETERMINISTIC)

Progress and early stop
-----------------------

.. code-block:: python

   def watch(event):
       print(f"{event.time:6.2f} s  {event.number_of_items} items  {event.label}")
       return event.number_of_items < 1000      # False stops the solve

   result = box.solve(instance, time_limit=60.0, progress_callback=watch)
   result.run.stop_reason                      # 'callback' if watch returned False, else None

``progress_callback`` is upstream's ``new_solution_callback``: it runs every time the incumbent improves, with a :class:`~packingsolver3d.result.ProgressEvent` holding the few numbers the bridge copies out of the incumbent (time on upstream's clock, items, bins, profit, cost, upstream's label for the algorithm that found it). The full packing is not available before the end; the event is a snapshot, not a handle. Return ``False`` to stop the solve at that point -- upstream checks the stop flag at its next node, so the solve returns within milliseconds with the incumbent as its result. An exception raised inside the callback stops the solve the same way and is re-raised unchanged once the solver has returned. The callback may run on one of upstream's worker threads (``box``'s anytime tree search uses several); it always holds the GIL, so plain Python code is safe, but keep it short.

How often it fires depends on the algorithm: ``box``'s anytime tree search reports every improvement, typically several per second; ``boxstacks`` reports once per queue-size level of its single-bin algorithm (a handful in the first seconds, then rarely) and once per iteration of its multi-bin one. In the ``NOT_ANYTIME_*`` modes there is usually a single event, at the end.

Stopping when the search stalls
-------------------------------

.. code-block:: python

   result = box.solve(instance, time_limit=120.0, stop_when_unimproved_for=10.0)
   result.run.stop_reason      # 'unimproved' if ten seconds passed without a new incumbent, else None

In ``ANYTIME`` mode the search only ends on the time limit, a stop signal or a proof of optimality (see :doc:`/explanations/upstream_behaviours/index`), so ``time_limit`` is normally the whole budget even when the incumbent stopped moving long ago. ``stop_when_unimproved_for`` adds the usual anytime termination: a watchdog thread compares upstream's clock with the time of the last improvement and raises upstream's own stop signal once the gap reaches the given number of seconds. The solve returns within milliseconds with the incumbent intact and ``result.run.stop_reason == 'unimproved'``.

Until a first solution exists the clock runs from the start of the solve. ``box`` finds a first solution within about a second on most instances, but the single-bin algorithm of ``boxstacks`` reports nothing before its first pass is complete (a few seconds on a container with several hundred stacks), so give it ``stop_when_unimproved_after`` when the patience is short:

.. code-block:: python

   result = boxstacks.solve(instance, time_limit=120.0,
                            stop_when_unimproved_for=5.0, stop_when_unimproved_after=15.0)

A fixed patience suits searches that improve at a steady rate. PackingSolver's anytime searches double their queues between passes, so the gaps between improvements grow with the time already spent, and a fixed patience either cuts a late pass short or wastes most of the budget. ``stop_when_unimproved_ratio`` makes the patience relative: the solve stops once no improvement has arrived for the larger of ``stop_when_unimproved_for`` and the ratio times the time of the last improvement, and never before a first solution exists:

.. code-block:: python

   result = boxstacks.solve(instance, time_limit=120.0, stop_when_unimproved_for=5.0, stop_when_unimproved_ratio=2.0)

A last improvement at 6 s then buys 12 s of silence before the stop, one at 30 s buys 60 s. :func:`~packingsolver3d.recommend_time_budget` sets the ratio from ``alpha``.

All three knobs compose with ``progress_callback``: a callback that returns ``False`` wins (``stop_reason == 'callback'``), and the watchdog never calls into Python.

Letting the library pick the budget
-----------------------------------

.. code-block:: python

   from packingsolver3d import recommend_time_budget

   budget = recommend_time_budget(instance, solver='box')          # alpha defaults to 4 for box, 8 for boxstacks
   result = box.solve(instance, **budget.as_options())
   budget.time_limit, budget.stop_when_unimproved_for, budget.stop_when_unimproved_after, budget.stop_when_unimproved_ratio, budget.path

:func:`~packingsolver3d.recommend_time_budget` turns the instance into a :class:`~packingsolver3d.TimeBudget`: a ``time_limit`` that is a loose upper bound, plus the three stall-stop knobs above (a relative patience of ``alpha/2`` times the time of the last improvement, a 5 s floor, and the predicted first-solution latency as the earliest stop) so that most solves end well before it. The numbers come from a model fitted on 3158 recorded improvement curves (upstream's benchmark families, a ROADEF 2022 sample, synthetic container loads); :doc:`/explanations/time_budget/index` explains it. Two dials matter:

* ``alpha`` weighs quality against waiting the way F-beta weighs recall against precision: ``4.0`` stops once further passes stop paying for themselves, ``8.0`` waits for the last few tenths of a percent. The default depends on the solver (``DEFAULT_ALPHA``: ``box`` 4, ``boxstacks`` 8, because the single-bin ``boxstacks`` algorithm keeps improving overfull containers for minutes). On the 40' container of the examples ``box`` gets about 13 s at ``alpha=4``, ``boxstacks`` about 70 s at ``alpha=8``; the median solve ends earlier through the stall stop.
* ``speed`` is the speed of the current machine relative to the reference machine (see ``packingsolver3d._time_budget_constants.REFERENCE``); every duration is divided by it. Calibrate it from a solve you have already run: ``speed = budget.typical_latency * budget.speed / measured_first_solution_time`` (``typical_latency`` is the median prediction; ``latency`` is the covered upper estimate the budget itself is built on, so comparing against it would overstate the speed).

The four values form one stopping policy; :doc:`/explanations/time_budget/index` compares it with a bare time limit and a bare stagnation stop on every recorded curve and says what a calling application should do with each field. The recommendation is only as good as upstream's algorithm for the instance shape, and :func:`~packingsolver3d.algorithm_path` tells you which one that is. Two shapes are honest but slow: ``boxstacks`` knapsack (or variable-sized bin packing) with several bins runs ``SVC`` (sequential value correction), whose first complete solution takes tens of seconds on a few hundred items and which ends by itself right after -- the budget is then just that latency, at the 98 % coverage quantile -- and ``box`` / ``boxstacks`` on a container with more cargo than fits keep improving for minutes, which is what ``alpha=8`` pays for. Multi-bin ``boxstacks`` *bin packing* takes ``SSK`` (sequential single knapsack) since upstream ``9bfb9431`` and reports within a second on the container loads of the examples.

Algorithm switches
------------------

The ``box`` solver exposes its portfolio as keyword arguments, each ``True`` / ``False`` / ``None`` (leave to upstream): ``use_tree_search``, ``use_tree_search_maximal_spaces``, ``use_sequential_single_knapsack``, ``use_sequential_value_correction``, ``use_column_generation``, ``use_dichotomic_search``, ``use_dual_feasible_functions``. ``boxstacks`` has no switches. :doc:`/reference/solver_options/index` maps each to the upstream parameter.

Logs
----

``verbosity_level=1`` (or higher) makes upstream print its progress table; the text is captured into ``result.run.stdout`` instead of your terminal.

Running many instances
----------------------

Every result carries what is needed to reproduce it. A campaign loop typically keeps the status, the achieved value and the reported bound apart:

.. code-block:: python

   rows = []
   for name, inst in instances.items():
       r = box.solve(inst, time_limit=35.0, memory_limit=4096,
                     optimization_mode=OptimizationMode.NOT_ANYTIME_DETERMINISTIC)
       rows.append({
           'instance': name,
           'status': r.status.value,           # 'optimal' / 'feasible' / 'no-solution' / 'infeasible'
           'value': r.value, 'bound': r.bound, # never merge these two columns
           'bins': r.number_of_bins,
           'solve_time': r.solve_time, 'wall_time': r.run.wall_time,
           'options': r.run.options,           # exactly what upstream received
       })

``result.to_json()`` is a machine-independent snapshot of the packing (it leaves ``run`` out on purpose).

Isolation: hard limits and crash containment
--------------------------------------------

The solver runs inside your interpreter. Two consequences follow: a crash inside upstream ends the process, and no hard memory limit can be applied from within. When either matters, run each solve in a worker process. :class:`~packingsolver3d.model.Instance` and :class:`~packingsolver3d.result.Result` are picklable, so this is a few lines:

.. code-block:: python

   import multiprocessing as mp
   import resource

   def _worker(conn, instance, kwargs, mem_mib):
       limit = mem_mib * 1024 * 1024
       resource.setrlimit(resource.RLIMIT_AS, (limit, limit))   # POSIX only
       from packingsolver3d import box
       try:
           conn.send(('ok', box.solve(instance, **kwargs)))
       except Exception as err:                                  # upstream-side failure
           conn.send(('error', repr(err)))

   def solve_isolated(instance, time_limit=35.0, mem_mib=4096, grace=30.0, **kwargs):
       parent, child = mp.Pipe(duplex=False)
       kwargs.update(time_limit=time_limit, memory_limit=mem_mib)
       p = mp.get_context('spawn').Process(target=_worker, args=(child, instance, kwargs, mem_mib))
       p.start()
       p.join(time_limit + grace)
       if p.is_alive():
           p.kill(); p.join()
           return 'timeout', None
       if not parent.poll():
           return 'crashed', p.exitcode
       return parent.recv()

This gives the three layers a benchmark harness usually wants: upstream's own soft limits, a hard address-space limit, and a wall-clock guard that also contains crashes.
