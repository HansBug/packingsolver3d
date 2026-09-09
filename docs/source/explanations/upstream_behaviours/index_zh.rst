必须了解的上游行为
==================

packingsolver3d 是忠实的绑定：它做的就是上游 PackingSolver 在锁定提交上做的事，不掩盖上游的选择。以下行为是在构建本包过程中发现的，每条都有上游源码位置或可复现的观察作为依据，并说明本包如何处理。如果你依赖其中某条，submodule 移动后请回来重读本页。

LP 后端固定为 HiGHS
-------------------

*上游。* ``OptimizeParameters::linear_programming_solver_name`` 默认为 ``CLP``\ ；解析名字的工厂是一串 ``#if <backend>_FOUND`` 守卫，末尾是一个裸 ``throw``\ （"no linear programming solver found"）。内置构建只编了 HiGHS。小实例走不到列生成，会把问题掩盖起来。

*本包。* 每次调用都把求解器名设为 HiGHS；``linear_programming_solver`` 参数只为自定义构建保留。

``copies_min`` 默认为"全部副本"
-------------------------------

*上游。* ``InstanceBuilder::build`` 把物品类型的 ``copies_min == -1`` 解析为 ``copies``\ （knapsack 目标除外，解析为 ``0``\ ）。因此显式的 ``copies_min = 0`` 会让装箱返回零个箱作为真正的最优。

*本包。* :attr:`ItemType.copies_min <packingsolver3d.model.ItemType.copies_min>` 默认为 ``None`` 并交给上游。只在你确实想表达"至少这么多件"时才设它。

``boxstacks`` 分堆时不比较底面积
--------------------------------

*上游。* ``tree_search.cpp`` 只按 ``(group_id, stackability_id)`` 给物品类型分桶；随后 ``SolutionBuilder::add_item`` 在物品底面积与所在堆不符时抛错。两个 id 默认都是 ``0``\ ，所以一个含两种形状的普通实例就会触发。

*本包。* :func:`packingsolver3d.boxstacks.validate` 在两种物品类型共享一个桶却在允许的旋转下没有共同底面积时抛出 :class:`~packingsolver3d.errors.StackSemanticsError`。给形状不同的物品不同的 ``stackability_id``\ 。

``boxstacks`` 保持物品直立
--------------------------

*上游。* 顺序一维/矩形阶段只会选 ``XYZ`` 或 ``YXZ``\ （``sequential_onedimensional_rectangle.cpp``\ ），树搜索按 ``z(Rotation::XYZ)`` 取高度。只允许侧翻旋转的物品类型最终在 ``SolutionBuilder::add_item`` 处抛出 "forbidden rotation"。

*本包。* :func:`packingsolver3d.boxstacks.validate` 对 ``rotations`` 既不含 ``XYZ`` 也不含 ``YXZ`` 的物品类型抛出 :class:`~packingsolver3d.errors.UnsupportedFeatureError`。``box`` 求解器六种旋转都能放。

``boxstacks`` 接受缺陷却把堆放在缺陷上
--------------------------------------

*观察。* 在锁定提交上，地面 :class:`~packingsolver3d.model.Defect` 位于角落、内部或横贯整箱宽度的实例，产生的堆都与缺陷重叠；上游证书列出了缺陷，搜索把它当作插入锚点，但没有重叠检查拒绝该放置。这是上游行为而非翻译错误：本包的测试只断言这类实例被接受。

*本包。* ``defects`` 原样转发。上游改变之前不要依赖缺陷会被避开；:func:`packingsolver3d.boxstacks.solve` 的 docstring 重申了这一点。

``box`` 模型没有堆叠、缺陷与卸载
--------------------------------

*上游。* ``box`` 求解器只知道箱、物品、旋转与承重。它的读取器忽略未知列且不给任何提示。

*本包。* :func:`packingsolver3d.box.validate` 在实例带有堆叠字段、缺陷或卸载约束时抛出 :class:`~packingsolver3d.errors.UnsupportedFeatureError`，而不是悄悄求解另一个问题。这些请用 :func:`packingsolver3d.boxstacks.solve`。

限制是上游的，求解器在进程内运行
--------------------------------

*上游。* ``time_limit`` 送入上游计时器，在算法检查点检查；``memory_limit`` 送入 ``memory_limit_megabytes``\ ，在检查点与常驻内存比较。

*本包。* 两者原样转发。没有墙钟 kill，没有硬性地址空间限制，上游内部的崩溃会结束解释器。:doc:`/how_to/budgets/index_zh` 给出需要时恢复硬限制与崩溃隔离的工作进程模式。

物品利润与箱成本默认为几何量
----------------------------

*上游。* 未设置的物品利润变为 ``x * y * z``\ ；未设置的箱成本变为 ``x * y``——是面积，不是体积。

*本包。* 两个字段默认 ``None`` 并交给上游。当箱型高度不同且优化 ``VARIABLE_SIZED_BIN_PACKING`` 时，请显式传 ``cost``\ 。

anytime 运行不可逐次复现
------------------------

*上游。* 默认的 ``ANYTIME`` 模式使用线程与墙钟检查点；到时限时的当前解可能因运行而异。报告的界不依赖时序。

*本包。* 需要两次运行一致时用 ``OptimizationMode.NOT_ANYTIME_DETERMINISTIC``\ （或上游测试所用的 ``NOT_ANYTIME_SEQUENTIAL``\ ），并总是记录 ``result.run.options``\ 。

``default`` 目标不产生任何解
----------------------------

*上游。* ``Objective::Default`` 是 ``Instance`` 在设置目标之前携带的占位符；上游命令行的 ``--objective`` 没有默认值，其优化器只为显式目标运行算法。以 ``default`` 求解的实例在箱子有多份时完全不返回装法，其他情况下返回的结果没有定义。

*本包。* :class:`~packingsolver3d.model.Instance` 要求显式给出 ``objective``\ ，而 :attr:`Objective.DEFAULT <packingsolver3d.model.Objective.DEFAULT>`\ （因为是上游令牌而保留）会在调用求解器之前以 :class:`~packingsolver3d.errors.InvalidInstanceError` 拒绝。
