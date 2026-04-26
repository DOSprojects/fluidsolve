'''Auto-generated tests for fluidsolve.comp_base.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring

import inspect
import types
import pytest
import fluidsolve.comp_base as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Comp_Base', 'Comp_Dummy', 'Comp_Reverse'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

def test_public_functions_are_callable() -> None:
  public_function_names = [
    name
    for name, obj in inspect.getmembers(module_under_test, inspect.isfunction)
    if obj.__module__ == module_under_test.__name__ and not name.startswith('_')
  ]
  for name in public_function_names:
    obj = getattr(module_under_test, name)
    assert callable(obj)

@pytest.mark.parametrize('name', ['NO_DIAMETER', 'NO_LENGTH', 'NO_MEDIUM', 'Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_comp_base_defaults_and_properties() -> None:
  comp = module_under_test.Comp_Base(name='base', state=3)
  assert comp.name == 'base'
  assert comp.group == 'Base'
  assert comp.part == 'Base'
  assert comp.nports == 2
  assert comp.ports == [[1, 2]]
  assert comp.state == 3
  assert comp.sign == -1.0
  assert comp.e == module_under_test.flsme.CTE_E_RVS.to(module_under_test.u.um)
  assert isinstance(comp.medium, module_under_test.flsme.Medium)

def test_comp_base_medium_and_roughness_setters() -> None:
  comp = module_under_test.Comp_Base()
  medium = module_under_test.flsme.Medium(prd='water')
  comp.medium = medium
  assert comp.medium is medium
  comp.medium = 'water'
  assert isinstance(comp.medium, module_under_test.flsme.Medium)
  assert comp.medium.name == 'water'
  comp.e = 15
  roughness = comp.e
  assert isinstance(roughness, module_under_test.Quantity)
  assert getattr(roughness, 'magnitude') == 15
  assert getattr(roughness, 'units') == module_under_test.u.um

def test_comp_base_medium_setter_rejects_invalid_type() -> None:
  comp = module_under_test.Comp_Base()
  with pytest.raises(TypeError, match='Medium must be a string or an instance of Medium'):
    comp.medium = 123  # type: ignore[assignment]

def test_comp_base_state_setter_updates_state() -> None:
  comp = module_under_test.Comp_Base()
  comp.state = 2.5
  assert comp.state == 2.5

def test_comp_base_calc_methods_and_clone() -> None:
  comp = module_under_test.Comp_Base(name='base')

  assert comp.calcH(5).to(module_under_test.u.m).magnitude == 0.0
  assert comp.calcP(5).to(module_under_test.u.bar).magnitude == pytest.approx(0.0)

  clone = comp.clone()
  assert isinstance(clone, module_under_test.Comp_Base)
  assert clone is not comp
  assert clone.name == comp.name
  assert clone.medium is not comp.medium
  assert clone.medium.name == comp.medium.name

def test_comp_base_calcq_uses_root_result(monkeypatch) -> None:
  comp = module_under_test.Comp_Base()

  def fake_root(func=None, x0=None, method=None):
    assert x0 == 200
    assert method in ('hybr', 'lm', 'df-sane')
    assert func(12) == pytest.approx(0.0)
    return types.SimpleNamespace(success=True, x=[12], message='ok', status=1)

  def fake_calcH(flow, sense=1, pin=1, pout=2):
    assert sense == 1
    assert pin == 1
    assert pout == 2
    return flow.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude * module_under_test.u.m / 12

  monkeypatch.setattr(module_under_test, 'root', fake_root)
  monkeypatch.setattr(comp, 'calcH', fake_calcH)

  result = comp.calcQ(1 * module_under_test.u.m, guess=200)
  assert result.magnitude == 12
  assert result.units == module_under_test.u.m**3 / module_under_test.u.h

def test_comp_base_string_representation_contains_metadata() -> None:
  comp = module_under_test.Comp_Base(name='base', state=2)

  text = str(comp)
  assert 'Component: "base" [Base]' == text

def test_comp_base_format_representation_supports_detail() -> None:
  comp = module_under_test.Comp_Base(name='base', state=2)

  text = f'{comp:1}'
  assert 'Component: "base" [Base:Base]' in text
  assert 'state: 2' in text
  assert 'sign: -1' in text

def test_comp_dummy_initializes_as_resistance() -> None:
  comp = module_under_test.Comp_Dummy(name='dummy')

  assert comp.group == 'Base'
  assert comp.part == 'Dummy'
  assert comp.name == 'dummy'
  assert isinstance(comp.medium, module_under_test.flsme.Medium)

def test_comp_reverse_delegates_calc_methods_and_attributes() -> None:
  class ReverseableComp(module_under_test.Comp_Base):
    def __init__(self):
      super().__init__(name='wrapped')

    def calcK(self, Q, sense=1, pin=1, pout=2):
      return (Q, sense, pin, pout)

    def calcH(self, Q, sense=1, pin=1, pout=2):
      return sense * 3 * module_under_test.u.m

  wrapped = ReverseableComp()
  comp = module_under_test.Comp_Reverse(name='rev', reverse=wrapped)

  assert comp.calcK(5, sense=1, pin=2, pout=3) == (5, -1, 2, 3)
  assert comp.calcH(5, sense=1, pin=2, pout=3) == -3 * module_under_test.u.m
  assert comp.name == 'rev'
  assert comp.part == 'Reverse'
  assert 'reverse:' in str(comp)
  assert '"wrapped"  [Base]' in str(comp)
  assert ' reverse' in f'{comp:1}'
  assert 'Component: "wrapped" [Base:Base]' in f'{comp:1}'

def test_comp_reverse_raises_when_wrapped_component_has_no_calck() -> None:
  class HeadOnlyComp(module_under_test.Comp_Base):
    def calcH(self, Q, sense=1, pin=1, pout=2):
      return 0 * module_under_test.u.m

  wrapped = HeadOnlyComp(name='wrapped')
  comp = module_under_test.Comp_Reverse(reverse=wrapped)

  with pytest.raises(AttributeError, match='has no calcK'):
    comp.calcK(5)
