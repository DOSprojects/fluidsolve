'''Behavioral unit tests for fluidsolve.plotext.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,protected-access,unused-argument

import inspect
from types import SimpleNamespace
import numpy as np
import pytest
import fluidsolve.plotext as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['PlotQHcurve'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize('name', [])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

class DummyFigure:
  def __init__(self, **kwargs):
    self.kwargs = kwargs
    self.hw = kwargs.get('hw', 50)
    self.nrw = kwargs.get('nrw', 1)
    self.ncw = kwargs.get('ncw', 1)
    self.prepare_show_calls = 0
    self.show_calls = 0
    self.update_calls = 0
    self.update_data_calls = 0

  def prepareShow(self) -> None:
    self.prepare_show_calls += 1

  def show(self) -> None:
    self.show_calls += 1

  def update(self) -> None:
    self.update_calls += 1

  def updateData(self) -> None:
    self.update_data_calls += 1

class DummyGraph:
  def __init__(self, figure, r=0, c=0):
    self.figure = figure
    self.r = r
    self.c = c
    self.xaxis = None
    self.yaxis = None
    self.grid = None

  def setXAxis(self, **kwargs) -> None:
    self.xaxis = kwargs

  def setYAxis(self, **kwargs) -> None:
    self.yaxis = kwargs

  def setGrid(self, **kwargs) -> None:
    self.grid = kwargs

class DummyCurve:
  def __init__(self, graph, **kwargs):
    self.graph = graph
    self.kwargs = kwargs
    self.x = None
    self.y = None

class DummyAnnotation:
  def __init__(self, graph, **kwargs):
    self.graph = graph
    self.kwargs = kwargs
    self.x = None
    self.y = None
    self.label = None

class DummyButton:
  def __init__(self, figure, **kwargs):
    self.figure = figure
    self.kwargs = kwargs

class DummySlider:
  def __init__(self, figure, **kwargs):
    self.figure = figure
    self.kwargs = kwargs
    self.reset_calls = 0
    self.widget = SimpleNamespace(reset=self._reset)

  def _reset(self) -> None:
    self.reset_calls += 1

def _install_plot_stubs(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test.flsp, 'PlotFigure', DummyFigure)
  monkeypatch.setattr(module_under_test.flsp, 'PlotGraph', DummyGraph)
  monkeypatch.setattr(module_under_test.flsp, 'PlotCurve', DummyCurve)
  monkeypatch.setattr(module_under_test.flsp, 'PlotAnnotation', DummyAnnotation)
  monkeypatch.setattr(module_under_test.flsp, 'PlotButton', DummyButton)
  monkeypatch.setattr(module_under_test.flsp, 'PlotSlider', DummySlider)

def test_plot_qhcurve_initializes_graph_axes_and_optional_widgets(monkeypatch) -> None:
  _install_plot_stubs(monkeypatch)

  plotter = module_under_test.PlotQHcurve(
    xmin=1,
    xmax=9,
    xstep=2,
    ymin=0,
    ymax=12,
    ystep=3,
    xlabel='Flow',
    ylabel='Head',
    sliders=[{'label': 'Speed'}],
    title='Plot',
  )
  fig_kwargs = getattr(plotter._fig, 'kwargs')
  graph_xaxis = getattr(plotter._graph, 'xaxis')
  graph_yaxis = getattr(plotter._graph, 'yaxis')
  graph_grid = getattr(plotter._graph, 'grid')

  assert isinstance(plotter._fig, DummyFigure)
  assert isinstance(plotter._graph, DummyGraph)
  assert fig_kwargs == {'title': 'Plot'}
  assert graph_xaxis == {'vmin': 1, 'vmax': 9, 'vstep': 2, 'labeltxt': 'Flow'}
  assert graph_yaxis == {'vmin': 0, 'vmax': 12, 'vstep': 3, 'labeltxt': 'Head'}
  assert graph_grid == {'axis': 'both'}
  assert plotter._fig.hw == 60
  assert plotter._fig.nrw == 2
  assert plotter._fig.ncw == 10
  assert isinstance(plotter._buttonreset, DummyButton)
  assert len(plotter._sliders) == 1
  assert plotter._sliders[0].kwargs['label'] == 'Speed'
  assert plotter._sliders[0].kwargs['r'] == 1
  assert plotter._sliders[0].kwargs['c'] == '0:9'

def test_prepare_show_creates_plot_objects_and_populates_data(monkeypatch) -> None:
  _install_plot_stubs(monkeypatch)

  class DummyPump:
    def __init__(self):
      self.Qb = SimpleNamespace(magnitude=1.0)
      self.Qe = SimpleNamespace(magnitude=4.0)

    def calcH(self, flow, sense):
      return SimpleNamespace(magnitude=np.array([9.0, 7.0, 0.0, -1.0]))

  class DummyCircuit:
    def calcH(self, flow, sense):
      return SimpleNamespace(magnitude=np.array([-1.0, -2.0, -3.0, -4.0]))

  class DummyPoint:
    def __init__(self, name: str, qmag: float, hmag: float):
      self.name = name
      self.Qmag = qmag
      self.Hmag = hmag
      self.update_calls = 0

    def update(self) -> None:
      self.update_calls += 1

  monkeypatch.setattr(module_under_test.np, 'linspace', lambda start, stop, count: np.array([start, 2.0, 3.0, stop]))
  monkeypatch.setattr(module_under_test.np, 'argmax', lambda values: next((i for i, value in enumerate(values) if value), 0))

  wpoint = DummyPoint('WP1', 2.5, 6.0)
  spoint = DummyPoint('SP1', 1.5, 3.0)
  plotter = module_under_test.PlotQHcurve(
    pumps=[DummyPump()],
    circuits=[DummyCircuit()],
    wpoints=[wpoint],
    spoints=[spoint],
    npts=4,
    Qmax=8,
  )

  plotter.prepareShow()
  prepare_show_calls = getattr(plotter._fig, 'prepare_show_calls')

  assert plotter._prepare is False
  assert prepare_show_calls == 1
  assert len(plotter._curvepumps) == 1
  assert len(plotter._curvecircuits) == 1
  assert len(plotter._curvewpts) == 1
  assert len(plotter._curvespts) == 1
  assert np.allclose(np.asarray(plotter._curvepumps[0].x), np.asarray([1.0, 2.0]))
  assert np.allclose(np.asarray(plotter._curvepumps[0].y), np.asarray([9.0, 7.0]))
  assert np.allclose(np.asarray(plotter._curvecircuits[0].x), np.asarray([0.001, 2.0, 3.0, 8.0]))
  assert np.allclose(np.asarray(plotter._curvecircuits[0].y), np.asarray([1.0, 2.0, 3.0, 4.0]))
  assert plotter._curvewpts[0].x == [2.5]
  assert plotter._curvewpts[0].y == [6.0]
  assert plotter._annotationwpts[0].label == ['WP1']
  assert plotter._curvespts[0].x == [1.5]
  assert plotter._curvespts[0].y == [3.0]
  assert plotter._annotationspts[0].label == ['SP1']
  assert wpoint.update_calls == 1
  assert spoint.update_calls == 1

def test_prepare_show_runs_only_once_and_show_delegates(monkeypatch) -> None:
  _install_plot_stubs(monkeypatch)

  plotter = module_under_test.PlotQHcurve()

  plotter.prepareShow()
  plotter.prepareShow()
  plotter.show()
  prepare_show_calls = getattr(plotter._fig, 'prepare_show_calls')
  show_calls = getattr(plotter._fig, 'show_calls')

  assert prepare_show_calls == 1
  assert show_calls == 1

def test_update_and_update_data_delegate_to_figure(monkeypatch) -> None:
  _install_plot_stubs(monkeypatch)
  plotter = module_under_test.PlotQHcurve()

  calls = []
  monkeypatch.setattr(plotter, '_calcAndUpdate', lambda: calls.append('calc'))

  plotter.update()
  plotter.updateData()
  update_calls = getattr(plotter._fig, 'update_calls')
  update_data_calls = getattr(plotter._fig, 'update_data_calls')

  assert calls == ['calc', 'calc']
  assert update_calls == 2
  assert update_data_calls == 1

def test_reset_controls_resets_each_slider(monkeypatch) -> None:
  _install_plot_stubs(monkeypatch)
  plotter = module_under_test.PlotQHcurve(sliders=[{'label': 'A'}, {'label': 'B'}])

  plotter._resetControls(event=None)

  assert [slider.reset_calls for slider in plotter._sliders] == [1, 1]
