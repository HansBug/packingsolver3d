状态、值与界
============

每个 :class:`~packingsolver3d.result.Result` 报告三件彼此独立的事，本包拒绝把它们混为一谈：

* ``value`` —— 求解器返回的装箱的目标值。这是**达到**的。
* ``bound`` —— 上游为所请求目标报告的界（``BinPackingBound``、``KnapsackBound`` ……）。这是**证明**的。
* ``status`` —— 结论，由上面两者与上游的可行性标志推导。

四种状态
--------

.. list-table::
   :header-rows: 1

   * - 状态
     - 含义
   * - ``OPTIMAL``
     - 存在装箱，且其 ``value`` 达到上游为该目标报告的 ``bound``\ （最小化目标下相等，knapsack 下利润不低于界）。是证明出来的，不是猜的。
   * - ``FEASIBLE``
     - 存在装箱，但该目标没有报告界，或值没有达到界。启发式当前解无论看起来多好都停在这里。
   * - ``NO_SOLUTION``
     - 上游没有返回装箱（没有箱，或没有放下任何物品）。
   * - ``INFEASIBLE``
     - 上游设置了 ``IsProvenInfeasible``\ 。

``FEASIBILITY`` 目标的规则天然不同：全部物品都放下则 ``OPTIMAL``\ ，否则 ``FEASIBLE``\ 。

哪些目标带界
------------

.. list-table::
   :header-rows: 1

   * - 目标
     - ``value`` 读自
     - ``bound`` 读自
     - 方向
   * - ``BIN_PACKING``
     - ``NumberOfBins``
     - ``BinPackingBound``
     - 最小化
   * - ``VARIABLE_SIZED_BIN_PACKING``
     - ``BinCost``
     - ``VariableSizedBinPackingBound``
     - 最小化
   * - ``KNAPSACK``
     - ``ItemProfit``
     - ``KnapsackBound``
     - 最大化
   * - ``OPEN_DIMENSION_X`` / ``_Y`` / ``_Z``
     - ``XMax`` / ``YMax`` / ``ZMax``
     - ``OpenDimension?Bound``\ （仅 ``box``\ ；``boxstacks`` 不报告）
     - 最小化
   * - 其它所有目标（``DEFAULT``、``BIN_PACKING_WITH_LEFTOVERS`` ……）
     - --
     - 无
     - 永不 ``OPTIMAL``

为什么重要
----------

上游自己的 ``is_proven_optimal()`` 用的就是同一比较，本包没有发明更严的标准，只是在上游没有证明时拒绝把结果称为最优。发表实验数字时请保留两列："最好找到的"与"最好的界"。两者之间的差距才是这次运行真正建立起来的东西，也是读者拿它和别的求解器比较时需要的。
