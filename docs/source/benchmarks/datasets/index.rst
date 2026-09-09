The three benchmarks
====================

All three families are public, long established in the container-loading literature, and ship in PackingSolver's own ``data/box`` directory in the CSV format this package reads. They were chosen because they are small enough to visualise, hard enough to separate the participants, and come with a proven or constructive optimum for most cases. The instance files are read unmodified; the only addition is the number of bin copies for the bin packing families, which the files leave open.

Egeblad-Pisinger three-dimensional knapsack
-------------------------------------------

**Source.** Jens Egeblad and David Pisinger, "Heuristic approaches for the two- and three-dimensional knapsack packing problem", *Computers & Operations Research* 36(4), 1026-1049, 2009. The instances are distributed as ``kp2d3d-data.zip`` under "2D/3D Knapsack Packing instances" on David Pisinger's code page, http://hjemmesider.diku.dk/~pisinger/codes.html; PackingSolver ships them converted in ``data/box/egeblad2009``.

**Problem.** One container, a set of items each with a profit, maximise the total profit of the items packed. Items keep their orientation (the fixed-pose variant, ``rotations=[Rotation.XYZ]``); this is the variant the proven optima below refer to.

**Instances.** Names read ``ep3d-<n>-<shape>-<profit>-<ratio>``. ``n`` is the number of items; the shape letter describes the boxes -- ``C`` cubes, ``D`` near-cubic boxes, ``F`` flat boxes with one short side, ``L`` long boxes with one long side, ``U`` sides drawn from the whole range; ``ratio`` 50 means the container holds half of the total item volume, so about half of the items can be packed. In the files as distributed with PackingSolver every item's profit is its volume plus 200, so the objective is packed volume plus 200 per packed item and the middle letter does not change the profits. The tables use the ten ``ep3d-20-*-50`` instances: twenty items, one container, five shape classes.

**What is known.** An exact CP-SAT model (see :doc:`../participants/index`) proves the optimum of eight of the ten cases within 20 s; on the remaining two, ``ep3d-20-D-C-50`` and ``ep3d-20-F-R-50``, PackingSolver's own bound closes the gap, so all ten optima are proven.

Martello-Pisinger-Vigo generator, class 9
-----------------------------------------

**Source.** Silvano Martello, David Pisinger and Daniele Vigo, "The three-dimensional bin packing problem", *Operations Research* 48(2), 256-267, 2000, and the general-packing follow-up by Martello, Pisinger, Vigo, den Boef and Korst (*ACM Transactions on Mathematical Software* 33(1), 2007). The authors' instance generator ``test3dbpp.c`` and exact code ``3dbpp.c`` are the "General 3D Bin-packing Problem" entry on http://hjemmesider.diku.dk/~pisinger/codes.html (directory ``new3dbpp``). The code page states that the codes are free of charge for academic purposes.

**Problem.** Identical bins, all items must be packed, minimise the number of bins. Items keep their orientation, as the generator's own solver assumes.

**Instances.** The generator was run with bin dimension 100, class 9 and ``n = 30``, replicates 1 to 10 (seeds 31 to 40, the generator's ``srand(n + replicate)`` rule). Class 9 is the generator's ``/* guillotine cut three bins */`` class: three full bins are cut into the items by random orthogonal cuts, so every instance packs into exactly three bins by construction and three is also the volume lower bound. The twenty CSV files are committed under ``tools/benchmarks/instances/mpv_t9`` with a ``SOURCE.md`` stating the parameters; being generated data they carry the generator's academic-use note.

**What is known.** The optimum is three bins for every replicate. Finding it means rediscovering a perfect three-bin cut with no slack at all, which is what makes the class discriminative: a heuristic that leaves any gap needs a fourth bin.

Ivancic-Mathur-Mohanty (THPACK9)
--------------------------------

**Source.** N. Ivancic, K. Mathur and B. B. Mohanty, "An integer programming based heuristic approach to the three-dimensional packing problem", *Journal of Manufacturing and Operations Management* 2, 268-298, 1989. The 47 instances circulate as ``thpack9.txt``, the ninth of the ``thpack`` files that Bischoff and Ratcliff collected for OR-Library; today they are maintained in the ESICUP dataset repository, https://github.com/ESICUP/datasets (``3d_rectangular/thpack/thpack9.txt``). PackingSolver ships them in ``data/box/ivancic1989``.

**Problem.** Identical containers, two to five item types with many copies each, all items must be loaded, minimise the number of containers. All six orientations are allowed, as in the original paper and the files.

**Instances.** The tables use eight of the 47: instance 1 (70 items, 25 containers, the case most often quoted) and the seven instances whose volume lower bound is at most five containers and whose item count is below 100 -- instances 18, 19, 20 (47 items), 24, 25, 26 (72 items) and 46 (99 items). They are weakly heterogeneous cargo, the shape of many real loading problems, and small enough that a three- or five-container solution is easy to inspect.

**What is known.** No published proof of optimality is bundled with the files; the bound used in the tables is the tighter of the volume bound and PackingSolver's own reported bound. Seven of the eight cases are proven optimal by that bound; instance 25 is packed into five containers against a bound of four.
