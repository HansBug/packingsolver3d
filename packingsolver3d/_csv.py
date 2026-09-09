"""
Overview:
    CSV codec between :mod:`packingsolver3d.model` and the native executables.

    PackingSolver's own file format is the interface we target, so this module
    is the whole serialisation layer.  Two properties of the upstream readers
    shape the code here.

    First, they are if/else chains keyed on the header labels with no trailing
    error branch, so an unknown column is dropped without a word.  That lets us
    emit one superset header for both solvers, and it is also why
    :func:`packingsolver3d.box.solve` validates instead of trusting the reader
    to complain.

    Second, an absent column means "use the built-in default", but an empty
    *cell* means ``std::stod("")`` and a crash.  Because a header is shared by
    every row, a column is emitted only when at least one object sets it, and
    the objects that do not get the upstream default written out explicitly.
"""

import csv
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .errors import InvalidInstanceError
from .model import ALL_ROTATIONS, BinType, Defect, Instance, ItemType, Rotation
from .result import PackedBin, Placement, Stack

__all__ = [
    'write_instance',
    'parse_certificate',
]

#: Upstream default for ``MAXIMUM_STACKABILITY``.
#:
#: ``ItemPos`` is ``int32_t`` while the CSV reader parses with ``std::stol``
#: and narrows the result, so a 64-bit sentinel wraps to a negative number and
#: the instance silently becomes unsatisfiable.  This must stay 32-bit.
_MAX_STACKABILITY = 2 ** 31 - 1

#: Upstream default for weight-like columns, accepted by ``std::stod``.
_UNLIMITED = 'inf'

#: ``-1`` tells the upstream reader to derive the value itself: an item profit
#: becomes ``x * y * z`` and a bin cost becomes ``x * y``.
_AUTO = '-1'


def _item_columns(item_types: Sequence[ItemType]) -> List[Tuple[str, Any]]:
    """
    Decide which item columns to emit and how to fill unset cells.

    :param item_types: The item types about to be written.
    :return: ``(label, default)`` pairs for every column that must appear.
    """
    columns = [
        ('X', None),
        ('Y', None),
        ('Z', None),
        ('PROFIT', _AUTO),
        ('WEIGHT', 0),
        ('COPIES', 1),
        ('COPIES_MIN', _AUTO),
    ]
    if any(t.rotations is not None for t in item_types):
        for rotation in ALL_ROTATIONS:
            columns.append(('ROTATION_' + rotation.value, 0))
    optional = [
        ('GROUP_ID', 'group_id', 0),
        ('STACKABILITY_ID', 'stackability_id', 0),
        ('NESTING_HEIGHT', 'nesting_height', 0),
        ('MAXIMUM_STACKABILITY', 'maximum_stackability', _MAX_STACKABILITY),
        ('MAXIMUM_WEIGHT_ABOVE', 'maximum_weight_above', _UNLIMITED),
    ]
    for label, attribute, default in optional:
        if any(getattr(t, attribute) is not None for t in item_types):
            columns.append((label, default))
    return columns


def _item_row(item_type: ItemType, columns: Sequence[Tuple[str, Any]]) -> List[Any]:
    """
    Render one item type against a fixed column layout.

    :param item_type: The item type to render.
    :param columns: Column layout from :func:`_item_columns`.
    :return: The cell values, in column order.
    """
    rotations = frozenset(item_type.rotations or ())
    values = {
        'X': item_type.x,
        'Y': item_type.y,
        'Z': item_type.z,
        'PROFIT': item_type.profit,
        'WEIGHT': item_type.weight,
        'COPIES': item_type.copies,
        'COPIES_MIN': item_type.copies_min,
        'GROUP_ID': item_type.group_id,
        'STACKABILITY_ID': item_type.stackability_id,
        'NESTING_HEIGHT': item_type.nesting_height,
        'MAXIMUM_STACKABILITY': item_type.maximum_stackability,
        'MAXIMUM_WEIGHT_ABOVE': item_type.maximum_weight_above,
    }
    for rotation in ALL_ROTATIONS:
        values['ROTATION_' + rotation.value] = 1 if rotation in rotations else 0

    row = []
    for label, default in columns:
        value = values.get(label)
        row.append(default if value is None else value)
    return row


def _bin_columns(bin_types: Sequence[BinType]) -> List[Tuple[str, Any]]:
    """
    Decide which bin columns to emit and how to fill unset cells.

    :param bin_types: The bin types about to be written.
    :return: ``(label, default)`` pairs for every column that must appear.
    """
    columns = [
        ('X', None),
        ('Y', None),
        ('Z', None),
        ('COST', _AUTO),
        ('COPIES', 1),
        ('COPIES_MIN', 0),
    ]
    if any(t.maximum_weight is not None for t in bin_types):
        columns.append(('MAXIMUM_WEIGHT', _UNLIMITED))
    if any(t.maximum_stack_density is not None for t in bin_types):
        columns.append(('MAXIMUM_STACK_DENSITY', _UNLIMITED))
    return columns


