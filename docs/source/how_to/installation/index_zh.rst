安装 packingsolver3d
====================

用本页确认你的平台是否有预编译 wheel，以及没有时该怎么做。

Wheel
-----

``pip install packingsolver3d`` 会自动选择 wheel。以下平台的 wheel 均为原生构建（无模拟、无交叉编译）：

.. list-table:: 预编译 wheel
   :header-rows: 1

   * - 平台
     - 架构
     - CPython 版本
   * - Linux（manylinux 与 musllinux）
     - x86_64
     - 3.7 -- 3.14
   * - Linux（manylinux 与 musllinux）
     - aarch64
     - 3.8 -- 3.14
   * - macOS 11+
     - arm64（Apple silicon）
     - 3.8 -- 3.14
   * - macOS 11+
     - x86_64（Intel）
     - 3.8 -- 3.14
   * - Windows
     - AMD64
     - 3.7 -- 3.14
   * - Windows
     - ARM64
     - 3.11 -- 3.14

空缺来自我们的上游：CPython 3.11 之前没有官方 Windows ARM64 构建，Python 3.7（2023 年停止维护）没有 Linux/macOS 的 arm64 构建。不构建自由线程（``t``\ ）与 PyPy 解释器的 wheel。

一个 wheel 只包含一个扩展模块 ``packingsolver3d._core``\ ，上游求解器静态链接其中，标准库之外没有运行时依赖。

其它架构
--------

i686、ppc64le、s390x、armv7l、riscv64、loongarch64 不构建 wheel，``pip`` 在这些平台会退回 sdist。源码构建需要 CMake 3.28 及以上、C++17 编译器（GCC 10+、Clang 或 MSVC 2022）以及网络访问——上游在配置阶段通过 CMake ``FetchContent`` 拉取 Boost、HiGHS 和它的求解器库。工作站上约需十到二十分钟：

.. code-block:: bash

   pip install packingsolver3d --no-binary packingsolver3d

验证
----

.. code-block:: python

   >>> import packingsolver3d
   >>> from packingsolver3d import BinType, Instance, ItemType, Objective, box
   >>> instance = Instance(bin_types=[BinType(x=10, y=10, z=10)],
   ...                     item_types=[ItemType(x=5, y=5, z=5, copies=8)],
   ...                     objective=Objective.BIN_PACKING)
   >>> box.solve(instance, time_limit=1.0).status
   <Status.OPTIMAL: 'optimal'>

如果导入时报 ``packingsolver3d._core is not built for this interpreter``\ ，说明安装的包里没有你这个解释器的扩展——通常是源码安装时跳过了构建步骤。重新安装，或在检出的仓库里 ``make build``\ 。

开发安装
--------

.. code-block:: bash

   git clone --recursive https://github.com/HansBug/packingsolver3d.git
   cd packingsolver3d
   pip install -r requirements-build.txt -r requirements-test.txt -r requirements-cov.txt
   make build      # CMake 配置 + 构建上游与桥接层，模块放入包目录
   make unittest   # pytest、docstring 示例、覆盖率

``build/cmake`` 中的 CMake 构建树在不同解释器之间复用：切换 Python 只重编桥接层。
