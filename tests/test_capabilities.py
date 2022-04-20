##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from typing import List

import pytest
from qiskit_qir.elements import QiskitModule

from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit_qir.capability import Capability, ConditionalBranchingOnResultError, QubitUseAfterMeasurementError
from qiskit_qir.visitor import BasicQisVisitor

static_generator_variations = [
    [False, False],
    [False, True],
    [True, False],
    [True, True]
]

# test circuits


def teleport() -> QuantumCircuit:
    qq = QuantumRegister(3, name="qq")
    cr = ClassicalRegister(2, name="cr")
    circuit = QuantumCircuit(qq, cr, name="Teleport")
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
    qq = QuantumRegister(2, name="qq")
    cr = ClassicalRegister(2, name="cr")
    circuit = QuantumCircuit(qq, cr)

    circuit.h(1)
    circuit.measure(1, 1)
    circuit.h(1)


    return circuit


def use_another_after_measure():
    circuit = QuantumCircuit(3, 2)

    circuit.h(0)
    circuit.measure(0, 0)
    circuit.h(1)
    circuit.cx(1, 2)
    circuit.measure(1, 1)

    return circuit


def use_another_after_measure_and_condition():
    qq = QuantumRegister(3, name="qq")
    cr = ClassicalRegister(2, name="cr")
    circuit = QuantumCircuit(qq, cr)

    circuit.h(0)
    circuit.measure(0, 0)
    circuit.h(1)
    circuit.cx(1, 2)
    circuit.measure(1, 1)
    circuit.x(2).c_if(cr, int("10", 2))

    return circuit

# Create override visitor which allows us to vary the
# codegen behavior


class ConfigurableQisVisitor(BasicQisVisitor):
    def __init__(self, matrix: List[bool], capabilities: Capability):
        BasicQisVisitor.__init__(self, capabilities)
        self._matrix = matrix

    def visit_qiskit_module(self, module):
        BasicQisVisitor.visit_qiskit_module(self, module)
        self._module.use_static_qubit_alloc(self._matrix[0])
        self._module.use_static_result_alloc(self._matrix[1])


# Utility using new visitor and codegen matrix
def matrix_to_qir(circuit, matrix: List[bool], capabilities: Capability):
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = ConfigurableQisVisitor(matrix, capabilities)
    module.accept(visitor)
    return visitor.ir()


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_branching_on_measurement_fails_without_required_capability(matrix):
    circuit = teleport()
    with pytest.raises(ConditionalBranchingOnResultError) as exc_info:
        _ = matrix_to_qir(circuit, matrix, Capability.NONE)

    exception_raised = exc_info.value
    assert str(exception_raised.instruction) == "Instruction(name='x', num_qubits=1, num_clbits=0, params=[])"
    assert str(exception_raised.instruction.condition) == "(ClassicalRegister(2, 'cr'), 2)"
    assert str(exception_raised.qargs) == "[Qubit(QuantumRegister(3, 'qq'), 2)]"
    assert str(exception_raised.cargs) == "[]"
    assert exception_raised.instruction_string == "if(cr[2]) x qq[2]"


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_branching_on_measurement_passses_with_required_capability(matrix):
    circuit = teleport()
    _ = matrix_to_qir(
        circuit, matrix, Capability.CONDITIONAL_BRANCHING_ON_RESULT)


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_reuse_after_measurement_fails_without_required_capability(matrix):
    circuit = use_after_measure()
    with pytest.raises(QubitUseAfterMeasurementError) as exc_info:
        _ = matrix_to_qir(circuit, matrix, Capability.NONE)

    exception_raised = exc_info.value
    assert str(exception_raised.instruction) == "Instruction(name='h', num_qubits=1, num_clbits=0, params=[])"
    assert exception_raised.instruction.condition is None
    assert str(exception_raised.qargs) == "[Qubit(QuantumRegister(2, 'qq'), 1)]"
    assert str(exception_raised.cargs) == "[]"
    assert exception_raised.instruction_string == "h qq[1]"


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_reuse_after_measurement_passes_with_required_capability(matrix):
    circuit = use_after_measure()
    _ = matrix_to_qir(circuit, matrix, Capability.QUBIT_USE_AFTER_MEASUREMENT)


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_using_an_unread_qubit_after_measuring_passes_without_required_capability(matrix):
    circuit = use_another_after_measure()
    _ = matrix_to_qir(circuit, matrix, Capability.NONE)


@pytest.mark.parametrize("matrix", static_generator_variations)
def test_use_another_after_measure_and_condition_passes_with_required_capability(matrix):
    circuit = use_another_after_measure_and_condition()
    _ = matrix_to_qir(circuit, matrix, Capability.QUBIT_USE_AFTER_MEASUREMENT |
                      Capability.CONDITIONAL_BRANCHING_ON_RESULT)
