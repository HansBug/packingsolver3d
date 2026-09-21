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

anytime 模式会一直运行直到被停止
--------------------------------

*上游。* ``ANYTIME`` 模式下的搜索只在三种情况结束：到达时限、收到停止信号、或证明不存在更好的解（所有物品都已装入，或达到了界）。否则它会不断扩大搜索：``box`` 的树搜索按倍数扩大队列且没有尺寸上限；自锁定的提交（``2a598481``\ ，`fontanf/packingsolver#578 <https://github.com/fontanf/packingsolver/pull/578>`_\ ）起，``boxstacks`` 的单箱算法也如此，逐级扩大矩形子问题与三维兜底搜索的队列，并上报每一次改进。此前 ``boxstacks`` 只做一次固定扫描并自行返回，但短于该扫描（约 130 根立柱需 12 s）的时限会把扫描截在中途，并把截断的前缀当作结果上报；现在任何时限得到的都是已找到的最好的一次完整扫描。维护者在 `fontanf/packingsolver#580 <https://github.com/fontanf/packingsolver/issues/580>`_ 中确认"运行直到被停止"就是预期语义。

*本包。* ``ANYTIME``\ （默认模式）求解务必传 ``time_limit``\ ：在装不满且搜索树耗不尽的实例上，``box.solve`` 与 ``boxstacks.solve`` 不传时限就永不返回。``NOT_ANYTIME_*`` 各模式仍只做一次固定扫描并自行返回，代价是时限短于该扫描时会出现上述截断。``stop_when_unimproved_for``\ （见 :doc:`/how_to/budgets/index_zh`\ ）提供上游期望由调用方发出的那个停止信号：多少秒没有新的当前解，求解即结束。

多箱 ``boxstacks`` 逐箱装载
-----------------------------

*上游。* 多箱时 ``boxstacks`` 没有树搜索：bin packing 在箱子能装下的平均件数超过 16（份数密集的货）或 64（其余）时走*序贯单背包*（``SSK``：用逐级增长的单箱搜索装满一箱、扣掉已装货物、继续下一箱），低于阈值时以及 knapsack、变尺寸装箱始终走*序贯价值修正*（``SVC``：用定长的一轮把所有箱子装一遍、调整货物价值、再来一轮）。``SVC`` 要整轮跑完所有箱子才报出第一个解，一千件货物上要几十秒，且一旦 bin packing 的解只用了两个以内的箱子就立即返回；``SSK`` 在示例的 40 尺柜货载上一秒内报解。两者互不回退：贪心一轮装不下的箱数会以"到时限无解"收场，在 1.2 到 2 倍柜容配三四个箱子的货载上这多半说明箱数本身不够。``9bfb9431`` 之前多箱只有 ``SVC``；``63ed7915``（`fontanf/packingsolver#584 <https://github.com/fontanf/packingsolver/pull/584>`_）把计时器传进了定价子问题，此前 ``SSK`` 会超出时限最多 25 秒。0.0.5（上游 ``9ae71316``）修掉了这条路径的两个崩溃：箱重检查在搜索里按乘法容差 ``PSTOL`` 放宽、在 ``Solution::build`` 里却严格比较，被放宽接受的一次放置会以 *solution doesn't satisfy bin weight capacity* 中止（`fontanf/packingsolver#582 <https://github.com/fontanf/packingsolver/issues/582>`_，由 `#586 <https://github.com/fontanf/packingsolver/pull/586>`_ 改为按实例最高箱重预计算的一个绝对容差）；多箱 knapsack 的 ``SVC`` 对整轮未装入的品类除以其 0 份已装数，下一轮以 *Items must have strictly positive profits.* 中止（`#587 <https://github.com/fontanf/packingsolver/issues/587>`_，由 `#588 <https://github.com/fontanf/packingsolver/pull/588>`_ 改为该品类价值保持不变）。

*本包。* :func:`~packingsolver3d.algorithm_path` 复刻这一选择，:func:`~packingsolver3d.recommend_time_budget` 对两条路径分别给预算。涉及堆叠限制或只能直立的货物时，bin packing 的箱数请比体积下界多给一个；这类货载上的 ``NO_SOLUTION`` 先理解为"这些箱子不够"，再考虑"时间不够"。43 个集装箱货载、60 秒上限的实测：``2a598481`` 首解中位 30 秒、31 个无解；钉住的提交首解中位 0.5 秒、15 个无解，而这 15 个在此前每个提交上同样无解（`fontanf/packingsolver#583 <https://github.com/fontanf/packingsolver/issues/583>`_）。

``default`` 目标不产生任何解
----------------------------

*上游。* ``Objective::Default`` 是 ``Instance`` 在设置目标之前携带的占位符；上游命令行的 ``--objective`` 没有默认值，其优化器只为显式目标运行算法。以 ``default`` 求解的实例在箱子有多份时完全不返回装法，其他情况下返回的结果没有定义。

*本包。* :class:`~packingsolver3d.model.Instance` 要求显式给出 ``objective``\ ，而 :attr:`Objective.DEFAULT <packingsolver3d.model.Objective.DEFAULT>`\ （因为是上游令牌而保留）会在调用求解器之前以 :class:`~packingsolver3d.errors.InvalidInstanceError` 拒绝。
