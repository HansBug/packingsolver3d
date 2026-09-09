Welcome to packingsolver3d
==========================

Overview
--------

**packingsolver3d** is an unofficial Python distribution of the two three-dimensional solvers of `PackingSolver <https://github.com/fontanf/packingsolver>`_, ``box`` and ``boxstacks``. Every wheel ships the two upstream executables precompiled, and the Python layer talks to them through files and a subprocess boundary only, so no Python object ever owns solver memory.

Key Features
~~~~~~~~~~~~~

* **Value-in / value-out API** built on frozen dataclasses: :class:`~packingsolver3d.model.Instance` goes in, :class:`~packingsolver3d.result.Result` comes out
* **Two solvers, one model**: :mod:`packingsolver3d.box` for plain 3D packing, :mod:`packingsolver3d.boxstacks` for stacking, unloading and weight rules
* **Auditable runs**: every result carries the argv, exit code, streams, wall time and executable digest that produced it
* **Honest statuses**: a solver-reported bound is never relabelled as a proven optimum; ``OPTIMAL`` means the achieved value met the reported bound
* **Real resource gates**: ``time_limit`` plus a wall-clock guard, ``memory_limit`` enforced as a POSIX address-space rlimit
* **Prebuilt wheels** for Linux, macOS and Windows on CPython 3.7 through 3.14

Quick Start
~~~~~~~~~~~

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, box

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
       item_types=[ItemType(x=20, y=30, z=40, copies=6)],
       objective=Objective.BIN_PACKING,
   )
   result = box.solve(instance, time_limit=2.0)

   assert result.status.name == 'OPTIMAL'
   assert result.number_of_bins == 1
   for placement in result.placements:
       print(placement.bin_id, placement.x, placement.y, placement.z, placement.rotation)

Architecture
~~~~~~~~~~~~

* **Package root** (``packingsolver3d``): re-exports the model, result and error types plus the two solver modules
* **Solver modules** (``packingsolver3d.box``, ``packingsolver3d.boxstacks``): one ``solve`` function each, mirroring the upstream command line options
* **Metadata layer** (``packingsolver3d.config``): package version, pinned upstream commit and build options
* **Executables** (``packingsolver3d.bin``): the precompiled upstream binaries a wheel ships

Upstream and Source
~~~~~~~~~~~~~~~~~~~

* **GitHub Repository**: https://github.com/HansBug/packingsolver3d
* **PackingSolver Upstream**: https://github.com/fontanf/packingsolver

.. include:: api_doc_en.rst
