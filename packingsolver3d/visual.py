"""
Overview:
    Interactive three-dimensional views of a :class:`~packingsolver3d.result.Result`.

    The drawing follows upstream's own ``scripts/visualize_box.py`` and
    ``scripts/visualize_boxstacks.py``: every bin is a translucent grey box,
    every placement an opaque cuboid with a black outline and its item type id
    at the centre, one 3D scene per bin arranged in a grid.  Figures are plotly
    objects, so they can be shown in a notebook or browser, saved as HTML with
    :meth:`plotly.graph_objects.Figure.write_html`, or exported to PNG with
    :meth:`plotly.graph_objects.Figure.write_image` (needs ``kaleido``).

    plotly is an optional dependency (``pip install packingsolver3d[plot]``);
    importing this module without it raises :class:`ImportError` with that hint.

Example::

    >>> from packingsolver3d import BinType, Instance, ItemType, Objective, box
    >>> from packingsolver3d.visual import plot_result
    >>> instance = Instance(
    ...     bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
    ...     item_types=[ItemType(x=20, y=30, z=40, copies=6), ItemType(x=15, y=15, z=15, copies=4)],
    ...     objective=Objective.BIN_PACKING,
    ... )
    >>> figure = plot_result(box.solve(instance, time_limit=2.0))
    >>> type(figure).__name__
    'Figure'
    >>> sum(1 for trace in figure.data if trace.type == 'mesh3d')  # 1 bin + 10 items
    11
"""

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .result import PackedBin, Placement, Result

try:
    import plotly.graph_objects as go
    import plotly.subplots
    from plotly.colors import qualitative as _palettes
except ImportError as err:  # pragma: no cover - exercised only without the optional dependency
    raise ImportError(
        'packingsolver3d.visual needs plotly ({err}); install it with '
        '"pip install plotly" or "pip install packingsolver3d[plot]"'.format(err=err)
    )

__all__ = ['plot_result', 'plot_bin', 'COLOR_KEYS']

#: Accepted values of ``color_by``: one colour per item type (upstream's
#: default), one per stack (``boxstacks`` results), or a single colour.
COLOR_KEYS = ('item_type', 'stack', 'same')

#: Upstream's palette (``plotly.express.colors.qualitative.Pastel``).
_PALETTE = _palettes.Pastel

#: How much every item is shrunk on each side so neighbouring faces do not
#: z-fight; upstream uses the same value.
_EPSILON = 0.1

# Triangle indices of a cuboid whose eight corners are listed as
# (x1,y1,z1) (x2,y1,z1) (x1,y2,z1) (x2,y2,z1) (x1,y1,z2) (x2,y1,z2) (x1,y2,z2) (x2,y2,z2);
# copied from upstream's item mesh.
_ITEM_I = (0, 3, 4, 7, 0, 5, 2, 7, 0, 6, 1, 7)
_ITEM_J = (1, 1, 5, 5, 1, 1, 3, 3, 2, 2, 3, 3)
_ITEM_K = (2, 2, 6, 6, 4, 4, 6, 6, 4, 4, 5, 5)


