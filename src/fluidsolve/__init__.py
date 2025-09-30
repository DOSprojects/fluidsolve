# __init__.py
'''
    FluidSolve module
    Fluid Dynamics Calculations
'''
#******************************************************************************
# EXTERNAL MODULE REFERENCES
#******************************************************************************

#******************************************************************************
# IMPORTS
#******************************************************************************
# unit juggling
#from pint       import _DEFAULT_REGISTRY as u

from .___version import (
  __version__,
  )
from .aux_tools import (
  toUnits,
  prepareArgs,
  getPumpCurveDataText,
  GetArgs,
  vFun,
  )
from .catalogue import (
  Catalogue,
  )
from .comp_base import (
  NO_DIAMETER,
  NO_LENGTH,
  NO_MEDIUM,
  Comp_Base,
  )
from .comp_pump import (
  N_CURVE_POINTS,
  Comp_Pump,
  Comp_PumpCentrifugal,
  Comp_PumpSerial,
  Comp_PumpParallel,
  )
from .comp_resist import (
  Comp_Dummy,
  Comp_Hstatic,
  Comp_Appendage,
  Comp_Kstatic,
  Comp_Tube,
  Comp_Bend,
  Comp_BendLong,
  Comp_Entrance,
  Comp_SharpReduction,
  Comp_ConicalReduction,
  C_EntranceBeveled,
  Comp_PHE,
  Comp_Serial,
  Comp_Parallel,
  Comp_Parallel2,
  )
from .core import (
  ComponentBuilder,
  )
from .medium import (
  CTE_G,
  CTE_NT,
  CTE_NP,
  CTE_WATER,
  CTE_RHO,
  CTE_MU,
  CTE_NU,
  CTE_K,
  CTE_E_RVS,
  Medium,
  unitRegistry,
  Quantity,
  )
from .network import (
  Network,
  )
from .plotext import (
  PlotQHcurve,
  )
from .plotlib import (
  PlotFigure,
  PlotGraph,
  PlotCurve,
  PlotLine,
  PlotAxis,
  PlotAnnotation,
  PlotGrid,
  PlotButton,
  PlotSlider,
  )
from .util import (
  calcOrifice,
  KtoFd,
  FdtoK,
  KvtoK,
  KtoKv,
  CvtoK,
  KtoCv,
  CvtoKv,
  KvtoCv,
  KtoH,
  Ktop,
  Htop,
  ptoH,
  Qtov,
  vtoQ,
  calcCurve,
  )
from .wpoint import (
  calcOperatingPoint,
  Wpoint,
  WpointDyn,
  )

__all__ = [
  '__version__',
  'unitRegistry',
  'Quantity',
  #VAR
  '__version__',
  'CTE_E_RVS',
  'CTE_G',
  'CTE_K',
  'CTE_MU',
  'CTE_NP',
  'CTE_NT',
  'CTE_NU',
  'CTE_RHO',
  'CTE_WATER',
  'NO_DIAMETER',
  'NO_LENGTH',
  'NO_MEDIUM',
  'N_CURVE_POINTS',
  #FUN
  'CvtoK',
  'CvtoKv',
  'FdtoK',
  'Htop',
  'KtoCv',
  'KtoFd',
  'KtoH',
  'KtoKv',
  'Ktop',
  'KvtoCv',
  'KvtoK',
  'Qtov',
  'calcCurve',
  'calcOperatingPoint',
  'calcOrifice',
  'getPumpCurveDataText',
  'prepareArgs',
  'ptoH',
  'toUnits',
  'vtoQ',
  #CLS
  'C_EntranceBeveled',
  'Catalogue',
  'Comp_Appendage',
  'Comp_Base',
  'Comp_Bend',
  'Comp_BendLong',
  'Comp_ConicalReduction',
  'Comp_Dummy',
  'Comp_Entrance',
  'Comp_Hstatic',
  'Comp_Kstatic',
  'Comp_PHE',
  'Comp_Parallel',
  'Comp_Parallel2',
  'Comp_Pump',
  'Comp_PumpCentrifugal',
  'Comp_PumpParallel',
  'Comp_PumpSerial',
  'Comp_Serial',
  'Comp_SharpReduction',
  'Comp_Tube',
  'ComponentBuilder',
  'GetArgs',
  'Medium',
  'Network',
  'PlotAnnotation',
  'PlotAxis',
  'PlotButton',
  'PlotCurve',
  'PlotFigure',
  'PlotGraph',
  'PlotGrid',
  'PlotLine',
  'PlotQHcurve',
  'PlotSlider',
  'QHcurve',
  'Wpoint',
  'WpointDyn',
  'vFun',
]
