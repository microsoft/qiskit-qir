##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from unittest import result
from qiskit_qir.translate import to_qir, to_qir_bitcode
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Qubit, Clbit
from qiskit.circuit.exceptions import CircuitError

import pytest
from pyqir.evaluator import GateLogger, GateSet, NonadaptiveEvaluator
import tempfile
from typing import List, Optional

# result_stream, condition value, expected gates
single_bit_varitions = [
    [[False], False, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[False], 0, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],

    [[False], True, ['m qubit[0] => out[0]']],
    [[False], 1, ['m qubit[0] => out[0]']],

    [[True], False, ['m qubit[0] => out[0]']],
    [[True], 0, ['m qubit[0] => out[0]']],

    [[True], True, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[True], 1, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
]

invalid_single_bit_varitions = [
    [[False], -1, []],
    [[True], -1, []],
]

@pytest.mark.parametrize("matrix", single_bit_varitions)
def test_single_clbit_variations(matrix) -> None:
    circuit = QuantumCircuit(2,0,name=f"test_single_clbit_variations-{matrix[0]}-{matrix[1]}")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0,0)
    bit : Clbit = cr[0]
    circuit.measure(1,1).c_if(bit, matrix[1])

    generated_bitcode = to_qir_bitcode(circuit, record_output=False)

    logger = GateLogger()
    _eval(generated_bitcode, logger, matrix[0])
    assert logger.instructions == matrix[2]


@pytest.mark.parametrize("matrix", single_bit_varitions)
def test_single_register_index_variations(matrix) -> None:
    circuit = QuantumCircuit(2,0,name=f"test_single_register_index_variations-{matrix[0]}-{matrix[1]}")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0,0)
    circuit.measure(1,1).c_if(0, matrix[1])

    generated_bitcode = to_qir_bitcode(circuit, record_output=False)

    logger = GateLogger()
    _eval(generated_bitcode, logger, matrix[0])
    assert logger.instructions == matrix[2]

@pytest.mark.parametrize("matrix", single_bit_varitions)
def test_single_register_variations(matrix) -> None:
    circuit = QuantumCircuit(2,0,name=f"test_single_register_variations-{matrix[0]}-{matrix[1]}")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0,0)
    circuit.measure(1,1).c_if(cr, matrix[1])

    generated_bitcode = to_qir_bitcode(circuit, record_output=False)

    logger = GateLogger()
    _eval(generated_bitcode, logger, matrix[0])
    assert logger.instructions == matrix[2]

@pytest.mark.parametrize("matrix", invalid_single_bit_varitions)
def test_single_clbit_invalid_variations(matrix) -> None:
    circuit = QuantumCircuit(2,0,name=f"test_single_clbit_invalid_variations-{matrix[0]}-{matrix[1]}")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0,0)
    bit : Clbit = cr[0]

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(1,1).c_if(bit, matrix[1])

    assert exc_info is not None

@pytest.mark.parametrize("matrix", invalid_single_bit_varitions)
def test_single_register_index_invalid_variations(matrix) -> None:
    circuit = QuantumCircuit(2,0,name=f"test_single_register_index_invalid_variations-{matrix[0]}-{matrix[1]}")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0,0)

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(1,1).c_if(0, matrix[1])

    assert exc_info is not None

@pytest.mark.parametrize("matrix", invalid_single_bit_varitions)
def test_single_register_invalid_variations(matrix) -> None:
    circuit = QuantumCircuit(2,0,name=f"test_single_register_invalid_variations-{matrix[0]}-{matrix[1]}")
    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    circuit.measure(0,0)

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(1,1).c_if(cr, matrix[1])

    assert exc_info is not None

# result_stream, condition value, expected gates
two_bit_variations = [
    [[False, False], False, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]', 'm qubit[2] => out[2]']], # 00 => 00 (0)
    [[False, False], 0, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]', 'm qubit[2] => out[2]']], # 00 => 00 (0)

    [[False, False], True, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[False, False], 1, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[False, False], 2, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[False, False], 3, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],

    [[False, True], False, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[False, True], 0, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],

    [[False, True], True, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[False, True], 1, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[False, True], 2, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]', 'm qubit[2] => out[2]']], # 01 => 10 (2)
    [[False, True], 3, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],

    [[True, False], False, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[True, False], 0, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],

    [[True, False], True, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]', 'm qubit[2] => out[2]']], # 10 => 01 (1)
    [[True, False], 1, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]', 'm qubit[2] => out[2]']], # 10 => 01 (1)
    [[True, False], 2, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[True, False], 3, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],

    [[True, True], False, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[True, True], 0, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],

    [[True, True], True, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[True, True], 1, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[True, True], 2, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]']],
    [[True, True], 3, ['m qubit[0] => out[0]', 'm qubit[1] => out[1]', 'm qubit[2] => out[2]']], # 11 => 11 (3)
]

# -1: 11
# -2: 10
# -3: 01
# -4: 00
invalid_two_bit_variations = [
    [[False, False], -4, []],
    [[False, False], -3, []],
    [[False, False], -2, []],
    [[False, False], -1, []],

    [[False, True], -4, []],
    [[False, True], -3, []],
    [[False, True], -2, []],
    [[False, True], -1, []],

    [[True, False], -1, []],
    [[True, False], -2, []],
    [[True, False], -3, []],
    [[True, False], -4, []],

    [[True, True], -4, []],
    [[True, True], -3, []],
    [[True, True], -2, []],
    [[True, True], -1, []],
]

@pytest.mark.parametrize("matrix", two_bit_variations)
def test_two_bit_register_variations(matrix) -> None:
    circuit = QuantumCircuit(3,0,name=f"test_two_bit_register_variations-{matrix[0][0]}-{matrix[0][1]}-{matrix[1]}")

    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    cond = ClassicalRegister(1, "cond")
    circuit.add_register(cond)

    circuit.measure(0,0)
    circuit.measure(1,1)
    circuit.measure(2,2).c_if(cr, matrix[1])

    generated_bitcode = to_qir_bitcode(circuit, record_output=False)

    logger = GateLogger()
    _eval(generated_bitcode, logger, matrix[0])
    assert logger.instructions == matrix[2]

@pytest.mark.parametrize("matrix", invalid_two_bit_variations)
def test_two_bit_register_invalid_variations(matrix) -> None:
    circuit = QuantumCircuit(3,0,name=f"test_two_bit_register_invalid_variations-{matrix[0][0]}-{matrix[0][1]}-{matrix[1]}")

    cr = ClassicalRegister(2, "creg")
    circuit.add_register(cr)
    cond = ClassicalRegister(1, "cond")
    circuit.add_register(cond)

    circuit.measure(0,0)
    circuit.measure(1,1)

    with pytest.raises(CircuitError) as exc_info:
        _ = circuit.measure(2,2).c_if(cr, matrix[1])

    assert exc_info is not None

def _eval(ir : bytes,
          gates: GateSet,
          result_stream: Optional[List[bool]] = None) -> None:
    with tempfile.NamedTemporaryFile(suffix=".bc") as f:
        f.write(ir)
        f.flush()
        NonadaptiveEvaluator().eval(f.name, gates, None, result_stream)
