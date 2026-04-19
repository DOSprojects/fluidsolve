'''Behavioral unit tests for fluidsolve.plotlib.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,protected-access,unused-argument,disallowed-name

import inspect
from types import SimpleNamespace
import pytest
import fluidsolve.plotlib as module_under_test

class DummyParent:
  def __init__(self, axes=None):
    self.axes = axes if axes is not None else DummyAxes()

  def addCurve(self, _curve):
    return 0

  def addAnnotation(self, _annotation):
    return 0

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['PlotAnnotation', 'PlotAxis', 'PlotButton', 'PlotCurve', 'PlotFigure', 'PlotGraph', 'PlotGrid', 'PlotLine', 'PlotSlider'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize('name', [])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

@pytest.mark.parametrize('name', [])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

class DummyCanvas:
  def __init__(self):
    self.draw_idle_calls = 0

  def draw_idle(self) -> None:
    self.draw_idle_calls += 1

class DummyFigureObject:
  def __init__(self):
    self.canvas = DummyCanvas()
    self.suptitle_calls = []
    self.subplots = []

  def suptitle(self, title: str, **kwargs) -> None:
    self.suptitle_calls.append((title, kwargs))

  def add_subplot(self, spec, **kwargs):
    axis = DummyAxes()
    self.subplots.append((spec, kwargs, axis))
    return axis

class DummyGridSpec:
  def __init__(self, nrows: int, ncols: int, figure=None):
    self.nrows = nrows
    self.ncols = ncols
    self.figure = figure

  def __getitem__(self, item):
    return item

class DummyAxes:
  def __init__(self):
    self.calls = []
    self.xaxis = SimpleNamespace(set_minor_locator=lambda loc: self.calls.append(('xminor', loc)))
    self.yaxis = SimpleNamespace(set_minor_locator=lambda loc: self.calls.append(('yminor', loc)))

  def set_title(self, *args, **kwargs):
    self.calls.append(('set_title', args, kwargs))

  def set_xlim(self, *args, **kwargs):
    self.calls.append(('set_xlim', args, kwargs))

  def set_xticks(self, *args, **kwargs):
    self.calls.append(('set_xticks', args, kwargs))

  def set_ylim(self, *args, **kwargs):
    self.calls.append(('set_ylim', args, kwargs))

  def set_yticks(self, *args, **kwargs):
    self.calls.append(('set_yticks', args, kwargs))

  def set_xlabel(self, *args, **kwargs):
    self.calls.append(('set_xlabel', args, kwargs))

  def set_ylabel(self, *args, **kwargs):
    self.calls.append(('set_ylabel', args, kwargs))

  def grid(self, **kwargs):
    self.calls.append(('grid', kwargs))

  def annotate(self, *args, **kwargs):
    self.calls.append(('annotate', args, kwargs))
    return SimpleNamespace(remove=lambda: self.calls.append(('remove_anno',)))

  def plot(self, x, y, **kwargs):
    line = SimpleNamespace(
      set_xdata=lambda data: self.calls.append(('line_x', data)),
      set_ydata=lambda data: self.calls.append(('line_y', data)),
    )
    self.calls.append(('plot', x, y, kwargs))
    return [line]

  def scatter(self, x, y, **kwargs):
    obj = SimpleNamespace(set_offsets=lambda data: self.calls.append(('scatter_offsets', data.tolist() if hasattr(data, 'tolist') else data)))
    self.calls.append(('scatter', x, y, kwargs))
    return obj

  def bar(self, x, **kwargs):
    bar = SimpleNamespace(
      set_xdata=lambda data: self.calls.append(('bar_x', data)),
      set_ydata=lambda data: self.calls.append(('bar_y', data)),
    )
    self.calls.append(('bar', x, kwargs))
    return [bar]

class DummyWidget:
  def __init__(self):
    self.callbacks = []

  def on_clicked(self, callback):
    self.callbacks.append(callback)

  def on_changed(self, callback):
    self.callbacks.append(callback)

def test_plotfigure_prepare_show_and_update_paths(monkeypatch) -> None:
  created_figures = []

  def fake_figure(**kwargs):
    fig = DummyFigureObject()
    created_figures.append((kwargs, fig))
    return fig

  monkeypatch.setattr(module_under_test.plt, 'figure', fake_figure)
  monkeypatch.setattr(module_under_test.gridspec, 'GridSpec', DummyGridSpec)

  fig = module_under_test.PlotFigure(title='Title', nr=2, nc=3, nrw=2, ncw=4)
  graph = SimpleNamespace(show_calls=0, update_calls=0, update_data_calls=0)
  graph.show = lambda: setattr(graph, 'show_calls', graph.show_calls + 1)
  graph.update = lambda: setattr(graph, 'update_calls', graph.update_calls + 1)
  graph.updateData = lambda: setattr(graph, 'update_data_calls', graph.update_data_calls + 1)
  fig.addGraph(graph)
  fig.addButton(SimpleNamespace(show=lambda: None))
  fig.addSlider(SimpleNamespace(show=lambda: None))

  fig.prepareShow()
  fig.update()
  fig.updateData()

  assert len(created_figures) == 2
  assert graph.show_calls == 1
  assert graph.update_calls == 1
  assert graph.update_data_calls == 1
  assert getattr(fig.figure, 'suptitle_calls')[0][0] == 'Title'
  assert fig.gridspec.nrows == 2
  assert fig.gridspec.ncols == 3
  assert fig.gridspec_widgets.nrows == 2
  assert fig.gridspec_widgets.ncols == 4
  assert getattr(fig.figure, 'canvas').draw_idle_calls == 2

def test_plotgraph_show_creates_axes_and_invokes_children() -> None:
  fig = module_under_test.PlotFigure()
  fig._fig = DummyFigureObject()
  fig._gs = DummyGridSpec(1, 1, figure=fig._fig)

  graph = module_under_test.PlotGraph(fig, r='0:1', c=':')
  graph.setXAxis(vmin=0, vmax=10, vstep=5, auto=False, labeltxt='Q')
  graph.setYAxis(vmin=0, vmax=10, vstep=5, auto=False, labeltxt='H')
  graph.setGrid(axis='both')

  curve = SimpleNamespace(show_calls=0, update_calls=0, update_data_calls=0)
  curve.show = lambda: setattr(curve, 'show_calls', curve.show_calls + 1)
  curve.update = lambda: setattr(curve, 'update_calls', curve.update_calls + 1)
  curve.updateData = lambda: setattr(curve, 'update_data_calls', curve.update_data_calls + 1)
  annotation = SimpleNamespace(show_calls=0, update_calls=0, update_data_calls=0)
  annotation.show = lambda: setattr(annotation, 'show_calls', annotation.show_calls + 1)
  annotation.update = lambda: setattr(annotation, 'update_calls', annotation.update_calls + 1)
  annotation.updateData = lambda: setattr(annotation, 'update_data_calls', annotation.update_data_calls + 1)
  graph._curves.append(curve)
  graph._annotations.append(annotation)

  graph.show()
  graph.update()
  graph.updateData()

  assert graph.axes is not None
  assert curve.show_calls == 1
  assert curve.update_calls == 1
  assert curve.update_data_calls == 1
  assert annotation.show_calls == 1
  assert annotation.update_calls == 1
  assert annotation.update_data_calls == 1

def test_plotcurve_line_scatter_bar_show_and_update_data() -> None:
  parent = DummyParent()

  line = module_under_test.PlotCurve(parent, type='line', x=[1, 2], y=[3, 4])
  line.show()
  line.x = [2, 3]
  line.y = [4, 5]
  line.updateData()

  scatter = module_under_test.PlotCurve(parent, type='scatter', x=[1, 2], y=[3, 4])
  scatter.show()
  scatter.x = [2, 3]
  scatter.y = [5, 6]
  scatter.updateData()

  bar = module_under_test.PlotCurve(parent, type='bar', x=[1, 2], y=[3, 4])
  bar.show()
  bar.x = [2, 3]
  bar.y = [6, 7]
  bar.updateData()

  calls = parent.axes.calls
  assert any(c[0] == 'plot' for c in calls)
  assert any(c[0] == 'scatter' for c in calls)
  assert any(c[0] == 'bar' for c in calls)
  assert any(c[0] == 'line_x' for c in calls)
  assert any(c[0] == 'scatter_offsets' for c in calls)
  assert any(c[0] == 'bar_y' for c in calls)

def test_plotannotation_validates_and_updates_annotations() -> None:
  parent = DummyParent()
  annotation = module_under_test.PlotAnnotation(parent, x=[1, 2], y=[3, 4], label=['A', 'B'], xtoggle=1)
  annotation.show()
  annotation.updateData()

  assert len(annotation._annotations) == 2

  bad = module_under_test.PlotAnnotation(parent, x=[1], y=[2, 3], label=['A'])
  with pytest.raises(ValueError, match='Size of x list'):
    bad.show()

def test_plotaxis_grid_and_extra_validation() -> None:
  graph = DummyParent()
  axis = module_under_test.PlotAxis(graph, type='x1', auto=False, vmin=0, vmax=10, vstep=5, labeltxt='Q')
  axis.show()

  grid = module_under_test.PlotGrid(graph, axis='both', color='gray')
  grid.show()

  with pytest.raises(ValueError, match='Need vmin, vmax and vstep'):
    module_under_test.PlotAxis(graph, type='y1', auto=False, vmin=0, vmax=10).show()
  with pytest.raises(ValueError, match='Invalid extra'):
    grid.setExtra('bad', alpha=0.5)

def test_plotaxis_applies_manual_limits_even_when_auto_ticks_remain_enabled() -> None:
  graph = DummyParent()

  axis = module_under_test.PlotAxis(graph, type='y1', vmax=30)
  axis.show()

  assert ('set_ylim', (), {'bottom': None, 'top': 30}) in graph.axes.calls

def test_plotbutton_and_plotslider_show_bind_callbacks(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test, 'Button', lambda *args, **kwargs: DummyWidget())
  monkeypatch.setattr(module_under_test, 'Slider', lambda *args, **kwargs: DummyWidget())

  fig = module_under_test.PlotFigure()
  fig._figwidgets = DummyFigureObject()
  fig._gswidgets = DummyGridSpec(2, 2, figure=fig._figwidgets)

  button = module_under_test.PlotButton(fig, r=0, c=0, label='Run', fun=lambda event: None)
  slider = module_under_test.PlotSlider(fig, r=1, c=0, label='S', vmin=0, vmax=10, fun=lambda value: None)
  button.show()
  slider.show()
  button_widget = getattr(button, '_widget')
  slider_widget = getattr(slider, '_widget')
  button_callbacks = getattr(button_widget, 'callbacks')
  slider_callbacks = getattr(slider_widget, 'callbacks')

  assert button_widget is not None
  assert slider_widget is not None
  assert len(button_callbacks) == 1
  assert len(slider_callbacks) == 1
