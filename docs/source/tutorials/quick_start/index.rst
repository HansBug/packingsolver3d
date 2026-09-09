Quick start: your first packing
===============================

This tutorial takes a fresh Python environment to a solved three-dimensional bin packing instance and shows how to read what came back. Everything runs in-process; no external executable, no files on disk.

Install
-------

.. code-block:: bash

   pip install packingsolver3d

Wheels exist for Linux, macOS and Windows on x86_64 and arm64; see :doc:`/how_to/installation/index` for the exact Python versions per platform and for installing from source elsewhere.

Describe the instance
---------------------

An :class:`~packingsolver3d.model.Instance` is built from bin types and item types. Both are frozen dataclasses; ``copies`` says how many identical pieces exist.

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, box

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
       item_types=[
           ItemType(x=20, y=30, z=40, copies=6),
           ItemType(x=15, y=15, z=15, copies=4),
       ],
       objective=Objective.BIN_PACKING,
   )

Every item type is mandatory by default: the solver must place all ten pieces. That default comes from upstream (``copies_min = -1`` means "all copies" for every objective except knapsack), and :doc:`/explanations/upstream_behaviours/index` explains why passing ``copies_min=0`` would make an empty packing the correct answer.

Solve
-----

.. code-block:: python

   result = box.solve(instance, time_limit=2.0)

``time_limit`` is in seconds and is handed to upstream's own timer. On a ten-item instance the solver finishes in a few milliseconds, so the limit never triggers; on real instances you should always pass one, otherwise the solver runs until its schedule is exhausted.

Read the result
---------------

.. code-block:: python

   >>> result.status
   <Status.OPTIMAL: 'optimal'>
   >>> result.value, result.bound
   (1.0, 1.0)
   >>> result.number_of_bins, len(result.placements)
   (1, 10)
   >>> result.placements[0]
   Placement(item_type_id=0, bin_id=0, x=0, y=0, z=0, lx=20, ly=30, lz=40, rotation=<Rotation.XYZ: 'XYZ'>, stack_id=None, group_id=None)

.. raw:: html
   :file: ../../_static/figures/box_bin_packing.html

.. only:: latex

   .. image:: ../../_static/figures/box_bin_packing.png
      :width: 90%

The figure is the same result drawn with :func:`packingsolver3d.visual.plot_result` (see :doc:`/how_to/visualization/index`); drag to rotate it.

Three things are worth pausing on:

* ``value`` is what the solver achieved (one bin); ``bound`` is what it proved (at least one bin is needed). The status is ``OPTIMAL`` only because the two agree; had the solver stopped at a two-bin packing with the same bound, the status would be ``FEASIBLE``. :doc:`/explanations/statuses/index` has the full rule.
* ``placements`` are plain values: item type, bin, lower corner, placed extents after rotation, and the rotation token upstream used.
* ``result.statistics`` holds upstream's own statistics block verbatim (``VolumeLoad``, ``NumberOfUnpackedItems``, ...), and ``result.run`` records the exact options that were passed, upstream's log if you asked for one, and the wall time, so the run can be reproduced.

Objectives other than bin packing
---------------------------------

Change ``objective`` and the same call answers a different question:

.. code-block:: python

   knapsack = Instance(
       bin_types=[BinType(x=100, y=100, z=100, copies=1)],
       item_types=instance.item_types,
       objective=Objective.KNAPSACK,
   )
   result = box.solve(knapsack, time_limit=2.0)
   result.value   # 157500.0: item profit, which defaults to volume upstream

:class:`~packingsolver3d.model.Objective` lists every upstream token; :doc:`/reference/solver_options/index` says which ones report a bound.

Next
----

* Stacking rules, weights and trucks: :doc:`/tutorials/boxstacks/index`.
* Running many instances under a budget: :doc:`/how_to/budgets/index`.
