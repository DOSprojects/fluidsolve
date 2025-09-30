'''
This module implements some classes that represent a hydraulic component.
Most of these classe inherit from a generic one.

#https://www.h2xengineering.com/blogs/hardy-cross-method-sizing-a-ring-main/
#https://www.colorado.edu/lab/krg/software-and-resources/tutorial-python-hardy-cross-method

D:/_pgm/penv/fluidsolve/Scripts/activate

TODO: str, tostring en repl
TODO calcH dimensionless
TODO think of the to and from dimensions....
TODO tostring met 1234 en elke volgende digit is voor sublevel
TODO: check for invalid parameters
TODO: demoplot00: set sliders in comment and button is not printed
TODO expose private values??? look at eg: _hw
'''
# ====================================y=========================================
# IMPORTS
# =============================================================================
from typing                 import Optional
#import fluids.vectorized as fv
# module own
import fluidsolve.aux_tools   as flsa
import fluidsolve.medium      as flsm
import fluidsolve.comp_base   as flsb
import fluidsolve.comp_resist as flsc
import fluidsolve.comp_pump   as flsp
import fluidsolve.wpoint      as flswp
import fluidsolve.network     as flsn
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity
# =============================================================================
# SENTINEL OBJECTS
# =============================================================================
NO_DIAMETER = object()
NO_LENGTH   = object()
NO_MEDIUM   = object()

# =============================================================================
# BUILDER CLASSES
# =============================================================================

