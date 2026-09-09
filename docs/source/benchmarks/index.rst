Benchmark roadmap
=================

This section is a small, fully reproducible capability study. It runs packingsolver3d, and through it the ``box`` solver of upstream PackingSolver, on three public families of three-dimensional packing instances next to the open-source 3D packing libraries people most often reach for from Python, Go, Rust and Java-adjacent ecosystems, plus two exact codes that serve as references. The families are small enough to draw, and for most of the 97 cases the optimum is known or proven, so the tables separate "found a good packing" from "found the best packing" and say where ten seconds are not enough for anybody.

What it is not: a general ranking of packing software. The instances are deliberately small and constraint-free (no weights, no stability, no stacking rules), the budgets are short, and each number is a single run. Read :doc:`protocol/index` before quoting a figure.

Pages
-----

* :doc:`datasets/index` -- the three benchmarks: who published them, where the official files live, what the instances look like and which cases the tables use.
* :doc:`participants/index` -- every library and reference code that took part, with links, versions, the algorithm behind each one and how it was driven.
* :doc:`protocol/index` -- budgets, machine, the independent geometry check applied to every solution, how bounds, totals and gaps are computed, and the caveats.
* :doc:`leaderboards/index` -- the complete results: the participant roster, a cross-benchmark summary, and per benchmark the cases with their bounds, the leaderboard (one row per participant, one column per case), the items placed and the times.
* :doc:`gallery/index` -- side-by-side drawings of our solution and the other libraries' solutions on one case of each benchmark.

Reproduce it
------------

.. code-block:: bash

   pip install "packingsolver3d[plot]" kaleido
   make benchmarks          # tools/make_benchmarks.py --solve --render

The solve step runs ``box.solve`` with a 10 s time limit on the 97 cases and rewrites ``tools/benchmarks/ours.json``; the render step re-validates every stored solution, ours and third-party alike, recomputes the objectives from the placements and regenerates the tables and figures in this section.

.. toctree::
    :maxdepth: 1
    :hidden:

    datasets/index
    participants/index
    protocol/index
    leaderboards/index
    gallery/index
