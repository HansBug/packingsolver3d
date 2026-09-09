快速开始：登机箱里装得下什么
============================

本教程从一个全新的 Python 环境出发，解一个能"看得见"的三维装箱问题。问题人人都遇过：一个 55 x 40 x 23 cm 的登机箱，想带的东西比装得下的多，而你心里对每件东西有个"多想带"的分数。求解器决定带哪些、每件放在哪；最后的图把装法画出来，可以旋转查看。一切都在进程内运行，没有外部可执行文件，也不落盘。

安装
----

.. code-block:: bash

   pip install "packingsolver3d[plot]"

``plot`` 附加项引入 plotly 用于画图；求解器本身没有任何依赖。Linux、macOS、Windows 的 x86_64 与 arm64 都有 wheel；各平台支持的 Python 版本以及在其他平台从源码安装见 :doc:`/how_to/installation/index_zh`\ 。

描述行李
--------

:class:`~packingsolver3d.model.Instance` 由箱型和物品类型构成，两者都是冻结的 dataclass。这里唯一的箱子就是登机箱，每个物品类型是一类要带的东西：厘米尺寸、表示"多想带"的 ``profit``\ ，以及同类有几件的 ``copies``\ 。``rotations=ALL_ROTATIONS`` 允许求解器任意转动一件物品；不写的话物品保持你写下的朝向，这是上游的默认。

.. code-block:: python

   from packingsolver3d import ALL_ROTATIONS, BinType, Instance, ItemType, Objective, box

   luggage = {  # name: (x, y, z, value, copies)
       'laptop': (36, 25, 3, 10, 1), 'camera': (15, 10, 8, 9, 1), 'shoes': (30, 20, 12, 8, 1),
       'jacket': (35, 20, 15, 6, 1), 'sweater': (30, 25, 8, 5, 2), 'toiletry bag': (25, 12, 10, 4, 1),
       'hair dryer': (22, 9, 20, 3, 1), 'book': (24, 16, 4, 3, 4), 'souvenir': (10, 10, 10, 2, 6),
       'water bottle': (8, 8, 25, 1, 1),
   }
   names = list(luggage)
   instance = Instance(
       bin_types=[BinType(x=55, y=40, z=23)],
       item_types=[ItemType(x=x, y=y, z=z, profit=value, copies=n, rotations=ALL_ROTATIONS)
                   for x, y, z, value, n in luggage.values()],
       objective=Objective.KNAPSACK,
   )

十九件东西合计 54,304 立方厘米，箱子只有 50,600，总得有东西留在家里。``Objective.KNAPSACK`` 要求在真正装得下的前提下选出总分最高的子集——全带上的话是 75 分。目标必须显式给出，没有默认值，因为上游自己的 ``default`` 令牌不产生任何解。

求解
----

.. code-block:: python

   result = box.solve(instance, time_limit=3.0)

``time_limit`` 以秒计，交给上游自己的计时器。默认的 anytime 搜索会在时限内不断改进当前最好的装法；这个实例三秒足够。真实实例上务必给时限，否则求解器会一直跑到自己的调度用尽。

读结果
------

.. code-block:: python

   >>> result.status, result.value, result.bound
   (<Status.FEASIBLE: 'feasible'>, 69.0, 72.0)
   >>> len(result.placements)
   18
   >>> packed = [0] * len(names)
   >>> for placement in result.placements:
   ...     packed[placement.item_type_id] += 1
   >>> [(name, count) for name, count in zip(names, packed) if count < luggage[name][4]]
   [('jacket', 0)]

除了夹克全都装进去了，75 分里拿到 69 分。两个数字值得停一下：

* ``value`` 是求解器做到的；``bound`` 是它证明的：这些东西的任何装法都不会超过 72 分。两者没有相遇，所以状态是 ``FEASIBLE`` 而不是 ``OPTIMAL``\ ；也许存在 70、71 或 72 分的装法，也许不存在，求解器只是没能在三秒内定论。本包从不把一个好的当前解改写成已证明最优，见 :doc:`/explanations/statuses/index_zh`\ 。
* ``placements`` 是普通值：物品类型、箱子、下角坐标、旋转后的放置尺寸，以及上游使用的旋转令牌。``result.statistics`` 原样保存上游的统计块，``result.run`` 记录传入的精确选项和墙钟时间，运行可以复现。anytime 搜索逐次运行并不确定；换一台机器，被留下的可能是另一件低分物品。

看一眼
------

.. code-block:: python

   from packingsolver3d.visual import plot_result

   figure = plot_result(result, title='What fits in the carry-on')
   figure.show()                       # 或 figure.write_html('carry-on.html')

.. raw:: html
   :file: ../../_static/figures/quick_start_suitcase.html

.. only:: latex

   .. image:: ../../_static/figures/quick_start_suitcase.png
      :width: 90%

拖动旋转，滚轮缩放，悬停在盒子上显示物品类型；图例按 ``names`` 的顺序把颜色对应到物品类型，所以类型 7 是书、类型 8 是纪念品。画图选项见 :doc:`/how_to/visualization/index_zh`\ 。

换个问题
--------

改一下 ``objective``\ ，同一个实例回答另一个问题。给几个箱子并用 ``Objective.BIN_PACKING``\ ，求解器会把\ *所有*\ 东西装进尽量少的箱子；用 ``VARIABLE_SIZED_BIN_PACKING`` 则还会按成本在不同箱型之间挑选。

.. code-block:: python

   two_bags = Instance(
       bin_types=[BinType(x=55, y=40, z=23, cost=1, copies=3)],
       item_types=instance.item_types,
       objective=Objective.BIN_PACKING,
   )
   result = box.solve(two_bags, time_limit=3.0)
   result.status, result.number_of_bins    # (<Status.OPTIMAL: 'optimal'>, 2)

两个箱子就能装下全部，而且这次状态是 ``OPTIMAL``\ ：求解器的界证明一个箱子装不下 54,304 立方厘米。:class:`~packingsolver3d.model.Objective` 列出上游的每个令牌；:doc:`/reference/solver_options/index_zh` 说明哪些目标会报告界。

下一步
------

* 堆叠规则、重量与卡车：:doc:`/tutorials/boxstacks/index_zh`\ 。
* 在预算内跑很多实例：:doc:`/how_to/budgets/index_zh`\ 。
* 求解器在公开基准上与其他库的比较：:doc:`/benchmarks/index_zh`\ 。
