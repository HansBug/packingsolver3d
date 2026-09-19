Welcome to packingsolver3d
==========================

Overview
--------

**packingsolver3d** is an unofficial Python distribution of the two three-dimensional solvers of `PackingSolver <https://github.com/fontanf/packingsolver>`_, ``box`` and ``boxstacks``. The upstream C++ is compiled together with a thin pybind11 bridge into one extension module; every solve runs in-process and copies its result back into plain Python values, so no Python object ever owns solver memory. The package is maintained independently of PackingSolver and is not endorsed by its author; the solvers themselves are built unmodified from a pinned upstream commit.

Key Features
~~~~~~~~~~~~~

* **Value-in / value-out API** built on frozen dataclasses: :class:`~packingsolver3d.model.Instance` goes in, :class:`~packingsolver3d.result.Result` comes out
* **Two solvers, one model**: :mod:`packingsolver3d.box` for plain 3D packing, :mod:`packingsolver3d.boxstacks` for stacks, weights, trucks, unloading order and defects
* **Honest statuses**: a solver-reported bound is never relabelled as a proven optimum; ``OPTIMAL`` means the achieved value met the reported bound
* **Auditable runs**: every result carries the exact options handed to upstream, upstream's captured log and the wall time
* **Upstream's own limits**: ``time_limit`` and ``memory_limit`` go to the solver's timer and memory check
* **Prebuilt wheels** for Linux, macOS and Windows on x86_64 and arm64, CPython 3.7 through 3.14 where the platform has one

Quick Start
~~~~~~~~~~~

.. code-block:: bash

   pip install packingsolver3d

.. code-block:: python

   from packingsolver3d import ALL_ROTATIONS, BinType, Instance, ItemType, Objective, box
   from packingsolver3d.visual import plot_result       # pip install "packingsolver3d[plot]"

   luggage = {  # name: (x, y, z, value, copies) -- a 55 x 40 x 23 cm carry-on and what you would like to take
       'laptop': (36, 25, 3, 10, 1), 'camera': (15, 10, 8, 9, 1), 'shoes': (30, 20, 12, 8, 1),
       'jacket': (35, 20, 15, 6, 1), 'sweater': (30, 25, 8, 5, 2), 'toiletry bag': (25, 12, 10, 4, 1),
       'hair dryer': (22, 9, 20, 3, 1), 'book': (24, 16, 4, 3, 4), 'souvenir': (10, 10, 10, 2, 6),
       'water bottle': (8, 8, 25, 1, 1),
   }
   instance = Instance(
       bin_types=[BinType(x=55, y=40, z=23)],
       item_types=[ItemType(x=x, y=y, z=z, profit=value, copies=n, rotations=ALL_ROTATIONS)
                   for x, y, z, value, n in luggage.values()],
       objective=Objective.KNAPSACK,                    # maximise the value of what fits
   )
   result = box.solve(instance, time_limit=3.0)

   print(result.status, result.value, result.bound)      # Status.FEASIBLE 69.0 72.0 -- everything but the jacket
   plot_result(result, title='What fits in the carry-on').show()

.. raw:: html
   :file: _static/figures/quick_start_suitcase.html

.. only:: latex

   .. image:: _static/figures/quick_start_suitcase.png
      :width: 90%

The full walkthrough is :doc:`tutorials/quick_start/index`; the behaviours inherited from upstream that you should know before trusting a number are collected in :doc:`explanations/upstream_behaviours/index`.

Architecture
~~~~~~~~~~~~

* **Package root** (``packingsolver3d``): re-exports the model, result and error types plus the two solver modules
* **Solver modules** (``packingsolver3d.box``, ``packingsolver3d.boxstacks``): one ``solve`` function each, mirroring upstream's parameters
* **Native bridge** (``packingsolver3d._core``): upstream ``box`` and ``boxstacks`` plus the pybind11 glue, one extension module
* **Metadata** (``packingsolver3d.config``): package version, pinned upstream commit and build options

Upstream and Source
~~~~~~~~~~~~~~~~~~~

* **GitHub Repository**: https://github.com/HansBug/packingsolver3d
* **PackingSolver Upstream**: https://github.com/fontanf/packingsolver

Tutorials
---------

Tutorials are learning paths with one observable success each. The roadmap explains the reading order; the pages follow it.

.. toctree::
    :maxdepth: 2
    :caption: Tutorials
    :hidden:

    Tutorial roadmap <tutorials/index>
    tutorials/quick_start/index
    tutorials/boxstacks/index

* :doc:`Tutorial roadmap <tutorials/index>`
* :doc:`tutorials/quick_start/index`
* :doc:`tutorials/boxstacks/index`

How-to Guides
-------------

How-to guides are task pages for readers who already know what they want to do.

.. toctree::
    :maxdepth: 2
    :caption: How-to Guides
    :hidden:

    How-to roadmap <how_to/index>
    how_to/installation/index
    how_to/budgets/index
    how_to/visualization/index

* :doc:`How-to roadmap <how_to/index>`
* :doc:`how_to/installation/index`
* :doc:`how_to/budgets/index`
* :doc:`how_to/visualization/index`

Explanations
------------

Explanations give the reasoning behind the design and the upstream behaviours that shape results.

.. toctree::
    :maxdepth: 2
    :caption: Explanations
    :hidden:

    Explanation roadmap <explanations/index>
    explanations/architecture/index
    explanations/statuses/index
    explanations/upstream_behaviours/index

* :doc:`Explanation roadmap <explanations/index>`
* :doc:`explanations/architecture/index`
* :doc:`explanations/statuses/index`
* :doc:`explanations/upstream_behaviours/index`

Benchmarks
----------

A small, reproducible capability study on three public instance families, next to the open-source 3D packing libraries commonly used from Python, Go and Rust and two exact reference codes, with every solution re-validated and drawn.

.. toctree::
    :maxdepth: 2
    :caption: Benchmarks
    :hidden:

    Benchmark roadmap <benchmarks/index>
    benchmarks/datasets/index
    benchmarks/participants/index
    benchmarks/protocol/index
    benchmarks/leaderboards/index
    benchmarks/gallery/index

* :doc:`Benchmark roadmap <benchmarks/index>`
* :doc:`benchmarks/datasets/index`
* :doc:`benchmarks/participants/index`
* :doc:`benchmarks/protocol/index`
* :doc:`benchmarks/leaderboards/index`
* :doc:`benchmarks/gallery/index`

Reference
---------

Reference pages state facts: fields, options, errors, and the generated API map.

.. toctree::
    :maxdepth: 2
    :caption: Reference
    :hidden:

    Reference map <reference/index>
    reference/model_fields/index
    reference/solver_options/index
    reference/errors/index

* :doc:`Reference map <reference/index>`
* :doc:`reference/model_fields/index`
* :doc:`reference/solver_options/index`
* :doc:`reference/errors/index`

.. include:: api_doc_en.rst
