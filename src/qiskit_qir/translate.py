##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor
from qiskit.circuit.quantumcircuit import QuantumCircuit
from typing import List, Union
from pyqir import Context, Module, run_basic_passes


def to_qir(
    circuits: Union[QuantumCircuit, List[QuantumCircuit()]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> str:
    r"""Converts the Qiskit QuantumCircuit to QIR as a string

    :param circuits:
        Qiskit circuit(s) to be converted to QIR
    :type circuit: ``Union[QuantumCircuit, List[QuantumCircuit()]]``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
    """
    module = _build_module(circuits, profile=profile, kwargs=kwargs)
    return str(module)


def to_qir_bitcode(
    circuits: Union[QuantumCircuit, List[QuantumCircuit()]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> bytes:
    r"""Converts the Qiskit QuantumCircuit to QIR bitcode as bytes

    :param circuits:
        Qiskit circuit to be converted to QIR
    :type circuit: ``Union[QuantumCircuit, List[QuantumCircuit()]]``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
    """

    module = _build_module(circuits, profile=profile, kwargs=kwargs)
    return module.bitcode()


def _build_module(
    circuits: Union[QuantumCircuit, List[QuantumCircuit()]],
    profile: str = "AdaptiveExecution",
    **kwargs
) -> Module:
    circuits = circuits if isinstance(circuits, List[QuantumCircuit]) else [circuits]
    if len(circuits) == 0:
        raise "No QuantumCircuits provided"
    name = "batch"
    if len(circuits) == 1:
        name = circuits[0].name

    llvm_module = Module(Context(), name)
    modules = circuits.map(
        lambda circuit: QiskitModule.from_quantum_circuit(
            circuit=circuit, module=llvm_module
        )
    )
    for module in modules:
        visitor = BasicQisVisitor(profile, kwargs=kwargs)
        module.accept(visitor)
    run_basic_passes(llvm_module)
    llvm_module.verify()
    return llvm_module
