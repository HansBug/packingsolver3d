欢迎来到 packingsolver3d 的文档
============================================================

概览
----

\ **packingsolver3d**\ 是 `PackingSolver <https://github.com/fontanf/packingsolver>`_ 两个三维求解器（``box`` 与 ``boxstacks``\ ）的非官方 Python 发行版。上游 C++ 与一层很薄的 pybind11 桥接一起编译成一个扩展模块；每次求解在进程内完成，结果拷贝成普通 Python 值返回，不存在任何持有求解器内存的 Python 对象。本包独立于 PackingSolver 维护，未获其作者认可；求解器本身从锁定的上游提交原样编译而来。

主要特性
~~~~~~~~

* **值进值出的 API**，基于 frozen dataclass：传入 :class:`~packingsolver3d.model.Instance`，返回 :class:`~packingsolver3d.result.Result`
* **两个求解器共用一套模型**：:mod:`packingsolver3d.box` 处理普通三维装箱，:mod:`packingsolver3d.boxstacks` 处理堆叠、重量、卡车、卸载顺序与缺陷
* **状态不掺水**：求解器报告的界从不被改称已证最优；``OPTIMAL`` 只表示达到值与报告的界相符
* **每次求解可审计**：结果携带传给上游的全部选项、上游被捕获的日志与墙钟时间
* **上游自身的限制**：``time_limit`` 与 ``memory_limit`` 直接透传给求解器的计时器与内存检查
* **预编译 wheel** 覆盖 Linux、macOS、Windows 的 x86_64 与 arm64，各平台有官方构建的 CPython 3.7 至 3.14

快速开始
~~~~~~~~

.. code-block:: bash

   pip install packingsolver3d

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, box

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
       item_types=[ItemType(x=20, y=30, z=40, copies=6)],
       objective=Objective.BIN_PACKING,
   )
   result = box.solve(instance, time_limit=2.0)

   assert result.status.name == 'OPTIMAL'
   assert result.number_of_bins == 1
   for placement in result.placements:
       print(placement.bin_id, placement.x, placement.y, placement.z, placement.rotation)

.. raw:: html
   :file: _static/figures/box_bin_packing.html

.. only:: latex

   .. image:: _static/figures/box_bin_packing.png
      :width: 90%

完整流程见 :doc:`tutorials/quick_start/index_zh`；在信任数字之前应了解的、继承自上游的行为汇总在 :doc:`explanations/upstream_behaviours/index_zh`。

架构
~~~~

* **包根** (``packingsolver3d``)：重导出模型、结果、错误类型以及两个求解器模块
* **求解器模块** (``packingsolver3d.box``、``packingsolver3d.boxstacks``)：各一个 ``solve`` 函数，与上游参数一一对应
* **原生桥接** (``packingsolver3d._core``)：上游 ``box``、``boxstacks`` 与 pybind11 胶水，合成一个扩展模块
* **元数据** (``packingsolver3d.config``)：包版本、锁定的上游提交与构建选项

上游与源码
~~~~~~~~~~

* **GitHub 仓库**：https://github.com/HansBug/packingsolver3d
* **PackingSolver 上游**：https://github.com/fontanf/packingsolver

教程
----

教程是每步都有可观察成功的学习路径。路线图说明阅读顺序，各页依次展开。

.. toctree::
    :maxdepth: 2
    :caption: 教程
    :hidden:

    教程路线图 <tutorials/index_zh>
    tutorials/quick_start/index_zh
    tutorials/boxstacks/index_zh

* :doc:`教程路线图 <tutorials/index_zh>`
* :doc:`tutorials/quick_start/index_zh`
* :doc:`tutorials/boxstacks/index_zh`

任务指南
--------

任务指南面向已经知道自己要做什么的读者。

.. toctree::
    :maxdepth: 2
    :caption: 任务指南
    :hidden:

    任务指南路线图 <how_to/index_zh>
    how_to/installation/index_zh
    how_to/budgets/index_zh
    how_to/visualization/index_zh

* :doc:`任务指南路线图 <how_to/index_zh>`
* :doc:`how_to/installation/index_zh`
* :doc:`how_to/budgets/index_zh`
* :doc:`how_to/visualization/index_zh`

解释
----

解释类页面给出设计背后的理由，以及影响结果的上游行为。

.. toctree::
    :maxdepth: 2
    :caption: 解释
    :hidden:

    解释路线图 <explanations/index_zh>
    explanations/architecture/index_zh
    explanations/statuses/index_zh
    explanations/upstream_behaviours/index_zh

* :doc:`解释路线图 <explanations/index_zh>`
* :doc:`explanations/architecture/index_zh`
* :doc:`explanations/statuses/index_zh`
* :doc:`explanations/upstream_behaviours/index_zh`

参考
----

参考页陈述事实：字段、选项、错误，以及自动生成的 API 地图。

.. toctree::
    :maxdepth: 2
    :caption: 参考
    :hidden:

    参考地图 <reference/index_zh>
    reference/model_fields/index_zh
    reference/solver_options/index_zh
    reference/errors/index_zh

* :doc:`参考地图 <reference/index_zh>`
* :doc:`reference/model_fields/index_zh`
* :doc:`reference/solver_options/index_zh`
* :doc:`reference/errors/index_zh`

.. include:: api_doc_zh.rst
