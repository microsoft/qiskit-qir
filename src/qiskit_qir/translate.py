##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor
from qiskit.circuit.quantumcircuit import QuantumCircuit

def to_qir(circuit: QuantumCircuit, profile: str = "AdaptiveExecution", **kwargs) -> str:
    r"""Converts the Qiskit QuantumCircuit to QIR as a string

    :param circuit:
        Qiskit circuit to be converted to QIR
    :type circuit: ``QuantumCircuit``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
        * *use_static_qubit_alloc* (``bool``) --
          Whether to use static qubit allocation, default `True`
        * *use_static_result_alloc* (``bool``) --
          Whether to use static result allocation, default `True`
    """

    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(profile, kwargs=kwargs)
    module.accept(visitor)
    return visitor.ir()


def to_qir_bitcode(circuit: QuantumCircuit, profile: str = "AdaptiveExecution", **kwargs) -> bytes:
    r"""Converts the Qiskit QuantumCircuit to QIR bitcode as bytes

    :param circuit:
        Qiskit circuit to be converted to QIR
    :type circuit: ``QuantumCircuit``
    :param profile:
        The target profile for capability verification
    :type profile: ``str``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *record_output* (``bool``) --
          Whether to record output calls for registers, default `True`
        * *use_static_qubit_alloc* (``bool``) --
          Whether to use static qubit allocation, default `True`
        * *use_static_result_alloc* (``bool``) --
          Whether to use static result allocation, default `True`
    """

    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(profile, kwargs=kwargs)
    module.accept(visitor)
    return visitor.bitcode()
