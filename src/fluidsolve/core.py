'''
Factory and registry entry points for fluidsolve objects.

This module centralizes object creation and naming for components,
working points, paths, and networks. Direct class construction is still
possible, but using the factory helpers is recommended because they enforce
consistent defaults and unique names.

Main responsibilities:

* initialize module-wide defaults (prefixes, default medium/material),
* create and register components through builder helpers,
* create working points, paths, and networks with consistent naming,
* expose lookup helpers for already-created objects.

Why this matters:

Several parts of the toolkit rely on stable object naming and centralized
defaults. Bypassing the factories can lead to duplicate names or mismatched
default conditions, which may affect downstream network and plotting tools.

Typical usage::

  initFluidsolve(prefix_comp='Comp_', prefix_wpt='Wp_')
  pump = getComp(comp='PumpCentrifugal', dataQH=curve, speed0=2900)
  tube = getComp(comp='Tube', L=100, D=50)

Registry internals:

* components, paths, networks, and working points are kept in module-level
  dictionaries,
* helper getters return existing objects by name,
* auto-index counters generate deterministic names when explicit names are not
  provided.

Naming/default policy:

* prefixes are configurable through ``initFluidsolve``,
* default medium and material are configured once and reused by factories,
* this ensures consistent assumptions across independently created objects.

Typical end-to-end flow::

  initFluidsolve(default_medium='water')
  p1 = getComp(comp='PumpCentrifugal', dataQH=curve, speed0=2900)
  r1 = getComp(comp='Tube', L=120, D=50)
  net = getNetwork(name='N1', components=[
      {'nodes': ['A', 'B'], 'comp': p1},
      {'nodes': ['B', 'A'], 'comp': r1},
  ])
  result = net.calcNetwork(1.0)

The goal of this module is to keep model construction concise and reproducible,
while avoiding duplicated setup logic in scripts and examples.
'''
# =============================================================================
# IMPORTS
# =============================================================================
from typing                 import Any, Optional
#import fluids.vectorized as fv
# module own
import fluidsolve.aux_tools   as flsa
import fluidsolve.medium      as flsme
import fluidsolve.material    as flsma
import fluidsolve.comp_base   as flsb
import fluidsolve.comp_resist as flsc
import fluidsolve.comp_pump   as flsp
import fluidsolve.comp_valve  as flsv
import fluidsolve.wpoint      as flswp
import fluidsolve.path        as flspath
import fluidsolve.network     as flsnet
# units
u         = flsme.unitRegistry
Quantity  = flsme.Quantity  # type: ignore[misc]

# =============================================================================
# INITIALISATION
# =============================================================================
_nets   : dict    = {}
_paths  : dict    = {}
_comps  : dict    = {}
_wpts   : dict    = {
  's' : flswp.Wpoint,
  'd' : flswp.WpointDyn,
}
_comp_index : int     = 0  # Track the next auto-generated component index.
_wpt_index  : int     = 0  # Track the next auto-generated workingpoint index.

_prefix_comp: str = 'C'
_prefix_wpt: str = 'Wp'
_default_material: flsma.Material = flsma.Material(mat='rvs')
_default_medium: flsme.Medium = flsme.Medium(prd='water')

# =============================================================================
# MODULE FUNCTIONS
# =============================================================================

