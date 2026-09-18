求解器选项
==========

两个 ``solve`` 函数共享核心选项；``box.solve`` 多出算法开关，``boxstacks.solve`` 多出卸载约束覆盖。每个选项对应上游 ``OptimizeParameters`` 的一个字段；``None`` 表示保留上游默认。

共享选项
--------

.. list-table::
   :header-rows: 1

   * - 关键字
     - 上游
     - 说明
   * - ``time_limit``
     - ``timer.set_time_limit``
     - 秒；在算法检查点检查
   * - ``memory_limit``
     - ``memory_limit_megabytes``
     - MiB；上游自己的软检查
   * - ``verbosity_level``
     - ``verbosity_level``
     - 默认 ``0``\ ；日志捕获进 ``RunRecord.stdout``
   * - ``optimization_mode``
     - ``optimization_mode``
     - :class:`~packingsolver3d.model.OptimizationMode` 令牌
   * - ``linear_programming_solver``
     - ``linear_programming_solver_name``
     - 总是设置；除自定义构建外为 ``highs``
   * - ``progress_callback``
     - ``new_solution_callback``
     - 每次当前解改进时以一个 :class:`~packingsolver3d.result.ProgressEvent` 调用；返回 ``False`` 可提前停止求解（此时 ``RunRecord.stop_reason == 'callback'``\ ）；见 :doc:`/how_to/budgets/index_zh`

``box.solve`` 的开关
--------------------

各取 ``True``、``False`` 或 ``None``\ ：

``use_tree_search``、``use_tree_search_maximal_spaces``、``use_sequential_single_knapsack``、``use_sequential_value_correction``、``use_column_generation``、``use_dichotomic_search``、``use_dual_feasible_functions`` -> 同名的 ``OptimizeParameters`` 字段。都不设时上游根据实例自选组合。

``boxstacks.solve`` 的额外选项
------------------------------

``unloading_constraint`` -> ``InstanceBuilder::set_unloading_constraint``\ ，在本次调用中覆盖 :attr:`Instance.unloading_constraint <packingsolver3d.model.Instance.unloading_constraint>`。

返回什么
--------

``Result.value`` 与 ``Result.bound`` 按 :doc:`/explanations/statuses/index_zh` 所列从上游输出读取；``Result.statistics`` 是上游 ``Solution`` 块原文（``NumberOfItems``、``NumberOfBins``、``ItemProfit``、``ItemWeight``、``BinCost``、``VolumeLoad``、``WeightLoad``、``Waste``、``XMax``、``YMax``、``ZMax``、``NumberOfStacks``、``NumberOfUnpackedItems`` ……）；``Result.solve_time`` 是上游的 ``Time``\ ；``Result.run`` 是 :class:`~packingsolver3d.result.RunRecord`。
