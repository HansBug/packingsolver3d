Quick start: what fits in the carry-on
======================================

This tutorial takes a fresh Python environment to a solved three-dimensional packing problem you can look at. The problem is one everybody has had: a 55 x 40 x 23 cm carry-on, more things than will fit, and a sense of how much you want each of them. The solver decides which pieces to take and where each one goes; the figure at the end shows the packing and lets you rotate it. Everything runs in-process; no external executable, no files on disk.

Install
-------

.. code-block:: bash

   pip install "packingsolver3d[plot]"

The ``plot`` extra adds plotly for the figure; the solver itself has no dependencies. Wheels exist for Linux, macOS and Windows on x86_64 and arm64; see :doc:`/how_to/installation/index` for the exact Python versions per platform and for installing from source elsewhere.

Describe the luggage
--------------------

An :class:`~packingsolver3d.model.Instance` is built from bin types and item types, both frozen dataclasses. Here the single bin is the suitcase and every item type is one kind of thing to take: its size in centimetres, a ``profit`` that says how much you want it, and ``copies`` for things you have several of. ``rotations=ALL_ROTATIONS`` lets the solver turn a piece any way it likes; without it an item keeps the orientation you wrote, which is upstream's default.

.. code-block:: python

   from packingsolver3d import ALL_ROTATIONS, BinType, Instance, ItemType, Objective, box

   luggage = {  # name: (x, y, z, value, copies)
       'laptop': (36, 25, 3, 10, 1), 'camera': (15, 10, 8, 9, 1), 'shoes': (30, 20, 12, 8, 1),
       'jacket': (35, 20, 15, 6, 1), 'sweater': (30, 25, 8, 5, 2), 'toiletry bag': (25, 12, 10, 4, 1),
       'hair dryer': (22, 9, 20, 3, 1), 'book': (24, 16, 4, 3, 4), 'souvenir': (10, 10, 10, 2, 6),
       'water bottle': (8, 8, 25, 1, 1),
   }
   names = list(luggage)
   instance = Instance(
       bin_types=[BinType(x=55, y=40, z=23)],
       item_types=[ItemType(x=x, y=y, z=z, profit=value, copies=n, rotations=ALL_ROTATIONS)
                   for x, y, z, value, n in luggage.values()],
       objective=Objective.KNAPSACK,
   )

The nineteen pieces add up to 54,304 cubic centimetres and the suitcase holds 50,600, so something has to stay home. ``Objective.KNAPSACK`` asks for the subset with the highest total value that can actually be packed -- a value of 75 if everything went in. The objective is always explicit: there is no default, because upstream's own ``default`` token produces no solution.

Solve
-----

.. code-block:: python

   result = box.solve(instance, time_limit=3.0)

``time_limit`` is in seconds and is handed to upstream's own timer. The default anytime search keeps improving its best packing until the limit; on this instance three seconds are plenty. Always pass a limit on real instances, otherwise the solver runs until its schedule is exhausted.

Read the result
---------------

.. code-block:: python

   >>> result.status, result.value, result.bound
   (<Status.FEASIBLE: 'feasible'>, 69.0, 72.0)
   >>> len(result.placements)
   18
   >>> packed = [0] * len(names)
   >>> for placement in result.placements:
   ...     packed[placement.item_type_id] += 1
   >>> [(name, count) for name, count in zip(names, packed) if count < luggage[name][4]]
   [('jacket', 0)]

Everything but the jacket fits, for a value of 69 out of 75. Two numbers deserve a pause:

* ``value`` is what the solver achieved. ``bound`` is what it proved: no packing of these pieces is worth more than 72. The two do not meet, so the status is ``FEASIBLE`` and not ``OPTIMAL``; there may or may not be a 70-, 71- or 72-point packing, the solver just could not settle it in three seconds. The package never relabels a good incumbent as a proven optimum, see :doc:`/explanations/statuses/index`.
* ``placements`` are plain values: item type, bin, lower corner, placed extents after rotation and the rotation token upstream used. ``result.statistics`` carries upstream's own statistics block verbatim and ``result.run`` the exact options and the wall time, so the run can be reproduced. Anytime search is not deterministic run to run; on another machine a different low-value piece may be the one left out.

Look at it
----------

.. code-block:: python

   from packingsolver3d.visual import plot_result

   figure = plot_result(result, title='What fits in the carry-on')
   figure.show()                       # or figure.write_html('carry-on.html')

.. raw:: html
   :file: ../../_static/figures/quick_start_suitcase.html

.. only:: latex

   .. image:: ../../_static/figures/quick_start_suitcase.png
      :width: 90%

Drag to rotate, scroll to zoom, hover a box for its item type; the legend maps colours to item types in the order of ``names``, so type 7 is the books and type 8 the souvenirs. :doc:`/how_to/visualization/index` explains the drawing options.

Change the question
-------------------

The same instance answers other questions when ``objective`` changes. With several suitcases and ``Objective.BIN_PACKING`` the solver packs *everything* into as few of them as possible; with ``VARIABLE_SIZED_BIN_PACKING`` it also chooses among suitcase sizes by cost.

.. code-block:: python

   two_bags = Instance(
       bin_types=[BinType(x=55, y=40, z=23, cost=1, copies=3)],
       item_types=instance.item_types,
       objective=Objective.BIN_PACKING,
   )
   result = box.solve(two_bags, time_limit=3.0)
   result.status, result.number_of_bins    # (<Status.OPTIMAL: 'optimal'>, 2)

Two bags are enough for everything, and this time the status is ``OPTIMAL``: the solver's bound proves that one bag cannot hold 54,304 cubic centimetres. :class:`~packingsolver3d.model.Objective` lists every upstream token; :doc:`/reference/solver_options/index` says which ones report a bound.

Next
----

* Stacking rules, weights and trucks: :doc:`/tutorials/boxstacks/index`.
* Running many instances under a budget: :doc:`/how_to/budgets/index`.
* How the solver compares with other libraries on public benchmarks: :doc:`/benchmarks/index`.
