packingsolver3d.result
========================================================

.. currentmodule:: packingsolver3d.result

.. automodule:: packingsolver3d.result


\_\_all\_\_
-----------------------------------------------------

.. autodata:: __all__


Status
-----------------------------------------------------

.. autoclass:: Status
    :members: OPTIMAL,FEASIBLE,NO_SOLUTION,INFEASIBLE


Placement
-----------------------------------------------------

.. autoclass:: Placement
    :members: item_type_id,bin_id,x,y,z,lx,ly,lz,rotation,stack_id,group_id


Stack
-----------------------------------------------------

.. autoclass:: Stack
    :members: stack_id,bin_id,x,y,lx,ly,lz


PackedBin
-----------------------------------------------------

.. autoclass:: PackedBin
    :members: bin_id,bin_type_id,copies,x,y,z,placements,stacks


RunRecord
-----------------------------------------------------

.. autoclass:: RunRecord
    :members: problem_type,options,stdout,stderr,wall_time


Result
-----------------------------------------------------

.. autoclass:: Result
    :members: is_proven_optimal,number_of_bins,placements,to_json,status,bins,objective,value,bound,statistics,solve_time,run
