##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##

from qiskit_qir.translate import to_qir_module
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.circuit import Clbit
from qiskit.circuit.exceptions import CircuitError

import pytest
import pyqir

import os
from pathlib import Path

# result_stream, condition value, expected gates
falsy_single_bit_variations = [False, 0]

truthy_single_bit_variations = [True, 1]

invalid_single_bit_varitions = [-1]


def compare_reference_ir(generated_bitcode: bytes, name: str) -> None:
    module = pyqir.Module.from_bitcode(pyqir.Context(), generated_bitcode, f"{name}")
    ir = str(module)

    file = os.path.join(os.path.dirname(__file__), f"resources/{name}.ll")
    expected = Path(file).read_text()
    assert ir == expected


@pytest.mark.parametrize("value", falsy_single_bit_variations)
def test_single_clbit_variations_falsy(value: bool) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_clbit_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)
    bit: Clbit = cr[0]
    circuit.measure(1, 1).c_if(bit, value)

    generated_bitcode = to_qir_module(circuit, record_output=False)[0].bitcode
    compare_reference_ir(generated_bitcode, "test_single_clbit_variations_falsy")


@pytest.mark.parametrize("value", truthy_single_bit_variations)
def test_single_clbit_variations_truthy(value: bool) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_clbit_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)
    bit: Clbit = cr[0]
    circuit.measure(1, 1).c_if(bit, value)

    generated_bitcode = to_qir_module(circuit, record_output=False)[0].bitcode
    compare_reference_ir(generated_bitcode, "test_single_clbit_variations_truthy")


@pytest.mark.parametrize("value", truthy_single_bit_variations)
def test_single_register_index_variations_truthy(value: bool) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_register_index_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)
    circuit.measure(1, 1).c_if(0, value)

    generated_bitcode = to_qir_module(circuit, record_output=False)[0].bitcode

    compare_reference_ir(
        generated_bitcode, "test_single_register_index_variations_truthy"
    )


@pytest.mark.parametrize("value", falsy_single_bit_variations)
def test_single_register_index_variations_falsy(value: bool) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_register_index_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)
    circuit.measure(1, 1).c_if(0, value)

    generated_bitcode = to_qir_module(circuit, record_output=False)[0].bitcode

    compare_reference_ir(
        generated_bitcode, "test_single_register_index_variations_falsy"
    )


@pytest.mark.parametrize("value", truthy_single_bit_variations)
def test_single_register_variations_truthy(value: bool) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_register_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)
    circuit.measure(1, 1).c_if(cr, value)

    generated_bitcode = to_qir_module(circuit, record_output=False)[0].bitcode

    compare_reference_ir(generated_bitcode, "test_single_register_variations_truthy")


@pytest.mark.parametrize("value", falsy_single_bit_variations)
def test_single_register_variations_falsy(value: bool) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_register_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)
    circuit.measure(1, 1).c_if(cr, value)

    generated_bitcode = to_qir_module(circuit, record_output=False)[0].bitcode

    compare_reference_ir(generated_bitcode, "test_single_register_variations_falsy")


@pytest.mark.parametrize("value", invalid_single_bit_varitions)
def test_single_clbit_invalid_variations(value: int) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_clbit_invalid_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)
    bit: Clbit = cr[0]

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(1, 1).c_if(bit, value)

    assert exc_info is not None


@pytest.mark.parametrize("value", invalid_single_bit_varitions)
def test_single_register_index_invalid_variations(value: int) -> None:
    circuit = QuantumCircuit(
        2,
        0,
        name=f"test_single_register_index_invalid_variations",
    )
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(1, 1).c_if(0, value)

    assert exc_info is not None


@pytest.mark.parametrize("value", invalid_single_bit_varitions)
def test_single_register_invalid_variations(value: int) -> None:
    circuit = QuantumCircuit(2, 0, name=f"test_single_register_invalid_variations")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0, 0)

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(1, 1).c_if(cr, value)

    assert exc_info is not None


two_bit_variations = [
    [False, "falsy"],
    [0, "falsy"],
    [True, "truthy"],
    [1, "truthy"],
    [2, "two"],
    [3, "three"],
]

# # -1: 11
# # -2: 10
# # -3: 01
# # -4: 00
invalid_two_bit_variations = [-4, -3, -2, -1]


@pytest.mark.parametrize("matrix", two_bit_variations)
def test_two_bit_register_variations(matrix) -> None:
    value, name = matrix
    circuit = QuantumCircuit(
        3,
        0,
        name=f"test_two_bit_register_variations",
    )

    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    cond = ClassicalRegister(1, "cond")
    circuit.add_register(cond)

    circuit.measure(0, 0)
    circuit.measure(1, 1)
    circuit.measure(2, 2).c_if(cr, value)

    generated_bitcode = to_qir_module(circuit, record_output=False)[0].bitcode

    compare_reference_ir(generated_bitcode, f"test_two_bit_register_variations_{name}")


@pytest.mark.parametrize("value", invalid_two_bit_variations)
def test_two_bit_register_invalid_variations(value: int) -> None:
    circuit = QuantumCircuit(
        3,
        0,
        name=f"test_two_bit_register_invalid_variations",
    )

    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    cond = ClassicalRegister(1, "cond")
    circuit.add_register(cond)

    circuit.measure(0, 0)
    circuit.measure(1, 1)

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(2, 2).c_if(cr, value)

    assert exc_info is not None
