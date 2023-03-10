##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from datetime import datetime
from pathlib import Path
import pytest
import logging

from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor
from qiskit_qir.translate import to_qir_module

from test_circuits import core_tests, noop_tests
from test_circuits.control_flow_circuits import cf_fixtures
from test_circuits.basic_gates import (
    single_op_tests,
    adj_op_tests,
    rotation_tests,
    double_op_tests,
    triple_op_tests,
    measurement_tests,
)

import test_utils

_log = logging.getLogger(__name__)
_test_output_dir = Path(f"test_output.{datetime.now().strftime('%Y%m%d_%H%M')}")
if _log.isEnabledFor(logging.DEBUG) and not _test_output_dir.exists():
    _test_output_dir.mkdir()


@pytest.mark.parametrize("circuit_name", core_tests)
def test_visitor(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor()
    module.accept(visitor)
    generated_ir = visitor.ir()
    _log.debug(generated_ir)
    assert generated_ir is not None


@pytest.mark.parametrize("circuit_name", core_tests)
def test_to_qir_string(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    generated_ir = str(to_qir_module(circuit)[0])
    assert generated_ir is not None
    if _log.isEnabledFor(logging.DEBUG):
        qasm_path = _test_output_dir.joinpath(circuit_name + ".qasm")
        circuit.qasm(filename=str(qasm_path))
        qir_path = _test_output_dir.joinpath(circuit_name + ".ll")
        qir_path.write_text(generated_ir)


@pytest.mark.parametrize("circuit_name", core_tests)
def test_to_qir_bitcode(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    generated_bitcode = to_qir_module(circuit)[0].bitcode
    assert generated_bitcode is not None


@pytest.mark.parametrize("circuit_name", noop_tests)
def test_noop_gates(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor()
    module.accept(visitor)
    generated_ir = visitor.ir()
    _log.debug(generated_ir)
    assert generated_ir is not None


@pytest.mark.xfail(Reason="OpenQASM 3.0-style control flow is not supported yet")
@pytest.mark.parametrize("circuit_name", cf_fixtures)
def test_control_flow(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    generated_ir = str(to_qir_module(circuit)[0])
    assert generated_ir is not None
    if _log.isEnabledFor(logging.DEBUG):
        qasm_path = _test_output_dir.joinpath(circuit_name + ".qasm")
        circuit.qasm(filename=str(qasm_path))
        qir_path = _test_output_dir.joinpath(circuit_name + ".ll")
        qir_path.write_text(generated_ir)


@pytest.mark.parametrize("circuit_name", single_op_tests)
def test_single_qubit_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()
    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.get_entry_point_body(generated_qir)
    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string(qir_op, 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


@pytest.mark.parametrize("circuit_name", adj_op_tests)
def test_adj_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()
    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.get_entry_point_body(generated_qir)
    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.adj_op_call_string(qir_op, 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


@pytest.mark.parametrize("circuit_name", rotation_tests)
def test_rotation_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()
    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.get_entry_point_body(generated_qir)
    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.rotation_call_string(qir_op, 0.5, 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


@pytest.mark.parametrize("circuit_name", double_op_tests)
def test_double_qubit_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()
    test_utils.check_attributes(generated_qir, 2, 0)
    func = test_utils.get_entry_point_body(generated_qir)
    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.double_op_call_string(qir_op, 0, 1)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


@pytest.mark.parametrize("circuit_name", triple_op_tests)
def test_triple_qubit_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()
    test_utils.check_attributes(generated_qir, 3, 0)
    func = test_utils.get_entry_point_body(generated_qir)
    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.generic_op_call_string(qir_op, [2, 0, 1])
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


@pytest.mark.parametrize("circuit_name", measurement_tests)
def test_measurement(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()
    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.measure_call_string(qir_op, 0, 0)
    assert func[2] == test_utils.array_record_output_string(1)
    assert func[3] == test_utils.result_record_output_string(0)
    assert func[4] == test_utils.return_string()
    assert len(func) == 5
