##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from datetime import datetime
from pathlib import Path

from sympy import false
import pytest
import logging

from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor
from qiskit_qir.translate import to_qir, to_qir_bitcode
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

import test_utils

_log = logging.getLogger(__name__)
_test_output_dir = Path(
    f"test_output.{datetime.now().strftime('%Y%m%d_%H%M')}")
if _log.isEnabledFor(logging.DEBUG) and not _test_output_dir.exists():
    _test_output_dir.mkdir()


def test_single_array():
    circuit = QuantumCircuit(4, 3)
    circuit.name = "test_single_array"
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure([0, 1, 2], [0, 1, 2])

    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor()
    module.accept(visitor)
    generated_ir = visitor.ir()
    print(generated_ir)
    _log.debug(generated_ir)
    assert generated_ir is not None
    assert false


def test_no_measure():
    circuit = QuantumCircuit(4, 3)
    circuit.name = "test_no_measure"
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)

    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor()
    module.accept(visitor)
    generated_ir = visitor.ir()
    print(generated_ir)
    _log.debug(generated_ir)
    assert generated_ir is not None
    assert false


def test_two_arrays():
    cr0 = ClassicalRegister(3, "first")
    cr1 = ClassicalRegister(3, "second")
    circuit = QuantumCircuit(4)
    circuit.add_register(cr0)
    circuit.add_register(cr1)
    circuit.name = "test_two_arrays"
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure([0, 1, 2], [0, 1, 5])

    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor()
    module.accept(visitor)
    generated_ir = visitor.ir()
    print(generated_ir)
    _log.debug(generated_ir)
    assert generated_ir is not None
    assert false
