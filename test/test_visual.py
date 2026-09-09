import pytest

from packingsolver3d import BinType, Instance, ItemType, Objective, PackedBin, Placement, Rotation, box, boxstacks

plotly = pytest.importorskip('plotly')  # optional dependency; the wheel test environments do not install it

from packingsolver3d.visual import COLOR_KEYS, plot_bin, plot_result  # noqa: E402


def _types(figure):
    return [trace.type for trace in figure.data]


@pytest.mark.unittest
class TestPlotResult:
    def test_box_result(self, box_instance):
        result = box.solve(box_instance, time_limit=2.0)
        figure = plot_result(result)
        types = _types(figure)
        # one bin shell, ten items, one border polyline, one label trace
        assert types.count('mesh3d') == 1 + len(result.placements)
        assert types.count('scatter3d') == 2
        names = {trace.name for trace in figure.data if trace.showlegend}
        assert names == {'Bins', 'Item type 0', 'Item type 1'}
        assert figure.layout.scene.aspectmode == 'data'
        assert tuple(figure.layout.scene.xaxis.range) == (0, 100)

    def test_color_by_stack(self, stack_instance):
        result = boxstacks.solve(stack_instance, time_limit=2.0)
        figure = plot_result(result, color_by='stack')
        names = {trace.name for trace in figure.data if trace.showlegend}
        assert names == {'Bins'} | {'Stack {i}'.format(i=s.stack_id) for s in result.bins[0].stacks}

    def test_color_by_same_and_no_ids(self, box_instance):
        result = box.solve(box_instance, time_limit=2.0)
        figure = plot_result(result, color_by='same', show_ids=False)
        assert {trace.name for trace in figure.data if trace.showlegend} == {'Bins', 'Items'}
        assert _types(figure).count('scatter3d') == 1  # borders only
        colors = {trace.color for trace in figure.data if trace.type == 'mesh3d' and trace.name == 'Items'}
        assert colors == {'cornflowerblue'}

    def test_copies_are_drawn_once(self):
        # Upstream reports identical bins as one bin with copies; the title says how many.
        instance = Instance(
            bin_types=[BinType(x=10, y=10, z=10, copies=5)],
            item_types=[ItemType(x=10, y=10, z=10, copies=3)],
            objective=Objective.BIN_PACKING,
        )
        result = box.solve(instance, time_limit=2.0)
        assert result.number_of_bins == 3 and len(result.bins) == 1
        figure = plot_result(result)
        assert [a.text for a in figure.layout.annotations] == ['Bin 0 (type 0) x3']

    def test_grid_for_distinct_bins(self):
        bins = tuple(
            PackedBin(bin_id=i, bin_type_id=i % 2, copies=1, x=10, y=10, z=10 + i, placements=(
                Placement(item_type_id=i, bin_id=i, x=0, y=0, z=0, lx=5, ly=5, lz=5, rotation=Rotation.XYZ),
            ))
            for i in range(3)
        )
        figure = plot_result(bins, title='three bins')
        assert [a.text for a in figure.layout.annotations] == ['Bin 0 (type 0)', 'Bin 1 (type 1)', 'Bin 2 (type 0)']
        assert figure.layout.title.text == 'three bins'
        assert figure.layout.scene3.zaxis.range[1] == 12
        assert len(plot_result(bins, columns=1).layout.annotations) == 3

    def test_rejects_bad_arguments(self, box_instance):
        result = box.solve(box_instance, time_limit=2.0)
        with pytest.raises(ValueError):
            plot_result(result, color_by='rainbow')
        with pytest.raises(ValueError):
            plot_result(())
        assert COLOR_KEYS == ('item_type', 'stack', 'same')


@pytest.mark.unittest
class TestPlotBin:
    def test_single_bin(self):
        packed = PackedBin(bin_id=0, bin_type_id=0, copies=1, x=10, y=10, z=10, placements=(
            Placement(item_type_id=0, bin_id=0, x=0, y=0, z=0, lx=5, ly=5, lz=5, rotation=Rotation.XYZ),
            Placement(item_type_id=1, bin_id=0, x=5, y=0, z=0, lx=5, ly=5, lz=5, rotation=Rotation.XYZ),
        ))
        figure = plot_bin(packed)
        assert _types(figure) == ['mesh3d', 'mesh3d', 'mesh3d', 'scatter3d', 'scatter3d']
        labels = [trace for trace in figure.data if trace.type == 'scatter3d' and trace.mode == 'text'][0]
        assert list(labels.text) == ['0', '1']
        # items are shrunk by the epsilon on every side so faces do not z-fight
        item = [trace for trace in figure.data if trace.name == 'Item type 0'][0]
        assert min(item.x) > 0 and max(item.x) < 5
