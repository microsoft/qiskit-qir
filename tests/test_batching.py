##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.translate import to_qir_bitcode
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.circuit import Parameter
import numpy as np
from pyqir import Module, is_entry_point
from typing import List
import test_utils


def get_parameterized_circuit(num_qubits: int, num_params: int) -> List[QuantumCircuit]:
    theta_range = np.linspace(0, 2 * np.pi, num_params)

    theta = Parameter("θ")
    circuit = QuantumCircuit(num_qubits, 1)

    circuit.h(0)
    for i in range(num_qubits - 1):
        circuit.cx(i, i + 1)

    circuit.barrier()
    circuit.rz(theta, range(num_qubits))
    circuit.barrier()

    for i in reversed(range(num_qubits - 1)):
        circuit.cx(i, i + 1)
    circuit.h(0)
    circuit.measure(0, 0)

    circuits = [
        circuit.bind_parameters({theta: theta_val}) for theta_val in theta_range
    ]

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
    qc2 = QuantumCircuit(1, name="second")
    bitcode = to_qir_bitcode(list([qc1, qc2]))
    mod = Module.from_bitcode(bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 2
    for function in functions:
        assert function.name in ["first", "second"]


def test_batch_entry_points_make_unique_names_on_duplicates() -> None:
    qc1 = QuantumCircuit(1, name="first")
    qc2 = QuantumCircuit(1, name="first")
    bitcode = to_qir_bitcode(list([qc1, qc2]))
    mod = Module.from_bitcode(bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 2
    for function in functions:
        assert function.name.startswith("first")


def test_batch_entry_points_have_appropriate_attributes() -> None:
    qc1 = QuantumCircuit(1, 2, name="first")
    qc2 = QuantumCircuit(1, name="second")
    qc3 = QuantumCircuit(name="second")
    qc4 = QuantumCircuit(name="second")
    cr = ClassicalRegister(2, "creg")
    qc4.add_register(cr)
    bitcode = to_qir_bitcode(list([qc1, qc2, qc3, qc4]))
    mod = Module.from_bitcode(bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 4
    test_utils.check_attributes_on_entrypoint(functions[0], 1, 2)
    test_utils.check_attributes_on_entrypoint(functions[1], 1)
    test_utils.check_attributes_on_entrypoint(functions[2])
    test_utils.check_attributes_on_entrypoint(functions[3], expected_results=2)
