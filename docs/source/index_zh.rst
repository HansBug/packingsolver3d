欢迎来到 packingsolver3d 的文档
============================================================

概览
----

\ **packingsolver3d**\ 是 `PackingSolver <https://github.com/fontanf/packingsolver>`_ 两个三维求解器（``box`` 与 ``boxstacks``）的非官方 Python 发行版。每个 wheel 都内置预编译好的上游可执行文件，Python 层只通过文件和子进程边界与之交互，不存在任何持有求解器内存的 Python 对象。

主要特性
~~~~~~~~

* **值进值出的 API**，基于 frozen dataclass：传入 :class:`~packingsolver3d.model.Instance`，返回 :class:`~packingsolver3d.result.Result`
* **两个求解器共用一套模型**：:mod:`packingsolver3d.box` 处理普通三维装箱，:mod:`packingsolver3d.boxstacks` 处理堆叠、卸载顺序与重量约束
* **每次求解可审计**：结果携带产生它的 argv、退出码、输出流、墙钟时间与可执行文件摘要
* **状态不掺水**：求解器报告的界从不被改称已证最优；``OPTIMAL`` 只表示达到值与报告的界相符
* **真实的资源门禁**：``time_limit`` 加墙钟保护，``memory_limit`` 以 POSIX 地址空间 rlimit 硬性执行
* **预编译 wheel** 覆盖 Linux、macOS、Windows 上的 CPython 3.7 至 3.14

快速开始
~~~~~~~~

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

架构
~~~~

* **包根** (``packingsolver3d``)：重导出模型、结果、错误类型以及两个求解器模块
* **求解器模块** (``packingsolver3d.box``、``packingsolver3d.boxstacks``)：各一个 ``solve`` 函数，与上游命令行选项一一对应
* **元数据层** (``packingsolver3d.config``)：包版本、锁定的上游 commit 与构建选项
* **可执行文件** (``packingsolver3d.bin``)：wheel 内置的预编译上游二进制

上游与源码
~~~~~~~~~~

* **GitHub 仓库**：https://github.com/HansBug/packingsolver3d
* **PackingSolver 上游**：https://github.com/fontanf/packingsolver

.. include:: api_doc_zh.rst
