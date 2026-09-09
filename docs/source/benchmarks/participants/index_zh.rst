参与者
======

在 :doc:`../leaderboards/index_zh` 里产生过数字的每一个程序都列在这里：项目链接、实际运行的版本、背后的算法以及驱动方式。"参与者"行在统一的 10 s 预算下竞争；"参照"行是按自身预算运行的精确程序，职责是认证最优值。

名录
----

.. list-table::
   :header-rows: 1
   :widths: 22 10 16 30 22

   * - 参与者
     - 语言
     - 测试版本
     - 方法
     - 角色
   * - `packingsolver3d <https://github.com/HansBug/packingsolver3d>`__\ （PackingSolver ``box``\ ）
     - C++ 核心，Python API
     - 上游 commit ``a7e53303``
     - anytime 组合：基于插入分支方案的迭代束搜索、对偶可行函数界；多箱时叠加顺序单背包、顺序价值修正、列生成与二分搜索
     - 参与者
   * - `py3dbp <https://github.com/enzoruiz/3dbinpacking>`__
     - Python
     - 1.1.2（PyPI）
     - 枢轴点贪心启发式
     - 参与者，固定姿态族上放松旋转约束
   * - `jerry800416/3D-bin-packing <https://github.com/jerry800416/3D-bin-packing>`__
     - Python
     - commit ``75764a2``
     - py3dbp 的 fork：枢轴点贪心加定点重力下落
     - 参与者，固定姿态族上放松旋转约束
   * - `gedex/bp3d <https://github.com/gedex/bp3d>`__
     - Go
     - commit ``0ba3dcd``
     - 枢轴点贪心启发式
     - 参与者，固定姿态族上放松旋转约束
   * - `U-Nesting <https://github.com/iyulab/U-Nesting>`__ ExtremePoint
     - Rust
     - 0.9.0，commit ``8cde85b``
     - 极点构造式启发式
     - 参与者
   * - `U-Nesting <https://github.com/iyulab/U-Nesting>`__ BottomLeftFill
     - Rust
     - 0.9.0，commit ``8cde85b``
     - 左下填充（分层）构造式启发式
     - 参与者
   * - `U-Nesting <https://github.com/iyulab/U-Nesting>`__ GA
     - Rust
     - 0.9.0，commit ``8cde85b``
     - 作用于物品序列的遗传算法
     - 参与者
   * - `U-Nesting <https://github.com/iyulab/U-Nesting>`__ BRKGA
     - Rust
     - 0.9.0，commit ``8cde85b``
     - 偏置随机键遗传算法
     - 参与者
   * - `U-Nesting <https://github.com/iyulab/U-Nesting>`__ SA
     - Rust
     - 0.9.0，commit ``8cde85b``
     - 作用于物品序列的模拟退火
     - 参与者
   * - `OR-Tools CP-SAT <https://developers.google.com/optimization/cp/cp_solver>`__ 精确模型
     - C++ 核心，Python API
     - OR-Tools 9.15
     - 固定姿态三维背包的精确约束规划模型
     - 参照（20 s，单线程，4 GiB）
   * - `Martello-Pisinger-Vigo 3dbpp.c <http://hjemmesider.diku.dk/~pisinger/codes.html>`__
     - C
     - ``new3dbpp`` 一般装箱版本
     - 带单箱精确子程序与下界的分支定界
     - 参照（1 s，单线程）

packingsolver3d，即 PackingSolver ``box``
-----------------------------------------

`PackingSolver <https://github.com/fontanf/packingsolver>`__ 由 Florian Fontan 开发，是面向二维与三维装箱问题的 C++ 求解器；本包把它的 ``box`` 求解器编进 Python 扩展并在进程内调用（见 :doc:`../../explanations/architecture/index_zh`\ ）。``box`` 是 anytime 优化求解器，不是装载启发式。它的核心是基于插入分支方案的树搜索 -- 每个节点是一个部分装法，子节点在某个候选位置多放一件 -- 用配套库 `treesearchsolver <https://github.com/fontanf/treesearchsolver>`__ 的迭代束搜索来探索，束宽逐步放大直到触及时限或搜完整棵树。上界来自对偶可行函数；上界与当前解相遇时运行提前结束并给出 ``OPTIMAL`` 状态，这正是每个第 9 类 replicate 和八个 THPACK9 case 中七个所发生的事。多箱时 ``box`` 在单箱搜索之上叠加一组算法：顺序单背包、顺序价值修正、列生成（内置 HiGHS 线性规划求解器）以及对箱数的二分搜索；每个子算法都可以通过 :func:`packingsolver3d.box.solve` 关闭。这里的运行全部使用默认值：anytime 模式、全部子算法、``time_limit=10.0``\ 、``memory_limit=1024``\ 。

