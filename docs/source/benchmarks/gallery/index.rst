Gallery
=======

One case per benchmark, every solution drawn with :func:`packingsolver3d.visual.plot_result` so the pictures are directly comparable: our solution first, then the exact reference where one exists, then the other participants from best to worst. Third-party solutions are rebuilt from the stored placements; the numbers in the titles are the ones recomputed by the validator, not the libraries' own reports. Every figure is interactive: drag to rotate, scroll to zoom, hover a box for its item type. Participants that returned the same packing as another one on a case are drawn once.

Twenty cubes, one container (``ep3d-20-C-C-50``)
-------------------------------------------------

Twenty cubes of side 27 to 84 in a 99 x 99 x 199 container whose volume is half of the total; profit is volume plus 200 per cube. The optimum, proven by CP-SAT, packs fourteen cubes for 1,388,961. py3dbp, jerry800416/3D-bin-packing, gedex/bp3d and U-Nesting ExtremePoint return the identical six-cube packing, drawn once.

packingsolver3d, 1,388,961 with fourteen cubes: one 84-cube at the bottom, a layer of small cubes above it and four mid-sized cubes on top, almost no wasted height. Its own bound stayed open, the proof is CP-SAT's.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.png
      :width: 90%

OR-Tools CP-SAT, the exact reference: the same profit and item count, a different arrangement of the same fourteen cubes, found and proven in 0.08 s.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__cp_sat.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__cp_sat.png
      :width: 90%

U-Nesting SA, the best participant that kept the orientation: also fourteen cubes, but smaller ones, for 1,070,882, 23 percent less profit in the same container.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.png
      :width: 90%

U-Nesting GA: thirteen cubes for 996,594; the genetic search over sequences did not find a sequence whose greedy decoding places a large cube well.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_ga.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_ga.png
      :width: 90%

U-Nesting BottomLeftFill: eleven cubes for 965,560; layers of unequal cubes leave the space above each short layer empty.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_layer.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_layer.png
      :width: 90%

py3dbp (identical to jerry800416/3D-bin-packing, gedex/bp3d and U-Nesting ExtremePoint): the two largest cubes fill the column, four small ones sit on top, and the remaining fourteen are left out for 1,265,340. Rotating cubes changes nothing, so the relaxation does not help here.

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.png
      :width: 90%

Three bins by construction (``MPV-GEN-T9-N30-R01``)
---------------------------------------------------

Thirty boxes cut from three 100 x 100 x 100 bins by random guillotine cuts; the optimum is the three-bin cut itself, with zero slack. jerry800416/3D-bin-packing returns the same four-bin packing as py3dbp and is not repeated.

packingsolver3d rebuilds three completely full bins in about one second; its bound proves that three is optimal.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.png
      :width: 90%

py3dbp, rotation relaxed: four bins. Three are well filled, the fourth takes the pieces that no longer fit the gaps its greedy order left.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.png
      :width: 90%

U-Nesting ExtremePoint, the best participant that kept the orientation: four bins; the extreme-point rule packs tightly but one misplaced slab costs a whole bin.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_extreme_point.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_extreme_point.png
      :width: 90%

gedex/bp3d, rotation relaxed: five bins.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__go_bp3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__go_bp3d.png
      :width: 90%

U-Nesting SA after 10 s of annealing per bin: five bins, no better than the constructive heuristics.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_sa.png
      :width: 90%

U-Nesting BottomLeftFill: six bins, twice the optimum; the layer-by-layer rule leaves large voids in every bin and the sixth bin holds a single box.

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.png
      :width: 90%

Weakly heterogeneous cargo (``IMM-26``)
---------------------------------------

Seventy-two boxes of four types in 35 x 32 x 40 containers, all rotations allowed for everybody; the volume bound is three containers. jerry800416/3D-bin-packing returns the same four-container loading as py3dbp and is not repeated.

packingsolver3d loads all seventy-two boxes into three containers in about one second, meeting the bound.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.png
      :width: 90%

py3dbp: four containers; the first three are loaded greedily by size and the leftovers need a fourth.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__py3dbp.png
      :width: 90%

gedex/bp3d: four containers with a different split of the same greedy idea.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__go_bp3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__go_bp3d.png
      :width: 90%

U-Nesting ExtremePoint: four containers.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__rust_extreme_point.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__rust_extreme_point.png
      :width: 90%

U-Nesting SA after 10 s of annealing per container: four containers as well, the last one nearly empty.

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__rust_sa.png
      :width: 90%
