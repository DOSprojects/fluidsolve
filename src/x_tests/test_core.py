'''Behavioral unit tests for fluidsolve.core.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,protected-access

import inspect
import pytest
import fluidsolve.core as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

def test_public_classes_exist() -> None:
  public_class_names = [
    name
    for name, obj in inspect.getmembers(module_under_test, inspect.isclass)
    if obj.__module__ == module_under_test.__name__ and not name.startswith('_')
  ]

  for name in public_class_names:
    obj = getattr(module_under_test, name)
    assert inspect.isclass(obj)

@pytest.mark.parametrize(
  'name',
  [
    'getComp',
    'getDefaultMaterial',
    'getDefaultMedium',
    'getNetwork',
    'getPath',
    'getWpt',
    'initFluidsolve',
    'registerAllComps',
    'registerComp',
    'registerComps',
    'setDefaultMaterial',
    'setDefaultMedium',
  ],
)
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_init_fluidsolve_applies_prefixes_and_default_objects() -> None:
  material = module_under_test.flsma.Material(name='steel', rho=800.0, k=2.0, e=5.0)
  medium = module_under_test.flsme.Medium(prd='water')

  module_under_test.initFluidsolve(
    prefix_comp='X',
    prefix_wpt='Y',
    default_material=material,
    default_medium=medium,
  )

  assert module_under_test._prefix_comp == 'X'
  assert module_under_test._prefix_wpt == 'Y'
  assert module_under_test.getDefaultMaterial() is material
  assert module_under_test.getDefaultMedium() is medium

def test_init_fluidsolve_converts_default_names_to_objects() -> None:
  module_under_test.initFluidsolve(default_material='rvs', default_medium='water')

  assert isinstance(module_under_test.getDefaultMaterial(), module_under_test.flsma.Material)
  assert isinstance(module_under_test.getDefaultMedium(), module_under_test.flsme.Medium)

def test_register_comp_rejects_duplicate_by_default(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test, '_comps', {'Demo': object()})

  with pytest.raises(ValueError, match='already registered'):
    module_under_test.registerComp('Demo', object())

def test_register_comp_returns_false_when_duplicate_and_raiseerror_false(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test, '_comps', {'Demo': object()})

  assert module_under_test.registerComp('Demo', object(), raiseerror=False) is False

def test_register_comp_adds_new_entry(monkeypatch) -> None:
  registry = {}
  monkeypatch.setattr(module_under_test, '_comps', registry)
  marker = object()

  assert module_under_test.registerComp('Demo', marker) is True
  assert registry['Demo'] is marker

def test_register_comps_returns_false_if_any_registration_fails(monkeypatch) -> None:
  calls = []

  def fake_register(name: str, value: object, raiseerror: bool=True) -> bool:
    calls.append((name, value, raiseerror))
    return name != 'Bad'

  monkeypatch.setattr(module_under_test, 'registerComp', fake_register)

  result = module_under_test.registerComps({'Good': 1, 'Bad': 2}, raiseerror=False)

  assert result is False
  assert calls == [('Good', 1, False), ('Bad', 2, False)]

def test_register_all_comps_returns_false_if_any_group_fails(monkeypatch) -> None:
  results = iter([True, False, True, True])
  calls = []

  def fake_register_comps(comps: dict, raiseerror: bool=True) -> bool:
    calls.append((set(comps), raiseerror))
    return next(results)

  monkeypatch.setattr(module_under_test, 'registerComps', fake_register_comps)

  assert module_under_test.registerAllComps() is False
  assert len(calls) == 4
  assert {'Dummy', 'Reverse'} == calls[0][0]
  assert 'Hstatic' in calls[1][0]
  assert 'Pump' in calls[2][0]
  assert 'Valve_NR' in calls[3][0]

def test_default_setters_replace_defaults() -> None:
  material = module_under_test.flsma.Material(name='custom', rho=900.0, k=3.0, e=6.0)
  medium = module_under_test.flsme.Medium(prd='water')

  module_under_test.setDefaultMaterial(material)
  module_under_test.setDefaultMedium(medium)

  assert module_under_test.getDefaultMaterial() is material
  assert module_under_test.getDefaultMedium() is medium

def test_get_comp_builds_instance_with_defaults(monkeypatch) -> None:
  class DummyComp:
    def __init__(self, **kwargs):
      self.kwargs = kwargs

  medium = module_under_test.flsme.Medium(prd='water')
  material = module_under_test.flsma.Material(name='custom', rho=900.0, k=2.0, e=4.0)
  monkeypatch.setattr(module_under_test, '_comps', {'Demo': DummyComp})
  monkeypatch.setattr(module_under_test, '_default_medium', medium)
  monkeypatch.setattr(module_under_test, '_default_material', material)
  monkeypatch.setattr(module_under_test, '_comp_index', 0)
  monkeypatch.setattr(module_under_test, '_prefix_comp', 'C')

  comp = module_under_test.getComp(comp='Demo', answer=42)

  assert isinstance(comp, DummyComp)
  assert comp.kwargs['name'] == 'CA'
  assert comp.kwargs['medium'] is medium
  assert comp.kwargs['e'] == material.e
  assert comp.kwargs['answer'] == 42

def test_get_comp_uses_explicit_values_and_rejects_unknown_type(monkeypatch) -> None:
  class DummyComp:
    def __init__(self, **kwargs):
      self.kwargs = kwargs

  medium = module_under_test.flsme.Medium(prd='water')
  monkeypatch.setattr(module_under_test, '_comps', {'Demo': DummyComp})

  comp = module_under_test.getComp(comp='Demo', name='P1', medium=medium, e=3, state=1)

  assert comp.kwargs == {'name': 'P1', 'medium': medium, 'e': 3, 'state': 1}

  with pytest.raises(ValueError, match='Component type "Missing" is not defined'):
    module_under_test.getComp(comp='Missing')

def test_get_wpt_builds_instance_with_generated_or_explicit_name(monkeypatch) -> None:
  class DummyWpt:
    def __init__(self, **kwargs):
      self.kwargs = kwargs

  monkeypatch.setattr(module_under_test, '_wpts', {'x': DummyWpt})
  monkeypatch.setattr(module_under_test, '_wpt_index', 0)
  monkeypatch.setattr(module_under_test, '_prefix_wpt', 'Wp')

  auto = module_under_test.getWpt(wpt='x', pressure=1)
  named = module_under_test.getWpt(wpt='x', name='Node1', pressure=2)

  assert auto.kwargs == {'name': 'Wp0', 'pressure': 1}
  assert named.kwargs == {'name': 'Node1', 'pressure': 2}

  with pytest.raises(ValueError, match='Workingpoint type "missing" is not defined'):
    module_under_test.getWpt(wpt='missing')

def test_get_path_and_network_delegate_to_target_classes(monkeypatch) -> None:
  class DummyPath:
    def __init__(self, **kwargs):
      self.kwargs = kwargs

  class DummyNetwork:
    def __init__(self, **kwargs):
      self.kwargs = kwargs

  monkeypatch.setattr(module_under_test.flspath, 'Path', DummyPath)
  monkeypatch.setattr(module_under_test.flsnet, 'Network', DummyNetwork)

  path = module_under_test.getPath(name='P', comps=[1, 2])
  network = module_under_test.getNetwork(name='N', components=[])
  path_kwargs = getattr(path, 'kwargs')
  network_kwargs = getattr(network, 'kwargs')

  assert isinstance(path, DummyPath)
  assert isinstance(network, DummyNetwork)
  assert path_kwargs == {'name': 'P', 'comps': [1, 2]}
  assert network_kwargs == {'name': 'N', 'components': []}

def test_generated_names_follow_current_sequence_rules(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test, '_comp_index', 0)
  monkeypatch.setattr(module_under_test, '_wpt_index', 0)
  monkeypatch.setattr(module_under_test, '_prefix_comp', 'C')
  monkeypatch.setattr(module_under_test, '_prefix_wpt', 'Wp')

  comp_names = [module_under_test._getCompName() for _ in range(28)]
  wpt_names = [module_under_test._getWptName() for _ in range(3)]

  assert comp_names[:4] == ['CA', 'CB', 'CC', 'CD']
  assert comp_names[25:] == ['CZ', 'CAA', 'CAB']
  assert wpt_names == ['Wp0', 'Wp1', 'Wp2']
