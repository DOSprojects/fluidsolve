#pytest test_medium.py

import pytest
from pint import UnitRegistry
from fluidsolve.medium import Medium  # Adjust the import path if needed

u = UnitRegistry()

def test_medium_default():
    m = Medium()
    assert m.name == 'water'
    assert m.T.magnitude == 20.0
    assert m.p.magnitude == pytest.approx((1.0 * u.atm).to(u.bar).magnitude, rel=1e-2)
    assert m.rho.magnitude > 0
    assert m.mu.magnitude > 0
    assert m.k.magnitude > 0

def test_medium_custom_conditions():
    m = Medium(T=50 * u.degC, p=2 * u.bar)
    assert m.T.magnitude == pytest.approx(50.0, rel=1e-2)
    assert m.p.magnitude == pytest.approx(2.0, rel=1e-2)

def test_medium_property_setters():
    m = Medium()
    m.T = 60 * u.degC
    m.p = 3 * u.bar
    m.rho = 950 * u.kg/u.m**3
    m.mu = 0.001 * u.Pa*u.s
    m.k = 0.6 * u.W/u.m/u.degK

    assert m.T.magnitude == pytest.approx(60.0, rel=1e-2)
    assert m.p.magnitude == pytest.approx(3.0, rel=1e-2)
    assert m.rho.magnitude == pytest.approx(950.0, rel=1e-2)
    assert m.mu.magnitude == pytest.approx(0.001, rel=1e-2)
    assert m.k.magnitude == pytest.approx(0.6, rel=1e-2)

def test_medium_str():
    m = Medium(name='test_medium')
    s = str(m)
    assert 'Medium test_medium' in s
    assert 'rho:' in s
    assert 'mu:' in s