py3dbp
------

`py3dbp <https://github.com/enzoruiz/3dbinpacking>`__\ （Enzo Ruiz，PyPI ``py3dbp`` 1.1.2）是下载量最大的 Python 三维装箱库。它实现了 Dube 与 Kanavathy（"Optimizing three-dimensional bin packing through simulation"）描述的枢轴点启发式：物品按体积排序，每件依次尝试已放置物品的角点生成的枢轴点、六种朝向，放进第一个能容纳的位置；箱子逐个填满。它没有目标函数也没有搜索，结果就是一次贪心遍历。表格取两次遍历（大件优先与按文件顺序）中较好的，并设 ``distribute_items=True`` 让剩余物品进入下一箱。它总是旋转，因此在两个固定姿态族上标"放松旋转约束"。

jerry800416/3D-bin-packing
--------------------------

`jerry800416/3D-bin-packing <https://github.com/jerry800416/3D-bin-packing>`__ 是 py3dbp 的 fork，增加了定点步骤（枢轴放置后把物品下落并向原点推挤直到搁到东西上）、可选的稳定性检查、承重限制和角点放置，并附带绘图工具。运行使用 ``fix_point=True`` 与 ``check_stable=False``\ ，只强制几何约束，物品顺序与 py3dbp 相同的两种。同样的枢轴点核心，因此同样有放松旋转的说明。

gedex/bp3d
----------

`gedex/bp3d <https://github.com/gedex/bp3d>`__ 是同一枢轴点启发式的 Go 移植，源自 ``bom-d-van/binpacking``\ ，使用 ``float64`` 尺寸。它无法被要求保持朝向，所以在固定姿态的变体上标"放松旋转约束"。每个 case 一次贪心遍历；在背包族上利润是它放进单个容器的物品之和。

U-Nesting
---------

`U-Nesting <https://github.com/iyulab/U-Nesting>`__\ （iyulab，Rust，MIT）是带 C FFI 的二维排样与三维装箱引擎。其三维模块提供五种策略，分别单独运行：\ **ExtremePoint** 按 Crainic、Perboli 与 Tadei 构造式启发式的思路把物品放到先前物品留下的极点上；\ **BottomLeftFill** 是分层构建的左下填充贪心；\ **GA** 与 **BRKGA** 分别用普通遗传算法和偏置随机键遗传算法演化物品序列，每个序列由构造式放置器解码；\ **SA** 对序列做模拟退火。该库一次调用只装一个容器，因此多箱通过重复调用处理，每次接收上一个容器剩下的物品。各策略遵守固定姿态并获得 10 s 预算；在允许所有旋转的 THPACK9 族上，其中四个在实例 1 上给出了伸出容器的摆放，被校验器判为非法。

OR-Tools CP-SAT 精确模型（参照）
--------------------------------

`CP-SAT <https://developers.google.com/optimization/cp/cp_solver>`__ 是 Google `OR-Tools <https://github.com/google/or-tools>`__\ （此处为 9.15）的约束规划求解器。参照是固定姿态三维背包的精确模型 -- 每件物品每个轴一个可选区间、两两不重叠析取、最大化利润 -- 以 20 s、单线程、4 GiB 运行。CP-SAT 以 ``OPTIMAL`` 状态结束时，其值就是已证明最优并进入理论界一行；只得到可行解时它的界很松，改用 PackingSolver 的界。它认证了十个背包 case 中的八个。

Martello-Pisinger-Vigo 3dbpp.c（参照）
--------------------------------------

`3dbpp.c <http://hjemmesider.diku.dk/~pisinger/codes.html>`__ 是作者们针对三维装箱问题的分支定界（Martello、Pisinger 与 Vigo，*Operations Research* 2000；与 den Boef、Korst 合作的一般装箱版本，*ACM TOMS* 2007）。它把箱数下界与精确的单箱填充子程序结合在对箱分配的分支定界里，被时限中止时报告一个下界和一个上界。它以 1 s、单线程、生成器默认的一般装箱参数运行在自己生成的第 9 类 replicate 上；表中显示其上界，其下界三进入理论界一行。
