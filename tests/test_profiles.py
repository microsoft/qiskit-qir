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
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit_qir.visitor import ProfileError

import test_utils

_log = logging.getLogger(__name__)
_test_output_dir = Path(
    f"test_output.{datetime.now().strftime('%Y%m%d_%H%M')}")
if _log.isEnabledFor(logging.DEBUG) and not _test_output_dir.exists():
    _test_output_dir.mkdir()


def teleport() -> QuantumCircuit:
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


def use_after_measure():
    circuit = QuantumCircuit(2, 2)

    circuit.h(0)
    circuit.measure(0, 0)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure(1, 1)

    return circuit


def use_another_after_measure():
    circuit = QuantumCircuit(3, 2)

    circuit.h(0)
    circuit.measure(0, 0)
    circuit.h(1)
    circuit.cx(1, 2)
    circuit.measure(1, 1)

    return circuit


def test_branching_on_measurement_fails_without_profileA():
    circuit = teleport()
    with pytest.raises(ProfileError) as exc_info:
        _ = to_qir(circuit, profiles=[""])

    exception_raised = str(exc_info.value)
    assert exception_raised == "Support branching based on measurement requires profileA"


def test_branching_on_measurement_passses_without_profileA():
    circuit = teleport()
    _ = to_qir(circuit, profiles=["profileA"])


def test_reuse_after_measurement_fails_without_profileB():
    circuit = use_after_measure()
    with pytest.raises(ProfileError) as exc_info:
        _ = to_qir(circuit, profiles=[""])

    exception_raised = str(exc_info.value)
    assert exception_raised == "Support for qubit reuse requires profileB"


def test_reuse_after_measurement_passses_without_profileB():
    circuit = use_after_measure()
    _ = to_qir(circuit, profiles=["profileB"])


def test_using_an_unread_qubit_after_measuring_passses_without_profileB():
    circuit = use_another_after_measure()
    _ = to_qir(circuit, profiles=["profileB"])
