##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from unittest import result
from qiskit_qir.translate import to_qir, to_qir_bitcode
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import numpy as np
from pyqir import Module, is_entry_point
import tempfile
from typing import List, Optional


def get_parameterized_circuit(nub_qubits: int, num_params: int) -> List[QuantumCircuit]:
    theta_range = np.linspace(0, 2 * np.pi, num_params)

    theta = Parameter("θ")
    circuit = QuantumCircuit(nub_qubits, 1)

    circuit.h(0)
    for i in range(nub_qubits - 1):
        circuit.cx(i, i + 1)

    circuit.barrier()
    circuit.rz(theta, range(nub_qubits))
    circuit.barrier()

    for i in reversed(range(nub_qubits - 1)):
        circuit.cx(i, i + 1)
    circuit.h(0)
    circuit.measure(0, 0)

    circuits = [circuit.bind_parameters({theta: theta_val}) for theta_val in theta_range]

    return circuits


def test_binding_generates_corresponding_entry_points() -> None:
    for i in range(1, 4):
        circuits = get_parameterized_circuit(2, i)
        bitcode = to_qir_bitcode(circuits)
        mod = Module.from_bitcode(bitcode)
        funcs = list(filter(is_entry_point, mod.functions))
        assert len(funcs) == i


def test_batch_entry_points_use_circuit_names() -> None:
    qc1 = QuantumCircuit(1, name="first")
    qc1.h(0)
    qc2 = QuantumCircuit(1, name="second")
    qc2.h(0)
    bitcode = to_qir_bitcode(list([qc1, qc2]))
    mod = Module.from_bitcode(bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 2
    for function in functions:
        assert function.name in ["first", "second"]


def test_batch_entry_points_make_unique_names_on_duplicates() -> None:
    qc1 = QuantumCircuit(1, name="first")
    qc1.h(0)
    qc2 = QuantumCircuit(1, name="first")
    qc2.h(0)
    bitcode = to_qir_bitcode(list([qc1, qc2]))
    mod = Module.from_bitcode(bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 2
    for function in functions:
        assert function.name.startswith("first")
