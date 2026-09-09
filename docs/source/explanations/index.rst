Explanation roadmap
===================

Explanations answer "why is it like this?". They are not needed to run a solve, but they are needed to trust one. Read them when a result surprises you, or before you publish numbers produced with this package.

Pages
-----

* :doc:`architecture/index` -- how the upstream C++ is compiled into the extension module, what crosses the boundary, and what that implies for isolation and lifetimes.
* :doc:`statuses/index` -- what ``OPTIMAL``, ``FEASIBLE``, ``NO_SOLUTION`` and ``INFEASIBLE`` mean here, and why the achieved value and the reported bound are kept apart.
* :doc:`upstream_behaviours/index` -- the behaviours of upstream PackingSolver at the pinned commit that affect results, with the evidence for each and what the package does about it.

.. toctree::
    :maxdepth: 1
    :hidden:

    architecture/index
    statuses/index
    upstream_behaviours/index