def _bin_row(bin_type: BinType, columns: Sequence[Tuple[str, Any]]) -> List[Any]:
    """
    Render one bin type against a fixed column layout.

    :param bin_type: The bin type to render.
    :param columns: Column layout from :func:`_bin_columns`.
    :return: The cell values, in column order.
    """
    values = {
        'X': bin_type.x,
        'Y': bin_type.y,
        'Z': bin_type.z,
        'COST': bin_type.cost,
        'COPIES': bin_type.copies,
        'COPIES_MIN': bin_type.copies_min,
        'MAXIMUM_WEIGHT': bin_type.maximum_weight,
        'MAXIMUM_STACK_DENSITY': bin_type.maximum_stack_density,
    }
    row = []
    for label, default in columns:
        value = values.get(label)
        row.append(default if value is None else value)
    return row


def _validate(instance: Instance) -> None:
    """
    Reject instances the native readers would reject or misread.

    Upstream throws a ``std::runtime_error`` for these, which reaches us as an
    opaque non-zero exit; failing here keeps the error message useful.

    :param instance: The instance to check.
    :raise InvalidInstanceError: When the instance is empty or carries a
        non-positive dimension, a negative count or an out-of-range defect.
    """
    if not instance.bin_types:
        raise InvalidInstanceError('instance has no bin types')
    if not instance.item_types:
        raise InvalidInstanceError('instance has no item types')

    for kind, types in (('bin', instance.bin_types), ('item', instance.item_types)):
        for index, type_ in enumerate(types):
            for axis in ('x', 'y', 'z'):
                if getattr(type_, axis) <= 0:
                    raise InvalidInstanceError(
                        '{kind} type #{index} has non-positive {axis}: {value!r}'.format(
                            kind=kind, index=index, axis=axis, value=getattr(type_, axis),
                        )
                    )
            if type_.copies <= 0:
                raise InvalidInstanceError(
                    '{kind} type #{index} has non-positive copies: {value!r}'.format(
                        kind=kind, index=index, value=type_.copies,
                    )
                )
            if type_.copies_min is not None and not 0 <= type_.copies_min <= type_.copies:
                raise InvalidInstanceError(
                    '{kind} type #{index} has copies_min outside [0, {copies}]: '
                    '{value!r}'.format(
                        kind=kind, index=index, copies=type_.copies,
                        value=type_.copies_min,
                    )
                )

    for index, defect in enumerate(instance.defects):
        if not 0 <= defect.bin_type_id < len(instance.bin_types):
            raise InvalidInstanceError(
                'defect #{index} refers to unknown bin type {bin_type_id!r}'.format(
                    index=index, bin_type_id=defect.bin_type_id,
                )
            )
        if defect.lx <= 0 or defect.ly <= 0:
            raise InvalidInstanceError(
                'defect #{index} has a non-positive extent'.format(index=index)
            )