#******************************************************************************
# Component Builder
class ComponentBuilder():
  '''
  Builder/factory for hydraulic component classes (Singleton).
  Usage:
    Builder().getComp(comp='Tube', ...) -> instance of Comp_Tube
  '''
  _comps      : dict    = {}
  _wpts       : dict    = {
    's' : flswp.Wpoint,
    'd' : flswp.WpointDyn,
  }
  _comp_index : int     = 0  # class variable to track the next component index
  _wpt_index  : int     = 0  # class variable to track the next workpoint index
  _instance   : object  = None

  def __new__(cls, *args, **kwargs):
    ''' Singleton instance creation.

    Args:
      cls: Class reference.
      *args: Positional arguments.
      **kwargs: Keyword arguments.

    Returns:
      (Singleton) Instance of the Builder class.
    '''
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls.registerAllComps()
    return cls._instance

  def __init__(self, **kwargs: int) -> None:
    ''' Initialize the Builder instance.
    '''
    args_in = flsa.GetArgs(kwargs)
    self._prefix_comp: str = args_in.getArg(
      'prefix_comp',
      [
          flsa.vFun.default(''),
          flsa.vFun.istype(str),
      ]
    )
    self._prefix_wpt: str = args_in.getArg(
      'prefix_wpt',
      [
          flsa.vFun.default(''),
          flsa.vFun.istype(str),
      ]
    )
    self._e: str = args_in.getArg(
      'e',
      [
          flsa.vFun.default(flsm.CTE_E_RVS),
          flsa.vFun.istype((int, float, Quantity)),
          flsa.vFun.tolambda(lambda x: x.to(u.um) if isinstance(x, Quantity) else x * u.um),
      ]
    )
    self._medium: flsm.Medium = args_in.getArg(
      'medium',
      [
          flsa.vFun.default(flsm.Medium(prd='water')),
          flsa.vFun.istype((str, flsm.Medium)),
          flsa.vFun.tolambda(lambda x: x if isinstance(x, flsm.Medium) else flsm.Medium(prd=x))
      ]
    )

  @staticmethod
  def registerAllComps(raiseerror: bool=True) -> bool:
    '''_summary_

    Args:
        raiseerror (bool, optional): _description_. Defaults to True.

    Returns:
        bool: _description_
    '''
    result = True
    if not __class__.registerComps({
        'Dummy'             : flsc.Comp_Dummy,
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
    if not __class__.registerComps({
        'Pump'              : flsp.Comp_Pump,
        'PumpCentrifugal'   : flsp.Comp_PumpCentrifugal,
        'PumpSerial'        : flsp.Comp_PumpSerial,
        'PumpParallel'      : flsp.Comp_PumpParallel,
    }):
      result = False
    if not __class__.registerComps({
        # 'Valve'   : flsc.Comp_Valve,
    }):
      result = False
    return result


  @staticmethod
  def registerComps(comps: dict, raiseerror: bool=True) -> bool:
    '''_summary_

    Args:
        comps (dict): _description_
        raiseerror (bool, optional): _description_. Defaults to True.

    Returns:
        bool: _description_
    '''
    result = True
    for key, value in comps.items():
      if not __class__.registerComp(key, value, raiseerror):
        result = False
    return result

  @staticmethod
  def registerComp(name: str, comp: flsb.Comp_Base, raiseerror: bool=True) -> bool:
    '''_summary_

    Args:
        name (str): _description_
        comp (flsb.Comp_Base): _description_
        raiseerror (bool, optional): _description_. Defaults to True.

    Returns:
        bool: _description_
    '''
    if name in __class__._comps:
      if raiseerror:
        raise ValueError(f'Error: component {name} already registered {__class__._comps.keys()}.')
      return False
    else:
      __class__._comps[name] = comp
      return True

  def getComp(self, **kwargs: int) -> flsb.Comp_Base:
    ''' Build (and return) a component .

    Args:
      comp (str): Name/type of the component (must match a key in self._comps).
      kwargs: Arguments to pass to the component constructor.

    Returns:
      Instance of the requested component class.
    '''
    args = {}
    comp_key = kwargs.get('comp', None)
    if comp_key not in self._comps:
      raise ValueError(f'Component type \"{comp_key}\" is not defined')
    if 'name' not in kwargs:
      args['name'] = self._getCompName()
    else:
      args['name'] = kwargs['name']
    args['medium'] = kwargs.get('medium', self._medium)
    # is it an issue if not needed?
    # or put it in base and not in appendage?
    args['e'] = kwargs.get('e', self._e)
    # Pass all other kwargs except 'comp', 'name', 'medium'
    for key, value in kwargs.items():
      if key not in ['comp', 'name', 'medium']:
        args[key] = value
    comp_cls = self._comps[comp_key]
    return comp_cls(**args)

  def getWpt(self, **kwargs: int) -> flswp.Wpoint:
    ''' Build (and return) a workingpoint .

    Args:
      kwargs: Arguments to pass to the wpt constructor.

    Returns:
      Instance of the requested wpt class.
    '''
    args = {}
    wpt_key = kwargs.get('wpt', None)
    if wpt_key not in self._wpts:
      raise ValueError(f'Workingpoint type \"{wpt_key}\" is not defined')
    if 'name' not in kwargs:
      args['name'] = self._getWptName()
    else:
      args['name'] = kwargs['name']
    for key, value in kwargs.items():
      if key not in ['wpt', 'name']:
        args[key] = value
    wpt_cls = self._wpts[wpt_key]
    return wpt_cls(**args)

  def getNetwork(self, **kwargs: int) -> flsn.Network:
    ''' Build (and return) a network.

    Args:
      kwargs: Arguments to pass to the network constructor.

    Returns:
      Instance of the requested network class.
    '''
    network_cls = flsn.Network
    return network_cls(**kwargs)

  def _getCompName(self) -> str:
    ''' Get the component name.

    Returns:
      str: Component name.
    '''
    idx = self._comp_index
    letters = ''
    while True:
      idx, rem = divmod(idx, 26)
      letters = chr(65 + rem) + letters
      if idx == 0:
        break
      idx -= 1
    self._comp_index += 1
    return f'{self._prefix_comp}{letters}'

  def _getWptName(self) -> str:
    ''' Get the workingpoint name.

    Returns:
      str: Workingpoint name.
    '''
    idx = self._wpt_index
    name = f'{self._prefix_wpt}{idx}'
    self._wpt_index += 1
    return name

