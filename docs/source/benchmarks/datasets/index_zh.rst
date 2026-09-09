三个基准
========

三个实例族都是公开的、在集装箱装载文献里沿用多年的数据，并且都以本包能读的 CSV 格式收在 PackingSolver 自己的 ``data/box`` 目录里。选它们的原因：小到能可视化，难到能把参与者拉开，而且大多数 case 有已证明的或构造性的最优值。实例文件原样读取，唯一的补充是装箱类实例的 bin 份数，文件里没有给。

Egeblad-Pisinger 三维背包
-------------------------

**来源。** Jens Egeblad 与 David Pisinger，"Heuristic approaches for the two- and three-dimensional knapsack packing problem"，*Computers & Operations Research* 36(4)，1026-1049，2009。实例以 ``kp2d3d-data.zip`` 发布在 David Pisinger 的代码页 "2D/3D Knapsack Packing instances" 条目下，http://hjemmesider.diku.dk/~pisinger/codes.html\ ；PackingSolver 把它们转换后收在 ``data/box/egeblad2009``\ 。

**问题。** 一个容器，一组带利润的物品，最大化装入物品的利润之和。物品保持给定朝向（固定姿态变体，``rotations=[Rotation.XYZ]``\ ），下面的已证明最优值都针对这个变体。

**实例。** 名字形如 ``ep3d-<n>-<形状>-<利润>-<比例>``\ 。``n`` 是物品数；形状字母描述箱子形态 -- ``C`` 立方体，``D`` 近似立方体，``F`` 有一条短边的扁盒，``L`` 有一条长边的长盒，``U`` 边长在整个范围内取值；比例 50 表示容器容积是物品总体积的一半，大约能装一半物品，难点在选子集；比例 90 表示容积是总体积的九成，几乎全部都应装得下，难点转到摆放上。在 PackingSolver 附带的文件里每个物品的利润都等于体积加 200，所以目标就是装入体积加上每件 200，中间那个字母不改变文件中的利润。表格使用全部二十个 ``ep3d-20-*`` 实例：二十件物品，一个容器，五种形状类别，两种比例。

**已知结论。** 精确 CP-SAT 模型（见 :doc:`../participants/index_zh`\ ）在 20 s 内证明了多数 case 的最优值；它超时且界很松的地方，有时由 PackingSolver 自己的界收口。:doc:`../leaderboards/index_zh` 的 case 表逐个说明当前生效的界是哪一个、从哪来。

Martello-Pisinger-Vigo 生成器第 9 类
------------------------------------

**来源。** Silvano Martello、David Pisinger 与 Daniele Vigo，"The three-dimensional bin packing problem"，*Operations Research* 48(2)，256-267，2000；以及 Martello、Pisinger、Vigo、den Boef、Korst 的一般装箱后续工作（*ACM Transactions on Mathematical Software* 33(1)，2007）。作者的实例生成器 ``test3dbpp.c`` 与精确程序 ``3dbpp.c`` 是 http://hjemmesider.diku.dk/~pisinger/codes.html 上 "General 3D Bin-packing Problem" 条目（目录 ``new3dbpp``\ ）。代码页声明这些程序对学术用途免费。

**问题。** 相同的箱子，所有物品必须装入，最小化箱子数。物品保持朝向，与生成器自带求解器的假设一致。

**实例。** 生成器以箱子边长 100、第 9 类、``n = 30``\ 、``60``\ 、``90`` 运行，每个规模 replicate 1 到 10（种子 ``n + replicate``\ ，生成器的 ``srand`` 规则），共三十个实例。第 9 类是生成器的 ``/* guillotine cut three bins */`` 类：把三个整箱用随机的正交切割切成物品，所以每个实例按构造恰好装进三个箱子，三也是体积下界。六十个 CSV 文件提交在 ``tools/benchmarks/instances/mpv_t9`` 下，附 ``SOURCE.md`` 说明参数；它们是生成的数据，沿用生成器的学术用途说明。

**已知结论。** 无论件数多少，每个 replicate 的最优值都是三箱。找到它意味着重新发现一个毫无余量的完美三箱切割，这正是该类区分度高的原因：任何留下缝隙的启发式都需要第四个箱子，而三种规模显示每个参与者在多少件时开始找不到这个切割。

Ivancic-Mathur-Mohanty（THPACK9）
---------------------------------

**来源。** N. Ivancic、K. Mathur 与 B. B. Mohanty，"An integer programming based heuristic approach to the three-dimensional packing problem"，*Journal of Manufacturing and Operations Management* 2，268-298，1989。这 47 个实例以 ``thpack9.txt`` 流传，是 Bischoff 与 Ratcliff 为 OR-Library 收集的 ``thpack`` 系列文件的第九个；如今由 ESICUP 数据集仓库维护，https://github.com/ESICUP/datasets\ （``3d_rectangular/thpack/thpack9.txt``\ ）。PackingSolver 收在 ``data/box/ivancic1989``\ 。

**问题。** 相同的集装箱，两到五种物品各有多件，全部必须装入，最小化集装箱数。允许全部六种朝向，与原论文和文件一致。

**实例。** 表格使用全部 47 个实例：两到五种共 47 到 181 个盒子，集装箱从 10 x 6 x 16 到工业尺寸，最优值从两个到约五十个集装箱。它们是弱异质货物，也是很多真实装载问题的形态。图集画的是实例 26（72 个盒子，三个集装箱），是小到可以逐箱检查的实例之一。

**已知结论。** 文件没有附带发表过的最优性证明；表格里的界取体积界与 PackingSolver 自报界中更紧的那个，:doc:`../leaderboards/index_zh` 的 case 表逐个说明该界是否被达到。
