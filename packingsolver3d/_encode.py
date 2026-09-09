"""
Overview:
    Turn an :class:`~packingsolver3d.model.Instance` into the plain values the
    native module consumes.

    The native side calls upstream's ``InstanceBuilder`` setters for exactly
    the keys present in the payload, so ``None`` fields are simply omitted and
    upstream's own defaults apply -- the same defaults its CSV readers use
    when a column is absent.
"""

from typing import Any, Dict, Optional

from .errors import InvalidInstanceError
from .model import BinType, Instance, ItemType, UnloadingConstraint

__all__ = ['instance_payload']

_ITEM_OPTIONAL = (
    'profit', 'weight', 'copies', 'copies_min',
    'group_id', 'stackability_id', 'nesting_height', 'maximum_stackability', 'maximum_weight_above',
)
_BIN_OPTIONAL = ('cost', 'copies', 'copies_min', 'maximum_weight', 'maximum_stack_density')


def _item_spec(item_type: ItemType) -> Dict[str, Any]:
    spec = {'x': item_type.x, 'y': item_type.y, 'z': item_type.z}  # type: Dict[str, Any]
    for name in _ITEM_OPTIONAL:
        value = getattr(item_type, name)
        if value is not None:
            spec[name] = value
    if item_type.rotations is not None:
        spec['rotations'] = [rotation.value for rotation in item_type.rotations]
    return spec


def _bin_spec(bin_type: BinType) -> Dict[str, Any]:
    spec = {'x': bin_type.x, 'y': bin_type.y, 'z': bin_type.z}  # type: Dict[str, Any]
    for name in _BIN_OPTIONAL:
        value = getattr(bin_type, name)
        if value is not None:
            spec[name] = value
    return spec


def _validate(instance: Instance) -> None:
    """
    Reject instances the native builders would reject or misread.

    Upstream throws ``std::invalid_argument`` for most of these, which would
    surface as a bare ``ValueError``; failing here keeps the message specific.

    :param instance: The instance to check.
    :raise InvalidInstanceError: When the instance is empty or carries a
        non-positive dimension, a non-positive count, a ``copies_min`` outside
        ``[0, copies]`` or a defect on an unknown bin type.
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
                'defect #{index} has a non-positive extent: {lx!r} x {ly!r}'.format(
                    index=index, lx=defect.lx, ly=defect.ly,
                )
            )


def instance_payload(
        instance: Instance,
        unloading_constraint: Optional[UnloadingConstraint] = None,
) -> Dict[str, Any]:
    """
    Validate an instance and render it as plain values.

    :param instance: The instance to encode.
    :param unloading_constraint: Overrides the instance's own setting when
        given.
    :return: A mapping with ``objective``, ``bins``, ``items``, ``defects`` and
        ``unloading_constraint``; every optional field that is ``None`` is left
        out so upstream's default applies.
    :raise InvalidInstanceError: When the instance is structurally invalid.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType
        >>> from packingsolver3d._encode import instance_payload
        >>> payload = instance_payload(Instance(
        ...     bin_types=[BinType(x=10, y=10, z=10, cost=3)],
        ...     item_types=[ItemType(x=1, y=2, z=3, copies=4)],
        ... ))
        >>> payload['objective'], payload['bins'][0]['cost'], payload['items'][0]['copies']
        ('default', 3, 4)
        >>> 'profit' in payload['items'][0]
        False
    """
    _validate(instance)
    if unloading_constraint is None:
        unloading_constraint = instance.unloading_constraint
    return {
        'objective': instance.objective.value,
        'bins': [_bin_spec(bin_type) for bin_type in instance.bin_types],
        'items': [_item_spec(item_type) for item_type in instance.item_types],
        'defects': [
            {'bin_type_id': d.bin_type_id, 'x': d.x, 'y': d.y, 'lx': d.lx, 'ly': d.ly}
            for d in instance.defects
        ],
        'unloading_constraint': None if unloading_constraint is None else unloading_constraint.value,
    }
