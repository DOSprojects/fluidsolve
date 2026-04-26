'''
Hydraulic network solver using graph topology plus component physics.

This module represents a hydraulic system as a graph:

* nodes are connection points,
* segments (edges) are component port-to-port links,
* a spanning tree and chord set define fundamental cycles.

The solver assembles a nonlinear system from two equation groups:

* node continuity equations, assembled in matrix B,
* loop energy equations, assembled in matrix C using component head laws.

Unknowns are segment flow rates. Component physics is delegated to each
component through calcH(Q, sense). The network module is responsible for
topology construction, incidence matrices, validation, and numerical solve.

Internal data artifacts exposed by the class include:

* ``Segments``: per-segment dictionaries with node endpoints, sense, ports,
  and owning component,
* ``Nodes`` / ``Edges``: graph-level views used by solvers and diagnostics,
* ``Adjacency`` and ``SpanningTree``: traversal structures used for cycle
  basis generation,
* ``FundamentalCycles``: loop basis used for energy equations,
* ``Funcs``: assembled ``B`` and ``C`` matrices,
* ``Result``: solved per-segment flow/head values.

Assumptions and conventions:

* the topology should form a connected graph,
* each component defines ports and usable internal connections,
* segment direction and sense are tracked explicitly,
* energy sources and resistances are validated per loop before solve.

Solve pipeline summary:

1. Register components and expand them into graph segments.
2. Build adjacency, spanning tree, and fundamental cycle basis.
3. Assemble incidence matrices ``B`` and ``C``.
4. Solve flow unknowns with Newton-Raphson.
5. Back-calculate and store per-segment ``Q`` and ``H`` results.

Typical workflow::

  net = getNetwork(name='N1', components=[...])
  result = net.calcNetwork()
  print(net.toString(detail=1))

This design keeps topology logic centralized while allowing each component
class to own its physical constitutive behavior.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================

# =============================================================================
# IMPORTS
# =============================================================================
from typing import Any
import warnings
import numpy as np
from scipy.optimize import root
# module own
import fluidsolve.medium      as flsme
import fluidsolve.aux_tools   as flsa
import fluidsolve.comp_base   as flsb
# units
u         = flsme.unitRegistry
Quantity  = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# NETWORK CLASS
# =============================================================================
class Network:
  ''' Class representing a hydraulic network.

  Args:
    name (str, optional): Network label.
    components (list, optional): Initial list of components to register.
  '''
  # --------------------------------------------------------------------------
  # FIXED PROPERTIES

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> None:
    # arguments
    args_in = flsa.GetArgs(kwargs)
    self._name: str = args_in.getArg(
      'name',
      [
        flsa.vFun.default(''),
        flsa.vFun.istype(str),
      ]
    )
    components: list = args_in.getArg(
      'components',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(list),
      ]
    )
    args_in.isEmpty()
    # instance vars
    self._components        : list = []
    self._segments          : dict = {}
    self._nodes             : list = []
    self._adjacency         : dict = {}
    self._spanningtree      : list = []
    self._fundamentalcycles : list = []
    self._allcycles         : list = []
    self._funcs             : dict = {'B': np.empty((0, 0)), 'C': np.empty((0, 0))}
    self._result            : list = []
    # some calculations
    self.addComponents(components)
    self._infodict = {}

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def components(self) -> Any:
    ''' Ordered list of components. '''
    return self._components

  @property
  def segments(self) -> dict[str, dict]:
    ''' Return the segments of the network.

    Returns:
      list[dict]: Segment dictionary.
    '''
    return self._segments

  @property
  def nodes(self) -> tuple[str, ...]:
    ''' Return the nodes in this network.

    Returns:
      list[str]: Node list.
    '''
    return self._nodes

  @property
  def edges(self) -> list[tuple[str, str]]:
    ''' Return the edges in this network.

    Returns:
      list[tuple[str, str]]: Edge list.
    '''
    return list(self._segments.keys())

  @property
  def adjacency(self) -> dict[str, list[str]]:
    ''' Return the adjacency list.

    Returns:
      dict[str, list[str]]: Adjacency list.
    '''
    return self._adjacency

  @property
  def spanningTree(self) -> list[tuple[str, str]]:
    ''' Return the spanning tree.

    Returns:
      list[tuple[str, str]]: Spanning tree.
    '''
    return self._spanningtree

  @property
  def fundamentalCycles(self) -> list[list[str]]:
    ''' Return fundamental cycles in the graph.

    Returns:
      list[list[str]]: Fundamental cycles.
    '''
    return self._fundamentalcycles

  @property
  def funcs(self) -> dict[str, list]:
    ''' Return the incidence matrices used to build the system of equations.

    Returns:
      dict[str, list]: B and C matrices.
    '''
    return self._funcs

  @property
  def result(self) -> list[dict]:
    ''' Return the solver result.

    Returns:
      list[dict]: Per segment: name, Q, and H.
    '''
    return self._result

  #----------------------------------------------------------------------------
  # METHODS
  def addComponents(self, components: list) -> None:
    ''' Add components to the network and rebuild the graph.

    Args:
      components (list): List of component dicts with keys ``comp``, ``nodes``, and optional ``sense``.
    '''
    for item in components:
      if not isinstance(item, dict):
        raise ValueError(f'Invalid component entry: {item}')
      if 'comp' not in item or 'nodes' not in item:
        raise ValueError(f'Component entry must contain "comp" and "nodes": {item}')
      nodes = item['nodes']
      sense = item.get('sense', +1)
      comp = item['comp']
      if len(nodes) != comp.nports:
        raise ValueError(f'Node count {len(nodes)} does not match component ports {comp.nports}')
      if sense not in (+1, -1):
        raise ValueError(f'sense must be +1 or -1, got {sense}')
      if not isinstance(comp, flsb.Comp_Base):
        raise ValueError(f'Unknown component: {comp}')
      if not isinstance(nodes, (list, tuple)):
        raise ValueError(f'Invalid nodes: {nodes}')
      self._components.append({'nodes': list(nodes), 'sense': sense, 'comp': comp,  })
    self._recalc()

  def calcNetwork(self, guess: Any=None) -> Any:
    ''' Solve the network using Newton-Raphson.

    Args:
      guess (float, list, tuple, or np.ndarray, optional): Initial flow guess for all segments.

    Returns:
      list[dict]: Per segment: name, Q, and H.
    '''

    # Rebuild topology and equation matrices to reflect runtime state changes
    # of components like multi-way valves.
    self._recalc()

    def F(x: Any) -> Any:
      Q = np.asarray(x)
      res = []
      # Node continuity equations: B @ Q = 0
      if B.shape[0] > 1:
        res.extend((B @ Q)[:-1])
      # Loop energy equations: C @ H(Q) = 0
      if C.shape[0] > 0:
        H = np.zeros(nseg)
        for i, key in enumerate(seg_keys):
          seg = self._segments[key]
          comp = seg['comp']
          H[i] = comp.calcH(Q[i] * u.m**3 / u.h, seg['sense'], seg['pB'], seg['pE']).magnitude
        res.extend(C @ H)
      return res

    B = np.asarray(self._funcs['B'])    # (n_nodes, n_segments)
    C = np.asarray(self._funcs['C'])    # (n_loops, n_segments)
    seg_keys = self._usedSegmentKeys()
    nseg = len(seg_keys)
    neq = max(B.shape[0] - 1, 0) + C.shape[0]
    if nseg != neq:
      raise ValueError(f'Inconsistent equation system: {nseg} unknown flows but {neq} equations')
    if guess is None:
      guess_list = [0.5, 2.0, 10.0, 50.0, 200.0]
    elif isinstance(guess, (list, tuple, np.ndarray)):
      guess_list = [float(item) for item in guess]
    else:
      guess_list = [float(guess)]
    x0_list = [np.full(nseg, g, dtype=float) for g in guess_list]
    err_msg = f'Network {self._name} solve did not converge.'
    sol = None
    methods = ('hybr', 'lm', 'df-sane')
    # Try each method for each initial guess until a finite solution is found.
    for x0 in x0_list:
      for method in methods:
        root_res = root(F, x0=x0, method=method)
        self._infodict = {'solver': f'root:{method}', 'result': root_res}
        if root_res.success:
          result_arr = np.asarray(root_res.x, dtype=float)
          if np.all(np.isfinite(result_arr)):
            sol = result_arr
            break
          err_msg = f'Network {self._name} solve invalid root Q={result_arr}'
          continue
        root_msg = str(root_res.message)
        if root_msg:
          err_msg = f'Network {self._name} solve [{method}] failed: {root_msg}'
        else:
          err_msg = f'Network {self._name} solve [{method}] failed with status={root_res.status}'
      if sol is not None:
        break
    if sol is None:
      self._result = [{'segment': key, 'Q': 0.0 * u.m**3 / u.h, 'H': 0.0 * u.m} for key in seg_keys]
      warnings.warn(err_msg, RuntimeWarning, stacklevel=1)
      return self._result
    self._result = []
    for i, key in enumerate(seg_keys):
      Q = sol[i] * u.m**3 / u.h
      seg = self._segments[key]
      H = seg['comp'].calcH(Q, seg['sense'], seg['pB'], seg['pE'])
      self._result.append({'segment': key, 'Q': Q, 'H': H})
    return self._result

  #----------------------------------------------------------------------------
  # GRAPH BUILDING
  def _recalc(self) -> None:
    ''' Rebuild the full graph representation after component changes. '''
    self._calcSegments()
    self._calcAdjacency()
    self._calcSpanningTree()
    self._calcSmallestCycleBase()
    self._calcValidation()
    self._calcFuncs()

  def _usedSegmentKeys(self) -> list[str]:
    ''' Return segment keys enabled for calculation. '''
    return [key for key, seg in self._segments.items() if seg.get('use', True)]

  def _calcSegments(self) -> None:
    ''' Build segment dictionary from component port definitions. '''
    nodeset = set()
    self._segments = {}
    for item in self._components:
      nodes = item['nodes']
      sense = item['sense']
      comp = item['comp']
      nodeset.update(nodes)
      active_ports = {tuple(conn) for conn in comp.connections(getattr(comp, 'state', None))}
      for port_begin, port_end in comp.ports:
        port_pair = (port_begin, port_end)
        node_begin = nodes[port_begin - 1]
        node_end = nodes[port_end - 1]
        key = f'{comp.name}:{node_begin}-{node_end}'
        if key in self._segments:
          raise ValueError(f'Duplicate segment {key}')
        self._segments[key] = {'use': port_pair in active_ports, 'B': node_begin, 'E': node_end, 'sense': sense, 'pB': port_begin, 'pE': port_end, 'comp': comp, 'name': key}
    self._nodes = tuple(sorted(nodeset))

  def _calcAdjacency(self) -> None:
    ''' Build an adjacency list including flow sense. '''
    self._adjacency = {}
    for key, seg in self._segments.items():
      if not seg.get('use', True):
        continue
      B = seg['B']
      E = seg['E']
      sense = seg['sense']
      self._adjacency.setdefault(B, []).append((key, E, sense))
      self._adjacency.setdefault(E, []).append((key, B, -sense))

  def _calcSpanningTree(self) -> None:
    ''' Compute the spanning tree using depth-first search. '''

    def dfs(start_node: Any) -> Any:
      visited.add(start_node)
      for key, next_node, sense in self._adjacency.get(start_node, []):
        if next_node not in visited:
          self._spanningtree.append((key, start_node, next_node, sense))
          dfs(next_node)

    self._spanningtree = []
    visited = set()
    if self._nodes:
      dfs(self._nodes[0])


  def _calcSmallestCycleBase(self) -> Any:
    ''' Build a fundamental cycle basis from spanning-tree chords.

    Returns:
      None
    '''

    def dfs(node_current: Any, node_target: Any, visited: Any) -> Any:
      if node_current == node_target:
        return []
      visited.add(node_current)
      for seg_key, node_next, _ in self._adjacency.get(node_current, []):
        if seg_key not in tree_keys:
          continue  # Only follow tree edges.
        if node_next in visited:
          continue
        result = dfs(node_next, node_target, visited)
        if result is not None:
          seg = self._segments[seg_key]
          if seg['sense'] > 0:
            return [(seg_key, seg['B'], seg['E'], 1)] + result
          else:
            return [(seg_key, seg['E'], seg['B'], 1)] + result
      return None

    # Set of tree segment keys for fast lookup
    tree_keys = {k for k, _, _, _ in self._spanningtree}
    self._fundamentalcycles = []
    # Each chord (non-tree edge) defines one fundamental cycle.
    for seg_key in self._usedSegmentKeys():
      seg = self._segments[seg_key]
      if seg_key in tree_keys:
        continue  # Skip tree edges; process chords only.
      node_start = seg['B']
      node_end = seg['E']
      sense = seg['sense']
      path = dfs(node_start, node_end, set())
      if not path:
        continue
      # Closing chord (always added explicitly)
      if sense > 0:
        cycle = path + [(seg_key, node_start, node_end, 1)]
      else:
        cycle = path + [(seg_key, node_end, node_start, 1)]
      self._fundamentalcycles.append(self._sortCycle(cycle))

  def _calcValidation(self) -> None:
    ''' Validate fundamental loop equations.

    Raises ValueError when a loop is physically invalid.
    '''
    txt = ''
    if not self._fundamentalcycles:
      return 'Empty'
    has_source = any(seg['comp'].isSource for seg in self._segments.values() if seg.get('use', True))
    if not has_source:
      raise ValueError('Network has no energy source (no pump / pressure source present)')
    for li, loop in enumerate(self._fundamentalcycles):
      seen = set()
      has_resistance = False
      txt += f'Loop {li + 1}:\n'
      for seg_key, B, E, sense in loop:
        if seg_key in seen:
          raise ValueError(f'Loop {li + 1}: segment "{seg_key}" appears more than once')
        seen.add(seg_key)
        if sense not in (-1, +1):
          raise ValueError(f'Loop {li + 1}: segment "{seg_key}" : invalid sense {sense}')
        comp = self._segments[seg_key]['comp']
        if comp.sign > 0:
          txt += f'  {"+" if sense > 0 else "-"} {comp.name} ({B} → {E}) [Power]\n'  # pylint: disable=inconsistent-quotes
        if comp.sign < 0:
          has_resistance = True
          txt += f'  {"+" if sense > 0 else "-"} {comp.name} ({B} → {E}) [Resist]\n'  # pylint: disable=inconsistent-quotes
      if not has_resistance:
        raise ValueError(f'Loop {li + 1}: no resistance in loop (singular energy equation)')
    return txt + '\n'

  def _calcFuncs(self) -> None:
    ''' Build B (node continuity) and C (loop energy) incidence matrices. '''
    self._funcs = {'B': None, 'C': None}
    # B matrix
    nodes = list(self._nodes)
    seg_keys = self._usedSegmentKeys()
    B = np.zeros((len(nodes), len(seg_keys)))
    for j, key in enumerate(seg_keys):
      seg = self._segments[key]
      B[nodes.index(seg['B']), j] = -1
      B[nodes.index(seg['E']), j] = +1
    self._funcs['B'] = B
    # C matrix
    C = np.zeros((len(self._fundamentalcycles), len(seg_keys)))
    for i, loop in enumerate(self._fundamentalcycles):
      for seg_key, _, _, sense in loop:
        C[i, seg_keys.index(seg_key)] = sense
    self._funcs['C'] = C
    #print(self.format_BC_matrix())

  #----------------------------------------------------------------------------
  # PATH UTILITIES
  def _sortCycle(self, cycle: list[list[tuple]]) -> list[list[tuple]]:
    ''' Sort a cycle so it starts from the smallest node deterministically. '''
    adj = {}
    for comp in cycle:
      adj.setdefault(comp[1], []).append(comp)
    # deterministic ordering
    for edges in adj.values():
      edges.sort(key=lambda c: c[2])
    # alphabetically smallest start node
    start_node = min(adj)
    stack = [start_node]
    edge_stack = []
    result = []
    while stack:
      node = stack[-1]
      if node in adj and adj[node]:
        comp = adj[node].pop(0)
        stack.append(comp[2])
        edge_stack.append(comp)
      else:
        stack.pop()
        if edge_stack:
          result.append(edge_stack.pop())
    sortedlist = list(reversed(result))
    # rotate so that smallest (start, end) edge is first
    min_index = min(range(len(sortedlist)), key=lambda i: (sortedlist[i][1], sortedlist[i][2]))
    return sortedlist[min_index:] + sortedlist[:min_index]

  #----------------------------------------------------------------------------
  # REPRESENTATION
  def __str__(self) -> str:
    ''' Return a compact string representation.

    Returns:
      str: Compact network summary.
    '''
    return self.toString(detail=0)

  def toString(self, detail: int = 0) -> str:
    ''' Return a formatted multi-line network description.

    Args:
      detail (int, optional): Include topology and matrix details when non-zero.

    Returns:
      str: Formatted network text.
    '''
    txt = f'Network "{self._name}":\n'
    txt += self.nodeString() + '\n'
    txt += self.segmentsString() + '\n'
    if detail:
      txt += self.adjacencyString() + '\n'
      txt += self.spanningTreeString() + '\n'
      txt += self.fundamentalCyclesString() + '\n'
      txt += self.functionString() + '\n'
    txt += self.resultString() + '\n'
    return txt

  def nodeString(self) -> str:
    ''' Format the node list for display.

    Returns:
      str: Node section text.
    '''
    txt = f' Nodes ({len(self._nodes)}):\n'
    if not self._nodes:
      txt += '  ---\n'
    else:
      txt += '   ' + ', '.join(str(node) for node in self._nodes) + '\n'
    return txt

  def segmentsString(self) -> str:
    ''' Format the segment table for display.

    Returns:
      str: Segment section text.
    '''
    txt = f' Segments ({len(self._segments)}):\n'
    if not self._segments:
      txt += '  ---\n'
    else:
      key_w = max(6, max(len(key) for key in self._segments))
      type_w = max(16, max(len(seg['comp'].__class__.__name__) for seg in self._segments.values()))
      dir_w = max(7,
        max(
          len(f"{seg['B']} → {seg['E']}") if seg['sense'] > 0 else len(f"({seg['B']} ← {seg['E']})")
          for seg in self._segments.values()
        )
      )
      ports_w = max(5, max(len(f"{seg['pB']} → {seg['pE']}") for seg in self._segments.values()))
      header = f'{"comp":<{key_w}} | {"nodes":<{dir_w}} | {"type":<{type_w}} | {"ports":<{ports_w}}'  # pylint: disable=inconsistent-quotes
      txt += f'   {header}\n'
      txt += f'   {"-" * len(header)}\n'  # pylint: disable=inconsistent-quotes
      for key, seg in self._segments.items():
        comp = seg['comp']
        comp_type = comp.__class__.__name__
        is_used = seg.get('use', True)
        if seg['sense'] > 0:
          dir_txt = f'{seg["B"]} → {seg["E"]}'  # pylint: disable=inconsistent-quotes
        else:
          dir_txt = f'({seg["B"]} ← {seg["E"]})'  # pylint: disable=inconsistent-quotes
        ports_txt = f'{seg["pB"]} → {seg["pE"]}'  # pylint: disable=inconsistent-quotes
        line = f'{key:<{key_w}} | {dir_txt:<{dir_w}} | {comp_type:<{type_w}} | {ports_txt:<{ports_w}}'
        if not is_used:
          line = f'[[ {line} ]]'
          txt += f'{line}\n'
        else:
          txt += f'   {line}\n'
    return txt

  def adjacencyString(self) -> str:
    ''' Format the adjacency list for display.

    Returns:
      str: Adjacency section text.
    '''
    txt = f' Adjacency ({len(self._adjacency)}):\n'
    if not self._adjacency:
      txt += '  ---\n'
    else:
      node_w = max(4, max(len(str(node)) for node in self._adjacency))
      seg_w = max(7, max(len(key) for entries in self._adjacency.values() for key, _, _ in entries))
      node_to_w = max(1, max(len(str(node_to)) for entries in self._adjacency.values() for _, node_to, _ in entries))
      link_template = f' {{:<{seg_w}}} -> {{:<{node_to_w}}} ({{:+d}}) '
      links_w = max(len(', '.join(link_template.format(seg_key, node_to, sense) for seg_key, node_to, sense in entries)) for entries in self._adjacency.values())
      header = f"{'node':<{node_w}} | {'links':<{links_w}}"
      txt += f'   {header}\n'
      txt += f'   {"-" * len(header)}\n'  # pylint: disable=inconsistent-quotes
      for node, entries in self._adjacency.items():
        links = ', '.join(link_template.format(seg_key, node_to, sense) for seg_key, node_to, sense in entries)
        txt += f'   {node:<{node_w}} | {links}\n'
    return txt

  def spanningTreeString(self) -> str:
    ''' Format the spanning tree for display.

    Returns:
      str: Spanning tree section text.
    '''
    txt = ' SpanningTree ({len(self._spanningtree)}):\n'
    if not self._spanningtree:
      txt += '  ---\n'
    else:
      seg_w = max(7, max(len(key) for key, _, _, _ in self._spanningtree))
      node_w = max(1, max(len(str(node)) for _, node_a, node_b, _ in self._spanningtree for node in (node_a, node_b)))
      header = f"{'segment':<{seg_w}} | {'path':<{node_w * 2 + 4}} | {'sense':<8}"
      txt += f'   {header}\n'
      txt += f'   {"-" * len(header)}\n'  # pylint: disable=inconsistent-quotes
      for seg_key, node_from, node_to, sense in self._spanningtree:
        txt += f'   {seg_key:<{seg_w}} | {node_from:<{node_w}} -> {node_to:<{node_w}} | {sense:+d}\n'
    return txt

  def fundamentalCyclesString(self) -> str:
    ''' Format the fundamental cycle basis for display.

    Returns:
      str: Fundamental cycle section text.
    '''
    txt = f' FundamentalCycles ({len(self._fundamentalcycles)}):\n'
    if not self._fundamentalcycles:
      txt += '  ---\n'
    else:
      seg_w = max(7, max(len(seg_key) for cycle in self._fundamentalcycles for seg_key, _, _, _ in cycle))
      node_w = max(1, max(len(str(node)) for cycle in self._fundamentalcycles for _, node_a, node_b, _ in cycle for node in (node_a, node_b)))
      for idx, cycle in enumerate(self._fundamentalcycles, start=1):
        txt += f'   Loop {idx}:\n'
        header = f"{'segment':<{seg_w}} | {'path':<{node_w * 2 + 4}} | {'sense':<8}"
        txt += f'      {header}\n'
        txt += f'      {"-" * len(header)}\n'  # pylint: disable=inconsistent-quotes
        for seg_key, node_from, node_to, sense in cycle:
          txt += f'      {seg_key:<{seg_w}} | {node_from:<{node_w}} -> {node_to:<{node_w}} | {sense:+d}\n'
    return txt

  def functionString(self) -> str:
    ''' Format incidence matrices B and C for display.

    Returns:
      str: Matrix section text.
    '''

    B = self._funcs.get('B')
    C = self._funcs.get('C')
    txt = f' Functions: Combined incidence matrix (B:{len(B)}) (C:{len(C)}):\n'
    if B is None or C is None:
      txt += '  B/C matrices not initialized\n'
    nodes = list(self._nodes)
    seg_keys = self._usedSegmentKeys()
    if not seg_keys:
      txt += '  No segments in network\n'
    else:
      # Column width (adaptive)
      w = max(8, max(len(k) for k in seg_keys) + 2)
      header = '    B (Node cont) | ' + ' | '.join(f'{k:^{w}}' for k in seg_keys) + '\n'
      sep = '    ' + '-' * len(header) + '\n'
      txt += header + sep
      # --- B block
      for i, node in enumerate(nodes):
        txt += f'    {node:<13} | ' + ' | '.join(f'{int(B[i, j]):^{w}}' for j in range(len(seg_keys))) + '\n'
      txt += sep
      # --- C block
      txt += '    C (Loop ener) | ' + ' | '.join(f'{k:^{w}}' for k in seg_keys) + '\n'
      txt += sep
      if C.shape[0] == 0:
        txt += '    <no loops>\n'
      else:
        for i in range(C.shape[0]):
          txt += f'    L{i+1:<12} | ' + ' | '.join(f'{int(C[i, j]):^{w}}' for j in range(len(seg_keys))) + '\n'
    return txt

  def resultString(self) -> str:
    ''' Format the solved flow/head results table.

    Returns:
      str: Result section text.
    '''
    txt = ' Result:\n'
    if not self._result:
      txt += '   not yet calculated\n'
    else:
      seg_w = max(8, max(len(str(item['segment'])) for item in self._result) + 2)
      nodes_w = max(
        5,
        max(
          len(f'{seg["B"]} → {seg["E"]}') if seg['sense'] > 0 else len(f'({seg["B"]} ← {seg["E"]})')  # pylint: disable=inconsistent-quotes
          for seg in self._segments.values()
        )
      )
      comp_w = 16
      header = f'{"Segment":<{seg_w}} | {"Nodes":<{nodes_w}} | {"Component":<{comp_w}} |          Q      |       H  \n'  # pylint: disable=inconsistent-quotes
      txt += '   ' + header + f'   {"-" * len(header)}\n'  # pylint: disable=inconsistent-quotes
      for item in self._result:
        seg_key = item['segment']
        seg = self._segments.get(seg_key, {})
        comp = seg.get('comp', None)
        comp_name = getattr(comp, 'name', '-') if comp is not None else '-'
        if seg:
          if seg['sense'] > 0:
            nodes_txt = f"{seg['B']} → {seg['E']}"
          else:
            nodes_txt = f"({seg['B']} ← {seg['E']})"
        else:
          nodes_txt = '-'
        txt += f'   {seg_key:<{seg_w}} | {nodes_txt:<{nodes_w}} | {comp_name:<{comp_w}} | {item["Q"]:>10.2g~P} | {item["H"]:>7.2g~P}\n'  # pylint: disable=inconsistent-quotes
    return txt

  def networkValidationtoString(self) -> str:
    ''' Return the validation report for fundamental cycles.

    Returns:
      str: Validation report.
    '''
    return self._calcValidation()
