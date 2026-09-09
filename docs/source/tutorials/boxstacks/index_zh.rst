用 ``boxstacks`` 处理堆叠、重量与卡车
======================================

``boxstacks`` 是上游的第二个三维求解器：物品以竖直的堆（stack）立在箱底，模型多出可堆叠分组、嵌套、上方承重、堆密度、卸载顺序、地面缺陷（defect）以及半挂车轴重模型。Python 侧仍是同一个 :class:`~packingsolver3d.model.Instance`，这些字段对 ``box`` 保持 ``None`` 即可。

一个堆叠实例
------------

.. code-block:: python

   from packingsolver3d import BinType, Instance, ItemType, Objective, boxstacks

   instance = Instance(
       bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5,
                          maximum_weight=1000, maximum_stack_density=10)],
       item_types=[
           ItemType(x=20, y=30, z=40, copies=6, weight=5,
                    stackability_id=0, maximum_stackability=3, maximum_weight_above=100),
       ],
       objective=Objective.BIN_PACKING,
   )
   result = boxstacks.solve(instance, time_limit=2.0)

结果现在带有堆：

.. code-block:: python

   >>> result.number_of_bins, len(result.bins[0].stacks), len(result.placements)
   (1, 3, 6)
   >>> result.bins[0].stacks[0]
   Stack(stack_id=0, bin_id=0, x=0, y=0, lx=20, ly=30, lz=80)
   >>> result.placements[0].stack_id, result.placements[0].group_id
   (0, 0)

每个放置知道自己属于哪个堆，每个堆知道自己的底面积与总高度。``maximum_stackability=3`` 把每堆限制在三件以内；这里上游的搜索选了三堆各两件（``lz=80`` 即两个 40 高的物品），这是若干箱数同为最优的装法之一。

求解器强加的两条规则
--------------------

两条都来自上游，都在送入上游之前检查：

* 共享同一 ``(group_id, stackability_id)`` 桶的物品类型必须有共同的底面积（考虑允许的旋转）。上游只按这个桶分堆，直到装配解时才发现底面积不匹配，因此本包提前抛出 :class:`~packingsolver3d.errors.StackSemanticsError`。给形状不同的物品不同的 ``stackability_id``\ 。
* 物品保持直立：只会以 ``XYZ`` 与 ``YXZ`` 两种旋转放置。``rotations`` 两者都不允许的物品类型会被 :class:`~packingsolver3d.errors.UnsupportedFeatureError` 拒绝。

把这个实例传给 :func:`packingsolver3d.box.solve` 会抛出 :class:`~packingsolver3d.errors.UnsupportedFeatureError`：``box`` 模型没有堆的概念，否则它会悄悄地求解另一个问题。

卸载顺序与缺陷
--------------

``group_id`` 决定卸载顺序（编号大的先卸）；:class:`~packingsolver3d.model.UnloadingConstraint` 限制物品可以怎样被移出，可以设在实例上，也可以按调用覆盖：

.. code-block:: python

   from packingsolver3d import UnloadingConstraint
   result = boxstacks.solve(instance, time_limit=2.0,
                            unloading_constraint=UnloadingConstraint.ONLY_X_MOVEMENTS)

地面缺陷是箱型上的 :class:`~packingsolver3d.model.Defect` 矩形，会原样转给上游；但请先读 :doc:`/explanations/upstream_behaviours/index_zh`：在锁定的上游提交上，上游并不会让堆避开它们。

一辆半挂车
----------

轴重通过箱型上的 :class:`~packingsolver3d.model.SemiTrailerTruck` 建模。下面的数字是上游自己的测试实例：

.. code-block:: python

   from packingsolver3d import SemiTrailerTruck

   truck = SemiTrailerTruck(
       tractor_weight=8000, front_axle_middle_axle_distance=380,
       front_axle_tractor_gravity_center_distance=100, front_axle_harness_distance=320,
       empty_trailer_weight=6000, harness_rear_axle_distance=800,
       trailer_gravity_center_rear_axle_distance=400, trailer_start_harness_distance=100,
       rear_axle_maximum_weight=20000, middle_axle_maximum_weight=9300,
   )
   instance = Instance(
       bin_types=[BinType(x=1360, y=240, z=260, copies=1, maximum_weight=24000,
                          maximum_stack_density=1000, semi_trailer_truck=truck)],
       item_types=[ItemType(x=100, y=200, z=200, copies=3, weight=2000,
                            stackability_id=0, maximum_stackability=1)],
       objective=Objective.KNAPSACK,
   )
   result = boxstacks.solve(instance)
   len(result.placements)   # 3 件里装了 2 件：第三件会让中轴超载

上游会校验几何参数（``SemiTrailerTruckData::check``\ ）；比如缺少 ``harness_rear_axle_distance`` 的卡车会被 :class:`~packingsolver3d.errors.InvalidInstanceError` 拒绝，消息即上游原话。

下一步
------

* 每个字段及其上游含义：:doc:`/reference/model_fields/index_zh`。
* 上面这些行为及其证据：:doc:`/explanations/upstream_behaviours/index_zh`。
