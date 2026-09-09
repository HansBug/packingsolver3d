可视化一个装箱结果
==================

当你想"看"结果而不是读数字时用本页。:mod:`packingsolver3d.visual` 以上游 ``scripts/visualize_box.py`` 同样的画法绘制 :class:`~packingsolver3d.result.Result`——半透明的箱体、每件物品一个带类型 id 的不透明长方体、每箱一个 3D 场景——返回一个可在浏览器或 notebook 里旋转的 `plotly <https://plotly.com/python/>`_ 图。

安装可选依赖
------------

.. code-block:: bash

   pip install "packingsolver3d[plot]"      # 或：pip install plotly

包里其它部分都不需要 plotly；缺少它时导入 :mod:`packingsolver3d.visual` 会抛出带此提示的 ``ImportError``。

绘制结果
--------

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, box
   from packingsolver3d.visual import plot_result

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
       item_types=[ItemType(x=20, y=30, z=40, copies=6), ItemType(x=15, y=15, z=15, copies=4)],
       objective=Objective.BIN_PACKING,
   )
   result = box.solve(instance, time_limit=2.0)

   figure = plot_result(result)          # 每种物品一种颜色，箱子上写着类型 id
   figure.show()                          # 打开浏览器标签页，或在 notebook 里内嵌渲染
   figure.write_html('packing.html')      # 自包含的交互式文件

.. raw:: html
   :file: ../../_static/figures/box_bin_packing.html

.. only:: latex

   .. image:: ../../_static/figures/box_bin_packing.png
      :width: 90%

按堆上色
--------

对 ``boxstacks`` 结果，``color_by='stack'`` 让每个堆有自己的颜色，堆的结构一目了然；``color_by='same'`` 全部用一种颜色，物品成百上千时可用 ``show_ids=False`` 去掉标注。

.. code-block:: python

   from packingsolver3d import boxstacks
   from packingsolver3d.visual import plot_result

   figure = plot_result(boxstacks.solve(instance, time_limit=2.0), color_by='stack')

.. raw:: html
   :file: ../../_static/figures/boxstacks_stacks.html

.. only:: latex

   .. image:: ../../_static/figures/boxstacks_stacks.png
      :width: 90%

多个箱
------

每个箱一个场景，按 ``ceil(sqrt(箱数))`` 列排成网格，也可用 ``columns`` 指定列数。:func:`~packingsolver3d.visual.plot_bin` 只画一个 :class:`~packingsolver3d.result.PackedBin`。

.. raw:: html
   :file: ../../_static/figures/box_multi_bin.html

.. only:: latex

   .. image:: ../../_static/figures/box_multi_bin.png
      :width: 90%

导出 PNG
--------

静态图走 plotly 的 ``write_image``，需要 `kaleido <https://github.com/plotly/Kaleido>`_\ （1.0 及以上）和本机的 Chrome/Chromium：

.. code-block:: bash

   pip install "kaleido>=1"

.. code-block:: python

   figure.write_image('packing.png', width=900, height=650, scale=2)

本文档中的配图正是仓库里的 ``tools/make_figures.py`` 用这种方式生成的。
