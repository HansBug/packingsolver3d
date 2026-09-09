Model fields
============

All models are frozen dataclasses. A field left ``None`` is not sent to upstream, so upstream's default applies -- the same default its CSV reader uses when the column is absent. "Solver" says which engine honours the field; :func:`packingsolver3d.box.validate` refuses instances that set a ``boxstacks``-only field.

``ItemType``
------------

.. list-table::
   :header-rows: 1

   * - Field
     - Upstream
     - Default
     - Solver
   * - ``x``, ``y``, ``z``
     - ``add_item_type(x, y, z)``
     - required, positive
     - both
   * - ``profit``
     - ``set_item_type_profit``
     - ``None`` -> upstream uses ``x * y * z``
     - both
   * - ``weight``
     - ``set_item_type_weight``
     - ``0.0``
     - both
   * - ``copies``
     - ``set_item_type_copies``
     - ``1``
     - both
   * - ``copies_min``
     - ``set_item_type_copies_min``
     - ``None`` -> upstream ``-1``: all copies mandatory, none under knapsack
     - both
   * - ``rotations``
     - ``add_item_type_rotation`` per entry
     - ``None`` -> upstream ``{XYZ}``; ``boxstacks`` places ``XYZ``/``YXZ`` only
     - both
   * - ``group_id``
     - ``set_item_type_group``
     - ``None`` -> ``0``
     - boxstacks
   * - ``stackability_id``
     - ``set_item_type_stackability_id``
     - ``None`` -> ``0``
     - boxstacks
   * - ``nesting_height``
     - ``set_item_type_nesting_height``
     - ``None`` -> ``0``
     - boxstacks
   * - ``maximum_stackability``
     - ``set_item_type_maximum_stackability``
     - ``None`` -> unlimited
     - boxstacks
   * - ``maximum_weight_above``
     - ``set_item_type_maximum_weight_above``
     - ``None`` -> unlimited
     - boxstacks

Rotation tokens are upstream's: ``XYZ, YXZ, ZYX, YZX, XZY, ZXY``. The placed extents of a box ``(x, y, z)`` under each are ``(x, y, z)``, ``(y, x, z)``, ``(z, y, x)``, ``(y, z, x)``, ``(x, z, y)``, ``(z, x, y)``, from upstream's ``ItemType::x/y/z(Rotation)``.

``BinType``
-----------

.. list-table::
   :header-rows: 1

   * - Field
     - Upstream
     - Default
     - Solver
   * - ``x``, ``y``, ``z``
     - ``add_bin_type(x, y, z)``
     - required, positive
     - both
   * - ``cost``
     - ``set_bin_type_cost``
     - ``None`` -> upstream uses ``x * y`` (an area)
     - both
   * - ``copies``
     - ``set_bin_type_copies``
     - ``1``
     - both
   * - ``copies_min``
     - ``set_bin_type_copies_min``
     - ``0``
     - both
   * - ``maximum_weight``
     - ``set_bin_type_maximum_weight``
     - ``None`` -> unlimited
     - both
   * - ``maximum_stack_density``
     - ``set_bin_type_maximum_stack_density``
     - ``None`` -> unlimited
     - boxstacks
   * - ``semi_trailer_truck``
     - ``set_bin_type_semi_trailer_truck_parameters``
     - ``None`` -> not a truck
     - boxstacks

``SemiTrailerTruck``
--------------------

Mirrors upstream's ``SemiTrailerTruckData`` (``algorithms/truck.hpp``). Distances are lengths, weights are weights, in the instance's units; geometry defaults to ``0`` and the two maxima to unlimited, exactly as upstream. Upstream's ``check()`` validates the geometry and rejects, for example, a zero ``harness_rear_axle_distance``.

``tractor_weight``, ``front_axle_middle_axle_distance``, ``front_axle_tractor_gravity_center_distance``, ``front_axle_harness_distance``, ``empty_trailer_weight``, ``harness_rear_axle_distance``, ``trailer_gravity_center_rear_axle_distance``, ``trailer_start_harness_distance``, ``rear_axle_maximum_weight``, ``middle_axle_maximum_weight``.

``Defect``
----------

``bin_type_id``, ``x``, ``y``, ``lx``, ``ly`` -> ``add_defect(bin_type_id, x, y, w, h)``; ``boxstacks`` only, and see :doc:`/explanations/upstream_behaviours/index` for what upstream does with it.

``Instance``
------------

.. list-table::
   :header-rows: 1

   * - Field
     - Upstream
     - Default
   * - ``bin_types``, ``item_types``
     - the builder calls above, in order; ids are positions
     - required, non-empty
   * - ``objective``
     - ``set_objective``
     - ``Objective.DEFAULT`` (upstream's ``default`` token)
   * - ``defects``
     - ``add_defect`` per entry
     - ``()``
   * - ``unloading_constraint``
     - ``set_unloading_constraint``
     - ``None``; ``boxstacks`` only, may be overridden per call
