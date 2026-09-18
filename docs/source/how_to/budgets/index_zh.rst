预算、算法开关与批量运行
========================

当实例不是瞬间就能解完——研究实验、基准测试、有响应时间要求的服务——请用本页。

时间预算
--------

.. code-block:: python

   result = box.solve(instance, time_limit=35.0)

``time_limit``\ （秒）交给上游的计时器。各搜索阶段在自己的检查点看表，因此一次运行可能超出一个检查点间隔；若精确数字重要，请测量 ``result.run.wall_time``\ 。不设限制时上游会跑完整个日程，在难实例上意味着非常久。

内存预算
--------

.. code-block:: python

   result = box.solve(instance, time_limit=35.0, memory_limit=4096)

``memory_limit``\ （MiB）即上游自己的 ``memory_limit_megabytes``\ ：求解器在检查点把常驻内存与之比较并停止增长。这是软限制——求解器之外没有任何东西强制它。下面"隔离"一节说明如何加硬限制。

优化模式
--------

:class:`~packingsolver3d.model.OptimizationMode` 选择上游的日程：

* ``ANYTIME``\ （默认）在限制内持续改进当前解；
* ``NOT_ANYTIME`` 与 ``NOT_ANYTIME_DETERMINISTIC`` 跑固定日程，后者可复现；
* ``NOT_ANYTIME_SEQUENTIAL`` 是把顺序模式一路下传到各子求解器的固定日程，上游自己的单元测试用它。

.. code-block:: python

   from packingsolver3d import OptimizationMode
   result = box.solve(instance, time_limit=35.0,
                      optimization_mode=OptimizationMode.NOT_ANYTIME_DETERMINISTIC)

进度与提前停止
--------------

.. code-block:: python

   def watch(event):
       print(f"{event.time:6.2f} s  {event.number_of_items} items  {event.label}")
       return event.number_of_items < 1000      # 返回 False 即停止求解

   result = box.solve(instance, time_limit=60.0, progress_callback=watch)
   result.run.stop_reason                      # watch 返回过 False 时为 'callback'，否则为 None

``progress_callback`` 就是上游的 ``new_solution_callback``\ ：每次当前解改进时被调用一次，参数是一个 :class:`~packingsolver3d.result.ProgressEvent`\ ，里面是桥接层从当前解复制出来的几个数字（上游时钟上的时间、件数、箱数、利润、成本、上游给找到它的算法打的标签）。完整的摆放方案要到结束才有；事件是快照，不是句柄。返回 ``False`` 即在此停止求解，上游会在下一个节点检查停止标志，几毫秒内以当前解返回。回调里抛出的异常同样会停止求解，并在求解器返回后原样重新抛出。回调可能在上游的工作线程上运行（``box`` 的 anytime 树搜索使用多个线程），但始终持有 GIL，普通 Python 代码是安全的，只是要写得短。

触发频率取决于算法：``box`` 的 anytime 树搜索每次改进都上报，通常每秒数次；``boxstacks`` 的单箱算法每个队列尺寸级别上报一次（前几秒有几次，之后很少），多箱算法每次迭代上报一次。``NOT_ANYTIME_*`` 各模式通常只在结束时有一次事件。

搜索停滞时自动停止
------------------

.. code-block:: python

   result = box.solve(instance, time_limit=120.0, stop_when_unimproved_for=10.0)
   result.run.stop_reason      # 十秒没有新的当前解则为 'unimproved'，否则为 None

``ANYTIME`` 模式下搜索只在到达时限、收到停止信号或证明最优时结束（见 :doc:`/explanations/upstream_behaviours/index_zh`\ ），所以哪怕当前解早已不再变化，``time_limit`` 通常也会被整个用完。``stop_when_unimproved_for`` 补上 anytime 求解惯用的终止条件：一个看门狗线程把上游的时钟与最近一次改进的时间作比较，间隔达到给定秒数时发出上游自己的停止信号。求解在几毫秒内返回，当前解完整保留，``result.run.stop_reason == 'unimproved'``\ 。

