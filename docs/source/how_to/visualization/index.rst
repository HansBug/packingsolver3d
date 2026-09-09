Visualise a packing
===================

Use this page when you want to look at a result rather than read its numbers. :mod:`packingsolver3d.visual` draws a :class:`~packingsolver3d.result.Result` the way upstream's own ``scripts/visualize_box.py`` does -- a translucent bin, one opaque cuboid per item with its type id, one 3D scene per bin -- and returns a `plotly <https://plotly.com/python/>`_ figure you can rotate in a browser or notebook.

Install the optional dependency
-------------------------------

.. code-block:: bash

   pip install "packingsolver3d[plot]"      # or: pip install plotly

Nothing else in the package needs plotly; importing :mod:`packingsolver3d.visual` without it raises ``ImportError`` with this hint.

Draw a result
-------------

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, box
   from packingsolver3d.visual import plot_result

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
       item_types=[ItemType(x=20, y=30, z=40, copies=6), ItemType(x=15, y=15, z=15, copies=4)],
       objective=Objective.BIN_PACKING,
   )
   result = box.solve(instance, time_limit=2.0)

   figure = plot_result(result)          # one colour per item type, ids written on the boxes
   figure.show()                          # opens a browser tab, or renders inline in a notebook
   figure.write_html('packing.html')      # self-contained interactive file

.. raw:: html
   :file: ../../_static/figures/box_bin_packing.html

.. only:: latex

   .. image:: ../../_static/figures/box_bin_packing.png
      :width: 90%

Colour by stack
---------------

For ``boxstacks`` results, ``color_by='stack'`` gives every stack its own colour so the piles stand out; ``color_by='same'`` draws everything in one colour and ``show_ids=False`` drops the labels when there are hundreds of items.

.. code-block:: python

   from packingsolver3d import boxstacks
   from packingsolver3d.visual import plot_result

   figure = plot_result(boxstacks.solve(instance, time_limit=2.0), color_by='stack')

.. raw:: html
   :file: ../../_static/figures/boxstacks_stacks.html

.. only:: latex

   .. image:: ../../_static/figures/boxstacks_stacks.png
      :width: 90%

Several bins
------------

Every bin gets its own scene; the scenes are laid out in a grid of ``ceil(sqrt(bins))`` columns, or as many as ``columns`` asks for. :func:`~packingsolver3d.visual.plot_bin` draws a single :class:`~packingsolver3d.result.PackedBin`.

.. raw:: html
   :file: ../../_static/figures/box_multi_bin.html

.. only:: latex

   .. image:: ../../_static/figures/box_multi_bin.png
      :width: 90%

Export to PNG
-------------

Static images go through plotly's ``write_image``, which needs `kaleido <https://github.com/plotly/Kaleido>`_ (version 1 or newer) and a Chrome or Chromium binary on the machine:

.. code-block:: bash

   pip install "kaleido>=1"

.. code-block:: python

   figure.write_image('packing.png', width=900, height=650, scale=2)

The figures on these pages were produced exactly this way by ``tools/make_figures.py`` in the repository.
