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
  spec,
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
  )
from .comp_pump import (
  N_CURVE_POINTS,
  )
from .core import (
  initFluidsolve,
  registerComp,
  registerComps,
  registerAllComps,
  getDefaultMedium,
  setDefaultMedium,
  getDefaultMaterial,
  setDefaultMaterial,
  getComp,
  getWpt,
  getPath,
  getNetwork,
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
  unitRegistry,
  Quantity,
  Medium,
  )
from .material import (
  Material,
  )
from .plotext import (
  PlotSimple,
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
  'spec',
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
  'initFluidsolve',
  'registerComp',
  'registerComps',
  'registerAllComps',
  'getDefaultMedium',
  'setDefaultMedium',
  'getDefaultMaterial',
  'setDefaultMaterial',
  'getComp',
  'getWpt',
  'getPath',
  'getNetwork',
  #CLS
  'Medium',
  'Material',
  'Catalogue',
  'GetArgs',
  'PlotAnnotation',
  'PlotAxis',
  'PlotButton',
  'PlotSlider',
  'PlotCurve',
  'PlotFigure',
  'PlotGraph',
  'PlotGrid',
  'PlotLine',
  'PlotSimple',
  'PlotQHcurve',
  'Wpoint',
  'WpointDyn',
  'vFun',
]
