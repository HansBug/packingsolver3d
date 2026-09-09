Stacks, weights and trucks with ``boxstacks``
=============================================

``boxstacks`` is upstream's second three-dimensional solver. Items are placed in vertical stacks standing on the bin floor, and the model gains stackability groups, nesting, weight limits above an item, stack density, unloading order, floor defects and a semi-trailer truck axle-weight model. The Python model is the same :class:`~packingsolver3d.model.Instance`; the extra fields are simply left ``None`` for ``box``.

A stacking instance
-------------------

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, boxstacks

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5,
                          maximum_weight=1000, maximum_stack_density=10)],
       item_types=[
           ItemType(x=20, y=30, z=40, copies=6, weight=5,
                    stackability_id=0, maximum_stackability=3, maximum_weight_above=100),
       ],
       objective=Objective.BIN_PACKING,
   )
   result = boxstacks.solve(instance, time_limit=2.0)

The result now carries stacks:

.. code-block:: python

   >>> result.number_of_bins, len(result.bins[0].stacks), len(result.placements)
   (1, 3, 6)
   >>> result.bins[0].stacks[0]
   Stack(stack_id=0, bin_id=0, x=0, y=0, lx=20, ly=30, lz=80)
   >>> result.placements[0].stack_id, result.placements[0].group_id
   (0, 0)

Each placement knows its stack; each stack knows its footprint and total height. ``maximum_stackability=3`` caps a stack at three copies; here upstream's search settled on three stacks of two (``lz=80`` is two 40-high items), which is one of several packings with the same, optimal, bin count.

.. raw:: html
   :file: ../../_static/figures/boxstacks_stacks.html

.. only:: latex

   .. image:: ../../_static/figures/boxstacks_stacks.png
      :width: 90%

The figure shows a two-item-type variant of this instance coloured by stack (``plot_result(result, color_by='stack')``).

Two rules the solver imposes
----------------------------

Both come from upstream and are checked before anything is sent to it:

* Item types that share a ``(group_id, stackability_id)`` bucket must have a footprint in common (over their allowed rotations). Upstream groups stacks by that bucket alone and only discovers a mismatch when it assembles the solution, so the package raises :class:`~packingsolver3d.errors.StackSemanticsError` up front. Give differently shaped items different ``stackability_id`` values.
* Items stay upright: only the ``XYZ`` and ``YXZ`` rotations are placed. An item type whose ``rotations`` allow neither is refused with :class:`~packingsolver3d.errors.UnsupportedFeatureError`.

Passing this instance to :func:`packingsolver3d.box.solve` instead raises :class:`~packingsolver3d.errors.UnsupportedFeatureError`: the ``box`` model has no notion of stacks and would otherwise solve a different problem in silence.

Unloading order and defects
---------------------------

``group_id`` orders unloading (higher groups leave first); an :class:`~packingsolver3d.model.UnloadingConstraint` restricts how items may be moved out, and can be set on the instance or overridden per call:

.. code-block:: python

   from packingsolver3d import UnloadingConstraint
   result = boxstacks.solve(instance, time_limit=2.0,
                            unloading_constraint=UnloadingConstraint.ONLY_X_MOVEMENTS)

Floor defects are :class:`~packingsolver3d.model.Defect` rectangles on a bin type. They are forwarded to upstream faithfully, but read :doc:`/explanations/upstream_behaviours/index` first: at the pinned commit upstream does not keep stacks off them.

A semi-trailer truck
--------------------

Axle weights are modelled with :class:`~packingsolver3d.model.SemiTrailerTruck` on the bin type. The numbers below are upstream's own test instance:

.. code-block:: python

   from packingsolver3d import SemiTrailerTruck

   truck = SemiTrailerTruck(
       tractor_weight=8000, front_axle_middle_axle_distance=380,
       front_axle_tractor_gravity_center_distance=100, front_axle_harness_distance=320,
       empty_trailer_weight=6000, harness_rear_axle_distance=800,
       trailer_gravity_center_rear_axle_distance=400, trailer_start_harness_distance=100,
       rear_axle_maximum_weight=20000, middle_axle_maximum_weight=9300,
   )
   instance = Instance(
       bin_types=[BinType(x=1360, y=240, z=260, copies=1, maximum_weight=24000,
                          maximum_stack_density=1000, semi_trailer_truck=truck)],
       item_types=[ItemType(x=100, y=200, z=200, copies=3, weight=2000,
                            stackability_id=0, maximum_stackability=1)],
       objective=Objective.KNAPSACK,
   )
   result = boxstacks.solve(instance)
   len(result.placements)   # 2 of 3: the third item would overload the middle axle

.. raw:: html
   :file: ../../_static/figures/boxstacks_truck.html

.. only:: latex

   .. image:: ../../_static/figures/boxstacks_truck.png
      :width: 90%

Upstream validates the geometry (``SemiTrailerTruckData::check``); a truck without, say, ``harness_rear_axle_distance`` is rejected with :class:`~packingsolver3d.errors.InvalidInstanceError` carrying upstream's message.

Next
----

* Every field and its upstream meaning: :doc:`/reference/model_fields/index`.
* The behaviours above, with evidence: :doc:`/explanations/upstream_behaviours/index`.
