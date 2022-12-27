##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.visitor import BasicQisVisitor
from qiskit.circuit.quantumcircuit import QuantumCircuit
from typing import List, Tuple, Union
from pyqir import Context, Module
from qiskit_qir.elements import QiskitModule


def to_qir(
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> str:
    r"""Converts the Qiskit QuantumCircuit to QIR as a string

    :param circuits:
        Qiskit circuit(s) to be converted to QIR
    :type circuit: ``Union[QuantumCircuit, List[QuantumCircuit]]``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
        * *emit_barrier_calls* (``bool``) --
          Whether to emit barrier calls in the QIR, default `False`
    """
    _, module = _build_module(circuits, profile, **kwargs)
    return str(module)


def to_qir_bitcode(
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> bytes:
    r"""Converts the Qiskit QuantumCircuit to QIR bitcode as bytes

    :param circuits:
        Qiskit circuit to be converted to QIR
    :type circuit: ``Union[QuantumCircuit, List[QuantumCircuit]]``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
        * *emit_barrier_calls* (``bool``) --
          Whether to emit barrier calls in the QIR, default `False`
    """

    _, module = _build_module(circuits, profile, **kwargs)
    return module.bitcode


def to_qir_bitcode_with_entry_points(
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> Tuple[bytes, List[str]]:
    r"""Converts the Qiskit QuantumCircuit to QIR bitcode as bytes

    :param circuits:
        Qiskit circuit to be converted to QIR
    :type circuit: ``Union[QuantumCircuit, List[QuantumCircuit]]``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
        * *emit_barrier_calls* (``bool``) --
          Whether to emit barrier calls in the QIR, default `False`
    """

    entry_points, module = _build_module(circuits, profile, **kwargs)
    return (module.bitcode, entry_points)


def _build_module(
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> Tuple[List[str], Module]:
    name = "batch"
    if isinstance(circuits, QuantumCircuit):
        name = circuits.name
        circuits = [circuits]
    elif isinstance(circuits, list):
        for value in circuits:
            if not isinstance(value, QuantumCircuit):
                raise ValueError(
                    "Input must be Union[QuantumCircuit, List[QuantumCircuit]]"
                )
    else:
        raise ValueError("Input must be Union[QuantumCircuit, List[QuantumCircuit]]")

    if len(circuits) == 0:
        raise ValueError("No QuantumCircuits provided")

    llvm_module = Module(Context(), name)
    entry_points = []
    for circuit in circuits:
        module = QiskitModule.from_quantum_circuit(circuit, llvm_module)
        module.accept(BasicQisVisitor(profile, **kwargs))
        entry_points.append(module.entry_point)
    err = llvm_module.verify()
    if err is not None:
        raise Exception(err)
    return (entry_points, llvm_module)
