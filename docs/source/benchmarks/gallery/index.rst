Gallery
=======

One case per benchmark, drawn with :func:`packingsolver3d.visual.plot_result` for every participant so the pictures are comparable: our solution first, then the closest same-problem participant, then the best of the greedy libraries. Third-party solutions are rebuilt from the stored placements; the numbers in the titles are the ones recomputed by the validator, not the libraries' own reports. Drag to rotate, scroll to zoom.

Twenty cubes, one container (``ep3d-20-C-C-50``)
-------------------------------------------------

Twenty cubes of side 27 to 84 in a 99 x 99 x 199 container whose volume is half the total; profit is volume plus 200 per cube. The optimum, proven by CP-SAT, packs fourteen cubes for 1,388,961.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.png
      :width: 90%

packingsolver3d finds the fourteen-cube optimum proven by CP-SAT: one 84-cube at the bottom, a layer of small cubes above it and four mid-sized cubes on top, with almost no wasted height.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.png
      :width: 90%

U-Nesting SA, the best fixed-pose heuristic on this case, also places fourteen cubes but chooses smaller ones, for 1,070,882, 23 percent less profit in the same container.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.png
      :width: 90%

py3dbp (like jerry800416/3D-bin-packing, gedex/bp3d and U-Nesting ExtremePoint, which return the same packing) takes the big cubes first and stops at six items for 1,265,340: the pivot rule fills the container with the largest pieces and leaves the small cubes out.

Three bins by construction (``MPV-GEN-T9-N30-R01``)
---------------------------------------------------

Thirty boxes cut from three 100 x 100 x 100 bins; the optimum is the three-bin cut itself, with zero slack.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.png
      :width: 90%

packingsolver3d rebuilds three completely full bins in about one second and its bound proves that three is optimal.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.png
      :width: 90%

py3dbp, even with free rotation, needs four bins: three well filled and a fourth for the pieces that no longer fit the gaps its greedy order left.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.png
      :width: 90%

U-Nesting BottomLeftFill needs six bins, twice the optimum: the layer-by-layer rule leaves large voids in every bin and the sixth bin holds a single box.

Weakly heterogeneous cargo (``IMM-26``)
---------------------------------------

Seventy-two boxes of four types in 35 x 32 x 40 containers, all rotations allowed; the volume bound is three containers.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.png
      :width: 90%

packingsolver3d loads all seventy-two boxes into three containers in about one second, meeting the bound.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__py3dbp.png
      :width: 90%

py3dbp needs a fourth container; the same is true of jerry800416/3D-bin-packing, gedex/bp3d and every U-Nesting strategy on this instance.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__rust_sa.png
      :width: 90%

U-Nesting SA after 10 s of annealing per container: four containers as well, the last one nearly empty.
