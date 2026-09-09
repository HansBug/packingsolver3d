教程路线图
==========

第一次接触 packingsolver3d、希望每一步都有一个可观察的小成功时，从这里开始。教程每页只教一条路径，刻意不覆盖所有选项和边角情况；当你的问题变成"怎么给一百个实例设预算"或"这个字段在上游到底什么意思"时，请转到 :doc:`/how_to/index_zh` 或 :doc:`/reference/index_zh`。

阅读顺序
--------

1. :doc:`quick_start/index_zh` —— 安装 wheel，用 ``box`` 求解一个十件物品的装箱实例，读懂结果：状态、目标值、报告的界、放置。
2. :doc:`boxstacks/index_zh` —— 同一套模型加上堆叠规则、重量、卸载约束与半挂车，用 ``boxstacks`` 求解。

下一步
------

* 预算、算法开关与批量运行：:doc:`/how_to/budgets/index_zh`。
* ``OPTIMAL`` 在这里究竟意味着什么、为什么看起来不错的解仍可能只是 ``FEASIBLE``\ ：:doc:`/explanations/statuses/index_zh`。
* 在信任结果之前必须了解的上游行为：:doc:`/explanations/upstream_behaviours/index_zh`。

.. toctree::
    :maxdepth: 1
    :hidden:

    quick_start/index_zh
    boxstacks/index_zh
