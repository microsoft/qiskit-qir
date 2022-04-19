##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from typing import List

import pytest
from qiskit_qir.elements import QiskitModule

from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit_qir.visitor import BasicQisVisitor, ProfileError

PROFILE_A_MESSAGE = "Support branching based on measurement requires profileA"
PROFILE_B_MESSAGE = "Support for qubit reuse requires profileB"

static_generator_variations = [
    [False, False],
    [False, True],
    [True, False],
    [True, True]
]

# test circuits


def teleport() -> QuantumCircuit:
    q = QuantumRegister(3, name="q")
    cr = ClassicalRegister(2, name="cr")
    circuit = QuantumCircuit(q, cr, name="Teleport")
    circuit.h(1)
    circuit.cx(1, 2)
    circuit.cx(0, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    circuit.x(2).c_if(cr, int("10", 2))
    circuit.z(2).c_if(cr, int("01", 2))
    return circuit


def use_after_measure():
    circuit = QuantumCircuit(2, 2)

    circuit.h(0)
    circuit.measure(0, 0)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure(1, 1)

    return circuit


def use_another_after_measure():
    circuit = QuantumCircuit(3, 2)

    circuit.h(0)
    circuit.measure(0, 0)
    circuit.h(1)
    circuit.cx(1, 2)
    circuit.measure(1, 1)

    return circuit

# Create override visitor which allows us to vary the
# codegen behavior


class ConfigurableQisVisitor(BasicQisVisitor):
    def __init__(self, matrix: List[bool], profiles: List[str] = []):
        BasicQisVisitor.__init__(self, profiles)
        self._matrix = matrix

    def visit_qiskit_module(self, module):
        BasicQisVisitor.visit_qiskit_module(self, module)
        self._module.use_static_qubit_alloc(self._matrix[0])
        self._module.use_static_result_alloc(self._matrix[1])


# Utility using new visitor and codegen matrix
def matrix_to_qir(circuit, matrix: List[bool], profiles: List[str] = []):
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = ConfigurableQisVisitor(matrix, profiles)
    module.accept(visitor)
    return visitor.ir()


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_branching_on_measurement_fails_without_profileA(matrix):
    circuit = teleport()
    with pytest.raises(ProfileError) as exc_info:
        _ = matrix_to_qir(circuit, matrix, profiles=[""])

    exception_raised = str(exc_info.value)
    assert exception_raised == PROFILE_A_MESSAGE


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_branching_on_measurement_passses_without_profileA(matrix):
    circuit = teleport()
    _ = matrix_to_qir(circuit, matrix, profiles=["profileA"])


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_reuse_after_measurement_fails_without_profileB(matrix):
    circuit = use_after_measure()
    with pytest.raises(ProfileError) as exc_info:
        _ = matrix_to_qir(circuit, matrix, profiles=[""])

    exception_raised = str(exc_info.value)
    assert exception_raised == PROFILE_B_MESSAGE


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_reuse_after_measurement_passses_without_profileB(matrix):
    circuit = use_after_measure()
    _ = matrix_to_qir(circuit, matrix, profiles=["profileB"])


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_using_an_unread_qubit_after_measuring_passes_without_profileB(matrix):
    circuit = use_another_after_measure()
    _ = matrix_to_qir(circuit, matrix)
