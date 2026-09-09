重放上游的测试实例
==================

当你想确认本包能复现上游 PackingSolver 的结果，或你的实例是上游 CSV 格式时，请用本页。

仓库已经做了什么
----------------

``test/testfile/upstream/`` 原样保存了上游单元测试所求解的实例——``box`` 七个（knapsack、open-dimension-x、变尺寸装箱），``boxstacks`` 三个（变尺寸装箱与两个半挂车轴重用例）。``test/test_upstream_cases.py`` 以上游 gtest 使用的参数重放每一个，并按上游 ``Solution::operator<`` 对该目标比较的量来比对 ``solution.csv``\ ：knapsack 比利润，变尺寸装箱比成本，open dimension x 比 ``x_max``\ ，装箱比箱数。

有一个用例需要说明。上游对半挂车 knapsack 实例的测试直接驱动一个子算法（``sequential_onedimensional_rectangle``\ ），其参考解为空；本包的公开入口是 ``optimize()``\ ，它装下了三件中的两件。因此该用例改为与上游自己的 ``packingsolver_boxstacks`` 可执行文件在同一文件上跑 ``optimize()`` 得到的证书比对（``solution_optimize.csv``\ ，来源记录在 ``SOURCE.md``\ ）。

读取上游 CSV 实例
-----------------

上游实例是三个 CSV 文件：``items.csv``、``bins.csv``、``parameters.csv``\ 。测试模块里有一个小读取器（``load_case``\ ）把上游列映射到 :class:`~packingsolver3d.model.ItemType` 与 :class:`~packingsolver3d.model.BinType`；它还不是公开 API，但映射很短，并在 :doc:`/reference/model_fields/index_zh` 有文档：

* ``X, Y, Z, COPIES, COPIES_MIN, PROFIT, WEIGHT`` 一一对应；列缺失或单元为空表示"字段留 ``None``"，让上游默认值生效，与上游读取器对待缺失列的方式一致。
* ``ROTATION_XYZ ... ROTATION_ZXY`` 中值为 ``1`` 的列构成 ``rotations`` 列表；没有旋转列时保持 ``rotations=None``\ 。
* ``GROUP_ID, STACKABILITY_ID, NESTING_HEIGHT, MAXIMUM_STACKABILITY, MAXIMUM_WEIGHT_ABOVE`` 是物品堆叠字段；``MAXIMUM_WEIGHT, MAXIMUM_STACK_DENSITY`` 是箱型字段。
* ``IS_SEMI_TRAILER_TRUCK=1`` 加 ``TRACTOR_WEIGHT ... MIDDLE_AXLE_MAXIMUM_WEIGHT`` 各列构成 :class:`~packingsolver3d.model.SemiTrailerTruck`。
* ``parameters.csv`` 的 ``objective`` 与 ``unloading-constraint`` 行即 :class:`~packingsolver3d.model.Objective` 与 :class:`~packingsolver3d.model.UnloadingConstraint` 的令牌。

与上游可执行文件比对
--------------------

本包调用的正是上游命令行调用的同一个 ``optimize()``\ ，因此在确定性模式下，同一实例在这里与用同一提交编译、带 ``--linear-programming-solver highs`` 和同样时间限制的 ``packingsolver_box`` 应得到相同目标值。anytime 模式依赖时序，当前解可能不同，报告的界不会。
