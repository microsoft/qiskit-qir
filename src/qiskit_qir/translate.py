##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.visitor import BasicQisVisitor
from qiskit.circuit.quantumcircuit import QuantumCircuit
from typing import List, Tuple, Union
from pyqir import Context, Module, qir_module
from qiskit_qir.elements import QiskitModule


def to_qir_module(
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> Tuple[Module, List[str]]:
    r"""Converts the Qiskit QuantumCircuit(s) to a QIR Module with
    its entry point names.

    :param circuits:
        Qiskit circuit(s) to be converted to QIR
    :type circuit: ``Union[QuantumCircuit, List[QuantumCircuit]]``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below
    :returns:
        Tuple containing the the QIR ``pyqir.Module`` representation of the input and
        the list of used entry point names generated from the input.

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
        * *emit_barrier_calls* (``bool``) --
          Whether to emit barrier calls in the QIR, default `False`
    """

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

    llvm_module = qir_module(Context(), name)
    entry_points = []
    for circuit in circuits:
        module = QiskitModule.from_quantum_circuit(circuit, llvm_module)
        visitor = BasicQisVisitor(profile, **kwargs)
        module.accept(visitor)
        entry_points.append(visitor.entry_point)
    err = llvm_module.verify()
    if err is not None:
        raise Exception(err)
    return (llvm_module, entry_points)
