'''
This module implements a wrapper around matplotlib.
https://medium.com/@basubinayak05/python-data-visualization-day-1-71334ff5044e
'''
# =============================================================================
# IMPORTS
# =============================================================================
import os
from typing                   import Any, Optional, Callable
import weakref
import tkinter                as tk
import numpy                  as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot      as plt
import matplotlib.gridspec    as gridspec
from matplotlib.ticker        import FormatStrFormatter, AutoMinorLocator
from matplotlib.widgets       import Slider, Button
# module own
import fluidsolve.aux_tools   as flsa

#******************************************************************************
# Helpler functions

#******************************************************************************
# PLOTFIGURE: matplotlib figure
class PlotFigure:
  '''_summary_
  '''
  def __init__(self, **kwargs: int) -> None:
    args : dict = flsa.GetArgs(kwargs)
    self._dpi: int = args.getArg(
      'dpi',
      [
        flsa.vFun.default(100),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=50, high=1200, need=False),
      ]
    )
    self._h: int = args.getArg(
      'h',
      [
        flsa.vFun.default(400),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=50, high=5000, need=False),
      ]
    )
    self._w: int = args.getArg(
      'w',
      [
        flsa.vFun.default(800),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=50, high=5000, need=False),
      ]
    )
    self._hw: int = args.getArg(
      'hw',
      [
        flsa.vFun.default(50),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=50, high=5000, need=False),
      ]
    )
    self._nr: int = args.getArg(
      'nr',
      [
        flsa.vFun.default(1),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=1, high=10, need=False),
      ]
    )
    self._nc: int = args.getArg(
      'nc',
      [
        flsa.vFun.default(1),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=1, high=10, need=False),
      ]
    )
    self._nrw: int = args.getArg(
      'nrw',
      [
        flsa.vFun.default(1),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=1, high=10, need=False),
      ]
    )
    self._ncw: int = args.getArg(
      'ncw',
      [
        flsa.vFun.default(1),
        flsa.vFun.istype(int, need=False),
        flsa.vFun.inrange(low=1, high=10, need=False),
      ]
    )
    self._facecolor: str = args.getArg(
      'facecolor',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._title: str = args.getArg(
      'title',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._toolbar: bool = args.getArg(
      'toolbar',
      [
        flsa.vFun.default(True),
        flsa.vFun.istype(bool),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    # TODO need to be modifiable?
    self._constrained_layout  : bool  = True
    #
    self._fig                 : Any   = None
    self._figwidgets          : Any   = None
    self._gs                  : Any   = None
    self._gswidgets           : Any   = None
    self._graphs              : list  = []
    self._buttons             : list  = []
    self._sliders             : list  = []
    self._prepare             : bool  = True

  @property
  def h(self) -> int:
    return self._h

  @h.setter
  def h(self, value: int) -> None:
    self._h = value

  @property
  def w(self) -> int:
    return self._w

  @w.setter
  def w(self, value: int) -> None:
    self._w = value

  @property
  def hw(self) -> int:
    return self._hw

  @hw.setter
  def hw(self, value: int) -> None:
    self._hw = value

  @property
  def nr(self) -> int:
    return self._nr

  @nr.setter
  def nr(self, value: int) -> None:
    self._nr = value

  @property
  def nc(self) -> int:
    return self._nc

  @nc.setter
  def nc(self, value: int) -> None:
    self._nc = value

  @property
  def nrw(self) -> int:
    return self._nrw

  @nrw.setter
  def nrw(self, value: int) -> None:
    self._nrw = value

  @property
  def ncw(self) -> int:
    return self._ncw

  @ncw.setter
  def ncw(self, value: int) -> None:
    self._ncw = value

  @property
  def figure(self) -> Any:
    return self._fig

  @property
  def gridspec(self) -> Any:
    return self._gs

  @property
  def figure_widgets(self) -> Any:
    return self._figwidgets

  @property
  def gridspec_widgets(self) -> Any:
    return self._gswidgets

  @property
  def buttons(self) -> dict:
    return self._buttons

  @property
  def sliders(self) -> dict:
    return self._sliders

  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('title'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs

  def addGraph(self, graph: 'PlotGraph') -> int:
    '''_summary_

    Args:
        graph (PlotGraph): _description_

    Returns:
        int: _description_
    '''
    self._graphs.append(graph)
    return len(self._graphs) - 1

  def addButton(self, button: 'PlotButton') -> int:
    '''_summary_

    Args:
        button (PlotButton): _description_

    Returns:
        int: _description_
    '''
    self._buttons.append(button)
    return len(self._buttons) - 1

  def addSlider(self, slider: 'PlotSlider') -> int:
    '''_summary_

    Args:
        slider (PlotSlider): _description_

    Returns:
        int: _description_
    '''
    self._sliders.append(slider)
    return len(self._sliders) - 1

  def prepareShow(self) -> None:
    '''_summary_
    '''
    if self._prepare:
      args = flsa.prepareArgs(
        figsize             = (self._w / self._dpi, self._h / self._dpi),
        dpi                 = self._dpi,
        facecolor           = self._facecolor,
        constrained_layout  = self._constrained_layout,
      ) | self._extra['main']
      self._fig = plt.figure(**args)
      if self._title:
        titleargs = self._extra['title'] if 'title' in self._extra else {}
        self._fig.suptitle(self._title, **titleargs)
      self._gs = gridspec.GridSpec(nrows=self._nr, ncols=self._nc, figure=self._fig)
      for g in self._graphs:
        g.show()
      # create widgets figure if necessary
      if len(self._buttons) != 0 and len(self._sliders) != 0:
        widgetargs = flsa.prepareArgs(
          figsize             = (self._w / self._dpi, self._hw / self._dpi),
          dpi                 = self._dpi,
          facecolor           = self._facecolor,
          constrained_layout  = self._constrained_layout,
        )
        self._figwidgets = plt.figure(**widgetargs)
        self._gswidgets = gridspec.GridSpec(nrows=self._nrw, ncols=self._ncw, figure=self._figwidgets)
        for b in self._buttons:
          b.show()
        for s in self._sliders:
          s.show()
    self._prepare = False

  def show(self) -> None:
    ''' Show the figure; This is the main routine building the complete drawing.
    '''
    def onClose():
      print('Closing plot window.')
      root.quit()
      root.destroy()

    #print('FIGURE show: ', self.__dict__)
    self.prepareShow()
    # show Tkinter window
    root = tk.Tk()
    root.title('FluidSolve')
    root.iconbitmap(os.path.join(os.path.dirname(__file__),'_matplotlib.ico'))
    root.protocol('WM_DELETE_WINDOW', onClose)
    canvas = FigureCanvasTkAgg(self._fig, master=root)  # A tk.DrawingArea.
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    if len(self._buttons) != 0 and len(self._sliders) != 0:
      canvaswidgets = FigureCanvasTkAgg(self._figwidgets, master=root)  # A tk.DrawingArea.
      canvaswidgets.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    if self._toolbar:
      toolbar = NavigationToolbar2Tk(canvas, root)
      toolbar.update()
    root.mainloop()

  def update(self) -> None:
    '''_summary_
    '''
    for g in self._graphs:
      g.update()
    #TODO
    self._fig.canvas.draw_idle()

  def updateData(self) -> None:
    '''_summary_
    '''
    for g in self._graphs:
      g.updateData()
    self._fig.canvas.draw_idle()

#******************************************************************************
# PLOTGRAPH: matplotlib axes
class PlotGraph:
  '''_summary_

  Args:
      figure (PlotFigure): _description_
  '''
  def __init__(self, figure: PlotFigure, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._r: int | str = args.getArg(
      'r',
      [
        flsa.vFun.istype(int, str, need=False),
        flsa.vFun.tolambda(lambda x: (
          x if isinstance(x, int) else
          slice(None) if x == ':' else
          slice(*map(int, x.split(':')))
        ), need=False),
      ]
    )
    self._c: int | str = args.getArg(
      'c',
      [
        flsa.vFun.istype((int, str)),
        flsa.vFun.tolambda(lambda x: (
          x if isinstance(x, int) else
          slice(None) if x == ':' else
          slice(*map(int, x.split(':')))
        ), need=False),
      ]
    )
    self._polar: bool = args.getArg(
      'polar',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(bool, need=False),
      ]
    )
    self._title: str = args.getArg(
      'title',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._facecolor: str = args.getArg(
      'facecolor',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._edgecolor: str = args.getArg(
      'edgecolor',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict, need=False),
      ]
    )
    #
    self._parent      : Any   = weakref.ref(figure)
    self._idx         : int   = figure.addGraph(self)
    #
    self._ax          : Any   = None
    self._curves      : Any   = []
    self._vlines      : Any   = []
    self._hlines      : Any   = []
    self._annotations : Any   = []
    self._xaxis       : Any   = None
    self._xaxis2      : Any   = None
    self._yaxis       : Any   = None
    self._yaxis2      : Any   = None
    self._grid        : Any   = None
    self._legend      : Any   = None

  @property
  def axes(self) -> Any:
    return self._ax

  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main', 'title', 'axisx1', 'axisy1', 'axisx2', 'axisy2', 'legend'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs

  def setXAxis(self, **kwargs) -> None:
    '''_summary_
    '''
    if not kwargs:
      self._xaxis = None
    else:
      kwargs['type'] = 'x1'
      self._xaxis = PlotAxis(self, **kwargs)

  def setYAxis(self, **kwargs):
    '''_summary_
    '''
    if not kwargs:
      self._yaxis = None
    else:
      kwargs['type'] = 'y1'
      self._yaxis = PlotAxis(self, **kwargs)

  def setXAxis2(self, **kwargs):
    '''_summary_
    '''
    if not kwargs:
      self._xaxis2 = None
    else:
      kwargs['type'] = 'x2'
      self._xaxis2 = PlotAxis(self, **kwargs)

  def setYAxis2(self, **kwargs):
    '''_summary_
    '''
    if not kwargs:
      self._yaxis2 = None
    else:
      kwargs['type'] = 'y2'
      self._yaxis2 = PlotAxis(self, **kwargs)

  def setGrid(self, **kwargs):
    '''_summary_
    '''
    if not kwargs:
      self._grid = None
    else:
      self._grid = PlotGrid(self, **kwargs)

  def setLegend(self, **kwargs):
    '''_summary_
    '''
    pass

  def addCurve(self, curve: 'PlotCurve') -> int:
    '''_summary_

    Args:
        curve (PlotCurve): _description_

    Returns:
        int: _description_
    '''
    self._curves.append(curve)
    return len(self._curves) - 1

  def addVline(self, line: 'PlotLine') -> int:
    '''_summary_

    Args:
        line (PlotLine): _description_

    Returns:
        int: _description_
    '''
    self._vlines.append(line)
    return len(self._vlines) - 1

  def addHline(self, line: 'PlotLine') -> int:
    '''_summary_

    Args:
        line (PlotLine): _description_

    Returns:
        int: _description_
    '''
    self._hlines.append(line)
    return len(self._hlines) - 1

  def addAnnotation(self, annotation: 'PlotAnnotation') -> int:
    '''_summary_

    Args:
        annotation (PlotAnnotation): _description_

    Returns:
        int: _description_
    '''
    self._annotations.append(annotation)
    return len(self._annotations) - 1

  def show(self) -> None:
    ''' Show the graph (axes); This is called by PlotFigure.show().
    '''
    #print('GRAPH show: ', self.__dict__)
    fig = self._parent().figure
    gs = self._parent().gridspec
    args = flsa.prepareArgs(
      polar   = self._polar,
    ) | self._extra['main']
    self._ax = fig.add_subplot(gs[self._r, self._c], **args)
    if self._title:
      titleargs = self._extra['title'] if 'title' in self._extra else {}
      self._ax.set_title(self._title, **titleargs)
    if self._xaxis is not None:
      self._xaxis.show()
    if self._yaxis is not None:
      self._yaxis.show()
    if self._xaxis2 is not None:
      self._xaxis2.show()
    if self._yaxis2 is not None:
      self._yaxis2.show()
    if self._grid is not None:
      self._grid.show()
    if self._legend is not None:
      self._legend.show()
    for c in self._curves:
      c.show()
    for a in self._annotations:
      a.show()
    #ax.title.set_text(self._title)

  def update(self) -> None:
    '''_summary_
    '''
    for c in self._curves:
      c.update()
    for a in self._annotations:
      a.update()
    #TODO

  def updateData(self) -> None:
    '''_summary_
    '''
    for c in self._curves:
      c.updateData()
    for a in self._annotations:
      a.updateData()

#******************************************************************************
# PLOTCURVE: matplotlib data plot
class PlotCurve:
  '''_summary_

  Args:
      graph (PlotGraph): _description_
  '''
  def __init__(self, graph: PlotGraph, **kwargs: int) -> None:
    args : dict = flsa.GetArgs(kwargs)
    self._type: str = args.getArg( #  (line, scatter, bar, ....)
      'type',
      [
        flsa.vFun.default('line'),
        flsa.vFun.istype(str),
        flsa.vFun.inlist('line', 'scatter', 'bar'),
      ]
    )
    self._x: str = args.getArg(
      'x',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(list),
      ]
    )
    self._y: str = args.getArg(
      'y',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(list),
      ]
    )
    self._label: str = args.getArg(
      'label',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._color: str = args.getArg(
      'color',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._alpha: float = args.getArg(
      'alpha',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(float, need=False),
      ]
    )
    self._linestyle: str = args.getArg(
      'linestyle',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._marker: str = args.getArg(
      'marker',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    #
    self._parent      : Any   = weakref.ref(graph)
    self._idx         : int   = graph.addCurve(self)
    #
    self._curve       : Any   = None

  @property
  def x(self) -> list:
    ''' x data.

    Returns:
      list: x data.
    '''
    return self._x

  @x.setter
  def x(self, value:list):
    ''' set x data.

    Args:
      value (list): x data.
    '''
    self._x = value

  @property
  def y(self) -> list:
    ''' y data.

    Returns:
      list: y data.
    '''
    return self._y

  @y.setter
  def y(self, value:list):
    ''' set y data.

    Args:
      value (list): y data.
    '''
    self._y = value

  @property
  def curve(self) -> Any:
    ''' curve object.

    Returns:
      Any: curve object.
    '''
    return self._curve


  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs

  def show(self) -> None:
    ''' Show the data; This is called by PlotGraph.show().
    '''
    #print('CURVE show: ', self.__dict__)
    ax = self._parent().axes
    args = flsa.prepareArgs(
      label     = self._label,
      color     = self._color,
      alpha     = self._alpha,
      linestyle = self._linestyle,
      marker    = self._marker,
    ) | self._extra['main']
    if self._type == 'line':
      self._curve = ax.plot(self._x, self._y, **args)
    elif self._type == 'scatter':
      self._curve = ax.scatter(self._x, self._y, **args)
    elif self._type == 'bar':
      self._curve = ax.bar(self._x, **args)

  def update(self) -> None:
    '''_summary_
    '''
    #TODO
    pass

  def updateData(self) -> None:
    '''_summary_
    '''
    #print('CURVE update: ', self.__dict__)
    if self._type == 'line':
      curve = self._curve[0]
      curve.set_xdata(self._x)
      curve.set_ydata(self._y)
    elif self._type == 'scatter':
      data = np.stack([self._x, self._y]).T
      self._curve.set_offsets(data)
    elif self._type == 'bar':
      curve = self._curve[0]
      curve.set_xdata(self._x)
      curve.set_ydata(self._y)


#******************************************************************************
# PLOTLINE: matplotlib horizontal and vertical lines
class PlotLine:
  '''_summary_

  Args:
      graph (PlotGraph): _description_
  '''
  def __init__(self, graph: PlotGraph, **kwargs: int) -> None:
    args : dict = flsa.GetArgs(kwargs)
    self._typev: str = args.getArg( #  (typev=true = vertical, false = horizontal)
      'typev',
      [
        flsa.vFun.istype(bool),
      ]
    )
    self._v: float = args.getArg(
      'v',
      [
        flsa.vFun.istype(int, float, need=False),
        flsa.vFun.totype(float, need=False),
      ]
    )
    self._min: float = args.getArg(
      'x',
      [
        flsa.vFun.default(1.0),
        flsa.vFun.istype(int, float, need=False),
        flsa.vFun.totype(float, need=False),
      ]
    )
    self._max: float = args.getArg(
      'y',
      [
        flsa.vFun.default(1.0),
        flsa.vFun.istype(int, float, need=False),
        flsa.vFun.totype(float, need=False),
      ]
    )
    self._label: str = args.getArg(
      'label',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._color: str = args.getArg(
      '_color',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._alpha: float = args.getArg(
      'alpha',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(float, need=False),
      ]
    )
    self._linestyle: str = args.getArg(
      'linestyle',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    #
    self._parent    : Any   = weakref.ref(graph)
    if self._typev:
      self._idx     : int   = graph.addVline(self)
    else:
      self._idx     : int   = graph.addHline(self)
    #

  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs


  def show(self) -> None:
    ''' Show the line; This is called by PlotGraph.show().
    '''
    #Axes.axhline(y=0, xmin=0, xmax=1, **kwargs)
    #Of
    #Axes.axvline(y=0, xmin=0, xmax=1, **kwargs)
    pass

#******************************************************************************
# PLOTAXIS: helpler class for matplotlib axis
class PlotAxis:
  '''Configures axis properties.

    Args:
      graph (PlotGraph): The parent graph object to which the axis belongs.
      **kwargs (int): Keyword arguments specifying axis configuration options.
        Supported keys include:
          - type (str): Type of axis ('x1', 'y1', 'x2', 'y2'). Default is None.
                        Is set by the PlotGraph class method
          - share (object): Axis to share values with (e.g., another axis). Default is None.
          - auto (bool): Whether to automatically determine axis limits. Default is True.
          - vmin (int | float): Minimum value of the axis. Default is None.
          - vmax (int | float): Maximum value of the axis. Default is None.
          - vstep (int | float): Step size between major ticks. Default is None.
          - vmstep (int | float): Step size between minor ticks. Default is None.
          - axison (bool): Whether the axis is visible. Default is True.
          - axiscolor (str): Color of the axis line. Default is None.
          - gridon (bool): Whether the grid is visible. Default is True.
          - gridcolor (str): Color of the grid lines. Default is None.
          - labeltxt (str): Label text for the axis. Default is None.
          - labelcolor (str): Color of the axis label. Default is None.
          - labelfmt (str): Format string for axis labels. Default is None.
          - extra (dict): Additional configuration options. Default is an empty dict.

  '''
  def __init__(self, graph: PlotGraph, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._type: str = args.getArg(
      'type',
      [
        flsa.vFun.inlist('x1', 'y1', 'x2', 'y2'),
        flsa.vFun.istype(str),
      ]
    )
    self._shared: str = args.getArg(
      'share',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(object, need=False),
      ]
    )
    self._auto: str = args.getArg(
      'auto',
      [
        flsa.vFun.default(True),
        flsa.vFun.istype(bool),
      ]
    )
    self._vmin: int | float = args.getArg(
      'vmin',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, need=False),
      ]
    )
    self._vmax: int | float = args.getArg(
      'vmax',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, need=False),
      ]
    )
    self._vstep: int | float = args.getArg(
      'vstep',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, need=False),
      ]
    )
    self._vmstep: int | float = args.getArg(  # minor step
      'vmstep',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, need=False),
      ]
    )
    self._axison: str = args.getArg(
      'axison',
      [
        flsa.vFun.default(True),
        flsa.vFun.istype(bool),
      ]
    )
    self._axiscolor: str = args.getArg(
      'axiscolor',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._labeltxt: str = args.getArg(
      'labeltxt',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._labelcolor: str = args.getArg(
      'labelcolor',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._labelfmt: str = args.getArg(
      'labelfmt',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    #
    self._parent: Any = weakref.ref(graph)

  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs

  def show(self) -> dict:
    ''' Show the axis; This is called by PlotGraph.show().
    '''
    ax = self._parent().axes
    if not self._auto:
      if self._vmin is None or self._vmax is None or self._vstep is None:
        raise ValueError ('Need vmin, vmax and vstep.')
      ticks = np.arange(self._vmin, self._vmax + 1, self._vstep)
    args = {}
    if self._type == 'x1':
      if self._shared:
        axshared = self._shared.ax
        ax.sharex(axshared)
      else:
        if not self._auto:
          ax.set_xlim(self._vmin, self._vmax)
          ax.set_xticks(ticks, **args)
          if self._vmstep is not None:
            ax.xaxis.set_minor_locator(AutoMinorLocator(self._vmstep))
        if self._labeltxt is not None:
          labelargs = flsa.prepareArgs(
            color     = self._labelcolor,
          )
          ax.set_xlabel(self._labeltxt, labelargs)
    elif self._type == 'y1':
      if self._shared:
        axshared = self._shared.ax
        ax.sharey(axshared)
      else:
        if not self._auto:
          ax.set_ylim(self._vmin, self._vmax)
          ax.set_yticks(ticks, **args)
          if self._vmstep is not None:
            ax.yaxis.set_minor_locator(AutoMinorLocator(self._vmstep))
        if self._labeltxt is not None:
          labelargs = flsa.prepareArgs(
            color     = self._labelcolor,
          )
          ax.set_ylabel(self._labeltxt, labelargs)
    elif self._type == 'x2':
      ######################## TODO
      pass
    elif self._type == 'y2':
      ######################## TODO
      pass

#******************************************************************************
# PLOTANNOTATION: matplotlib annotation
class PlotAnnotation:
  '''Configures annotation properties.

    Args:
      graph (PlotGraph): The parent graph object to which the annotation belongs.
      **kwargs (int): Keyword arguments specifying annotation configuration options.
        Supported keys include:
  '''
  def __init__(self, graph: PlotGraph, **kwargs: int) -> None:
    args : dict = flsa.GetArgs(kwargs)
    self._label: str = args.getArg(
      'label',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(list),
      ]
    )
    self._x: list = args.getArg(
      'x',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(list),
      ]
    )
    self._y: list = args.getArg(
      'y',
      [
        flsa.vFun.default([]),
        flsa.vFun.istype(list),
      ]
    )
    self._textcoords: str = args.getArg(
      'textcoords',
      [
        flsa.vFun.default('offset points'),
        flsa.vFun.inlist(('offset points', 'axes points', 'data')),
      ]
    )
    self._xoffset: int | float = args.getArg(
      'xoffset',
      [
        flsa.vFun.default(0),
        flsa.vFun.istype(int, float),
      ]
    )
    self._yoffset: int | float = args.getArg(
      'yoffset',
      [
        flsa.vFun.default(0),
        flsa.vFun.istype(int, float),
      ]
    )
    self._xtoggle: int | float = args.getArg(
      'xtoggle',
      [
        flsa.vFun.default(0),
        flsa.vFun.istype(int, float),
      ]
    )
    self._ytoggle: int | float = args.getArg(
      'ytoggle',
      [
        flsa.vFun.default(0),
        flsa.vFun.istype(int, float),
      ]
    )
    self._fontsize: int = args.getArg(
      'fontsize',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, need=False),
      ]
    )
    self._color: str = args.getArg(
      'color',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._bbox: dict = args.getArg(
      'bbox',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(dict, need=False),
      ]
    )
    self._arrow: dict = args.getArg(
      'arrow',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(dict, need=False),
      ]
    )
    self._halignment: str = args.getArg(
      'halignment',
      [
        flsa.vFun.default(None),
        flsa.vFun.inlist('center', 'left', 'right', need=False),
      ]
    )
    self._valignment: str = args.getArg(
      'valignment',
      [
        flsa.vFun.default(None),
        flsa.vFun.inlist('center', 'top', 'bottom', 'baseline', need=False),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    #
    self._parent  : Any = weakref.ref(graph)
    self._idx     : int = graph.addAnnotation(self)
    #
    self._annotations: list = []

  @property
  def x(self) -> list:
    ''' x data.

    Returns:
      list: x data.
    '''
    return self._x

  @x.setter
  def x(self, value:list):
    ''' set x data.

    Args:
      value (list): x data.
    '''
    self._x = value

  @property
  def y(self) -> list:
    ''' y data.

    Returns:
      list: y data.
    '''
    return self._y

  @y.setter
  def y(self, value:list):
    ''' set y data.

    Args:
      value (list): y data.
    '''
    self._y = value

  @property
  def label(self) -> list:
    ''' label data.

    Returns:
      list: label data.
    '''
    return self._label

  @label.setter
  def label(self, value:list):
    ''' set label data.

    Args:
      value (list): label data.
    '''
    self._label = value


  def setExtra(self, key: str, **values: Any) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | values

  def show(self) -> None:
    ''' Show the annotation; This is called by PlotGraph.show().
    '''
    if len(self._x) > 0 and len(self._y) > 0 and len(self._label) > 0:
      if len(self._x) != len(self._y):
        raise ValueError(f'PlotAnnotation: Size of x list: {len(self._x)} not equal to size of y list {len(self._y)}')
      if len(self._x) != len(self._label):
        raise ValueError(f'PlotAnnotation: Size of label list: {len(self._label)} not equal to size of x list {len(self._x)}')
      ax: plt.axes = self._parent().axes
      args = flsa.prepareArgs(
        textcoords  = self._textcoords,
        bbox        = self._bbox,
        arrowprops  = self._arrow,
        fontsize    = self._fontsize,
        color       = self._color,
        ha          = self._halignment,
        va          = self._valignment,
      ) | self._extra['main']
      toggle = 1
      for i in range(len(self._x)):
        self._annotations.append(
          ax.annotate(
            self._label[i],
            xy=(self._x[i], self._y[i]),
            xytext=(self._xoffset + toggle * self._xtoggle, self._yoffset + toggle * self._ytoggle),
            **args
          )
        )
        toggle = -toggle

  def update(self) -> None:
    ''' Update the annotation; This is called by PlotGraph.show().
        Because annotations are erased and redraw, update and updateData are the same.
    '''
    self.updateData()

  def updateData(self) -> None:
    ''' Update the annotation data; This is called by PlotGraph.show().
    '''
    for a in self._annotations:
      a.remove()
    self._annotations = []
    self.show()

#******************************************************************************
# PLOTGRID: helpler class for matplotlib grid
class PlotGrid:
  '''Configures grid properties.

    Args:
      graph (PlotGraph): The parent graph object to which the axis belongs.
      **kwargs (int): Keyword arguments specifying axis configuration options.
        Supported keys include:
          - extra (dict): Additional configuration options. Default is an empty dict.

  '''
  def __init__(self, graph: PlotGraph, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._axis: str = args.getArg(
      'axis',
      [
        flsa.vFun.default('both'),
        flsa.vFun.inlist('x', 'y', 'both'),
        flsa.vFun.istype(str),
      ]
    )
    self._color: str = args.getArg(
      'color',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._linestyle: str = args.getArg(
      'linestyle',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._linewidth: int | float = args.getArg(
      'linewidth',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(int, float, need=False),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    #
    self._parent: Any = weakref.ref(graph)

  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs

  def show(self) -> dict:
    ''' Show the grid; This is called by PlotGraph.show().
    '''
    ax = self._parent().axes
    args = flsa.prepareArgs(
      axis      = self._axis,
      color     = self._color,
      linestyle = self._linestyle,
      linewidth = self._linewidth,
    ) | self._extra['main']
    ax.grid(**args)

#******************************************************************************
# PLOTBUTTON: helpler class for matplotlib button
class PlotButton:
  '''_summary_

  Args:
      fig (PlotFigure): _description_
  '''
  def __init__(self, fig: PlotFigure, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._r: int | str = args.getArg(
      'r',
      [
        flsa.vFun.istype(int, str),
        flsa.vFun.tolambda(lambda x: (
          x if isinstance(x, int) else
          slice(None) if x == ':' else
          slice(*map(int, x.split(':')))
        )),
      ]
    )
    self._c: int | str = args.getArg(
      'c',
      [
        flsa.vFun.istype(int, str),
        flsa.vFun.tolambda(lambda x: (
          x if isinstance(x, int) else
          slice(None) if x == ':' else
          slice(*map(int, x.split(':')))
        )),
      ]
    )
    self._label: str = args.getArg(
      'label',
      [
        flsa.vFun.default(' '),
        flsa.vFun.istype(str),
      ]
    )
    self._color: str = args.getArg(
      'color',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._hovercolor: str = args.getArg(
      'hoovercolor',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._fun: Callable = args.getArg(
      'fun',
      [
        flsa.vFun.istype(Callable),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    #
    self._parent  : Any = weakref.ref(fig)
    self._idx     : int = fig.addButton(self)
    self._ax      : Any = None
    self._widget  : Any = None

  @property
  def widget(self) -> int:
    return self._widget

  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs

  def show(self) -> dict:
    ''' Show the button; This is called by PlotFigure.show().
    '''
    fig = self._parent().figure_widgets
    gs = self._parent().gridspec_widgets
    self._ax = fig.add_subplot(gs[self._r, self._c])
    #self._ax = fig.add_subplot(gs[self._r, self._c], **args)
    ###########################self._ax.set_zorder(10)
    args = flsa.prepareArgs(
      color       = self._color,
      hovercolor  = self._hovercolor,
    )
    self._widget = Button(self._ax, self._label, **args)
    self._widget.on_clicked(self._fun)
    #print('BUTTON show: ', self.__dict__)

#******************************************************************************
# PLOTSLIDER: helpler class for matplotlib slider
class PlotSlider:
  '''_summary_

  Args:
      fig (PlotFigure): _description_
  '''
  def __init__(self, fig: PlotFigure, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._r: int | str = args.getArg(
      'r',
      [
        flsa.vFun.istype(int, str),
        flsa.vFun.tolambda(lambda x: (
          x if isinstance(x, int) else
          slice(None) if x == ':' else
          slice(*map(int, x.split(':')))
        )),
      ]
    )
    self._c: int | str = args.getArg(
      'c',
      [
        flsa.vFun.istype(int, str),
        flsa.vFun.tolambda(lambda x: (
          x if isinstance(x, int) else
          slice(None) if x == ':' else
          slice(*map(int, x.split(':')))
        )),
      ]
    )
    self._label: str = args.getArg(
      'label',
      [
        flsa.vFun.default(' '),
        flsa.vFun.istype(str),
      ]
    )
    self._color: str = args.getArg(
      'color',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._hovercolor: str = args.getArg(
      'hoovercolor',
      [
        flsa.vFun.default(None),
        flsa.vFun.istype(str, need=False),
      ]
    )
    self._vmin: int | float = args.getArg(
      'vmin',
      [
        flsa.vFun.istype(int, float),
      ]
    )
    self._vmax: int | float = args.getArg(
      'vmax',
      [
        flsa.vFun.istype(int, float)
      ]
    )
    self._vstep: int | float = args.getArg(
      'vstep',
      [
        flsa.vFun.default(1),
        flsa.vFun.istype(int, float),
      ]
    )
    self._vinit: int | float = args.getArg(
      'vinit',
      [
        flsa.vFun.default(self._vmin),
        flsa.vFun.istype(int, float),
      ]
    )
    self._fun: Callable = args.getArg(
      'fun',
      [
        flsa.vFun.istype(Callable),
      ]
    )
    self._extra: dict = {}
    self._extra['main'] = args.getArg(
      'extra',
      [
        flsa.vFun.default({}),
        flsa.vFun.istype(dict),
      ]
    )
    #
    self._parent  : Any   = weakref.ref(fig)
    self._idx     : int   = fig.addSlider(self)
    self._ax      : Any   = None
    self._widget  : Any   = None

  @property
  def widget(self) -> int:
    return self._widget

  def setExtra(self, key: str, **kwargs: int) -> None:
    '''Updates extra configuration values for a given key.
       This method merges the provided keyword arguments into the existing
       dictionary stored under `self._extra[key]`.

    Args:
      key (str): The key under which to store extra configuration values.
        Must be one of the allowed values.
      **values (Any): Arbitrary keyword arguments to merge into the extra
        configuration dictionary.
    '''
    if key not in ('main'):
      raise ValueError(f'Invalid extra {key}')
    self._extra[key] = self._extra.get(key, {}) | kwargs

  def show(self) -> dict:
    ''' Show the button; This is called by PlotFigure.show().
    '''
    fig = self._parent().figure_widgets
    gs = self._parent().gridspec_widgets
    self._ax = fig.add_subplot(gs[self._r, self._c])
    ###########################self._ax.set_zorder(10)
    args = flsa.prepareArgs(
      color       = self._color,
      hovercolor  = self._hovercolor,
      label       = self._label,
      valmin      = self._vmin,
      valmax      = self._vmax,
      valinit     = self._vinit,
      valstep     = self._vstep,
    )
    self._widget = Slider(ax=self._ax, **args)
    self._widget.on_changed(self._fun)