def _write_rows(path: str, header: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    """
    Write one CSV file with LF line endings.

    ``newline=''`` matters on Windows: the default would turn the writer's
    ``\\r\\n`` into ``\\r\\r\\n``, and upstream's ``optimizationtools::split``
    would then leave a stray ``\\r`` in the last column of every row.

    :param path: Destination file path.
    :param header: Column labels.
    :param rows: Row values, already in column order.
    """
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(list(header))
        for row in rows:
            writer.writerow(list(row))


def write_instance(instance: Instance, directory: str) -> Dict[str, str]:
    """
    Encode an instance as the CSV file set the executables read.

    :param instance: The instance to encode.
    :param directory: An existing directory to write into.
    :return: A mapping from command line option name (``items``, ``bins``,
        ``defects``, ``parameters``) to the path written.  Keys are absent when
        the instance needs no such file.
    :raise InvalidInstanceError: When the instance is structurally invalid.

    Example::

        >>> import tempfile
        >>> from packingsolver3d import BinType, Instance, ItemType, Objective
        >>> from packingsolver3d._csv import write_instance
        >>> instance = Instance(
        ...     bin_types=[BinType(x=10, y=10, z=10)],
        ...     item_types=[ItemType(x=2, y=2, z=2, copies=3)],
        ...     objective=Objective.BIN_PACKING,
        ... )
        >>> with tempfile.TemporaryDirectory() as d:
        ...     paths = write_instance(instance, d)
        ...     sorted(paths)
        ...     open(paths['items']).readline().strip()
        ['bins', 'items', 'parameters']
        'X,Y,Z,PROFIT,WEIGHT,COPIES,COPIES_MIN'
    """
    _validate(instance)

    item_columns = _item_columns(instance.item_types)
    bin_columns = _bin_columns(instance.bin_types)

    paths = {
        'items': os.path.join(directory, 'items.csv'),
        'bins': os.path.join(directory, 'bins.csv'),
    }
    _write_rows(
        paths['items'],
        [label for label, _ in item_columns],
        [_item_row(t, item_columns) for t in instance.item_types],
    )
    _write_rows(
        paths['bins'],
        [label for label, _ in bin_columns],
        [_bin_row(t, bin_columns) for t in instance.bin_types],
    )

    if instance.defects:
        paths['defects'] = os.path.join(directory, 'defects.csv')
        _write_rows(
            paths['defects'],
            ['BIN', 'X', 'Y', 'LX', 'LY'],
            [[d.bin_type_id, d.x, d.y, d.lx, d.ly] for d in instance.defects],
        )

    parameters = [['objective', instance.objective.value]]
    if instance.unloading_constraint is not None:
        parameters.append(['unloading-constraint', instance.unloading_constraint.value])
    paths['parameters'] = os.path.join(directory, 'parameters.csv')
    _write_rows(paths['parameters'], ['NAME', 'VALUE'], parameters)

    return paths


def _cell_int(row: Dict[str, str], label: str) -> Optional[int]:
    """
    Read one integer cell, tolerating an absent column or an empty value.

    Certificate rows carry a fixed header but leave inapplicable cells blank --
    a ``BIN`` row has no rotation, a ``STACK`` row has no group.

    :param row: The parsed row.
    :param label: Column label.
    :return: The integer, or ``None`` when the cell is missing or empty.
    """
    value = (row.get(label) or '').strip()
    if not value:
        return None
    return int(value)


def parse_certificate(path: str) -> Tuple[PackedBin, ...]:
    """
    Parse a solution certificate into :class:`~packingsolver3d.result.PackedBin` objects.

    Both solvers write a ``TYPE``-tagged row per object, and the tags are the
    same (``BIN``, ``DEFECT``, ``STACK``, ``ITEM``) even though ``boxstacks``
    adds a ``STACK`` and a ``GROUP_ID`` column.  Dispatching on ``TYPE`` and
    looking columns up by label therefore handles both formats.

    :param path: Path to the certificate CSV.  A missing or header-only file
        means the solver found nothing.
    :return: The used bins, in the order the solver reported them.
    """
    if not os.path.isfile(path):
        return ()

    bins = []
    by_id = {}
    with open(path, 'r', newline='') as f:
        for row in csv.DictReader(f):
            kind = (row.get('TYPE') or '').strip()
            bin_id = _cell_int(row, 'BIN')
            if bin_id is None:
                continue

            if kind == 'BIN':
                packed = {
                    'bin_id': bin_id,
                    'bin_type_id': _cell_int(row, 'ID') or 0,
                    'copies': _cell_int(row, 'COPIES') or 1,
                    'x': _cell_int(row, 'LX') or 0,
                    'y': _cell_int(row, 'LY') or 0,
                    'z': _cell_int(row, 'LZ') or 0,
                    'placements': [],
                    'stacks': [],
                }
                by_id[bin_id] = packed
                bins.append(packed)
            elif kind == 'STACK' and bin_id in by_id:
                by_id[bin_id]['stacks'].append(Stack(
                    stack_id=_cell_int(row, 'ID') or 0,
                    bin_id=bin_id,
                    x=_cell_int(row, 'X') or 0,
                    y=_cell_int(row, 'Y') or 0,
                    lx=_cell_int(row, 'LX') or 0,
                    ly=_cell_int(row, 'LY') or 0,
                    lz=_cell_int(row, 'LZ') or 0,
                ))
            elif kind == 'ITEM' and bin_id in by_id:
                rotation = (row.get('ROTATION') or '').strip()
                by_id[bin_id]['placements'].append(Placement(
                    item_type_id=_cell_int(row, 'ID') or 0,
                    bin_id=bin_id,
                    x=_cell_int(row, 'X') or 0,
                    y=_cell_int(row, 'Y') or 0,
                    z=_cell_int(row, 'Z') or 0,
                    lx=_cell_int(row, 'LX') or 0,
                    ly=_cell_int(row, 'LY') or 0,
                    lz=_cell_int(row, 'LZ') or 0,
                    rotation=Rotation(rotation) if rotation else None,
                    stack_id=_cell_int(row, 'STACK'),
                    group_id=_cell_int(row, 'GROUP_ID'),
                ))

    return tuple(
        PackedBin(
            bin_id=packed['bin_id'],
            bin_type_id=packed['bin_type_id'],
            copies=packed['copies'],
            x=packed['x'],
            y=packed['y'],
            z=packed['z'],
            placements=tuple(packed['placements']),
            stacks=tuple(packed['stacks']),
        )
        for packed in bins
    )
