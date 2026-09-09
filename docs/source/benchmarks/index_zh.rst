基准测试路线图
==============

这一节是一项小规模、可完整复现的能力研究。它把 packingsolver3d，也就是上游 PackingSolver 的 ``box`` 求解器，放到三个公开的三维装箱实例族上，与 Python、Go、Rust 生态里最常被拿来用的开源三维装箱库以及两个作为参照的精确程序一起跑。每个实例都小到可以画出来，而且几乎每个实例的最优值都是已知的，所以表格能把"找到了一个不错的装法"和"找到了最优装法"区分开。

它不是什么：不是装箱软件的综合排名。实例刻意选得小且没有附加约束（没有重量、稳定性、堆叠规则），预算很短，每个数字都只跑了一次。引用任何数字之前请先读 :doc:`protocol/index_zh`。

页面
----

* :doc:`datasets/index_zh` -- 三个基准：谁发表的、官方文件在哪、实例长什么样、表格用了哪些 case。
* :doc:`participants/index_zh` -- 所有参与的库和参照程序：链接、版本、背后的算法、驱动方式。
* :doc:`protocol/index_zh` -- 预算、机器、对每个解做的独立几何校验、界/总计/差距的算法，以及注意事项。
* :doc:`leaderboards/index_zh` -- 完整结果：每个基准一张天梯，一行一个参与者，一列一个 case，另加跨基准汇总。
* :doc:`gallery/index_zh` -- 每个基准取一个 case，把我们的解和其他库的解并排画出来。

复现
----

.. code-block:: bash

   pip install "packingsolver3d[plot]" kaleido
   make benchmarks          # tools/make_benchmarks.py --solve --render

solve 一步以 10 s 时限对 28 个 case 调用 ``box.solve`` 并重写 ``tools/benchmarks/ours.json``\ ；render 一步重新校验每个存下来的解（我们的和第三方的一样），从摆放位置重算目标值，并重新生成本节的表格与图。

.. toctree::
    :maxdepth: 1
    :hidden:

    datasets/index_zh
    participants/index_zh
    protocol/index_zh
    leaderboards/index_zh
    gallery/index_zh
