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

* **Nodes**: returns a list with all the nodes in the network
  net.Nodes = ['A', 'B', 'C', 'D', 'E', 'F']
* **Edges**: returns a list with all the edges in the network. Each edge must contain a Component (Pump, Resistance, Dummy, ...).
  net.Edges = [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'), ('F', 'E'), ('F', 'A')]
* **Adjacency**: returns the adjacency dict of the network
  net.Adjacency = {'A': ['B', 'F'], 'B': ['A', 'C'], 'C': ['B', 'D'], 'D': ['C', 'E'], 'E': ['D', 'F'], 'F': ['E', 'A']}
* **SpanningTree**: returns a list with all the nodes in the network
  net.SpanningTree = [('A', 'F'), ('E', 'F'), ('D', 'E'), ('C', 'D'), ('B', 'C')]
* **FundamentalCycles**: returns a list with all the nodes in the network
  net.FundamentalCycles = [['A', 'F', 'E', 'D', 'C', 'B', 'A']]
* **findShortestPath**: Algorithm for an unweighted undirected graph using Breadth-First Search (BFS) to find the shortest path between two nodes of a graph.
  net.findShortestPath('B', 'E') = ['B', 'A', 'F', 'E']


The calculation of the network is done by solving a system of equations.
This system consists of:

* In every node the sum of flowrates has to be zero. In our case this generates 6 equations.
  The data for the equations in the example looks like below.
  The order of the rows is the order of the internal nodes storage ['A', 'B', 'C', 'D', 'E', 'F'].
  Every row has a position for every edge in the order of the internal edge storage [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'), ('F', 'E'), ('C', 'F'), ('F', 'A')].
  E.g. for the first line (node A):
  * The component in edge [A-B] has an internal forward use and is used forward, so gives 1 * 1 = 1.
  * The component in edge [B-C] has no connection wit node A, so gives 0.
  * ...
  * The component in edge [F-A] has no connection wit node A, has an internal forward use and is used backwards, so gives 1 * -1 = 1.

::

  [ 1.  0.  0.  0.  0.  0. -1.]
  [-1.  1.  0.  0.  0.  0.  0.]
  [ 0. -1.  1.  0.  0.  1.  0.]
  [ 0.  0. -1.  1.  0.  0.  0.]
  [ 0.  0.  0. -1. -1.  0.  0.]
  [ 0.  0.  0.  0.  1. -1.  1.]


* In every fundamental cycle the sum of heads has to be zero.
  In the example we determined 2 fundamental cycles: ['A', 'F', 'C', 'B', 'A'] and ['E', 'D', 'C', 'F', 'E']
  resulting in 2 additional equations.
  Every equation consists of an entry for every edge.
  If the edge is not included, the the component is Comp_Dummy, d(irection) = 0 and s is between brackets.
  If the edge is in anther direction than the defined use, d=-1, else d=+1.

::

  Equation 7:
  {'s': 'B-A', 'c': <fluidsolve.comp_pump.Comp_PumpCentrifugal object at 0x000002BFB0656360>, 'd': -1.0}
  {'s': 'C-B', 'c': <fluidsolve.comp_resist.Comp_Tube object at 0x000002BFA7E6F560>, 'd': -1.0}
  {'s': '(C-D)', 'c': <fluidsolve.comp_resist.Comp_Dummy object at 0x000002BFC04F66F0>, 'd': 0.0}
  {'s': '(D-E)', 'c': <fluidsolve.comp_resist.Comp_Dummy object at 0x000002BFC04F6F90>, 'd': 0.0}
  {'s': '(F-E)', 'c': <fluidsolve.comp_resist.Comp_Dummy object at 0x000002BFC04F7680>, 'd': 0.0}
  {'s': 'F-C', 'c': <fluidsolve.comp_resist.Comp_Tube object at 0x000002BFC04F5340>, 'd': -1.0}
  {'s': 'A-F', 'c': <fluidsolve.comp_resist.Comp_Tube object at 0x000002BFC04F5A90>, 'd': -1.0}

  Equation 8:
  {'s': '(A-B)', 'c': <fluidsolve.comp_resist.Comp_Dummy object at 0x000002BFC04F6630>, 'd': 0.0}
  {'s': '(B-C)', 'c': <fluidsolve.comp_resist.Comp_Dummy object at 0x000002BFC04F6B10>, 'd': 0.0}
  {'s': 'D-C', 'c': <fluidsolve.comp_resist.Comp_Tube object at 0x000002BFC00790D0>, 'd': -1.0}
  {'s': 'E-D', 'c': <fluidsolve.comp_resist.Comp_Tube object at 0x000002BFBFD72270>, 'd': -1.0}
  {'s': 'F-E', 'c': <fluidsolve.comp_pump.Comp_PumpCentrifugal object at 0x000002BFC04F5AC0>, 'd': 1.0}
  {'s': 'C-F', 'c': <fluidsolve.comp_resist.Comp_Tube object at 0x000002BFC04F5340>, 'd': 1.0}
  {'s': '(F-A)', 'c': <fluidsolve.comp_resist.Comp_Dummy object at 0x000002BFC058D940>, 'd': 0.0}

To solve the system of equations, the Newton-Raphson method is used.
The input above is used to do the actual calculations in the solver function.



.. automodule:: fluidsolve.network
   :members:
   :undoc-members:
   :show-inheritance:

