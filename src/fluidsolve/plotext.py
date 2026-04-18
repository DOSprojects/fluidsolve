'''
High-level plotting helpers for hydraulic Q-H analysis.

This module extends the lower-level plotting utilities by providing
domain-focused plotting workflows for pump/circuit interaction diagrams,
especially Q-H (flow-head) charts.

Main responsibilities:

* collect pumps, circuits, and operating points in a unified plot context,
* generate sampled Q-H curves and overlay system/working points,
* provide plotting controls for labels, ranges, and slider-driven interaction,
* bridge hydraulic model objects with matplotlib-based presentation.

Design intent:

* keep engineering plotting logic close to hydraulic concepts,
* reduce repetitive plotting boilerplate in examples and notebooks,
* allow quick visual comparison of pump curves vs circuit demand curves.

Typical usage::

  plotter = PlotQHcurve(
      pumps=[pump],
      circuits=[circuit],
      wpoints=[wp],
      npts=80,
  )
  plotter.show()

For generic figure/canvas mechanics, this module builds on ``plotlib`` and
adds hydraulic-specific composition rules on top.
'''
# =============================================================================
# IMPORTS
# =============================================================================
from typing                   import Any, Optional
import numpy                  as np
import matplotlib.pyplot      as mplt
# module own
import fluidsolve.aux_tools   as flsa
import fluidsolve.medium      as flsme
import fluidsolve.plotlib     as flsp
# units
u         = flsme.unitRegistry
Quantity  = flsme.Quantity  # type: ignore[misc]
# =============================================================================
# PLOT Q-H CURVE CLASS
# =============================================================================
class PlotQHcurve:
  ''' Plot a Q-H diagram with pump curves, circuit curves, and working points.

  Args:
    pumps (object | list): Pump or list of pumps.
    circuits (object | list): Circuit or list of circuits.
    wpoints (object | list, optional): Working points to mark.
    spoints (object | list, optional): System (static) points to mark.
    npts (int, optional): Number of curve sample points.
    Qmax (int | float | Quantity, optional): Maximum flow on Q axis.
    Hmax (int | float | Quantity, optional): Maximum head on H axis.
    xlabel (str, optional): X-axis label.
    ylabel (str, optional): Y-axis label.
    sliders (list, optional): Slider widget definitions.
    xmin (int | float, optional): X-axis minimum override.
    xmax (int | float, optional): X-axis maximum override.
    xstep (int | float, optional): X-axis major tick step override.
    ymin (int | float, optional): Y-axis minimum override.
    ymax (int | float, optional): Y-axis maximum override.
    ystep (int | float, optional): Y-axis major tick step override.
  '''

  def __init__(self, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._pumps: str = args.getArg(
      'pumps',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(object, list, tuple),
      ]
    )
    self._circuits: str = args.getArg(
      'circuits',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(object, list, tuple),
      ]
    )
    self._wpoints: str = args.getArg(
      'wpoints',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(object, list, tuple),
      ]
    )
    self._spoints: str = args.getArg(
      'spoints',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(object, list, tuple),
      ]
    )
    self._npts: float = args.getArg(
      'npts',
      [
          flsa.vFun.default(50),
          flsa.vFun.istype(int, float),
          flsa.vFun.totype(int),
      ]
    )
    self._Qmax: float = args.getArg(
      'Qmax',
      [
          flsa.vFun.default(50),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m**3/u.h, magnitude=True),
      ]
    )
    self._Hmax: float = args.getArg(
      'Hmax',
      [
          flsa.vFun.default(15),
          flsa.vFun.istype(int, float, Quantity),
          flsa.vFun.tounits(u.m, magnitude=True),
      ]
    )
    xmin: int | float = args.getArg(
      'xmin',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(float, int, need=False),
      ]
    )
    xmax: int | float = args.getArg(
      'xmax',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(float, int, need=False),
      ]
    )
    xstep: int | float = args.getArg(
      'xstep',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(float, int, need=False),
      ]
    )
    xlabel: float = args.getArg(
      'xlabel',
      [
          flsa.vFun.default('Q (m³/h'),
          flsa.vFun.istype(str),
      ]
    )
    ymin: int | float = args.getArg(
      'ymin',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(float, int, need=False),
      ]
    )
    ymax: int | float = args.getArg(
      'ymax',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(float, int, need=False),
      ]
    )
    ystep: int | float = args.getArg(
      'ystep',
      [
          flsa.vFun.default(None),
          flsa.vFun.istype(float, int, need=False),
      ]
    )
    ylabel: float = args.getArg(
      'ylabel',
      [
          flsa.vFun.default('H (m)'),
          flsa.vFun.istype(str),
      ]
    )
    sliders: list = args.getArg(
      'sliders',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(list, need=False),
      ]
    )
    self._extra: dict = {}
    # generate objects
    self._fig   : flsp.PlotFigure = flsp.PlotFigure(**args.restArgs())
    # specific configuration
    self._graph : flsp.PlotGraph = flsp.PlotGraph(self._fig, r=0, c=0)
    xaxis_args = flsa.prepareArgs(
      vmin      = xmin,
      vmax      = xmax,
      vstep     = xstep,
      labeltxt  = xlabel,
    )# | self._extra['xaxis']
    yaxis_args = flsa.prepareArgs(
      vmin      = ymin,
      vmax      = ymax,
      vstep     = ystep,
      labeltxt  = ylabel,
    )# | self._extra['yaxis']
    self._graph.setXAxis(**xaxis_args)
    self._graph.setYAxis(**yaxis_args)
    self._graph.setGrid(axis='both')
    # widgets
    self._buttonreset : Optional[flsp.PlotButton] = None
    self._sliders     : list = []
    if len(sliders) > 0:
      self._fig.hw = (len(sliders) + 1) * 30
      self._fig.nrw = len(sliders) + 1
      self._fig.ncw = 10
      # button to reset the sliders to initial values
      buttonreset_pars = dict(
        r=0, c=8,
        label='Reset',
        fun=self._resetControls,
        color='lightblue', hovercolor='yellow'
      )
      self._buttonreset = flsp.PlotButton(self._fig, **buttonreset_pars)
      for i in range(len(sliders)):
        slider_pars =  flsa.prepareArgs(
          r = i+1, c = '0:9',
        )  | sliders[i]
        self._sliders.append(flsp.PlotSlider(self._fig, **slider_pars))
    # local data
    self._curvepumps      : dict = []
    self._curvecircuits   : dict = []
    self._curvewpts       : dict = []
    self._curvespts       : dict = []
    self._annotationwpts  : dict = []
    self._annotationspts  : dict = []
    #
    self._prepare         : bool  = True

  def update(self) -> Any:
    ''' Recalculate and redraw the full figure. '''
    self._calcAndUpdate()
    self._fig.update()
    self._fig.update()

  def updateData(self) -> Any:
    ''' Recalculate and update only the plot data without a full redraw. '''
    self._calcAndUpdate()
    self._fig.updateData()


  def prepareShow(self) -> None:
    ''' Build plot objects and calculate initial data. '''
    if self._prepare:
      for _pump in self._pumps:
        self._curvepumps.append(flsp.PlotCurve(self._graph, type='line', extra=dict(zorder=1),))
      for _circuit in self._circuits:
        self._curvecircuits.append(flsp.PlotCurve(self._graph, type='line', extra=dict(zorder=2),))
      for _points in self._wpoints:
        self._curvewpts.append(flsp.PlotCurve(
          self._graph, type='scatter',
          color='red', marker='o', markersize=5, extra=dict(zorder=20),
        ))
        self._annotationwpts.append(flsp.PlotAnnotation(
          self._graph,
          halignment='left', xoffset=3, extra=dict(zorder=21),
        ))
      for _points in self._spoints:
        self._curvespts.append(flsp.PlotCurve(
          self._graph, type='scatter',
          color='green', marker='o', markersize=5, extra=dict(zorder=12),
        ))
        self._annotationspts.append(flsp.PlotAnnotation(
          self._graph,
          halignment='center', xoffset=10, xtoggle=1, extra=dict(zorder=11),
        ))
      self._calcAndUpdate()
      #TODO set axis, grid and labels and limits
      self._fig.prepareShow()
    self.prepare = False

  def show(self) -> None:
    ''' Prepare and display the plot. '''
    self.prepareShow()
    self._fig.show()

  def _calcAndUpdate(self) -> None:
    ''' Recalculate curves and push updated data to all plot objects.

        Q is in m3/h and H in m; all values are passed as bare magnitudes.
    '''
    for i in range(len(self._pumps)):
      pump = self._pumps[i]
      curve = self._curvepumps[i]
      Qpts_p_mag = np.linspace(pump._Qb.magnitude, pump._Qe.magnitude, self._npts)
      Hpts_p_mag = pump.calcH(Qpts_p_mag, 1).magnitude
      ptrim = np.argmax(Hpts_p_mag<=0)
      if ptrim>0:
        Qpts_p_mag = Qpts_p_mag[:ptrim]
        Hpts_p_mag = Hpts_p_mag[:ptrim]
      curve.x = Qpts_p_mag
      curve.y = Hpts_p_mag
    Qpts_c_mag = np.linspace(0.001, self._Qmax, self._npts)
    for i in range(len(self._circuits)):
      circuit = self._circuits[i]
      curve = self._curvecircuits[i]
      Hpts_c_mag = abs(circuit.calcH(Qpts_c_mag, 1).magnitude)
      curve.x =Qpts_c_mag
      curve.y =Hpts_c_mag
    for i in range(len(self._wpoints)):
      wpoint = self._wpoints[i]
      curve = self._curvewpts[i]
      annotation = self._annotationwpts[i]
      wpoint.update()
      curve.x =[wpoint.Qmag]
      curve.y =[wpoint.Hmag]
      annotation.x =[wpoint.Qmag]
      annotation.y =[wpoint.Hmag]
      annotation.label = [wpoint.name]
    for i in range(len(self._spoints)):
      spoint = self._spoints[i]
      curve = self._curvespts[i]
      annotation = self._annotationspts[i]
      spoint.update()
      curve.x =[spoint.Qmag]
      curve.y =[spoint.Hmag]
      annotation.x =[spoint.Qmag]
      annotation.y =[spoint.Hmag]
      annotation.label = [spoint.name]

  def _resetControls(self, event: Any) -> Any:
    ''' Reset all slider widgets to their initial values. '''
    for slider in self._sliders:
      slider.widget.reset()
