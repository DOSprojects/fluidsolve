'''Behavioral unit tests for fluidsolve.network.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,protected-access

import inspect
import types
import numpy as np
import pytest
import fluidsolve.network as module_under_test
import fluidsolve.comp_valve as comp_valve

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Network'])
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

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

class DummyResist(module_under_test.flsb.Comp_Base):
  _group = 'Resistance'
  _part = 'DummyResist'
  _sign = -1.0

  def __init__(self, name: str, head_factor: float=1.0) -> None:
    super().__init__(name=name)
    self.head_factor = head_factor
    self.calls = []

  def calcH(self, Q, sense: int=1, pin: int=1, pout: int=2):
    self.calls.append((Q, sense, pin, pout))
    flow = Q.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude if hasattr(Q, 'to') else float(Q)
    # Dummy friction model: always dissipative head contribution.
    return -self.head_factor * abs(flow) * module_under_test.u.m

class DummyPump(DummyResist):
  _group = 'Pump'
  _part = 'DummyPump'
  _sign = 1.0

class DummyDirectionalResist(module_under_test.flsb.Comp_Base):
  _group = 'Resistance'
  _part = 'DummyDirectionalResist'
  _sign = -1.0

  def __init__(self, name: str, k_forward: float=2.0, k_reverse: float=7.0) -> None:
    super().__init__(name=name)
    self.k_forward = k_forward
    self.k_reverse = k_reverse
    self.calls = []

  def calcH(self, Q, sense: int=1, pin: int=1, pout: int=2):
    self.calls.append((Q, sense, pin, pout))
    flow = Q.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude if hasattr(Q, 'to') else float(Q)
    k = self.k_forward if sense > 0 else self.k_reverse
    return -k * abs(flow) * module_under_test.u.m

def _triangle_network() -> module_under_test.Network:
  return module_under_test.Network(
    name='Loop',
    components=[
      {'comp': DummyPump('P1', head_factor=4.0), 'nodes': ['A', 'B']},
      {'comp': DummyResist('R1', head_factor=1.5), 'nodes': ['B', 'C']},
      {'comp': DummyResist('R2', head_factor=2.0), 'nodes': ['C', 'A']},
    ],
  )

def test_network_defaults_and_empty_strings() -> None:
  network = module_under_test.Network(name='N1')

  assert not network.components
  assert not network.nodes
  assert not network.edges
  assert not network.segments
  assert not network.result
  assert network.nodeString() == '   <none>\n'
  assert network.segmentsString() == '   <none>\n\n'
  assert network.resultString() == '   <empty: run calcNetwork()>\n\n'
  assert network.functionString() == 'No segments in network\n'

def test_network_add_components_validates_entries() -> None:
  comp = DummyResist('R1')

  with pytest.raises(ValueError, match='Invalid component entry'):
    module_under_test.Network(components=['bad'])
  with pytest.raises(ValueError, match='must contain "comp" and "nodes"'):
    module_under_test.Network(components=[{'comp': comp}])
  with pytest.raises(ValueError, match='Node count 1 does not match component ports 2'):
    module_under_test.Network(components=[{'comp': comp, 'nodes': ['A']}])
  with pytest.raises(ValueError, match=r'sense must be \+1 or -1'):
    module_under_test.Network(components=[{'comp': comp, 'nodes': ['A', 'B'], 'sense': 0}])
  with pytest.raises(AttributeError):
    module_under_test.Network(components=[{'comp': object(), 'nodes': ['A', 'B']}])
  with pytest.raises(ValueError, match='Invalid nodes'):
    module_under_test.Network(components=[{'comp': comp, 'nodes': 'AB'}])

def test_network_builds_segments_adjacency_tree_and_cycle_matrices() -> None:
  network = _triangle_network()

  assert len(network.components) == 3
  assert [item['comp'].name for item in network.components] == ['P1', 'R1', 'R2']
  assert list(network.nodes) == ['A', 'B', 'C']
  assert len(network.segments) == 3
  assert set(network.edges) == {'P1:A->B', 'R1:B->C', 'R2:C->A'}
  assert network.adjacency['A'][0] == ('P1:A->B', 'B', 1)
  assert ('R2:C->A', 'C', -1) in network.adjacency['A']
  assert len(network.spanningTree) == 2
  assert len(network.fundamentalCycles) == 1
  assert network.funcs['B'].shape == (3, 3)
  assert network.funcs['C'].shape == (1, 3)
  assert sorted(abs(value) for value in network.funcs['C'][0]) == [1.0, 1.0, 1.0]

def test_network_validation_requires_source_and_resistance_in_loops() -> None:
  with pytest.raises(ValueError, match='no energy source'):
    module_under_test.Network(
      components=[
        {'comp': DummyResist('R1'), 'nodes': ['A', 'B']},
        {'comp': DummyResist('R2'), 'nodes': ['B', 'C']},
        {'comp': DummyResist('R3'), 'nodes': ['C', 'A']},
      ]
    )

  with pytest.raises(ValueError, match='no resistance in loop'):
    module_under_test.Network(
      components=[
        {'comp': DummyPump('P1'), 'nodes': ['A', 'B']},
        {'comp': DummyPump('P2'), 'nodes': ['B', 'C']},
        {'comp': DummyPump('P3'), 'nodes': ['C', 'A']},
      ]
    )

def test_network_detects_duplicate_segments() -> None:
  with pytest.raises(ValueError, match='Duplicate segment R1:A->B'):
    module_under_test.Network(
      components=[
        {'comp': DummyResist('R1'), 'nodes': ['A', 'B']},
        {'comp': DummyResist('R1'), 'nodes': ['A', 'B']},
      ]
    )

def test_network_calc_network_returns_segment_results(monkeypatch) -> None:
  network = module_under_test.Network(
    name='Line',
    components=[{'comp': DummyResist('R1', head_factor=2.0), 'nodes': ['A', 'B']}],
  )
  monkeypatch.setattr(
    module_under_test,
    'root',
    lambda *args, **kwargs: types.SimpleNamespace(success=True, x=np.array([2.5]), message='ok', status=1),
  )
  result = network.calcNetwork(guess=1.2)
  assert len(result) == 1
  assert result[0]['segment'] == 'R1:A->B'
  assert result[0]['Q'].to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(2.5)
  assert result[0]['H'].to(module_under_test.u.m).magnitude == pytest.approx(-5.0)
  assert network.result == result

def test_network_calc_network_uses_segment_sense_and_ports(monkeypatch) -> None:
  comp_fwd = DummyDirectionalResist('R1', k_forward=2.0, k_reverse=7.0)
  network_fwd = module_under_test.Network(
    name='LineForward',
    components=[{'comp': comp_fwd, 'nodes': ['A', 'B'], 'sense': +1}],
  )
  comp_rev = DummyDirectionalResist('R2', k_forward=2.0, k_reverse=7.0)
  network_rev = module_under_test.Network(
    name='LineReverse',
    components=[{'comp': comp_rev, 'nodes': ['A', 'B'], 'sense': -1}],
  )
  def fake_root(func, x0, method='hybr'):  # pylint: disable=unused-argument
    func(np.asarray(x0, dtype=float))
    return types.SimpleNamespace(success=True, x=np.array([2.5]), message='ok', status=1)
  monkeypatch.setattr(
    module_under_test,
    'root',
    fake_root,
  )

  result_fwd = network_fwd.calcNetwork(guess=1.2)
  result_rev = network_rev.calcNetwork(guess=1.2)

  assert len(comp_fwd.calls) >= 1
  assert len(comp_rev.calls) >= 1
  assert comp_fwd.calls[-1][1:] == (+1, 1, 2)
  assert comp_rev.calls[-1][1:] == (-1, 1, 2)
  assert result_fwd[0]['H'].to(module_under_test.u.m).magnitude == pytest.approx(-5.0)
  assert result_rev[0]['H'].to(module_under_test.u.m).magnitude == pytest.approx(-17.5)

def test_network_calc_network_rejects_inconsistent_or_failed_systems(monkeypatch) -> None:
  network = module_under_test.Network(
    components=[
      {'comp': DummyResist('R1'), 'nodes': ['A', 'B']},
      {'comp': DummyResist('R2'), 'nodes': ['C', 'D']},
    ]
  )

  with pytest.raises(ValueError, match='Inconsistent equation system'):
    network.calcNetwork()

  solvable = module_under_test.Network(
    components=[{'comp': DummyResist('R3'), 'nodes': ['A', 'B']}],
  )
  monkeypatch.setattr(
    module_under_test,
    'root',
    lambda *args, **kwargs: types.SimpleNamespace(success=False, message='failed', status=4),
  )

  with pytest.warns(RuntimeWarning, match='did not converge|failed'):
    result = solvable.calcNetwork()

  assert result[0]['Q'].to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(0.0)

def test_network_string_helpers_include_topology_and_results() -> None:
  network = _triangle_network()
  network._result = [
    {
      'segment': 'P1:A->B',
      'Q': 2.0 * module_under_test.u.m**3 / module_under_test.u.h,
      'H': 8.0 * module_under_test.u.m,
    }
  ]

  text = network.toString(detail=1)
  validation = network.networkValidationtoString()

  assert 'Network "Loop"' in text
  assert 'Nodes:' in text
  assert 'A, B, C' in text
  assert 'Segments:' in text
  assert 'Adjacency:' in text
  assert 'node' in text
  assert 'links' in text
  assert 'A    |' in text
  assert 'P1:A->B' in text
  assert '-> B' in text
  assert 'SpanningTree:' in text
  assert 'segment' in text
  assert 'path' in text
  assert 'sense' in text
  assert ' | +1' in text
  assert 'FundamentalCycles:' in text
  assert 'Loop 1:' in text
  assert 'Functions: Combined incidence matrix [B; C]:' in text
  assert 'Result:' in text
  assert 'P1:A->B' in text
  assert 'Loop 1:' in validation
  assert 'Power' in validation
  assert 'Resist' in validation

def test_network_rebuilds_segments_when_valve_state_changes() -> None:
  network = module_under_test.Network(
    name='ValveLoop',
    components=[
      {'comp': DummyPump('P1', head_factor=4.0), 'nodes': ['A', 'B']},
      {'comp': comp_valve.Comp_Valve_3W(name='V1', D=50, state=1), 'nodes': ['B', 'C', 'D']},
      {'comp': DummyResist('R1', head_factor=1.5), 'nodes': ['C', 'A']},
      {'comp': DummyResist('R2', head_factor=1.5), 'nodes': ['D', 'A']},
    ],
  )

  monkey_root = lambda *args, **kwargs: types.SimpleNamespace(success=True, x=np.array([1.0, 1.0, 1.0, 1.0]), message='ok', status=1)
  original_root = module_under_test.root
  module_under_test.root = monkey_root

  def _line_for(segment_name: str, text: str) -> str:
    for line in text.splitlines():
      if segment_name in line:
        return line
    return ''

  try:
    network.calcNetwork(guess=1.0)
    keys_state_1 = set(network.segments.keys())
    assert 'V1:B->C' in keys_state_1
    assert 'V1:B->D' in keys_state_1
    assert network.segments['V1:B->C']['use'] is True
    assert network.segments['V1:B->D']['use'] is False
    text_state_1 = network.segmentsString()
    assert 'comp' in text_state_1
    assert 'nodes' in text_state_1
    assert 'type' in text_state_1
    assert 'ports' in text_state_1
    line_1_used = _line_for('V1:B->C', text_state_1)
    line_1_unused = _line_for('V1:B->D', text_state_1)
    assert '[unused]' not in line_1_used
    assert line_1_used.startswith('   V1:B->C')
    assert ' | ' in line_1_used
    assert 'Comp_Valve_3W' in line_1_used
    assert '1 → 3' in line_1_unused
    assert line_1_unused.startswith('[[ V1:B->D')
    assert line_1_unused.endswith(' ]]')

    network.components[1]['comp'].state = 2
    network.calcNetwork(guess=1.0)
    keys_state_2 = set(network.segments.keys())
    assert 'V1:B->D' in keys_state_2
    assert 'V1:B->C' in keys_state_2
    assert network.segments['V1:B->C']['use'] is False
    assert network.segments['V1:B->D']['use'] is True
    text_state_2 = network.segmentsString()
    line_2_unused = _line_for('V1:B->C', text_state_2)
    line_2_used = _line_for('V1:B->D', text_state_2)
    assert line_2_unused.startswith('[[ V1:B->C')
    assert line_2_unused.endswith(' ]]')
    assert '[unused]' not in line_2_used
    assert line_2_used.startswith('   V1:B->D')
    assert ' | ' in line_2_used
  finally:
    module_under_test.root = original_root
