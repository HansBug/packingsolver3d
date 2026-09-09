架构：一个扩展模块，值进值出
============================

编译了什么
----------

仓库以 git submodule 的形式内置上游 PackingSolver，锁定在一个固定提交（记录为 :mod:`packingsolver3d.config.meta` 中的 ``__UPSTREAM_COMMIT__``\ ），从不打补丁。根目录的 ``CMakeLists.txt`` 以固定选项集加入上游源码树——HiGHS 为唯一线性规划后端、不编可执行文件、不编上游测试——并把 ``PackingSolver::box`` 与 ``PackingSolver::boxstacks`` 两个库连同一层短小的 pybind11 桥接（``packingsolver3d/_core.cpp``\ ）链接成单个扩展模块 ``packingsolver3d._core``\ 。Boost、HiGHS 与上游自己的求解器库都静态链接其中；wheel 在标准库之外没有依赖。

什么跨越边界
------------

桥接层只暴露两个函数：``box_solve`` 与 ``boxstacks_solve``\ 。每个函数接收普通 Python 值（由 :class:`~packingsolver3d.model.Instance` 生成的 dict 与 list），通过上游的 ``InstanceBuilder`` 构造上游实例，填充 ``OptimizeParameters``\ ，释放 GIL，调用上游的 ``optimize()``\ ，再把最优解拷贝回普通值：箱、堆、放置、上游统计块、报告的界以及捕获的日志。没有任何上游对象存活到调用之后；Python 侧不持有任何指向求解器内存的指针、缓冲或引用，所以 C++ 的生命周期从不成为调用者的问题。

字段名、目标令牌、旋转名与选项名都是上游原文；桥接层用上游自己的流算符解析令牌而不是重新实现。载荷中缺失的键不会触发相应的 builder setter，于是上游默认值生效——与上游 CSV 读取器对缺失列的处理完全相同。

由此而来的含义
--------------

* **进程内。** 求解器运行在你的解释器里。上游内部的崩溃会结束进程，内存预算是上游自己的软检查。需要隔离或硬限制时，把求解放到工作进程里（:doc:`/how_to/budgets/index_zh` 给出做法）；本包刻意不在 API 背后藏一层子进程。
* **两层校验。** 结构性检查（空实例、非正尺寸、``copies_min`` 越界、缺陷落在未知箱型上）与 :doc:`/explanations/upstream_behaviours/index_zh` 描述的语义性拒绝在 Python 侧、调用桥接之前完成；上游 ``InstanceBuilder`` 自己的检查在桥接内部运行，以携带上游原话的 :class:`~packingsolver3d.errors.InvalidInstanceError` 抛出。
* **可审计。** 每个 :class:`~packingsolver3d.result.Result` 带有 :class:`~packingsolver3d.result.RunRecord`：传给上游的全部选项、上游被捕获的输出、墙钟时间。从本包发出的每个数字都能追溯到产生它的那次调用。
* **范围只有两种问题类型。** ``rectangle``、``rectangleguillotine``、``onedimensional``、``irregular`` 不编入；包名里的 ``3d`` 就是这个意思。
