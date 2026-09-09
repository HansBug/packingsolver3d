Install packingsolver3d
=======================

Use this page to find out whether a prebuilt wheel exists for your platform and what to do when it does not.

Wheels
------

``pip install packingsolver3d`` picks a wheel automatically. Wheels are built natively (no emulation, no cross-compilation) for these platforms:

.. list-table:: Prebuilt wheels
   :header-rows: 1

   * - Platform
     - Architecture
     - CPython versions
   * - Linux (manylinux and musllinux)
     - x86_64
     - 3.7 -- 3.14
   * - Linux (manylinux and musllinux)
     - aarch64
     - 3.8 -- 3.14
   * - macOS 11+
     - arm64 (Apple silicon)
     - 3.8 -- 3.14
   * - macOS 11+
     - x86_64 (Intel)
     - 3.8 -- 3.14
   * - Windows
     - AMD64
     - 3.7 -- 3.14
   * - Windows
     - ARM64
     - 3.11 -- 3.14

The gaps follow what exists upstream of us: CPython has no official Windows ARM64 build before 3.11, and Python 3.7 (end of life since 2023) has no arm64 builds for Linux or macOS. Free-threaded (``t``) and PyPy interpreters are not built.

A wheel contains one extension module, ``packingsolver3d._core``, with the upstream solvers statically linked in. It has no runtime dependency outside the standard library.

Other architectures
-------------------

i686, ppc64le, s390x, armv7l, riscv64 and loongarch64 are not built as wheels; ``pip`` falls back to the sdist there. A source build needs CMake 3.28 or newer, a C++17 compiler (GCC 10+, Clang, or MSVC 2022) and network access, because upstream fetches Boost, HiGHS and its solver libraries through CMake ``FetchContent`` at configure time. Expect ten to twenty minutes on a workstation:

.. code-block:: bash

   pip install packingsolver3d --no-binary packingsolver3d

Verify
------

.. code-block:: python

   >>> import packingsolver3d
   >>> from packingsolver3d import BinType, Instance, ItemType, Objective, box
   >>> instance = Instance(bin_types=[BinType(x=10, y=10, z=10)],
   ...                     item_types=[ItemType(x=5, y=5, z=5, copies=8)],
   ...                     objective=Objective.BIN_PACKING)
   >>> box.solve(instance, time_limit=1.0).status
   <Status.OPTIMAL: 'optimal'>

If the import fails with ``packingsolver3d._core is not built for this interpreter``, the installed package has no extension for your interpreter -- typically a source install whose build step was skipped. Reinstall, or build in a checkout with ``make build``.

Development install
-------------------

.. code-block:: bash

   git clone --recursive https://github.com/HansBug/packingsolver3d.git
   cd packingsolver3d
   pip install -r requirements-build.txt -r requirements-test.txt -r requirements-cov.txt
   make build      # CMake configure + build of upstream and the bridge, module placed in the package
   make unittest   # pytest, docstring examples, coverage

The CMake tree in ``build/cmake`` is reused across interpreters: switching Python only rebuilds the bridge.
