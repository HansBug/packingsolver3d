快速开始：第一次装箱
====================

本教程从一个全新的 Python 环境出发，求解一个三维装箱实例，并说明如何读取返回结果。全部在进程内完成，没有外部可执行文件，也不落盘。

安装
----

.. code-block:: bash

   pip install packingsolver3d

Linux、macOS、Windows 的 x86_64 与 arm64 都有 wheel；各平台对应的 Python 版本以及在其它平台从源码安装的方法见 :doc:`/how_to/installation/index_zh`。

描述实例
--------

:class:`~packingsolver3d.model.Instance` 由箱型（bin type）和物品类型（item type）组成，二者都是 frozen dataclass；``copies`` 表示同样的东西有几件。

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, box

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
       item_types=[
           ItemType(x=20, y=30, z=40, copies=6),
           ItemType(x=15, y=15, z=15, copies=4),
       ],
       objective=Objective.BIN_PACKING,
   )

默认情况下每种物品都是必装的：求解器必须放下全部十件。这个默认值来自上游（``copies_min = -1`` 表示"全部副本"，knapsack 目标除外）；:doc:`/explanations/upstream_behaviours/index_zh` 解释了为什么传 ``copies_min=0`` 会让"什么都不装"成为正确答案。

求解
----

.. code-block:: python

   result = box.solve(instance, time_limit=2.0)

``time_limit`` 单位为秒，直接交给上游自己的计时器。十件物品的实例几毫秒就解完，限制不会触发；真实实例上请务必传一个限制，否则求解器会跑完它的整个日程。

读结果
------

.. code-block:: python

   >>> result.status
   <Status.OPTIMAL: 'optimal'>
   >>> result.value, result.bound
   (1.0, 1.0)
   >>> result.number_of_bins, len(result.placements)
   (1, 10)
   >>> result.placements[0]
   Placement(item_type_id=0, bin_id=0, x=0, y=0, z=0, lx=20, ly=30, lz=40, rotation=<Rotation.XYZ: 'XYZ'>, stack_id=None, group_id=None)

三点值得停一下：

* ``value`` 是求解器**达到**的（用了一个箱），``bound`` 是它**证明**的（至少需要一个箱）。状态是 ``OPTIMAL`` 只因为两者相符；如果求解器停在一个两箱的解而界仍是 1，状态就是 ``FEASIBLE``\ 。完整规则见 :doc:`/explanations/statuses/index_zh`。
* ``placements`` 是普通值：物品类型、所在箱、下角坐标、旋转后的摆放尺寸，以及上游使用的旋转令牌。
* ``result.statistics`` 原样保存上游的统计块（``VolumeLoad``、``NumberOfUnpackedItems`` ……），``result.run`` 记录传入的全部选项、上游日志（若开启）与墙钟时间，运行可以复现。

装箱之外的目标
--------------

换一个 ``objective``\ ，同一个调用回答不同的问题：

.. code-block:: python

   knapsack = Instance(
       bin_types=[BinType(x=100, y=100, z=100, copies=1)],
       item_types=instance.item_types,
       objective=Objective.KNAPSACK,
   )
   result = box.solve(knapsack, time_limit=2.0)
   result.value   # 157500.0：物品利润，上游默认为体积

:class:`~packingsolver3d.model.Objective` 列出了全部上游令牌；哪些目标会报告界见 :doc:`/reference/solver_options/index_zh`。

下一步
------

* 堆叠规则、重量与卡车：:doc:`/tutorials/boxstacks/index_zh`。
* 在预算内批量运行：:doc:`/how_to/budgets/index_zh`。
