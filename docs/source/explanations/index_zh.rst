解释路线图
==========

解释类页面回答"为什么是这样"。跑一次求解并不需要它们，但要信任一次求解就需要。当结果让你意外，或在发表用本包得到的数字之前，请读一读。

页面
----

* :doc:`architecture/index_zh` —— 上游 C++ 如何被编进扩展模块、什么东西跨越边界、这对隔离与生命周期意味着什么。
* :doc:`statuses/index_zh` —— ``OPTIMAL``、``FEASIBLE``、``NO_SOLUTION``、``INFEASIBLE`` 在这里的含义，以及为什么达到值与报告的界必须分开。
* :doc:`upstream_behaviours/index_zh` —— 锁定提交上会影响结果的上游 PackingSolver 行为，每条都附证据与本包的处理方式。

.. toctree::
    :maxdepth: 1
    :hidden:

    architecture/index_zh
    statuses/index_zh
    upstream_behaviours/index_zh
