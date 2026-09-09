图集
====

每个基准取一个 case，所有解都用 :func:`packingsolver3d.visual.plot_result` 绘制，因此图之间可以直接比较：先是我们的解，然后是精确参照（如果有），然后是其他参与者从好到差。第三方的解从存储的摆放重建；标题里的数字是校验器重算的，不是各库自己报的。每张图都是可交互的：拖动旋转，滚轮缩放，悬停在盒子上显示物品类型。在某个 case 上与另一参与者返回完全相同装法的参与者只画一次。

二十个立方体，一个容器（``ep3d-20-C-C-50``\ ）
----------------------------------------------

二十个边长 27 到 84 的立方体，容器 99 x 99 x 199，容积是物品总体积的一半；利润为体积加每件 200。CP-SAT 证明的最优装法装十四个立方体，利润 1,388,961。py3dbp、jerry800416/3D-bin-packing、gedex/bp3d 与 U-Nesting ExtremePoint 返回完全相同的六立方体装法，只画一次。

packingsolver3d，十四个立方体、1,388,961：底部一个边长 84 的立方体，上面一层小立方体，顶上四个中等立方体，几乎没有浪费的高度。它自己的界没有收口，证明来自 CP-SAT。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.png
      :width: 90%

OR-Tools CP-SAT，精确参照：同样的利润和件数，同一批十四个立方体的另一种摆法，0.08 s 内找到并证明。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__cp_sat.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__cp_sat.png
      :width: 90%

U-Nesting SA，保持朝向的参与者里最好的：也是十四个立方体，但选的更小，利润 1,070,882，同一容器里少了百分之二十三。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.png
      :width: 90%

U-Nesting GA：十三个立方体、996,594；对序列的遗传搜索没有找到一个贪心解码后能把大立方体放好的序列。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_ga.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_ga.png
      :width: 90%

U-Nesting BottomLeftFill：十一个立方体、965,560；大小不一的立方体分层，每个矮层上方的空间就空着。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_layer.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_layer.png
      :width: 90%

py3dbp（与 jerry800416/3D-bin-packing、gedex/bp3d、U-Nesting ExtremePoint 相同）：两个最大的立方体填满一列，四个小的放在顶上，剩下十四个留在外面，利润 1,265,340。旋转立方体不改变任何东西，所以放松在这里没有帮助。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.png
      :width: 90%

按构造恰好三箱（``MPV-GEN-T9-N30-R01``\ ）
------------------------------------------

三十个由随机 guillotine 切割从三个 100 x 100 x 100 箱子切出来的盒子；最优解就是那个三箱切割本身，零余量。jerry800416/3D-bin-packing 返回与 py3dbp 相同的四箱装法，不重复画。

packingsolver3d 在约一秒内重建出三个完全填满的箱子，其界证明三是最优。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.png
      :width: 90%

py3dbp，放松旋转约束：四箱。三箱装得不错，第四箱装那些再也塞不进贪心顺序留下的缝隙的零件。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.png
      :width: 90%

U-Nesting ExtremePoint，保持朝向的参与者里最好的：四箱；极点规则装得紧，但一块放错的板就要付出整整一箱。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_extreme_point.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_extreme_point.png
      :width: 90%

gedex/bp3d，放松旋转约束：五箱。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__go_bp3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__go_bp3d.png
      :width: 90%

U-Nesting SA 每箱退火 10 s 之后：五箱，不比构造式启发式好。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_sa.png
      :width: 90%

U-Nesting BottomLeftFill：六箱，是最优的两倍；逐层规则在每个箱子里留下大块空洞，第六箱只放了一个盒子。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.png
      :width: 90%

弱异质货物（``IMM-26``\ ）
--------------------------

四种共七十二个盒子，集装箱 35 x 32 x 40，对所有人允许所有旋转；体积下界是三个集装箱。jerry800416/3D-bin-packing 返回与 py3dbp 相同的四箱装法，不重复画。

packingsolver3d 在约一秒内把七十二个盒子全部装进三个集装箱，达到下界。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.png
      :width: 90%

py3dbp：四个集装箱；前三个按尺寸贪心装载，剩下的需要第四个。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__py3dbp.png
      :width: 90%

gedex/bp3d：四个集装箱，同一贪心思路的另一种分配。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__go_bp3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__go_bp3d.png
      :width: 90%

U-Nesting ExtremePoint：四个集装箱。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__rust_extreme_point.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__rust_extreme_point.png
      :width: 90%

U-Nesting SA 每个容器退火 10 s 之后：同样四个集装箱，最后一个几乎是空的。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__rust_sa.png
      :width: 90%
