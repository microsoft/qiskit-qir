##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
import pytest

from qiskit import QuantumCircuit

@pytest.fixture()
def while_loop():
    circuit = QuantumCircuit(1, 1)
    circuit.name = "Simple while-loop circuit"
    with circuit.while_loop(circuit.clbits[0], 0):
        circuit.h(0)
        circuit.measure(0, 0)
    return circuit

@pytest.fixture()
def for_loop():
    circuit = QuantumCircuit(4, 0)
    circuit.name = "Simple for-loop circuit"
    circuit.h(3)
    with circuit.for_loop(range(3)) as i:
        circuit.cnot(3, i)
    return circuit

@pytest.fixture()
def for_loop():
    circuit = QuantumCircuit(4, 0)
    circuit.name = "Simple for-loop circuit"
    circuit.h(3)
    with circuit.for_loop(range(3)) as i:
        circuit.cnot(3, i)
    return circuit

@pytest.fixture()
def if_else():
    circuit = QuantumCircuit(3, 2)

    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure(0, 0)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure(0, 1)

    with circuit.if_test((circuit.clbits[0], 0)) as else_:
        circuit.x(2)
    with else_:
        circuit.h(2)
        circuit.z(2)
    return circuit

ignore = ['pytest', 'QuantumCircuit', 'ignore']
cf_fixtures = [s for s in locals() if not s.startswith('__') and s not in ignore]