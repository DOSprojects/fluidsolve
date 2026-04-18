'''
One-dimensional hydraulic path model (series-connected components).

This module implements a simplified hydraulic topology for ordered component
chains. A ``Path`` is effectively a restricted network with:

* no branches,
* no cycles,
* explicit component order,
* explicit per-component flow direction (sense).

Compared with the full network solver, this representation is easier to build
and reason about when modeling single-line circuits or pump-and-piping strings.

Main responsibilities:

* store and validate ordered component entries,
* evaluate total head/pressure behavior along the chain,
* solve for operating points when combined with pump/circuit relations,
* expose convenience views for plotting and reporting.

Conventions:

* each entry stores ``comp``, ``sense``, ``pin``, and ``pout``,
* component physics is delegated to each component's ``calcH`` / ``calcP``,
* path-level solve routines aggregate these local relations in order.

Typical usage::

  p = Path(name='loop', components=[
      {'comp': pump, 'sense': +1, 'pin': 1, 'pout': 2},
      {'comp': tube, 'sense': +1, 'pin': 1, 'pout': 2},
  ])
  H = p.calcH(2.0 * u.m**3 / u.h)

Use ``Path`` when a full graph-based network is unnecessary and a deterministic
series model is sufficient.
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
import fluidsolve.wpoint      as flswp
# units
u         = flsme.unitRegistry
Quantity  = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# PATH CLASS
# =============================================================================
class Path(flsb.Comp_Base):
  ''' One-dimensional hydraulic path of series-connected components.

  Ordered, branch-free, cycle-free subset of a network with
  an explicit flow direction per component.

  Args:
    name (str, optional): Path label.
    components (list, optional): Ordered list of component dicts to add via addComponents.
  '''

  # --------------------------------------------------------------------------
  # FIXED PROPERTIES

  # --------------------------------------------------------------------------
  # INITIALIZE
  def __init__(self, **kwargs: Any) -> None:
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
    self._items : list = []
    self.addComponents(components)

  #----------------------------------------------------------------------------
  # PROPERTIES
  @property
  def Name(self) -> str:
    ''' Path name. '''
    return self._name

  @property
  def Components(self) -> Any:
    ''' Ordered list of component entries (comp, sense, pin, pout). '''
    return self._items

  def getComp(self, idx: int) -> dict:
    ''' Return the component entry at index ``idx``.

    Args:
      idx (int): Component index.

    Returns:
      dict: Component entry with keys ``comp``, ``sense``, ``pin``, ``pout``.
    '''
    return self._items[idx]

  def setComp(self, idx: int, item: dict) -> dict:
    ''' Replace the component entry at index ``idx``.

    Args:
      idx (int): Component index.
      item (dict): Component entry with keys ``comp``, ``sense``, ``pin``, ``pout``.

    Returns:
      dict: Stored component entry.
    '''
    self._items[idx] = item
    return item

  #----------------------------------------------------------------------------
  # METHODS
  def addComponents(self, components: list) -> None:
    ''' Append components to the path.

    Args:
      components (list): List of dicts with keys ``comp``, optional ``sense``,
        ``pin``, and ``pout``.
    '''
    for item in components:
      if not isinstance(item, dict):
        raise ValueError(f'Invalid component entry (dict expected): {item}')
      if 'comp' not in item:
        raise ValueError(f'Component entry missing key "comp": {item}')
      comp = item['comp']
      sense = item.get('sense', +1)
      pin = item.get('pin', None)
      pout = item.get('pout', None)
      if not isinstance(comp, flsb.Comp_Base):
        raise ValueError(f'Unknown component: {comp}')
      if sense not in (+1, -1):
        raise ValueError(f'sense must be +1 or -1, got {sense}')
      if comp.nports > 2:
        if pin is None or pout is None:
          raise ValueError(f'Component "{comp.name}" has {comp.nports} ports, need pin and pout')
        if not (1 <= pin <= comp.nports and 1 <= pout <= comp.nports):
          raise ValueError(f'Invalid ports pin={pin}, pout={pout} for component "{comp.name}"')
      else:  # Implicit 2-port behavior.
        pin = 1
        pout = 2
      self._items.append({'comp': comp, 'sense': sense, 'pin': pin, 'pout': pout})

  #----------------------------------------------------------------------------
  # PHYSICS
  def calcH(self, Q: Quantity, sense: int=1, pin: Any=None, pout: Any=None) -> Quantity:
    ''' Calculate total head change along the path.

    Args:
      Q: Flow rate.
      sense: Path flow direction (+1 or -1).

    Returns:
      Quantity: Total head change (m).
    '''
    H = 0.0 * u.m
    for item in self._items:
      comp = item['comp']
      csense = item['sense'] * sense
      pin = item['pin']
      pout = item['pout']
      H += comp.calcH(Q, csense, pin, pout)
    return H

  def calcP(self, Q: Quantity, sense: int=1, pin: Any=None, pout: Any=None) -> Quantity:
    ''' Calculate total pressure change along the path.

    Args:
      Q: Flow rate.
      sense: Path flow direction (+1 or -1).

    Returns:
      Quantity: Total pressure change.
    '''
    P = 0.0 * u.bar
    for item in self._items:
      P += item['comp'].calcP(Q, item['sense']*sense, item['pin'], item['pout'])
    return P

  def calcHprofile(self, Q: int | float | Quantity, sense: int=1, pin: int=1, pout:int=2, incr: bool=False) -> Any:
    ''' Build a list of working points over the path.

    Args:
      Q (int | float | Quantity): Flow rate.
      sense (int, optional): Path flow direction (+1 or -1).
      pin (int, optional): Unused compatibility argument.
      pout (int, optional): Unused compatibility argument.
      incr (bool, optional): If True, head is accumulated component by component.

    Returns:
      list[flswp.Wpoint]: Working points per component plus total.
    '''
    lQ = flsa.toUnits(Q, u.m**3/u.h)
    pts = []
    H = 0 *u.m
    for i, item in enumerate(self._items):
      if incr:
        H = H + item['comp'].calcH(lQ, sense*item['sense'], item['pin'], item['pout'])
      else:
        H = item['comp'].calcH(lQ, sense*item['sense'], item['pin'], item['pout'])
      pts.append(flswp.Wpoint(name=f"{i}:{item['comp'].name}", Q=lQ, H=H))
    H = self.calcH(lQ, sense)
    pts.append(flswp.Wpoint(name='Tot', Q=lQ, H=H))
    return pts

  #----------------------------------------------------------------------------
  # REPRESENTATION
  def __str__(self) -> str:
    ''' Return a compact string representation.

    Returns:
      str: Compact path summary.
    '''
    return self.toString(detail=0)

  def toString(self, detail: int = 0) -> str:
    ''' Return a formatted multi-line path description.

    Args:
      detail (int, optional): Include extra metadata when non-zero.

    Returns:
      str: Formatted path text.
    '''
    txt = f'Path "{self._name}"\n'
    txt += ' Components:\n'
    txt += self.componentsString()
    if detail:
        txt += f' Count: {len(self._items)}\n'
    return txt

  def componentsString(self) -> str:
    ''' Format the ordered component list for display.

    Returns:
      str: Components section text.
    '''
    if not self._items:
      return '   <none>\n\n'
    idx_w = max(3, len(str(len(self._items))))
    name_w = max(10, max(len(getattr(item['comp'], 'name', item['comp'].__class__.__name__)) for item in self._items))
    type_w = max(10, max(len(item['comp'].__class__.__name__) for item in self._items))
    txt = ''
    for i, item in enumerate(self._items, start=1):
      comp = item['comp']
      comp_name = getattr(comp, 'name', comp.__class__.__name__)
      comp_type = comp.__class__.__name__
      dir_txt = '→' if item['sense'] > 0 else '←'
      txt += (
        f'   [{i:>{idx_w}}] '
        f'{comp_name:<{name_w}} '
        f'({comp_type:<{type_w}}) '
        f'dir: {dir_txt} '
        f'ports: {item["pin"]} -> {item["pout"]}\n'
      )
    return txt + '\n'
  