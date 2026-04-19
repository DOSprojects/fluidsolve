'''Behavioral unit tests for fluidsolve.path.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,protected-access

import inspect
import pytest
import fluidsolve.path as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Path'])
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

class DummyComp(module_under_test.flsb.Comp_Base):
  _group = 'Test'
  _part = 'Dummy'
  _nports = 2

  def __init__(self, name: str, head: float=0.0, pressure: float=0.0) -> None:
    super().__init__(name=name)
    self.head = head
    self.pressure = pressure
    self.calls = []

  def calcH(self, Q, sense: int=1, pin: int=1, pout: int=2):
    self.calls.append(('H', Q, sense, pin, pout))
    return self.head * sense * module_under_test.u.m

  def calcP(self, Q, sense: int=1, pin: int=1, pout: int=2):
    self.calls.append(('P', Q, sense, pin, pout))
    return self.pressure * sense * module_under_test.u.bar

class DummyValve(module_under_test.flsb.Comp_Base):
  _group = 'Valve'
  _part = 'Valve'
  _nports = 3

  def __init__(self, name: str='V1', head: float=0.0) -> None:
    super().__init__(name=name)
    self.head = head
    self.calls = []

  def calcH(self, Q, sense: int=1, pin: int=1, pout: int=2):
    self.calls.append(('H', Q, sense, pin, pout))
    return self.head * sense * module_under_test.u.m

def test_path_defaults_and_accessors() -> None:
  path = module_under_test.Path(name='Loop')

  assert path.Name == 'Loop'
  assert not path.Components
  assert path.componentsString() == '   <none>\n\n'
  assert str(path) == 'Path "Loop"\n Components:\n   <none>\n\n'

def test_path_add_components_normalizes_two_port_entries() -> None:
  comp = DummyComp('P1', head=2.0)
  path = module_under_test.Path(components=[{'comp': comp, 'sense': -1}])

  item = path.getComp(0)
  assert item == {'comp': comp, 'sense': -1, 'pin': 1, 'pout': 2}

  replacement = {'comp': comp, 'sense': 1, 'pin': 1, 'pout': 2}
  assert path.setComp(0, replacement) is replacement
  assert path.getComp(0) is replacement

def test_path_add_components_requires_valid_entries() -> None:
  comp = DummyComp('P1')
  valve = DummyValve('V1')

  with pytest.raises(ValueError, match='dict expected'):
    module_under_test.Path(components=['bad'])
  with pytest.raises(ValueError, match='missing key "comp"'):
    module_under_test.Path(components=[{'sense': 1}])
  with pytest.raises(ValueError, match='Unknown component'):
    module_under_test.Path(components=[{'comp': object()}])
  with pytest.raises(ValueError, match=r'sense must be \+1 or -1'):
    module_under_test.Path(components=[{'comp': comp, 'sense': 0}])
  with pytest.raises(ValueError, match='need pin and pout'):
    module_under_test.Path(components=[{'comp': valve}])
  with pytest.raises(ValueError, match='Invalid ports'):
    module_under_test.Path(components=[{'comp': valve, 'pin': 0, 'pout': 4}])

def test_path_add_components_keeps_explicit_ports_for_multiport_components() -> None:
  valve = DummyValve('V1', head=1.5)
  path = module_under_test.Path(components=[{'comp': valve, 'sense': -1, 'pin': 3, 'pout': 2}])

  assert path.getComp(0) == {'comp': valve, 'sense': -1, 'pin': 3, 'pout': 2}

def test_path_calcH_and_calcP_sum_component_results_with_sense() -> None:
  comp1 = DummyComp('A', head=2.0, pressure=0.5)
  comp2 = DummyComp('B', head=3.0, pressure=1.5)
  path = module_under_test.Path(
    components=[
      {'comp': comp1, 'sense': 1},
      {'comp': comp2, 'sense': -1},
    ]
  )

  total_h = path.calcH(4 * module_under_test.u.m**3 / module_under_test.u.h, sense=-1)
  total_p = path.calcP(4 * module_under_test.u.m**3 / module_under_test.u.h, sense=-1)

  assert total_h.to(module_under_test.u.m).magnitude == pytest.approx(1.0)
  assert total_p.to(module_under_test.u.bar).magnitude == pytest.approx(1.0)
  assert comp1.calls[0][2:] == (-1, 1, 2)
  assert comp2.calls[0][2:] == (1, 1, 2)
  assert comp1.calls[1][2:] == (-1, 1, 2)
  assert comp2.calls[1][2:] == (1, 1, 2)

def test_path_calcHprofile_returns_incremental_and_total_points() -> None:
  comp1 = DummyComp('A', head=2.0)
  comp2 = DummyComp('B', head=3.0)
  path = module_under_test.Path(components=[{'comp': comp1}, {'comp': comp2}])

  points = path.calcHprofile(5, incr=True)

  assert [point.name for point in points] == ['0:A', '1:B', 'Tot']
  assert [point.Qmag for point in points] == [5.0, 5.0, 5.0]
  assert [point.Hmag for point in points] == [2.0, 5.0, 5.0]

def test_path_calcHprofile_non_incremental_uses_component_head_per_step() -> None:
  comp1 = DummyComp('A', head=2.0)
  comp2 = DummyComp('B', head=3.0)
  path = module_under_test.Path(components=[{'comp': comp1}, {'comp': comp2}])

  points = path.calcHprofile(5, incr=False, sense=-1)

  assert [point.Hmag for point in points] == [-2.0, -3.0, -5.0]
  assert comp1.calls[0][2:] == (-1, 1, 2)
  assert comp2.calls[0][2:] == (-1, 1, 2)

def test_path_to_string_formats_component_listing_and_detail() -> None:
  comp1 = DummyComp('PumpA', head=2.0)
  valve = DummyValve('Valve1', head=1.0)
  path = module_under_test.Path(
    name='Loop',
    components=[
      {'comp': comp1, 'sense': 1},
      {'comp': valve, 'sense': -1, 'pin': 3, 'pout': 1},
    ]
  )

  text = path.toString(detail=1)

  assert 'Path "Loop"' in text
  assert 'Components:' in text
  assert 'PumpA' in text
  assert 'Valve1' in text
  assert 'dir: \u2192' in text
  assert 'dir: \u2190' in text
  assert 'ports: 3 -> 1' in text
  assert 'Count: 2' in text