# --------------------------------------------------------------------------
# INITIALIZE
def initFluidsolve(**kwargs: int) -> None:
  ''' Initialize module-wide defaults used by the factory helpers.

  Args:
    prefix_comp (str, optional): Prefix for auto-generated component names.
    prefix_wpt (str, optional): Prefix for auto-generated working point names.
    default_material (str | Material, optional): Default pipe material.
    default_medium (str | Medium, optional): Default fluid medium.
  '''
  global _prefix_comp, _prefix_wpt, _default_material, _default_medium
  args_in = flsa.GetArgs(kwargs)
  _prefix_comp = args_in.getArg(
    'prefix_comp',
    [
        flsa.vFun.default('C'),
        flsa.vFun.istype(str),
    ]
  )
  _prefix_wpt = args_in.getArg(
    'prefix_wpt',
    [
        flsa.vFun.default('Wp'),
        flsa.vFun.istype(str),
    ]
  )
  _default_material = args_in.getArg(
    'default_material',
    [
        flsa.vFun.default(flsma.Material(mat='rvs')),
        flsa.vFun.istype((str, flsma.Material)),
        flsa.vFun.tolambda(lambda x: x if isinstance(x, flsma.Material) else flsma.Material(mat=x))
    ]
  )
  _default_medium = args_in.getArg(
    'default_medium',
    [
        flsa.vFun.default(flsme.Medium(prd='water')),
        flsa.vFun.istype((str, flsme.Medium)),
        flsa.vFun.tolambda(lambda x: x if isinstance(x, flsme.Medium) else flsme.Medium(prd=x))
    ]
  )

# --------------------------------------------------------------------------
# REGISTERS
def registerComp(name: str, comp: flsb.Comp_Base, raiseerror: bool=True) -> bool:
  ''' Register one component class in the component catalogue.

  Args:
    name (str): Key used by getComp.
    comp (flsb.Comp_Base): Component class to register.
    raiseerror (bool, optional): Raise on duplicate key.

  Returns:
    bool: True if registration succeeded, False otherwise.
  '''
  if name in _comps:
    if raiseerror:
      raise ValueError(f'Error: component {name} already registered {_comps.keys()}.')
    return False
  else:
    _comps[name] = comp
    return True

def registerComps(comps: dict, raiseerror: bool=True) -> bool:
  ''' Register multiple component classes.

  Args:
    comps (dict): Mapping of component keys to component classes.
    raiseerror (bool, optional): Raise on duplicate keys.

  Returns:
    bool: True if all registrations succeeded, False otherwise.
  '''
  result = True
  for key, value in comps.items():
    if not registerComp(key, value, raiseerror):
      result = False
  return result

def registerAllComps(raiseerror: bool=True) -> bool:  # pylint: disable=unused-argument
  ''' Register all built-in component classes.

  Args:
    raiseerror (bool, optional): Raise on duplicate keys.

  Returns:
    bool: True if all registrations succeeded, False otherwise.
  '''
  result = True
  if not registerComps({
      'Dummy'             : flsb.Comp_Dummy,
      'Reverse'           : flsb.Comp_Reverse,
  }):
    result = False
  if not registerComps({
      'Hstatic'           : flsc.Comp_Hstatic,
      'Tube'              : flsc.Comp_Tube,
      'Bend'              : flsc.Comp_Bend,
      'BendLong'          : flsc.Comp_BendLong,
      'Entrance'          : flsc.Comp_Entrance,
      'SharpReduction'    : flsc.Comp_SharpReduction,
      'ConicalReduction'  : flsc.Comp_ConicalReduction,
      #
      'PHE'               : flsc.Comp_PHE,
      #
      'Serial'            : flsc.Comp_Serial,
      'Parallel'          : flsc.Comp_Parallel,
      'Parallel2'         : flsc.Comp_Parallel2,
  }):
    result = False
  if not registerComps({
      'Pump'              : flsp.Comp_Pump,
      'PumpCentrifugal'   : flsp.Comp_PumpCentrifugal,
      'PumpSerial'        : flsp.Comp_PumpSerial,
      'PumpParallel'      : flsp.Comp_PumpParallel,
  }):
    result = False
  if not registerComps({
      'Valve_NR'          : flsv.Comp_Valve_NR,
      'Valve_01'          : flsv.Comp_Valve_01,
      'Valve_Kv'          : flsv.Comp_Valve_Kv,
      'Valve_3W'          : flsv.Comp_Valve_3W,
      'Valve_DS'          : flsv.Comp_Valve_DS,
  }):
    result = False
  return result

