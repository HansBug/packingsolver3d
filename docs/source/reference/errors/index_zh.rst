错误
====

所有异常都派生自 :class:`~packingsolver3d.errors.PackingSolverError`，一个 ``except`` 子句即可兜住整个包。子类同时继承对应的内建异常，通用处理代码照常工作。

.. list-table::
   :header-rows: 1

   * - 类
     - 同时是
     - 抛出条件
   * - ``InvalidInstanceError``
     - ``ValueError``
     - 实例结构非法（空、非正尺寸、``copies_min`` 超出 ``[0, copies]``、缺陷落在未知箱型、缺陷尺寸非正）、选项令牌未知，或上游 ``InstanceBuilder`` 拒绝实例——此时消息为上游原话
   * - ``StackSemanticsError``
     - ``InvalidInstanceError``
     - 两种物品类型共享 ``(group_id, stackability_id)`` 桶却没有共同底面积（``boxstacks``\ ）
   * - ``UnsupportedFeatureError``
     - ``ValueError``
     - ``box.solve`` 收到堆叠字段、缺陷或卸载约束；``boxstacks.solve`` 收到只允许侧翻旋转的物品类型
   * - ``SolverFailedError``
     - ``RuntimeError``
     - 上游在求解中抛出异常；``.run`` 携带部分的 :class:`~packingsolver3d.result.RunRecord`

除上游侧的情形外，其余都在调用桥接之前抛出。该抛错的地方从不返回空解；上游正当产生的空装箱以 ``Status.NO_SOLUTION`` 报告，而不是异常。
