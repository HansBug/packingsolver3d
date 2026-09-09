packingsolver3d.model
========================================================

.. currentmodule:: packingsolver3d.model

.. automodule:: packingsolver3d.model


\_\_all\_\_
-----------------------------------------------------

.. autodata:: __all__


ALL\_ROTATIONS
-----------------------------------------------------

.. autodata:: ALL_ROTATIONS


Objective
-----------------------------------------------------

.. autoclass:: Objective
    :members: DEFAULT,FEASIBILITY,BIN_PACKING,BIN_PACKING_WITH_LEFTOVERS,OPEN_DIMENSION_X,OPEN_DIMENSION_Y,OPEN_DIMENSION_Z,OPEN_DIMENSION_XY,KNAPSACK,VARIABLE_SIZED_BIN_PACKING,BIN_PACKING_CUTTING_COST


Rotation
-----------------------------------------------------

.. autoclass:: Rotation
    :members: XYZ,YXZ,ZYX,YZX,XZY,ZXY


UnloadingConstraint
-----------------------------------------------------

.. autoclass:: UnloadingConstraint
    :members: NONE,ONLY_X_MOVEMENTS,ONLY_Y_MOVEMENTS,INCREASING_X,INCREASING_Y


OptimizationMode
-----------------------------------------------------

.. autoclass:: OptimizationMode
    :members: ANYTIME,NOT_ANYTIME,NOT_ANYTIME_DETERMINISTIC,NOT_ANYTIME_SEQUENTIAL


ItemType
-----------------------------------------------------

.. autoclass:: ItemType
    :members: is_stackable,__repr__,x,y,z,profit,weight,copies,copies_min,rotations,group_id,stackability_id,nesting_height,maximum_stackability,maximum_weight_above,STACKING_FIELDS


BinType
-----------------------------------------------------

.. autoclass:: BinType
    :members: is_stackable,__repr__,x,y,z,cost,copies,copies_min,maximum_weight,maximum_stack_density,STACKING_FIELDS


Defect
-----------------------------------------------------

.. autoclass:: Defect
    :members: bin_type_id,x,y,lx,ly


Instance
-----------------------------------------------------

.. autoclass:: Instance
    :members: __post_init__,needs_stacking,bin_types,item_types,objective,defects,unloading_constraint


