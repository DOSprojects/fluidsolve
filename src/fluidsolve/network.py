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
  result = net.calcNetwork(iguess=1.0)
  print(net.toString(detail=1))

This design keeps topology logic centralized while allowing each component
class to own its physical constitutive behavior.
'''
# =============================================================================
# IMPORTS
# =============================================================================
from typing import Optional, Any
import numpy as np
from scipy.optimize import fsolve
# module own
import fluidsolve.medium      as flsme
import fluidsolve.aux_tools   as flsa
import fluidsolve.comp_base   as flsb
import fluidsolve.comp_resist as flsc
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
    self._funcs             : dict = {'B': [], 'C': []}
    self._result            : list = []
    # some calculations
    self.addComponents(components)

  # --------------------------------------------------------------------------
  # PROPERTIES
  @property
  def Segments(self) -> list[dict]:
    ''' Return the segments of the network.

    Returns:
      list[dict]: Segment dictionary.
    '''
    return self._segments

  @property
  def Nodes(self) -> list[str]:
    ''' Return the nodes in this network.

    Returns:
      list[str]: Node list.
    '''
    return self._nodes

  @property
  def Edges(self) -> list[tuple[str, str]]:
    ''' Return the edges in this network.

    Returns:
      list[tuple[str, str]]: Edge list.
    '''
    return list(self._segments.keys())

  @property
  def Adjacency(self) -> dict[str, list[str]]:
    ''' Return the adjacency list.

    Returns:
      dict[str, list[str]]: Adjacency list.
    '''
    return self._adjacency

  @property
  def SpanningTree(self) -> list[tuple[str, str]]:
    ''' Return the spanning tree.

    Returns:
      list[tuple[str, str]]: Spanning tree.
    '''
    return self._spanningtree

  @property
  def FundamentalCycles(self) -> list[list[str]]:
    ''' Return fundamental cycles in the graph.

    Returns:
      list[list[str]]: Fundamental cycles.
    '''
    return self._fundamentalcycles

  @property
  def Funcs(self) -> dict[str, list]:
    ''' Return the incidence matrices used to build the system of equations.

    Returns:
      dict[str, list]: B and C matrices.
    '''
    return self._funcs

  @property
  def Result(self) -> list[dict]:
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

  def calcNetwork(self, iguess: Any=1.0) -> Any:
    ''' Solve the network using Newton-Raphson.

    Args:
      iguess (float): Initial flow guess for all segments.

    Returns:
      list[dict]: Per segment: name, Q, and H.
    '''

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
              comp = self._segments[key]['comp']
              H[i] = comp.calcH(Q[i] * u.m**3 / u.h, +1).magnitude
          res.extend(C @ H)
      return res

    B = self._funcs['B']    # (n_nodes, n_segments)
    C = self._funcs['C']    # (n_loops, n_segments)
    seg_keys = list(self._segments.keys())
    nseg = len(seg_keys)
    neq = max(B.shape[0] - 1, 0) + C.shape[0]
    if nseg != neq:
      raise ValueError(f'Inconsistent equation system: {nseg} unknown flows but {neq} equations')
    x0 = np.full(nseg, iguess)
    sol, _, ier, msg = fsolve(F, x0, full_output=True)
    if ier != 1:
        raise ValueError(msg)
    self._result = []
    for i, key in enumerate(seg_keys):
        Q = sol[i] * u.m**3 / u.h
        H = self._segments[key]['comp'].calcH(Q, +1)
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

  def _calcSegments(self) -> None:
    ''' Build segment dictionary from component port definitions. '''
    nodeset = set()
    self._segments = {}
    for item in self._components:
      nodes = item['nodes']
      sense = item['sense']
      comp = item['comp']
      nodeset.update(nodes)
      for port_begin, port_end in comp.ports:
        node_begin = nodes[port_begin - 1]
        node_end = nodes[port_end - 1]
        key = f'{comp.name}:{node_begin}->{node_end}'
        if key in self._segments:
          raise ValueError(f'Duplicate segment {key}')
        self._segments[key] = {'B': node_begin, 'E': node_end, 'sense': sense, 'pB': port_begin, 'pE': port_end, 'comp': comp, 'name': key}
    self._nodes = tuple(sorted(nodeset))

  def _calcAdjacency(self) -> None:
    ''' Build an adjacency list including flow sense. '''
    self._adjacency = {}
    for key, seg in self._segments.items():
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
      for seg_key, node_next, sense in self._adjacency.get(node_current, []):
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
    for seg_key, seg in self._segments.items():
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
    has_source = any(seg['comp'].sign > 0 for seg in self._segments.values())
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
          txt += f'  {"+" if sense > 0 else "-"} {comp.name} ({B} → {E}) [Power]\n'
        if comp.sign < 0:
          has_resistance = True
          txt += f'  {"+" if sense > 0 else "-"} {comp.name} ({B} → {E}) [Resist]\n'
      if not has_resistance:
        raise ValueError(f'Loop {li + 1}: no resistance in loop (singular energy equation)')
    return txt + '\n'

  def _calcFuncs(self) -> None:
    ''' Build B (node continuity) and C (loop energy) incidence matrices. '''
    self._funcs = {'B': None, 'C': None}
    # B matrix
    nodes = list(self._nodes)
    seg_keys = list(self._segments.keys())
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
    txt = f'Network "{self._name}"\n'
    txt += ' Nodes:\n'
    txt += self.nodeString()
    txt += ' Segments:\n'
    txt += self.segmentsString()
    if detail:
      txt += ' Adjacency:\n'
      for n, a in self._adjacency.items():
        txt += f'   {n} -> {a}\n'
      txt += ' SpanningTree:\n'
      for s in self._spanningtree:
        txt += f'   {s}\n'
      txt += ' FundamentalCycles:\n'
      for c in self._fundamentalcycles:
        txt += f'   {c}\n'
      txt += ' Functions: Combined incidence matrix [B; C]:\n'
      txt += self.functionString()
    txt += ' Result:\n'
    txt += self.resultString()
    return txt

  def nodeString(self) -> str:
    ''' Format the node list for display.

    Returns:
      str: Node section text.
    '''
    if not self._nodes:
      return '   <none>\n'
    node_w = max(4, max(len(str(node)) for node in self._nodes))
    txt = ''
    for i, node in enumerate(self._nodes, start=1):
      txt += f'   [{i:>2}] {str(node):<{node_w}}\n'
    return txt

  def segmentsString(self) -> str:
    ''' Format the segment table for display.

    Returns:
      str: Segment section text.
    '''
    if not self._segments:
      return '   <none>\n\n'
    key_w = max(12, max(len(key) for key in self._segments) + 1)
    comp_w = max(10, max(len(getattr(seg['comp'], 'name', seg['comp'].__class__.__name__)) for seg in self._segments.values()))
    type_w = max(10, max(len(seg['comp'].__class__.__name__) for seg in self._segments.values()))
    dir_w = max(
      9,
      max(
        len(f"{seg['B']} → {seg['E']}") if seg['sense'] > 0 else len(f"({seg['B']} ← {seg['E']})")
        for seg in self._segments.values()
      )
    )
    txt = ''
    for key, seg in self._segments.items():
      comp = seg['comp']
      comp_name = getattr(comp, 'name', comp.__class__.__name__)
      comp_type = comp.__class__.__name__
      if seg['sense'] > 0:
        dir_txt = f"{seg['B']} → {seg['E']}"
      else:
        dir_txt = f"({seg['B']} ← {seg['E']})"
      txt += (
        f"   [{key:<{key_w}}] "
        f"{dir_txt:<{dir_w}} : "
        f"{comp_name:<{comp_w}} ({comp_type:<{type_w}}) "
        f"ports: {seg['pB']} → {seg['pE']}\n"
      )
    return txt + "\n"

  def functionString(self) -> str:
    ''' Format incidence matrices B and C for display.

    Returns:
      str: Matrix section text.
    '''
    B = self._funcs.get('B')
    C = self._funcs.get('C')
    if B is None or C is None:
      return 'B/C matrices not initialized\n'
    nodes = list(self._nodes)
    seg_keys = list(self._segments.keys())
    if not seg_keys:
      return 'No segments in network\n'
    # Column width (adaptive)
    w = max(10, max(len(k) for k in seg_keys) + 2)
    header = '    Row \\ Seg'.ljust(12) + ' | ' + ' | '.join(f'{k:^{w}}' for k in seg_keys) + '\n'
    sep = '    ' + '-' * len(header) + '\n'
    txt = header + sep
    # --- B block
    txt += 'B  (Node continuity)\n'
    for i, node in enumerate(nodes):
      txt += f'    {node:<12} | ' + ' | '.join(f'{int(B[i, j]):^{w}}' for j in range(len(seg_keys))) + '\n'
    txt += sep
    # --- C block
    txt += 'C  (Loop energy)\n'
    if C.shape[0] == 0:
      txt += '    <no loops>\n'
    else:
      for i in range(C.shape[0]):
        txt += f'    L{i+1:<11} | ' + ' | '.join(f'{int(C[i, j]):^{w}}' for j in range(len(seg_keys))) + '\n'
    return txt + '\n'

  def resultString(self) -> str:
    ''' Format the solved flow/head results table.

    Returns:
      str: Result section text.
    '''
    if not self._result:
      return '   <empty: run calcNetwork()>\n\n'
    seg_w = max(12, max(len(str(item['segment'])) for item in self._result) + 2)
    nodes_w = max(
      9,
      max(
        len(f"{seg['B']} → {seg['E']}") if seg['sense'] > 0 else len(f"({seg['B']} ← {seg['E']})")
        for seg in self._segments.values()
      )
    )
    comp_w = 16
    header = (
      '   '
      + f"{'Segment':<{seg_w}}"
      + ' | '
      + f"{'Nodes':<{nodes_w}}"
      + ' | '
      + f"{'Component':<{comp_w}}"
      + ' | '
      + f"{'Q':>16}"
      + ' | '
      + f"{'H':>16}"
      + '\n'
    )
    sep = '   ' + '-' * len(header.rstrip('\n')) + '\n'
    txt = header + sep
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
      q_txt = f"{item['Q']:.4g~P}"
      h_txt = f"{item['H']:.4g~P}"
      txt += (
        '   '
        + f'{seg_key:<{seg_w}}'
        + ' | '
        + f'{nodes_txt:<{nodes_w}}'
        + ' | '
        + f'{comp_name:<{comp_w}}'
        + ' | '
        + f'{q_txt:>16}'
        + ' | '
        + f'{h_txt:>16}'
        + '\n'
      )
    return txt + '\n'

  def networkValidationtoString(self) -> str:
    ''' Return the validation report for fundamental cycles.

    Returns:
      str: Validation report.
    '''
    return self._calcValidation()
