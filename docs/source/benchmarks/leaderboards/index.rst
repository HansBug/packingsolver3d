Leaderboards
============

One table per benchmark. The first column names the participant and links to its project; the second is the total over all cases and orders the rows; the third repeats the theoretical bound total with the gap in parentheses; the remaining columns are the cases. ``*`` marks a proven optimum, "rotation relaxed" marks a participant that solved a relaxed variant, "reference" marks an exact code run at its own budget. The rules behind every cell are on :doc:`../protocol/index`.

Summary
-------

.. include:: ../_generated/summary_en.rst

Egeblad-Pisinger 3D knapsack, twenty items
------------------------------------------

Ten instances, one container each, fixed orientation, maximise packed profit. All ten optima are proven, eight by the CP-SAT reference and two by PackingSolver's own bound.

.. include:: ../_generated/ep3d_en.rst

packingsolver3d reaches the proven optimum on all ten cases; on five of them (``D-C``, ``F-C``, ``F-R``, ``L-C``, ``U-C``) its own bound closes and the solve stops after one to five seconds, on the other five it returns the optimal packing but keeps searching until the 10 s limit because its bound stays open. The best heuristic rows are about nine percent below the optimum in total profit, and that is with free rotation; among the fixed-pose participants U-Nesting SA is closest at ten percent below. On ``C-C``, the cube instance, every greedy library packs six of the twenty cubes for 1,265,340 where the optimum packs fourteen for 1,388,961 -- the case drawn in :doc:`../gallery/index`.

Martello-Pisinger-Vigo generator class 9, thirty items
------------------------------------------------------

Ten replicates, 100 x 100 x 100 bins, fixed orientation, minimise bins. Every replicate is exactly three bins by construction.

.. include:: ../_generated/mpv_t9_en.rst

packingsolver3d rediscovers the three-bin cut of every replicate in about one second and its bound proves it. The authors' own branch-and-bound closes four of the ten replicates within its one second budget and reports four or five bins on the others. Every heuristic needs at least one extra bin on every replicate, and even with free rotation py3dbp and jerry800416/3D-bin-packing use eleven bins more than necessary over the ten cases; the bottom-left-fill strategy needs almost twice the optimum.

Ivancic-Mathur-Mohanty THPACK9, eight instances
-----------------------------------------------

Weakly heterogeneous cargo, two to five item types, all six orientations allowed for every participant, minimise containers.

.. include:: ../_generated/imm_en.rst

packingsolver3d proves the optimum on seven of the eight instances within a second and packs instance 25 into five containers against a bound of four, one container above the bound total. The greedy libraries agree with it on the easy instances (18, 19, 46) and fall behind as the fit gets tighter: instance 1 needs 25 containers and every heuristic uses 50, instance 24 needs five and they use seven or eight. The four U-Nesting metaheuristics returned placements outside the 10 x 6 x 16 container on instance 1, so their totals are not comparable and are shown as ``n/a``.
