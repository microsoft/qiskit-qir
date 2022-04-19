##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from typing import List
from qiskit_qir.capability import Capability
from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor


def to_qir(circuit, capabilities: Capability = Capability.NONE):
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(capabilities)
    module.accept(visitor)
    return visitor.ir()


def to_qir_bitcode(circuit, capabilities: Capability = Capability.NONE):
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(capabilities)
    module.accept(visitor)
    return visitor.bitcode()
