Errors
======

Every exception derives from :class:`~packingsolver3d.errors.PackingSolverError`, so one ``except`` clause contains the whole package. The subclasses also inherit the matching built-in so that generic handlers keep working.

.. list-table::
   :header-rows: 1

   * - Class
     - Also a
     - Raised when
   * - ``InvalidInstanceError``
     - ``ValueError``
     - the instance is structurally invalid (empty, non-positive extents, ``copies_min`` outside ``[0, copies]``, defect on an unknown bin, non-positive defect extent), an option token is unknown, or upstream's ``InstanceBuilder`` rejects the instance -- the message is then upstream's own
   * - ``StackSemanticsError``
     - ``InvalidInstanceError``
     - two item types share a ``(group_id, stackability_id)`` bucket but have no footprint in common (``boxstacks``)
   * - ``UnsupportedFeatureError``
     - ``ValueError``
     - ``box.solve`` receives stacking fields, defects or an unloading constraint; ``boxstacks.solve`` receives an item type allowing only side rotations
   * - ``SolverFailedError``
     - ``RuntimeError``
     - upstream threw during the solve; ``.run`` carries the partial :class:`~packingsolver3d.result.RunRecord`

Raised before the bridge is called: everything but the upstream-side cases. Nothing returns an empty solution where an error is due; an empty packing that upstream legitimately produced is reported as ``Status.NO_SOLUTION``, not as an exception.
