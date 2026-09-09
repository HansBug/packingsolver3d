Reference map
=============

Reference pages state facts: what a field means, what an option maps to, which error is raised when. They do not teach or argue. For a first tour see :doc:`/tutorials/index`; for the reasoning behind a behaviour see :doc:`/explanations/index`.

Pages
-----

* :doc:`model_fields/index` -- every field of ``ItemType``, ``BinType``, ``SemiTrailerTruck``, ``Defect`` and ``Instance``, its upstream counterpart, its default and which solver honours it.
* :doc:`solver_options/index` -- every keyword argument of ``box.solve`` and ``boxstacks.solve`` and the upstream parameter behind it.
* :doc:`errors/index` -- the exception hierarchy and the condition that raises each class.
* :doc:`API map </api_doc_en>` -- the generated per-module API documentation.

.. toctree::
    :maxdepth: 1
    :hidden:

    model_fields/index
    solver_options/index
    errors/index