def _cuboid(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> Dict[str, Any]:
    """
    Mesh coordinates of an axis-aligned cuboid.

    :return: ``x``, ``y``, ``z``, ``i``, ``j``, ``k`` keyword arguments for
        :class:`plotly.graph_objects.Mesh3d`.
    """
    return dict(
        x=[x1, x2, x1, x2, x1, x2, x1, x2],
        y=[y1, y1, y2, y2, y1, y1, y2, y2],
        z=[z1, z1, z1, z1, z2, z2, z2, z2],
        i=list(_ITEM_I), j=list(_ITEM_J), k=list(_ITEM_K),
    )


def _outline(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> Tuple[list, list, list]:
    """
    The twelve edges of a cuboid as one ``None``-separated polyline, upstream's shape.
    """
    xs = [x1, x1, x2, x2, x2, x2, x1, x1, x1, None, x1, x1, x2, x2, x2, x2, x1, x1, x1, None]
    ys = [y1, y1, y1, y1, y2, y2, y2, y2, y1, None, y1, y1, y1, y1, y2, y2, y2, y2, y1, None]
    zs = [z1, z2, z2, z1, z1, z2, z2, z1, z1, None, z2, z1, z1, z2, z2, z1, z1, z2, z2, None]
    return xs, ys, zs


def _color_index(placement: Placement, color_by: str) -> Optional[int]:
    if color_by == 'item_type':
        return placement.item_type_id
    if color_by == 'stack':
        return placement.stack_id if placement.stack_id is not None else placement.item_type_id
    return None


def _bin_traces(packed: PackedBin, color_by: str, show_ids: bool, first: bool) -> List[Any]:
    """
    Traces for one bin: the bin shell, one mesh per placement, outlines, labels.
    """
    traces = [go.Mesh3d(
        name='Bins', legendgroup='bins', showlegend=first,
        opacity=0.1, color='grey', flatshading=True,
        **_cuboid(0, 0, 0, packed.x, packed.y, packed.z)
    )]
    borders = ([], [], [])  # type: Tuple[list, list, list]
    labels = ([], [], [], [])  # type: Tuple[list, list, list, list]
    seen = set()  # type: set
    for placement in packed.placements:
        x1, y1, z1 = placement.x, placement.y, placement.z
        x2, y2, z2 = x1 + placement.lx, y1 + placement.ly, z1 + placement.lz
        index = _color_index(placement, color_by)
        color = 'cornflowerblue' if index is None else _PALETTE[index % len(_PALETTE)]
        if color_by == 'item_type':
            name = 'Item type {index}'.format(index=index)
        elif color_by == 'stack':
            name = 'Stack {index}'.format(index=index)
        else:
            name = 'Items'
        traces.append(go.Mesh3d(
            name=name, legendgroup='items', showlegend=first and name not in seen,
            opacity=1, color=color, flatshading=True,
            **_cuboid(x1 + _EPSILON, y1 + _EPSILON, z1 + _EPSILON, x2 - _EPSILON, y2 - _EPSILON, z2 - _EPSILON)
        ))
        seen.add(name)
        xs, ys, zs = _outline(x1, y1, z1, x2, y2, z2)
        borders[0].extend(xs)
        borders[1].extend(ys)
        borders[2].extend(zs)
        labels[0].append((x1 + x2) / 2)
        labels[1].append((y1 + y2) / 2)
        labels[2].append((z1 + z2) / 2)
        labels[3].append(str(placement.item_type_id))
    traces.append(go.Scatter3d(
        x=borders[0], y=borders[1], z=borders[2], name='Item borders', legendgroup='items',
        showlegend=False, mode='lines', line=dict(color='black', width=1),
    ))
    if show_ids and labels[3]:
        traces.append(go.Scatter3d(
            x=labels[0], y=labels[1], z=labels[2], name='Item ids', legendgroup='items',
            showlegend=False, mode='text', text=labels[3], textfont=dict(size=8), textposition='middle center',
        ))
    return traces


def _bin_title(packed: PackedBin) -> str:
    """
    Scene title of a bin; upstream reports identical bins as copies of one bin.
    """
    title = 'Bin {bin_id} (type {bin_type_id})'.format(bin_id=packed.bin_id, bin_type_id=packed.bin_type_id)
    if packed.copies > 1:
        title += ' x{copies}'.format(copies=packed.copies)
    return title


def plot_bin(packed: PackedBin, color_by: str = 'item_type', show_ids: bool = True) -> 'go.Figure':
    """
    Draw one packed bin.

    :param packed: The bin to draw.
    :param color_by: One of :data:`COLOR_KEYS`.
    :param show_ids: Write each item type id at the centre of its box.
    :return: A plotly figure with a single 3D scene.
    :raise ValueError: When ``color_by`` is not one of :data:`COLOR_KEYS`.

    Example::

        >>> from packingsolver3d import PackedBin, Placement, Rotation
        >>> from packingsolver3d.visual import plot_bin
        >>> packed = PackedBin(bin_id=0, bin_type_id=0, copies=1, x=10, y=10, z=10, placements=(
        ...     Placement(item_type_id=0, bin_id=0, x=0, y=0, z=0, lx=5, ly=5, lz=5, rotation=Rotation.XYZ),
        ... ))
        >>> [trace.type for trace in plot_bin(packed).data]
        ['mesh3d', 'mesh3d', 'scatter3d', 'scatter3d']
    """
    return plot_result((packed,), color_by=color_by, show_ids=show_ids)


def plot_result(result, color_by: str = 'item_type', show_ids: bool = True,
                columns: Optional[int] = None, title: Optional[str] = None) -> 'go.Figure':
    """
    Draw every bin of a result, one 3D scene per bin.

    :param result: A :class:`~packingsolver3d.result.Result`, or any sequence
        of :class:`~packingsolver3d.result.PackedBin`.
    :param color_by: One of :data:`COLOR_KEYS`: ``'item_type'`` (upstream's
        default), ``'stack'`` for ``boxstacks`` results, or ``'same'``.
    :param show_ids: Write each item type id at the centre of its box.
    :param columns: Scenes per row; defaults to ``ceil(sqrt(bins))`` like
        upstream.  Identical bins that upstream reports as copies of one bin
        are drawn once, and the scene title carries the count.
    :param title: Figure title.
    :return: The plotly figure.
    :raise ValueError: When ``color_by`` is not one of :data:`COLOR_KEYS`, or
        there is nothing to draw.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective, boxstacks
        >>> from packingsolver3d.visual import plot_result
        >>> instance = Instance(
        ...     bin_types=[BinType(x=100, y=100, z=100, maximum_weight=1000)],
        ...     item_types=[ItemType(x=20, y=30, z=40, copies=6, weight=5, stackability_id=0,
        ...                          maximum_stackability=3, maximum_weight_above=100)],
        ...     objective=Objective.BIN_PACKING,
        ... )
        >>> figure = plot_result(boxstacks.solve(instance, time_limit=2.0), color_by='stack')
        >>> len(figure.layout.annotations) if figure.layout.annotations else 0  # one subplot title per bin
        1
    """
    if color_by not in COLOR_KEYS:
        raise ValueError('color_by must be one of {keys!r}, got {value!r}'.format(keys=COLOR_KEYS, value=color_by))
    bins = tuple(result.bins) if isinstance(result, Result) else tuple(result)
    if not bins:
        raise ValueError('nothing to draw: the result has no bins')

    number_of_columns = columns or int(math.ceil(math.sqrt(len(bins))))
    number_of_rows = int(math.ceil(len(bins) / number_of_columns))
    figure = plotly.subplots.make_subplots(
        rows=number_of_rows, cols=number_of_columns,
        specs=[[{'type': 'scene'} for _ in range(number_of_columns)] for _ in range(number_of_rows)],
        subplot_titles=[_bin_title(b) for b in bins],
        horizontal_spacing=0.02, vertical_spacing=0.05,
    )
    for position, packed in enumerate(bins):
        row, col = position // number_of_columns + 1, position % number_of_columns + 1
        for trace in _bin_traces(packed, color_by, show_ids, first=(position == 0)):
            figure.add_trace(trace, row=row, col=col)
        scene = 'scene' if position == 0 else 'scene{n}'.format(n=position + 1)
        figure.layout[scene].update(
            aspectmode='data',
            xaxis=dict(range=[0, packed.x], title='x'),
            yaxis=dict(range=[0, packed.y], title='y'),
            zaxis=dict(range=[0, packed.z], title='z'),
        )
    figure.update_layout(title=dict(text=title, y=0.98) if title else None,
                         margin=dict(l=0, r=0, t=80 if title else 40, b=0),
                         legend=dict(itemsizing='constant'))
    return figure
