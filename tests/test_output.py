##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from datetime import datetime
from pathlib import Path

from sympy import false
import pytest
import logging

from qiskit_qir.translate import to_qir
from qiskit import ClassicalRegister, QuantumCircuit

import test_utils

_log = logging.getLogger(__name__)
_test_output_dir = Path(
    f"test_output.{datetime.now().strftime('%Y%m%d_%H%M')}")
if _log.isEnabledFor(logging.DEBUG) and not _test_output_dir.exists():
    _test_output_dir.mkdir()


def test_single_array():
    circuit = QuantumCircuit(3, 3)
    circuit.name = "test_single_array"
    circuit.h(1)
    circuit.s(2)
    circuit.t(0)
    circuit.measure([0, 1, 2], [2, 0, 1])

    print(to_qir(circuit))
    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 3, 3)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 1)
    assert func[1] == test_utils.single_op_call_string("s", 2)
    assert func[2] == test_utils.single_op_call_string("t", 0)
    assert func[3] == test_utils.measure_call_string("mz", 2, 0)
    assert func[4] == test_utils.measure_call_string("mz", 0, 1)
    assert func[5] == test_utils.measure_call_string("mz", 1, 2)
    assert func[6] == test_utils.array_start_record_output_string()
    assert func[7] == test_utils.result_record_output_string(0)
    assert func[8] == test_utils.result_record_output_string(1)
    assert func[9] == test_utils.result_record_output_string(2)
    assert func[10] == test_utils.array_end_record_output_string()
    assert func[11] == test_utils.return_string()
    assert len(func) == 12


def test_no_measure_with_register():
    circuit = QuantumCircuit(1, 1)
    circuit.name = "test_no_measure_with_register"
    circuit.h(0)
    print(to_qir(circuit))
    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.array_start_record_output_string()
    assert func[2] == test_utils.result_record_output_string(0)
    assert func[3] == test_utils.array_end_record_output_string()
    assert func[4] == test_utils.return_string()
    assert len(func) == 5


def test_no_measure_without_registers():
    circuit = QuantumCircuit(1)
    circuit.name = "test_no_measure_no_registers"
    circuit.h(0)

    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.return_string()
    assert len(func) == 2


def test_measurement_into_multiple_registers_is_mapped_correctly():
    cr0 = ClassicalRegister(1, "first")
    cr1 = ClassicalRegister(3, "second")
    circuit = QuantumCircuit(4)
    circuit.add_register(cr0)
    circuit.add_register(cr1)
    circuit.name = "measurement_into_multiple_registers"
    circuit.h(0)

    circuit.measure([0, 0], [0, 2])

    print(to_qir(circuit))
    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 4, 4)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.measure_call_string("mz", 0, 0)
    assert func[2] == test_utils.measure_call_string("mz", 2, 0)
    assert func[3] == test_utils.array_start_record_output_string()
    assert func[4] == test_utils.result_record_output_string(0)
    assert func[5] == test_utils.array_end_record_output_string()
    assert func[6] == test_utils.array_start_record_output_string()
    assert func[7] == test_utils.result_record_output_string(1)
    assert func[8] == test_utils.result_record_output_string(2)
    assert func[9] == test_utils.result_record_output_string(3)
    assert func[10] == test_utils.array_end_record_output_string()
    assert func[11] == test_utils.return_string()
    assert len(func) == 12
