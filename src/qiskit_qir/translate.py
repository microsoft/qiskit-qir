##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor
from qiskit.circuit.quantumcircuit import QuantumCircuit
from typing import List, Union
from pyqir import Context, Module, verify_module


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
    """
    module = _build_module(circuits, profile, **kwargs)
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
    """

    module = _build_module(circuits, profile, **kwargs)
    return module.bitcode


def _build_module(
    circuits: Union[QuantumCircuit, List[QuantumCircuit]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> Module:
    name = "batch"
    if isinstance(circuits, QuantumCircuit):
        name = circuits.name
        circuits = [circuits]

    if len(circuits) == 0:
        raise "No QuantumCircuits provided"

    llvm_module = Module(Context(), name)
    modules = list(
        map(
            lambda circuit: QiskitModule.from_quantum_circuit(
                circuit=circuit, module=llvm_module
            ),
            circuits,
        )
    )
    for module in modules:
        visitor = BasicQisVisitor(profile, **kwargs)
        module.accept(visitor)
    verify_module(llvm_module)
    return llvm_module
