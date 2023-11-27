##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.translate import to_qir_module
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.circuit import Parameter
import numpy as np
from pyqir import Context, Module, is_entry_point
from typing import List
import test_utils
import pytest


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
        circuit.assign_parameters({theta: theta_val}, inplace=False)
        for theta_val in theta_range
    ]

    return circuits


@pytest.mark.parametrize("num_params", [1, 2, 3])
def test_binding_generates_corresponding_entry_points(num_params: int) -> None:
    circuits = get_parameterized_circuit(2, num_params)
    bitcode = to_qir_module(circuits)[0].bitcode
    mod = Module.from_bitcode(Context(), bitcode)
    funcs = list(filter(is_entry_point, mod.functions))
    assert len(funcs) == num_params


def test_batch_entry_points_use_circuit_names() -> None:
    qc1 = QuantumCircuit(1, name="first")
    qc2 = QuantumCircuit(1, name="second")
    module, entry_points = to_qir_module(list([qc1, qc2]))
    mod = Module.from_bitcode(Context(), module.bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 2
    for function in functions:
        assert function.name in ["first", "second"]
    assert entry_points == list([x.name for x in functions])


def test_batch_entry_points_make_unique_names_on_duplicates() -> None:
    name = "first"
    qc1 = QuantumCircuit(1, name=name)
    qc2 = QuantumCircuit(1, name=name)
    module, entry_points = to_qir_module(list([qc1, qc2]))
    mod = Module.from_bitcode(Context(), module.bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 2
    for function in functions:
        assert function.name.startswith(name)
    assert functions[0].name != functions[1].name
    assert entry_points == list([x.name for x in functions])


def test_batch_entry_points_have_appropriate_attributes() -> None:
    qc1 = QuantumCircuit(1, 2, name="first")
    qc2 = QuantumCircuit(1, name="second")
    qc3 = QuantumCircuit(name="second")
    qc4 = QuantumCircuit(name="second")
    cr = ClassicalRegister(2, "creg")
    qc4.add_register(cr)
    bitcode = to_qir_module(list([qc1, qc2, qc3, qc4]))[0].bitcode
    mod = Module.from_bitcode(Context(), bitcode)
    functions = list(filter(is_entry_point, mod.functions))
    assert len(functions) == 4
    test_utils.check_attributes_on_entrypoint(functions[0], 1, 2)
    test_utils.check_attributes_on_entrypoint(functions[1], 1)
    test_utils.check_attributes_on_entrypoint(functions[2])
    test_utils.check_attributes_on_entrypoint(functions[3], expected_results=2)


def test_passing_list_with_non_quantum_circuits_raises_value_error() -> None:
    qc = QuantumCircuit(1)
    with pytest.raises(ValueError):
        _ = to_qir_module(list([qc, 2]))
    with pytest.raises(ValueError):
        _ = to_qir_module(list([2, qc]))
    with pytest.raises(ValueError):
        _ = to_qir_module(list([2]))
    with pytest.raises(ValueError):
        _ = to_qir_module(list([qc, 2, qc]))


def test_passing_non_quantum_circuits_raises_value_error() -> None:
    with pytest.raises(ValueError):
        _ = to_qir_module(2)


def test_passing_empty_list_of_quantum_circuits_raises_value_error() -> None:
    with pytest.raises(ValueError):
        _ = to_qir_module(list([]))
