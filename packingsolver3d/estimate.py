"""Recommend a time budget for a solve from the instance alone.

PackingSolver's anytime modes run until their time limit (see
:doc:`/explanations/upstream_behaviours/index`), so the caller has to pick the
limit.  This module turns an :class:`~packingsolver3d.Instance` into a
:class:`TimeBudget` -- a ``time_limit`` plus matching ``stop_when_unimproved_*``
knobs -- with a model fitted on 3158 recorded improvement curves (upstream's
benchmark families, a ROADEF 2022 sample, synthetic container loads; see
``experiments/time_budget/`` for the campaign and the fit).

The model follows the algorithms rather than the data alone:

* upstream chooses one algorithm *path* from the instance shape
  (:func:`algorithm_path` replicates that choice);
* every path first pays a **latency** :math:`L` -- the cost of one full pass
  (block generation and a first beam pass for ``TSMS``, the first
  sequential-onedimensional-rectangle pass for ``SOR``, the first iteration over
  all bins for ``SSK`` / ``SVC``).  :math:`L` is a power law in the instance size
  (items for ``box``, stacks for ``boxstacks``) and the number of item types, with
  a constant block-generation step for ``TSMS`` and an *overfull* step for ``SOR``;
* *growth* paths (``TSMS``, ``TS``, ``SOR``) then double their queue between passes,
  so the time worth waiting after the first solution is a multiple
  :math:`m(\\alpha)` of :math:`L`; single-pass paths (``SSK``, ``SVC``) are essentially
  done after their first complete solution and end by themselves.

.. math::

    T(\\alpha) = L \\,(1 + m(\\alpha)) + c(\\alpha)

``alpha`` is the quality-versus-waiting dial of an F-beta style score: the
per-instance optimum of :math:`F_\\alpha = (1+\\alpha^2) S q / (\\alpha^2 S + q)` with
:math:`q` the relative quality and :math:`S = 1/(1 + t/60\\,\\mathrm{s})` the speed
score.  ``alpha=4`` is balanced and the ``box`` default, ``alpha=8`` leans towards quality
and is the ``boxstacks`` default (:data:`DEFAULT_ALPHA`).  Latencies are fitted at the 90 % (growth paths) or 98 % (single-pass paths)
coverage quantile, so the recommendation is a loose upper bound: with the
stall-stop knobs most solves end earlier.  Those knobs make the patience
*relative*: the run stops once it has been silent for ``alpha / 2`` times (1 to
4) the time of its last improvement, because the growth paths double their
queues between passes and a fixed patience would cut every late pass short;
on the recorded curves this ends a typical solve at a quarter to a half of the
time limit instead of just above half.

Prototype::

    >>> from packingsolver3d import BinType, Instance, ItemType, Objective, Rotation, recommend_time_budget, box
    >>> cargo = [(530, 290, 370, 300, 8), (530, 230, 290, 300, 6), (430, 210, 270, 400, 4),
    ...          (1200, 800, 1200, 24, 450), (1200, 1000, 1150, 12, 1100)]
    >>> instance = Instance(
    ...     bin_types=[BinType(x=12032, y=2352, z=2698, copies=1, cost=1, maximum_weight=26460)],
    ...     item_types=[ItemType(x=x, y=y, z=z, copies=c, weight=w, rotations=(Rotation.XYZ, Rotation.YXZ))
    ...                 for x, y, z, c, w in cargo],
    ...     objective=Objective.KNAPSACK)
    >>> budget = recommend_time_budget(instance, solver='box')          # alpha defaults to 4 for box
    >>> budget.path, budget.alpha
    ('TSMS', 4.0)
    >>> 5 < budget.time_limit < 120 and budget.stop_when_unimproved_after < budget.time_limit
    True
    >>> budget.stop_when_unimproved_ratio, budget.stop_when_unimproved_for
    (2.0, 5.0)
    >>> result = box.solve(instance, **budget.as_options())  # doctest: +SKIP
    >>> recommend_time_budget(instance, solver='boxstacks').alpha       # and to 8 for boxstacks
    8.0

The three fields of :meth:`TimeBudget.as_options` are the whole stopping policy: the time limit is the cap and the
progress-bar scale, the stall stop is what usually ends the run.  :doc:`/explanations/time_budget/index` compares this
combination with a bare time limit and with a bare stagnation stop on every recorded curve, and lists what a calling
application should do with each field.
"""
import math
from dataclasses import dataclass
from typing import Dict, Optional

from . import _time_budget_constants as _c
from .model import Instance, Objective

__all__ = ['DEFAULT_ALPHA', 'TimeBudget', 'algorithm_path', 'count_stacks', 'instance_features', 'recommend_time_budget']

