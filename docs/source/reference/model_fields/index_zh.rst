模型字段
========

所有模型都是 frozen dataclass。留为 ``None`` 的字段不会送给上游，因此上游默认值生效——与上游 CSV 读取器对缺失列的处理相同。"求解器"一列说明哪个引擎认这个字段；:func:`packingsolver3d.box.validate` 会拒绝设置了 ``boxstacks`` 专有字段的实例。

``ItemType``
------------

.. list-table::
   :header-rows: 1

   * - 字段
     - 上游
     - 默认
     - 求解器
   * - ``x``、``y``、``z``
     - ``add_item_type(x, y, z)``
     - 必填，正数
     - 两者
   * - ``profit``
     - ``set_item_type_profit``
     - ``None`` -> 上游用 ``x * y * z``
     - 两者
   * - ``weight``
     - ``set_item_type_weight``
     - ``0.0``
     - 两者
   * - ``copies``
     - ``set_item_type_copies``
     - ``1``
     - 两者
   * - ``copies_min``
     - ``set_item_type_copies_min``
     - ``None`` -> 上游 ``-1``\ ：全部副本必装，knapsack 下为 0
     - 两者
   * - ``rotations``
     - 逐项 ``add_item_type_rotation``
     - ``None`` -> 上游 ``{XYZ}``\ ；``boxstacks`` 只放 ``XYZ``/``YXZ``
     - 两者
   * - ``group_id``
     - ``set_item_type_group``
     - ``None`` -> ``0``
     - boxstacks
   * - ``stackability_id``
     - ``set_item_type_stackability_id``
     - ``None`` -> ``0``
     - boxstacks
   * - ``nesting_height``
     - ``set_item_type_nesting_height``
     - ``None`` -> ``0``
     - boxstacks
   * - ``maximum_stackability``
     - ``set_item_type_maximum_stackability``
     - ``None`` -> 无限
     - boxstacks
   * - ``maximum_weight_above``
     - ``set_item_type_maximum_weight_above``
     - ``None`` -> 无限
     - boxstacks

旋转令牌为上游原文：``XYZ, YXZ, ZYX, YZX, XZY, ZXY``\ 。尺寸为 ``(x, y, z)`` 的盒子在各旋转下的摆放尺寸依次为 ``(x, y, z)``、``(y, x, z)``、``(z, y, x)``、``(y, z, x)``、``(x, z, y)``、``(z, x, y)``\ ，来自上游 ``ItemType::x/y/z(Rotation)``\ 。

``BinType``
-----------

.. list-table::
   :header-rows: 1

   * - 字段
     - 上游
     - 默认
     - 求解器
   * - ``x``、``y``、``z``
     - ``add_bin_type(x, y, z)``
     - 必填，正数
     - 两者
   * - ``cost``
     - ``set_bin_type_cost``
     - ``None`` -> 上游用 ``x * y``\ （面积）
     - 两者
   * - ``copies``
     - ``set_bin_type_copies``
     - ``1``
     - 两者
   * - ``copies_min``
     - ``set_bin_type_copies_min``
     - ``0``
     - 两者
   * - ``maximum_weight``
     - ``set_bin_type_maximum_weight``
     - ``None`` -> 无限
     - 两者
   * - ``maximum_stack_density``
     - ``set_bin_type_maximum_stack_density``
     - ``None`` -> 无限
     - boxstacks
   * - ``semi_trailer_truck``
     - ``set_bin_type_semi_trailer_truck_parameters``
     - ``None`` -> 不是卡车
     - boxstacks

``SemiTrailerTruck``
--------------------

对应上游 ``SemiTrailerTruckData``\ （``algorithms/truck.hpp``\ ）。距离为长度、重量为重量，单位随实例；几何量默认 ``0``\ ，两个最大值默认无限，与上游一致。上游 ``check()`` 校验几何，比如拒绝 ``harness_rear_axle_distance`` 为零。

``tractor_weight``、``front_axle_middle_axle_distance``、``front_axle_tractor_gravity_center_distance``、``front_axle_harness_distance``、``empty_trailer_weight``、``harness_rear_axle_distance``、``trailer_gravity_center_rear_axle_distance``、``trailer_start_harness_distance``、``rear_axle_maximum_weight``、``middle_axle_maximum_weight``\ 。

``Defect``
----------

``bin_type_id``、``x``、``y``、``lx``、``ly`` -> ``add_defect(bin_type_id, x, y, w, h)``\ ；仅 ``boxstacks``\ ，上游对它的实际处理见 :doc:`/explanations/upstream_behaviours/index_zh`。

``Instance``
------------

.. list-table::
   :header-rows: 1

   * - 字段
     - 上游
     - 默认
   * - ``bin_types``、``item_types``
     - 按顺序调用上述 builder；id 即位置
     - 必填，非空
   * - ``objective``
     - ``set_objective``
     - 必填；``Objective.DEFAULT``\ （上游未设置时的占位符）会被拒绝
   * - ``defects``
     - 逐项 ``add_defect``
     - ``()``
   * - ``unloading_constraint``
     - ``set_unloading_constraint``
     - ``None``\ ；仅 ``boxstacks``\ ，可按调用覆盖
