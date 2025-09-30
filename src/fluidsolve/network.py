'''
This module implements the network functionality
A lot is based on graph math.
'''
#******************************************************************************
# IMPORTS
#******************************************************************************
from typing                   import Optional
import numpy                  as np
from scipy.optimize           import fsolve
# module own
import fluidsolve.medium      as flsm
import fluidsolve.aux_tools   as flsa
import fluidsolve.comp_base   as flsb
import fluidsolve.comp_resist as flsc
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity

#******************************************************************************
# BASE CLASSES
#******************************************************************************

#******************************************************************************
# Network
class Network ():
  ''' Network class to represent a hydraulic network.
      This class is used to calculate flows and pressure drops in a network of hydraulic components.

    Args:
    kwargs (dict): Keyword arguments for network initialization.
  '''

  def __init__(self, **kwargs: int) -> None:
    args_in = flsa.GetArgs(kwargs)
    self._name: str = args_in.getArg(
      'name',
      [
          flsa.vFun.default(''),
          flsa.vFun.istype(str),
      ]
    )
    segments: list = args_in.getArg(
      'segments',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(list),
      ]
    )
    #
    self._segments          : list  = []
    self._nodes             : list  = []
    self._adjacency         : dict[str, list]  = {}
    self._spanningtree      : list  = []
    self._fundamentalcycles : list  = []
    self._allcycles         : list  = []
    self._funcs             : dict[str, list] = {'N': [], 'L': []}
    self._result            : list  = []
    self.addSegments(segments)

  @property
  def Segments(self) -> list[dict]:
    '''Return the segments of the network.

    Returns:
      list[dict]: List of segments in the network.
    '''
    return self._segments

  @property
  def Nodes(self) -> list[str]:
    ''' Return the nodes of this network.

    Returns:
        list[str]: nodes
    '''
    return self._nodes

  @property
  def Edges(self) -> list[tuple[str, str]]:
    ''' Return the edges in this network.

    Returns:
        list[tuple[str, str]]: edges
    '''
    return [(s['B'], s['E']) for s in self._segments]

  @property
  def Adjacency(self) -> dict[str, list[str]]:
    ''' Return adjacency list.

    Returns:
        dict[str, list[str]]: adjacency list in graph.
    '''
    return self._adjacency

  @property
  def SpanningTree(self) -> list[tuple[str, str]]:
    ''' Return spanning tree.

    Returns:
        list[tuple[str, str]]: spanning tree in graph.
    '''
    return self._spanningtree

  @property
  def AllCycles(self) -> list[list[str]]:
    ''' Return all cycles in graph.

    Returns:
        list[list[str]]: all cycles in graph.
    '''
    return self._allcycles

  @property
  def FundamentalCycles(self) -> list[list[str]]:
    ''' Return fundamental cycles in graph.

    Returns:
        list[list[str]]: fundamental cycles in graph.
    '''
    return self._fundamentalcycles

  @property
  def Funcs(self) -> dict[str, list]:
    ''' Return the functions to execute the calculation algorithm (Newton Raphson).

    Returns:
        dict[str, list]: Data needed to create the system of equations.
    '''
    return self._funcs

  @property
  def Result(self) -> list[dict]:
    ''' Return the result of the calculation algorithm.

    Returns:
        list[dict]: for every segment: the name, Q and H.
    '''
    return self._result

  def addSegments(self, segments: list[tuple[str, str, flsb.Comp_Base]]) -> None:
    ''' Add a segment to the network

    Args:
        segments (list[tuple[str, str, flsb.Comp_Base]]): the segments to add.

    '''
    # Add segments nodes to the network
    for s in segments:
      if not isinstance(s, (set, tuple, list)):
        raise ValueError(f'Invalid section format: {s}')
      if len(s) != 3:
        raise ValueError(f'Invalid section format: {s}')
      lB, lE, lcomp = s
      if not isinstance(lB, str):
        raise ValueError(f'Invalid section format (B): {s}')
      if not isinstance(lE, str):
        raise ValueError(f'Invalid section format (E): {s}')
      if not isinstance(lcomp, flsb.Comp_Base):
        raise ValueError(f'Invalid section format (component): {s}')
      lname = f'{lB}-{lE}'
      if lname in self._segments:
        raise ValueError(f'Section {lname} already exists')
      if lB not in self._nodes:
        self._nodes.append(lB)
      if lE not in self._nodes:
        self._nodes.append(lE)
      #TODO: comp can be string (component name) or component
      self._segments.append({'name': lname, 'B': lB, 'E': lE, 'comp': lcomp, 'use': 1.0})
    self._recalc()

  def findSegment(self, start: str, stop: str = '') -> dict | None:
    '''Find the segment by start and stop nodes.

    Args:
      start (str): Start node name.
      stop (str): Stop node name.

    Returns:
      int: Index of the section or -1 if not found.
    '''
    if stop == '':
      split = start.split('-')
      if len(split) != 2:
        raise ValueError(f'Invalid segment name: {start}')
      else:
        start, stop = split
    segment = None
    for s in self._segments:
      if (s['B'] == start and s['E'] == stop):
        segment = s.copy()
        segment['idx'] = self._segments.index(s)
    if segment is None:
      for s in self._segments:
        if (s['B'] == start and s['E'] == stop) or (s['B'] == stop and s['E'] == start):
          segment = s.copy()
          segment['use'] = -1.0
          segment['idx'] = self._segments.index(s)
    return segment

  def findShortestPath(self, start: str, stop: str) -> Optional[list[str]]:
    '''Method to find the shortest path between two nodes of a graph.
       Algorithm for an unweighted undirected graph using Breadth-First Search (BFS).

    Args:
      start (str): Start node.
      stop (str): End node.

    Returns:
        Optional[list[str]]: Shortest path between 2 nodes.
    '''
    if start not in self._nodes or stop not in self._nodes:
      return None
    if start == stop:
      return [start, stop]
    explored = []
    # queue for traversing the graph in the BFS
    queue = [[start]]
    # loop to traverse the graph with the help of the queue
    while queue:
      path = queue.pop(0)
      node = path[-1]
      # check if the current node is not visited
      if node not in explored:
        neighbours = self._adjacency[node]
        # Loop to iterate over the neighbours of the node
        for neighbour in neighbours:
          new_path = list(path)
          new_path.append(neighbour)
          queue.append(new_path)
          # if the neighbour node is the goal then end
          if neighbour == stop:
            return new_path
        explored.append(node)
    # Condition when the nodes are not connected
    return None

  def segmentsFromNodes(self, nodes: list[str]=[]) -> Optional[list[str]]:
    '''Convert nodes to segments.

    Args:
      nodes (list): the input nodes.

    Returns:
      Optional[list]: List of segments or None if not applicable.
    '''
    lnodes = len(nodes)
    if lnodes < 2:
      return []
    segments = []
    for i in range(lnodes - 1):
      segments.append(f'{nodes[i]}-{nodes[i+1]}')
    #TODO: klopt dit? wanneer wel en waneer niet?
    if nodes[0] != nodes[lnodes-1]:
      segments.append(f'{nodes[lnodes-1]}-{nodes[0]}')
    return segments

  def segmentsFromAdjacency(self, node: str, adj: list[str]=[]) -> Optional[list[str]]:
    '''Convert nodes to segments.

    Args:
      node (str): the start node.
      adj (list): the adjacent nodes.

    Returns:
      Optional[list]: List of segments or None if not applicable.
    '''
    if adj == []:
      return []
    segments = []
    for a in adj:
      segments.append(f'{node}-{a}')
    return segments

  def calcNetwork(self, iguess = 1.0) -> None:
    '''  Resolve the network.

    Args:
        iguess (float | list, optional): The initial guess.
          This can be a float; then this value is used as start guess for all results.
          Can als be a list with the same number of elements as the final result.
          Defaults to 1.0.
    '''

    def F(x: list[float], args: dict[str, list]) -> list[float]:
      res = []
      for n in args['N']:
        res.append(sum(x[i] * n[i] for i in range(len(n))))
      for l in args['L']:
        res.append(sum(l[i]['d'] * l[i]['c'].calcH(x[i], 1).magnitude for i in range(len(l))))
      return res

    # Initial guess
    if isinstance(iguess, (int, float)):
      initial_guess = [iguess] * (len(self._funcs['N']) + len(self._funcs['L']))
    elif isinstance(iguess, list):
      if len(iguess) != (len(self._funcs['N']) + len(self._funcs['L'])):
        raise ValueError(f'Initial guess length {len(iguess)} does not match number of equations {len(self._funcs["N"]) + len(self._funcs["L"])}')
      initial_guess = iguess
    initial_guess = [iguess] * (len(self._funcs['N']) + len(self._funcs['L']))
    #print('initial_guess:', initial_guess)
    # Solve the system of equations
    FDEF = self._funcs
    result, self._infodict, ier, msg = fsolve(func=F, x0=initial_guess, args=FDEF, full_output=1)
    self._result = []
    if ier != 1:
      raise ValueError(f'Error in Network "{self._name}" calculation: {msg}')
    # process result
    n = len(self._segments)
    for i in range(n):
      Q = flsa.toUnits(result[i], u.m**3/u.h)
      self._result.append({'s':self._segments[i]['name'], 'Q': Q, 'H': self._segments[i]['comp'].calcH(Q, 1)})

  def _recalc(self) -> None:
    ''' Recalculate all graph properties.
    '''
    self._calcAdjacency()
    self._calcSpanningTree()
    self._calcAllCycles()
    self._calcSmallestCycleBase()
    self._calcFuncs()

  def _pathRotateToSmallest(self, path: list) -> list:
    ''' Rotate a path so it starts with the smallest node.

    Args:
        path (list): the source path

    Returns:
        list: the rotated path.
    '''
    min_index = path.index(min(path))
    return path[min_index:] + path[:min_index]

  def _pathInvert(self, path: list) -> list:
    ''' Invert the path order.

    Args:
        path (list): the source path

    Returns:
        list: The inverted path.
    '''
    return self._pathRotateToSmallest(path[::-1])

  def _calcAdjacency(self) -> None:
    ''' Create the list of adjacency nodes.
    '''
    self._adjacency = {}
    for s in self._segments:
      b = s['B']
      e = s['E']
      if b not in self._adjacency:
        self._adjacency[b] = []
      if e not in self._adjacency:
        self._adjacency[e] = []
      if e not in self._adjacency[b]:
        self._adjacency[b].append(e)
      if b not in self._adjacency[e]:
        self._adjacency[e].append(b)

  def _calcSpanningTree(self) -> None:
    ''' Create the spanning tree.
    '''
    self._spanningtree = []
    start = self._segments[0]['B']
    visited = []
    stack = [(start, None)]
    while stack:
      node, parent = stack.pop()
      if node in visited:
        continue
      visited.append(node)
      if parent is not None:
        self._spanningtree.append((min(node, parent), max(node, parent)))
      for neighbor in self._adjacency[node]:
        if neighbor not in visited:
          stack.append((neighbor, node))

  def _calcAllCycles(self) -> None:
    '''Find all simple cycles in the network.

    Returns:
      list[list[str]]: list with all cycles.
    '''

    def dfs(path: list[str], visited_edges: set) -> None:
      start_node = path[0]
      last_node = path[-1]
      edges = [(s['B'], s['E']) for s in self._segments]
      for node1, node2 in edges:
        if last_node in (node1, node2):
          next_node = node2 if node1 == last_node else node1
          edge = tuple(sorted((last_node, next_node)))
          if edge in visited_edges:
            continue
          if next_node not in path:
            visited_edges.add(edge)
            dfs(path + [next_node], visited_edges)
            visited_edges.remove(edge)
          elif len(path) > 2 and next_node == start_node:
            # Normalize cycle to start with smallest node
            cycle = self._pathRotateToSmallest(path[:])
            cycle.append(cycle[0])
            invcycle = self._pathInvert(cycle)
            if cycle not in self._allcycles and invcycle not in self._allcycles:
              self._allcycles.append(cycle)

    # no network
    if len(self._segments) < 2:
      self._allcycles = []
      return
    # special case: network = A-B, B-A
    if len(self._segments) == 2 and self._segments[0]['B'] == self._segments[1]['E'] and self._segments[0]['E'] == self._segments[1]['B']:
      self._allcycles = [[self._segments[0]['B'], self._segments[0]['E'], self._segments[0]['B']]]
      return
    # rest
    self._allcycles = []
    nodes = self._nodes
    for node in nodes:
      dfs([node], set())

  def _calcSmallestCycleBase(self) -> Optional[list]:
    ''' Find the smallest cycle base.

    Returns:
        Optional[list]: list with fundamental cycles.
    '''
    # no network
    if len(self._segments) < 2:
      self._fundamentalcycles = []
      return
    # special case: network = A-B, B-A
    if len(self._segments) == 2 and self._segments[0]['B'] == self._segments[1]['E'] and self._segments[0]['E'] == self._segments[1]['B']:
      self._fundamentalcycles = [[self._segments[0]['B'], self._segments[0]['E'], self._segments[0]['B']]]
      return
    # rest
    self._fundamentalcycles = []
    edges = [(s['B'], s['E']) for s in self._segments]
    tree_adj = {}
    for u, v in self._spanningtree:
      if u not in tree_adj:
        tree_adj[u] = []
      tree_adj[u].append(v)
      if v not in tree_adj:
        tree_adj[v] = []
      tree_adj[v].append(u)
    all_edges = [(min(u, v), max(u, v)) for u, v in edges]
    non_tree_edges = [x for x in all_edges if x not in self._spanningtree]
    for u, v in non_tree_edges:
      path = self._findPath(tree_adj, u, v)
      if path:
        cycle = path + [u]
        self._fundamentalcycles.append(cycle)

  def _findPath(self, tree: dict[str, list[str]], start: str, end: str, path: list[str]=[]) -> Optional[list[str]]:
    ''' Find a path in a graph using the adjacency tree.

    Args:
        tree (dict[str, list[str]]): adjacency tree to parse
        start (str): start node.
        end (str): end node.
        path (list[str], optional): the path being constructed. Defaults to [].

    Returns:
        Optional[list[str]]: the resulting path.
    '''
    path = path + [start]
    if start == end:
      return path
    for node in tree[start]:
      if node not in path:
        newpath = self._findPath(tree, node, end, path)
        if newpath:
          return newpath
    return None

  def _calcFuncs(self) -> None:
    ''' Update the system of functions to do the final calculations.
    '''
    self._funcs = {'N': [], 'L': []}
    # nodes
    adj = self.Adjacency
    if len(adj) == 0:
      return
    for key, value in adj.items():
      equation = np.array([0.0] * len(self._segments))
      adjsegment = self.segmentsFromAdjacency(key, value)
      for s in adjsegment:
        segment = self.findSegment(s)
        if segment is None:
          # TODO better error handling
          raise ValueError(f'Segment {key} to {value} not found in graph')
        equation[segment['idx']] = segment['use']
      self._funcs['N'].append(equation)
    # cycles
    cycl = self.FundamentalCycles
    if len(cycl) == 0:
      return
    for c in cycl:
      equation = []
      for s in self._segments:
        equation.append({'s': f'({s["name"]})', 'c': flsc.Comp_Dummy(), 'd': 0.0})
      nsegment = self.segmentsFromNodes(c)
      if len(nsegment) == 0 :
        # TODO better error handling
        raise ValueError(f'Segment for cycle {c} not found in graph')
      for s in nsegment:
        segment = self.findSegment(s)
        if segment is None:
          # TODO better error handling
          raise ValueError(f'Segment {s} not found in graph')
        equation[segment['idx']] = {'s': s, 'c': segment['comp'], 'd': segment['use']}
      self._funcs['L'].append(equation)

  def __str__(self) -> str:
    ''' String representation

    Returns:
        str: String representation
    '''
    return self.to_string(detail=False)

  def toString(self, detail: int=0) -> str:
    ''' String representation. Can be in more or less detail.

    Args:
        detail (int, optional): The details to be returned. Defaults to 0.

    Returns:
        str: String representation
    '''
    txt = f'Network'
    txt += f'\n  Nodes:\n    {self._nodes}'
    txt += '\n  Segments:\n    ' + '\n    '.join([str(i) for i in self._segments])
    if detail:
      txt += '\n  Edges:\n    ' + '\n    '.join([str(i) for i in self.Edges])
      txt += '\n  Adjacency:\n    ' + '\n    '.join([str(i) for i in self._adjacency.items()])
      txt += '\n  SpanningTree:\n    ' + '\n    '.join([str(i) for i in self._spanningtree])
      txt += '\n  FundamentalCycles:\n    ' + '\n    '.join([str(i) for i in self._fundamentalcycles])
    txt += 'Functions:\n'
    txt += '  N:\n'
    for n in self._funcs['N']:
      txt += '    ' + str(n) + '\n'
    txt += '  L:\n'
    for l in self._funcs['L']:
      for i in l:
        txt += f'    {i}\n'
      txt += '\n'
    return txt

  def __repr__(self) -> str:
    ''' Class representation.

    Returns:
        str: class representation
    '''
    segs = [(s["B"], s["E"], s["comp"]) for s in self._segments]
    return f'Graph({segs!r})'