DEFAULT_ALPHA = {'box': 4.0, 'boxstacks': 8.0}
MIN_TIME_LIMIT = 1.0
MAX_TIME_LIMIT = 600.0
MIN_PATIENCE = 5.0
RATIO_BOUNDS = (1.0, 4.0)
_MANY_ITEMS_IN_BINS = 16
_MANY_ITEMS_IN_BINS_2 = 64
_MANY_COPIES_FACTOR = 1.0
_GROWTH_PATHS = ('TSMS', 'TS', 'SOR')


@dataclass(frozen=True)
class TimeBudget:
    """A recommended ``time_limit`` and the stall-stop knobs that go with it.

    :param time_limit: Seconds to pass as ``time_limit``; a loose upper bound.
    :param stop_when_unimproved_for: Floor of the patience, ``stop_when_unimproved_for``.
    :param stop_when_unimproved_after: Earliest stall stop, ``stop_when_unimproved_after`` (the covered latency).
    :param stop_when_unimproved_ratio: Relative patience, ``stop_when_unimproved_ratio``: the run stops once it has
        been silent for that many times the time of its last improvement, ``alpha / 2`` clamped to 1 ... 4.
    :param path: Upstream algorithm path the recommendation is based on.
    :param latency: Predicted time to the first solution, in seconds, at the coverage quantile the budget is built on (an
        upper estimate: 90 % of the fitted instances get their first solution sooner).
    :param typical_latency: The median prediction of the same first-solution time. Compare the *observed* first-solution
        time with this one, not with ``latency``, when calibrating ``speed``: ``speed ≈ typical_latency × speed / observed``.
    :param improvement: Predicted time worth waiting after the first solution.
    :param alpha: The quality-versus-waiting dial the budget was computed for.
    :param speed: Machine speed factor the budget was scaled by.
    """

    time_limit: float
    stop_when_unimproved_for: float
    stop_when_unimproved_after: float
    stop_when_unimproved_ratio: float
    path: str
    latency: float
    typical_latency: float
    improvement: float
    alpha: float
    speed: float

    def as_options(self) -> Dict[str, float]:
        """Keyword arguments for :func:`packingsolver3d.box.solve` / :func:`packingsolver3d.boxstacks.solve`."""
        return {
            'time_limit': self.time_limit,
            'stop_when_unimproved_for': self.stop_when_unimproved_for,
            'stop_when_unimproved_after': self.stop_when_unimproved_after,
            'stop_when_unimproved_ratio': self.stop_when_unimproved_ratio,
        }


def count_stacks(instance: Instance) -> int:
    """Lower bound on the number of stacks ``boxstacks`` has to place: copies divided by how many fit in one stack."""
    max_z = max(bin_type.z for bin_type in instance.bin_types)
    total = 0
    for item in instance.item_types:
        per_stack = max(1, max_z // item.z)
        if item.maximum_stackability:
            per_stack = min(per_stack, item.maximum_stackability)
        total += math.ceil(item.copies / per_stack)
    return total


def instance_features(instance: Instance) -> Dict[str, float]:
    """The instance quantities the model and upstream's algorithm selection look at."""
    items = instance.item_types
    bins = instance.bin_types
    n_items = sum(item.copies for item in items)
    item_volume = sum(item.copies * item.x * item.y * item.z for item in items)
    largest_bin = max(bin_type.x * bin_type.y * bin_type.z for bin_type in bins)
    return {
        'n_items': n_items,
        'n_types': len(items),
        'n_bins': sum(bin_type.copies for bin_type in bins),
        'n_stacks': count_stacks(instance),
        'mean_items_per_bin': largest_bin / (item_volume / n_items),
        'mean_copies': n_items / len(items),
        'fill_ratio': item_volume / largest_bin,
    }


def algorithm_path(instance: Instance, solver: str = 'box') -> str:
    """Which upstream algorithm the default (automatic) selection runs for this instance.

    Replicates ``box/optimize.cpp``: single-bin knapsack uses ``TSMS`` (tree search over maximal spaces) when the bin
    holds more than 64 mean items, ``TS`` (tree search) otherwise; with several bins, copy-heavy instances go to ``SSK``
    (sequential single knapsack) or ``SVC`` (sequential value correction), the others to ``SSK`` or ``TS``.  ``boxstacks``
    (``boxstacks/optimize.cpp`` at the pinned commit) runs ``SOR`` (sequential onedimensional rectangle) on one bin; on
    several bins, bin packing takes ``SSK`` when the bin holds more than 16 (copy-heavy) or 64 mean items and ``SVC``
    otherwise, while knapsack and variable-sized bin packing always take ``SVC``.
    """
    f = instance_features(instance)
    mipb = int(f['mean_items_per_bin'])
    objective = instance.objective
    if solver == 'boxstacks':
        if f['n_bins'] <= 1:
            return 'SOR'
        if objective != Objective.BIN_PACKING:
            return 'SVC'
        threshold = _MANY_ITEMS_IN_BINS if f['mean_copies'] > _MANY_COPIES_FACTOR * mipb else _MANY_ITEMS_IN_BINS_2
        return 'SSK' if mipb > threshold else 'SVC'
    if solver != 'box':
        raise ValueError(f"solver must be 'box' or 'boxstacks', got {solver!r}")
    if f['n_bins'] <= 1:
        if objective in (Objective.KNAPSACK, Objective.FEASIBILITY) and mipb > _MANY_ITEMS_IN_BINS_2:
            return 'TSMS'
        return 'TS'
    if f['mean_copies'] > _MANY_COPIES_FACTOR * mipb:
        return 'SSK' if mipb > _MANY_ITEMS_IN_BINS else 'SVC'
    return 'SSK' if mipb > _MANY_ITEMS_IN_BINS_2 else 'TS'


def _interpolate(table: Dict[float, float], alpha: float) -> float:
    """Piecewise-linear in ``log(alpha)`` between the fitted grid points, clamped outside the grid."""
    grid = sorted(table)
    if alpha <= grid[0]:
        return table[grid[0]]
    if alpha >= grid[-1]:
        return table[grid[-1]]
    for lo, hi in zip(grid, grid[1:]):
        if alpha <= hi:
            weight = (math.log(alpha) - math.log(lo)) / (math.log(hi) - math.log(lo))
            return table[lo] + weight * (table[hi] - table[lo])
    raise AssertionError('unreachable')  # pragma: no cover


def _latency(entry: dict, solver: str, path: str, f: Dict[str, float], covered: bool = True) -> float:
    """Predicted first-solution latency; ``covered=False`` drops the coverage shift and gives the median prediction."""
    size = f['n_stacks'] if solver == 'boxstacks' else f['n_items']
    beta = entry['beta']
    log_latency = beta[0] + beta[1] * math.log(size) + beta[2] * math.log(f['n_types'])
    if path == 'SOR' and f['fill_ratio'] > 1.0:
        log_latency += beta[3]
    if not covered:
        log_latency -= entry['shift']
    latency = math.exp(log_latency)
    if path == 'TSMS' and f['n_types'] >= _c.BLOCK_TYPES:
        latency += entry['block']
    return max(latency, _c.MIN_LATENCY)


def recommend_time_budget(instance: Instance, solver: str = 'box', alpha: Optional[float] = None, speed: float = 1.0) -> TimeBudget:
    """Recommend ``time_limit`` and stall-stop knobs for solving ``instance`` with ``solver``.

    :param instance: The instance about to be solved.
    :param solver: ``'box'`` or ``'boxstacks'``.
    :param alpha: Quality-versus-waiting dial; ``4`` balanced, ``8`` quality-leaning.  ``None`` picks the solver's
        default from :data:`DEFAULT_ALPHA` (``box`` 4, ``boxstacks`` 8: on the container loads of the campaign
        ``alpha=4`` left 16 % of the single-bin ``boxstacks`` solves below 99 % of the reference while ``alpha=8``
        left none).  Values between the fitted grid points (0.25 ... 8) are interpolated, values outside are clamped.
    :param speed: Speed of this machine relative to the reference machine (``2.0`` = twice as fast); every duration
        is divided by it.  Calibrate it from an earlier run as ``budget.typical_latency * budget.speed / observed
        first-solution time`` (``typical_latency``, not the covered ``latency``, is the unbiased comparison point).
    :raises ValueError: On a non-positive ``alpha`` or ``speed`` or an unknown ``solver``.
    """
    if speed <= 0:
        raise ValueError(f'speed must be positive, got {speed!r}')
    path = algorithm_path(instance, solver)
    if alpha is None:
        alpha = DEFAULT_ALPHA[solver]
    if alpha <= 0:
        raise ValueError(f'alpha must be positive, got {alpha!r}')
    f = instance_features(instance)
    entry = _c.PATHS[(solver, path)]
    latency = _latency(entry, solver, path, f)
    typical = _latency(entry, solver, path, f, covered=False)
    improvement = latency * _interpolate(entry['m'], alpha) + _interpolate(entry['add'], alpha)
    time_limit = min(max(latency + improvement, MIN_TIME_LIMIT), MAX_TIME_LIMIT)
    # The stall stop is relative: the growth paths double their queues between passes, so the wait for the next pass
    # is about the time already spent, and the patience follows the time of the last improvement (ratio alpha / 2:
    # one more pass at alpha 2, two at alpha 8) above a floor of a few seconds.  It never fires before the first
    # solution, and not before the covered latency either; the time limit stays the cap.
    after = min(latency, time_limit)
    ratio = min(max(alpha / 2.0, RATIO_BOUNDS[0]), RATIO_BOUNDS[1])
    return TimeBudget(
        time_limit=time_limit / speed,
        stop_when_unimproved_for=MIN_PATIENCE / speed,
        stop_when_unimproved_after=after / speed,
        stop_when_unimproved_ratio=ratio,
        path=path,
        latency=latency / speed,
        typical_latency=typical / speed,
        improvement=improvement / speed,
        alpha=float(alpha),
        speed=float(speed),
    )
