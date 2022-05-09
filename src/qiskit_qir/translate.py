##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor
from qiskit.circuit.quantumcircuit import QuantumCircuit

def to_qir(circuit: QuantumCircuit, profile: str = "AdaptiveProfileExecution") -> str:
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(profile)
    module.accept(visitor)
    return visitor.ir()


def to_qir_bitcode(circuit: QuantumCircuit, profile: str = "AdaptiveProfileExecution") -> bytes:
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(profile)
    module.accept(visitor)
    return visitor.bitcode()