在首个解出现之前，计时从求解开始算。``box`` 在多数实例上一秒左右就有首个解，但 ``boxstacks`` 的单箱算法在第一轮扫描完成前不会上报任何东西（几百根立柱的集装箱要几秒），耐心值较短时请配 ``stop_when_unimproved_after``\ ：

.. code-block:: python

   result = boxstacks.solve(instance, time_limit=120.0,
                            stop_when_unimproved_for=5.0, stop_when_unimproved_after=15.0)

两个参数可与 ``progress_callback`` 组合：回调返回 ``False`` 优先（``stop_reason == 'callback'``\ ），看门狗线程从不进入 Python。

算法开关
--------

``box`` 求解器把算法组合暴露为关键字参数，各取 ``True`` / ``False`` / ``None``\ （交给上游）：``use_tree_search``、``use_tree_search_maximal_spaces``、``use_sequential_single_knapsack``、``use_sequential_value_correction``、``use_column_generation``、``use_dichotomic_search``、``use_dual_feasible_functions``\ 。``boxstacks`` 没有开关。各开关对应的上游参数见 :doc:`/reference/solver_options/index_zh`。

日志
----

``verbosity_level=1``\ （或更高）让上游打印进度表；文本被捕获进 ``result.run.stdout`` 而不是你的终端。

批量运行
--------

每个结果都带着复现所需的一切。一个实验循环通常把状态、达到值、报告的界分开保存：

.. code-block:: python

   rows = []
   for name, inst in instances.items():
       r = box.solve(inst, time_limit=35.0, memory_limit=4096,
                     optimization_mode=OptimizationMode.NOT_ANYTIME_DETERMINISTIC)
       rows.append({
           'instance': name,
           'status': r.status.value,           # 'optimal' / 'feasible' / 'no-solution' / 'infeasible'
           'value': r.value, 'bound': r.bound, # 永远不要把这两列合并
           'bins': r.number_of_bins,
           'solve_time': r.solve_time, 'wall_time': r.run.wall_time,
           'options': r.run.options,           # 上游实际收到的全部参数
       })

``result.to_json()`` 是与机器无关的装箱快照（有意不含 ``run``\ ）。

隔离：硬限制与崩溃隔离
----------------------

求解器运行在你的解释器内部，由此带来两个后果：上游内部的崩溃会结束整个进程；从内部无法施加硬性内存限制。两者任一重要时，把每次求解放到工作进程里跑。:class:`~packingsolver3d.model.Instance` 与 :class:`~packingsolver3d.result.Result` 都可 pickle，所以只需几行：

.. code-block:: python

   import multiprocessing as mp
   import resource

   def _worker(conn, instance, kwargs, mem_mib):
       limit = mem_mib * 1024 * 1024
       resource.setrlimit(resource.RLIMIT_AS, (limit, limit))   # 仅 POSIX
       from packingsolver3d import box
       try:
           conn.send(('ok', box.solve(instance, **kwargs)))
       except Exception as err:                                  # 上游侧失败
           conn.send(('error', repr(err)))

   def solve_isolated(instance, time_limit=35.0, mem_mib=4096, grace=30.0, **kwargs):
       parent, child = mp.Pipe(duplex=False)
       kwargs.update(time_limit=time_limit, memory_limit=mem_mib)
       p = mp.get_context('spawn').Process(target=_worker, args=(child, instance, kwargs, mem_mib))
       p.start()
       p.join(time_limit + grace)
       if p.is_alive():
           p.kill(); p.join()
           return 'timeout', None
       if not parent.poll():
           return 'crashed', p.exitcode
       return parent.recv()

这就给了基准测试通常想要的三层保护：上游自己的软限制、硬性的地址空间限制、以及同时能兜住崩溃的墙钟守卫。
