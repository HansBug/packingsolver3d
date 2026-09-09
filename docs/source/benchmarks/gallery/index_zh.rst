图集
====

每个基准取一个 case，所有参与者的解都用 :func:`packingsolver3d.visual.plot_result` 绘制，因此图之间可以直接比较：先是我们的解，然后是解同一问题中最接近的参与者，最后是贪心库里最好的那个。第三方的解从存储的摆放重建；标题里的数字是校验器重算的，不是各库自己报的。拖动旋转，滚轮缩放。

二十个立方体，一个容器（``ep3d-20-C-C-50``\ ）
----------------------------------------------

二十个边长 27 到 84 的立方体，容器 99 x 99 x 199，容积是物品总体积的一半；利润为体积加每件 200。CP-SAT 证明的最优装法装十四个立方体，利润 1,388,961。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__packingsolver3d.png
      :width: 90%

packingsolver3d 找到了 CP-SAT 证明的十四立方体最优解：底部一个边长 84 的立方体，上面一层小立方体，顶上四个中等立方体，几乎没有浪费的高度。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__rust_sa.png
      :width: 90%

U-Nesting SA 是这个 case 上最好的固定姿态启发式，也放了十四个立方体，但选的更小，利润 1,070,882，同一容器里少了百分之二十三。

.. raw:: html
   :file: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/ep3d__ep3d-20-C-C-50__py3dbp.png
      :width: 90%

py3dbp（jerry800416/3D-bin-packing、gedex/bp3d 与 U-Nesting ExtremePoint 返回同样的装法）先拿大立方体，装到六件、利润 1,265,340 就停了：枢轴规则用最大的几块填满容器，把小立方体留在外面。

按构造恰好三箱（``MPV-GEN-T9-N30-R01``\ ）
------------------------------------------

三十个从三个 100 x 100 x 100 箱子切出来的盒子；最优解就是那个三箱切割本身，零余量。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.png
      :width: 90%

packingsolver3d 在约一秒内重建出三个完全填满的箱子，其界证明三是最优。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.png
      :width: 90%

py3dbp 即便自由旋转也需要四箱：三箱装得不错，第四箱装那些再也塞不进贪心顺序留下的缝隙的零件。

.. raw:: html
   :file: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.html

.. only:: latex

   .. image:: ../../_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__rust_layer.png
      :width: 90%

U-Nesting BottomLeftFill 需要六箱，是最优的两倍：逐层规则在每个箱子里留下大块空洞，第六箱只放了一个盒子。

弱异质货物（``IMM-26``\ ）
--------------------------

四种共七十二个盒子，集装箱 35 x 32 x 40，允许所有旋转；体积下界是三个集装箱。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__packingsolver3d.png
      :width: 90%

packingsolver3d 在约一秒内把七十二个盒子全部装进三个集装箱，达到下界。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__py3dbp.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__py3dbp.png
      :width: 90%

py3dbp 需要第四个集装箱；jerry800416/3D-bin-packing、gedex/bp3d 以及 U-Nesting 的每个策略在这个实例上也都如此。

.. raw:: html
   :file: ../../_static/benchmarks/imm__IMM-26__rust_sa.html

.. only:: latex

   .. image:: ../../_static/benchmarks/imm__IMM-26__rust_sa.png
      :width: 90%

U-Nesting SA 每个容器退火 10 s 之后：同样四个集装箱，最后一个几乎是空的。
