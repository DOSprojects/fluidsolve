The ``network`` submodule
=========================

This module is based on the math graph theory.
For a more elaborate explanation we refer to the theory.
Some of the terms used here are:

Graph theory is the study of mathematical objects known as graphs, which consist of nodes or vertices (points) connected by segments or edges.

* **Nodes** or **Vertices**: are the fundamental units or points in a graph. Each node represents an entity or a location in the structure being modeled.
* **Adjacent Nodes**: Two nodes that are directly connected by a segment.
* **Segments** or **Edges**: are the connections or relationships between pairs of vertices. Each segment links two nodes, indicating a relationship or path between them.
* **Path**: is a sequence of nodes where each adjacent pair is connected by an segment. They can be simple (no repeated nodes) or general (allowing repeats). For instance, In a graph with nodes A, B, C, and D, a path could be A → B → C → D, where each node is connected to the next by a segment.
* **Cycle**: is a path that starts and ends at the same node, with no other repetitions of nodes or segments. Cycles can be simple (no repeated segments or nodes except for the start and end) or general. Here’s an example: In a graph with nodes A, B, C, and D, a simple cycle could be A → B → C → D → A.
* **Connected graph**: A graph is connected when there is a path between every pair of nodes. In a connected graph, there is no unreachable node.

We always presume that the input network forms a connected graph.

Following methods are used. We presume following network:

::

    B ────── C ────── D
    |        |        |
    |        |        |
    A ────── F ────── E

* **Nodes**: returns all node names (sorted).
  ``net.Nodes = ('A', 'B', 'C', 'D', 'E', 'F')``
* **Edges**: returns segment keys (one key per component port-to-port segment).
  ``net.Edges = ['Comp_1:A->B', 'Comp_2:B->C', ...]``
* **Adjacency**: returns adjacency entries as ``(segment_key, next_node, sense)``.
  ``net.Adjacency['A'] = [('Comp_1:A->B', 'B', 1), ('Comp_6:F->A', 'F', -1)]``
* **SpanningTree**: returns tree entries as ``(segment_key, node_from, node_to, sense)``.
  ``net.SpanningTree = [('Comp_1:A->B', 'A', 'B', 1), ...]``
* **FundamentalCycles**: returns cycle entries as ``(segment_key, node_from, node_to, sense)``.
  ``net.FundamentalCycles = [[('Comp_1:A->B', 'A', 'B', 1), ...], ...]``


The calculation of the network is done by solving a system of equations.
This system consists of:

* In every node the sum of flowrates has to be zero.
  For ``n`` nodes this contributes ``n-1`` independent equations.
  The data for the equations in the example looks like below.
  The order of the rows is the order of the internal nodes storage ['A', 'B', 'C', 'D', 'E', 'F'].
  Every row has a position for every segment key in the internal segment storage.
  E.g. for the first line (node A):
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


* In every fundamental cycle the sum of heads has to be zero.
  If there are ``m`` fundamental cycles, this contributes ``m`` additional equations.
  Every cycle equation has one entry per segment key:
  ``+1`` if the segment is traversed in the cycle direction,
  ``-1`` if traversed opposite,
  and ``0`` if the segment is not part of that cycle.

::

  C row i: [0, -1, +1, 0, 0, ...]

The solver builds matrix ``B`` (node continuity) and matrix ``C`` (loop energy),
evaluates component heads through ``calcH(Q, sense)``, and solves the resulting
nonlinear system with Newton-Raphson.



.. automodule:: fluidsolve.network
   :members:
   :undoc-members:
   :show-inheritance:

