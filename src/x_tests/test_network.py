'''Behavioral unit tests for fluidsolve.network.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,protected-access

import inspect
import pytest
import fluidsolve.network as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Network'])
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
    return self.head_factor * flow * sense * module_under_test.u.m

class DummyPump(DummyResist):
  _group = 'Pump'
  _part = 'DummyPump'
  _sign = 1.0

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

  assert not network.Nodes
  assert not network.Edges
  assert not network.Segments
  assert not network.Result
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

  assert list(network.Nodes) == ['A', 'B', 'C']
  assert len(network.Segments) == 3
  assert set(network.Edges) == {'P1:A->B', 'R1:B->C', 'R2:C->A'}
  assert network.Adjacency['A'][0] == ('P1:A->B', 'B', 1)
  assert ('R2:C->A', 'C', -1) in network.Adjacency['A']
  assert len(network.SpanningTree) == 2
  assert len(network.FundamentalCycles) == 1
  assert network.Funcs['B'].shape == (3, 3)
  assert network.Funcs['C'].shape == (1, 3)
  assert sorted(abs(value) for value in network.Funcs['C'][0]) == [1.0, 1.0, 1.0]

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
    'fsolve',
    lambda fun, x0, full_output=True: ([2.5], None, 1, 'ok'),
  )

  result = network.calcNetwork(iguess=1.2)

  assert len(result) == 1
  assert result[0]['segment'] == 'R1:A->B'
  assert result[0]['Q'].to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(2.5)
  assert result[0]['H'].to(module_under_test.u.m).magnitude == pytest.approx(5.0)
  assert network.Result == result

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
    'fsolve',
    lambda fun, x0, full_output=True: (x0, None, 0, 'failed'),
  )

  with pytest.raises(ValueError, match='failed'):
    solvable.calcNetwork()

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
  assert 'Segments:' in text
  assert 'Adjacency:' in text
  assert 'Functions: Combined incidence matrix [B; C]:' in text
  assert 'Result:' in text
  assert 'P1:A->B' in text
  assert 'Loop 1:' in validation
  assert 'Power' in validation
  assert 'Resist' in validation