# --------------------------------------------------------------------------
# DEFAULTS
def getDefaultMedium() -> flsme.Medium:
  ''' Return the current default medium.

  Returns:
    flsme.Medium: Default medium.
  '''
  return _default_medium

def setDefaultMedium(value: flsme.Medium) -> None:
  ''' Set the default medium.

  Args:
    value (flsme.Medium): Default medium.
  '''
  global _default_medium
  _default_medium = value

def getDefaultMaterial() -> flsma.Material:
  ''' Return the current default material.

  Returns:
    flsma.Material: Default material.
  '''
  return _default_material

def setDefaultMaterial(value: flsma.Material) -> None:
  ''' Set the default material.

  Args:
    value (flsma.Material): Default material.
  '''
  global _default_material
  _default_material = value

# --------------------------------------------------------------------------
# OBJECT FACTORIES
def getComp(**kwargs: Any) -> flsb.Comp_Base:
  ''' Build and return a component instance from the registry.

  Args:
    comp (str): Component key in the internal registry.
    kwargs: Arguments passed to the component constructor.

  Returns:
    flsb.Comp_Base: Instance of the requested component class.
  '''
  args_in = {}
  comp_key = kwargs.get('comp', None)
  if comp_key not in _comps:
    raise ValueError(f'Component type "{comp_key}" is not defined')
  if 'name' not in kwargs:
    args_in['name'] = _getCompName()
  else:
    args_in['name'] = kwargs['name']
  args_in['medium'] = kwargs.get('medium', _default_medium)
  args_in['e'] = kwargs.get('e', _default_material.e)
  for key, value in kwargs.items():
    if key not in ['comp', 'name', 'medium', 'e']:
      args_in[key] = value
  comp_cls = _comps[comp_key]
  return comp_cls(**args_in)

def getWpt(**kwargs: Any) -> flswp.Wpoint:
  ''' Build and return a workingpoint instance.

  Args:
    kwargs: Arguments passed to the workingpoint constructor.

  Returns:
    flswp.Wpoint: Instance of the requested workingpoint class.
  '''
  args_in = {}
  wpt_key = kwargs.get('wpt', None)
  if wpt_key not in _wpts:
    raise ValueError(f'Workingpoint type "{wpt_key}" is not defined')
  if 'name' not in kwargs:
    args_in['name'] = _getWptName()
  else:
    args_in['name'] = kwargs['name']
  for key, value in kwargs.items():
    if key not in ['wpt', 'name']:
      args_in[key] = value
  wpt_cls = _wpts[wpt_key]
  return wpt_cls(**args_in)

def getPath(**kwargs: Any) -> flspath.Path:
  ''' Build and return a path object.

  Args:
    kwargs: Arguments passed to the path constructor.

  Returns:
    flspath.Path: New path instance.
  '''
  return flspath.Path(**kwargs)


def getNetwork(**kwargs: Any) -> flsnet.Network:
  ''' Build and return a network object.

  Args:
    kwargs: Arguments passed to the network constructor.

  Returns:
    flsnet.Network: New network instance.
  '''
  network_cls = flsnet.Network
  return network_cls(**kwargs)

# --------------------------------------------------------------------------
# LOCAL UTILITIES
def _getCompName() -> str:
  ''' Generate the next automatic component name.

  Returns:
    str: Component name.
  '''
  global _comp_index
  idx = _comp_index
  letters = ''
  while True:
    idx, rem = divmod(idx, 26)
    letters = chr(65 + rem) + letters
    if idx == 0:
      break
    idx -= 1
  _comp_index += 1
  return f'{_prefix_comp}{letters}'

def _getWptName() -> str:
  ''' Generate the next automatic workingpoint name.

  Returns:
    str: Workingpoint name.
  '''
  global _wpt_index
  idx = _wpt_index
  name = f'{_prefix_wpt}{idx}'
  _wpt_index += 1
  return name

# =============================================================================
# RUN INITIALISATION
# =============================================================================
registerAllComps()
initFluidsolve()
