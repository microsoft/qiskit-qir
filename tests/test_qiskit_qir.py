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
from qiskit_qir.translate import to_qir, to_qir_bitcode

from test_circuits import __all__ as CIRCUITS

_log = logging.getLogger(__name__)
_test_output_dir = Path(f"test_output.{datetime.now().strftime('%Y%m%d_%H%M')}")
if _log.isEnabledFor(logging.DEBUG) and not _test_output_dir.exists():
    _test_output_dir.mkdir()


@pytest.mark.parametrize("circuit_name", CIRCUITS)
def test_visitor(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor()
    module.accept(visitor)
    generated_ir = visitor.ir()
    _log.debug(generated_ir)
    assert generated_ir is not None


@pytest.mark.parametrize("circuit_name", CIRCUITS)
def test_to_qir_string(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    generated_ir = to_qir(circuit)
    _log.debug(generated_ir)
    assert generated_ir is not None
    if _log.isEnabledFor(logging.DEBUG):
        qasm_path = _test_output_dir.joinpath(circuit_name + '.qasm')
        circuit.qasm(filename=str(qasm_path))
        qir_path = _test_output_dir.joinpath(circuit_name + '.ll')
        qir_path.write_text(generated_ir)


@pytest.mark.parametrize("circuit_name", CIRCUITS)
def test_to_qir_bitcode(circuit_name, request):
    circuit = request.getfixturevalue(circuit_name)
    generated_bitcode = to_qir_bitcode(circuit)
    _log.debug(generated_bitcode)
    assert generated_bitcode is not None
