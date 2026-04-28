The ``network`` submodule
=========================

This module models a hydraulic network as a graph and solves the resulting
nonlinear flow problem from topology plus component head laws.
It is based on graph theory.
For a more elaborate explanation we refer to the theory.
Some of the terms used here are:

Graph theory is the study of mathematical objects known as graphs, which consist of nodes or vertices (points) connected by segments or edges.

* **Nodes** or **Vertices**: are the fundamental units or points in a graph. Each node represents an entity or a location in the structure being modeled.
* **Adjacent Nodes**: Two nodes that are directly connected by a segment.
* **Segments** or **Edges**: are the connections or relationships between pairs of vertices. Each segment links two nodes, indicating a relationship or path between them.
* **Path**: is a sequence of nodes where each adjacent pair is connected by a segment. They can be simple (no repeated nodes) or general (allowing repeats). For instance, in a graph with nodes A, B, C, and D, a path could be A → B → C → D, where each node is connected to the next by a segment.
* **Cycle**: is a path that starts and ends at the same node, with no other repetitions of nodes or segments. Cycles can be simple (no repeated segments or nodes except for the start and end) or general. Here’s an example: In a graph with nodes A, B, C, and D, a simple cycle could be A → B → C → D → A.
* **Connected graph**: A graph is connected when there is a path between every pair of nodes. In a connected graph, there is no unreachable node.

We always presume that the input network forms a connected graph.

The properties below are useful when inspecting the internal graph build.
Assume the following network:

::

    B ────── C ────── D
    |        |        |
    |        |        |
    A ────── F ────── E

* **nodes**: returns all node names (sorted).
  ``net.nodes = ('A', 'B', 'C', 'D', 'E', 'F')``
* **edges**: returns segment keys, one key per component port-to-port segment.
  ``net.edges = ['Comp_A:A-B', 'Comp_B:B-C', ...]``
* **adjacency**: returns adjacency entries as ``(segment_key, next_node, sense)``.
  ``net.adjacency['A'] = [('Comp_A:A-B', 'B', 1), ('Comp_F:F-A', 'F', -1)]``
* **spanningTree**: returns tree entries as ``(segment_key, node_from, node_to, sense)``.
  ``net.spanningTree = [('Comp_A:A-B', 'A', 'B', 1), ...]``
* **cycleBase**: returns ordered loop entries as
  ``(segment_key, node_from, node_to, sense)``. The stored cycle keeps the full
  tree path plus the closing chord instead of collapsing the loop to a smaller
  representation.
  ``net.cycleBase = [[('Comp_A:A-B', 'A', 'B', 1), ...], ...]``


The network calculation solves a system of nonlinear equations made up of:

* In every node the sum of flowrates has to be zero.
  For ``n`` nodes this contributes ``n-1`` independent equations.
  The corresponding incidence matrix is stored in ``net.funcs['B']``.
  The order of the rows follows the internal node storage
  ``['A', 'B', 'C', 'D', 'E', 'F']`` and every row has one position per active
  segment key.
  For the first line (node A):
  * The segment connected to A and leaving A contributes ``-1``.
  * Segments not connected to A contribute ``0``.
  * ...
  * The segment connected to A and entering A contributes ``+1``.

::

  [ 1.  0.  0.  0.  0.  0. -1.]
  [-1.  1.  0.  0.  0.  0.  0.]
  [ 0. -1.  1.  0.  0.  1.  0.]
  [ 0.  0. -1.  1.  0.  0.  0.]
  [ 0.  0.  0. -1. -1.  0.  0.]
  [ 0.  0.  0.  0.  1. -1.  1.]


* In every cycle-base loop the sum of heads has to be zero.
  If there are ``m`` cycle-base loops, this contributes ``m`` additional
  equations. The corresponding loop matrix is stored in ``net.funcs['C']``.
  Every cycle equation has one entry per segment key: ``+1`` if the segment is
  traversed in the cycle direction, ``-1`` if traversed opposite, and ``0`` if
  the segment is not part of that cycle.

::

  C row i: [0, -1, +1, 0, 0, ...]

During ``calcNetwork()`` the solver rebuilds the topology, assembles matrices
``B`` and ``C``, evaluates segment heads through ``calcH(Q, sense, pin, pout)``,
and solves the resulting nonlinear system with ``scipy.optimize.root``.

Some implementation details that matter when reading results:

* Two-port source components are canonicalized so ``sense=-1`` is treated as the
  equivalent reversed node order with ``sense=+1``.
* Initial guesses are retried with both positive and negative seeds so the solve
  is less sensitive to segment orientation.
* Most resistance components compute head from ``|Q|``. The network solver
  reapplies the solved flow sign when forming loop equations so solutions remain
  invariant to how a segment's node order was entered.



.. automodule:: fluidsolve.network
   :members:
   :undoc-members:
   :show-inheritance:

