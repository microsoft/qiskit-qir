##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from builtins import format
import pytest

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

@pytest.fixture()
def ghz():
    circuit = QuantumCircuit(4, 3)
    circuit.name = "Qiskit Sample - 3-qubit GHZ circuit"
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure([0,1,2], [0, 1, 2])

    return circuit


@pytest.fixture()
def teleport():
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


@pytest.fixture()
def unroll():
    circ = QuantumCircuit(3)
    circ.ccx(0, 1, 2)
    circ.crz(theta=0.1, control_qubit=0, target_qubit=1)
    circ.id(0)

    return circ.decompose()

@pytest.fixture()
def teleport_with_subroutine():
    bell_circ = QuantumCircuit(2, name="CreateBellPair")
    bell_circ.h(0)
    bell_circ.cx(0, 1)
    q = QuantumRegister(3, name="q")
    cr = ClassicalRegister(2, name="cr")
    circuit = QuantumCircuit(q, cr, name="Teleport")
    circuit.append(bell_circ.to_instruction(), [1, 2])
    circuit.cx(0, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    circuit.x(2).c_if(cr, int("10", 2))
    circuit.z(2).c_if(cr, int("01", 2))

    return circuit

@pytest.fixture()
def bernstein_vazirani_with_barriers():
    num_qubits = 5
    qq = QuantumRegister(num_qubits+1, name="qq")
    cr = ClassicalRegister(num_qubits, name="cr")

    circuit = QuantumCircuit(qq, cr, name="Bernstein-Vazirani")

    circuit.h(num_qubits)
    circuit.z(num_qubits)

    for index in range(num_qubits):
        circuit.h(index)

    circuit.barrier()

    oracle = format(2, 'b').zfill(num_qubits)
    oracle = oracle[::-1]
    for index in range(num_qubits):
        if oracle[index] == '0':
            circuit.i(index)
        else:
            circuit.cx(index, num_qubits)

    circuit.barrier()

    for index in range(num_qubits):
        circuit.h(index)

    for index in range(num_qubits):
        circuit.measure(index, index)

    return circuit

@pytest.fixture()
def ghz_with_delay():
    qq = QuantumRegister(4, name="qq")
    cr = ClassicalRegister(3, name="cr")
    circuit = QuantumCircuit(qq, cr)
    circuit.name = "Qiskit Sample - 3-qubit GHZ circuit"
    circuit.delay(23.54, None, "us")
    circuit.h(0)
    circuit.delay(42, qq[0], "ps")
    circuit.cx(0, 1)
    circuit.delay(23, 2, "ms")
    circuit.cx(1, 2)
    circuit.delay(3, qq[1])
    circuit.measure([0,1,2], [0, 1, 2])

    return circuit
