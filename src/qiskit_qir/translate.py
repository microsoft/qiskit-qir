##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from typing import List
from qiskit_qir.elements import QiskitModule
from qiskit_qir.visitor import BasicQisVisitor


def to_qir(circuit, profiles: List[str] = []):
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(profiles)
    module.accept(visitor)
    return visitor.ir()


def to_qir_bitcode(circuit, profiles: List[str] = []):
    module = QiskitModule.from_quantum_circuit(circuit=circuit)
    visitor = BasicQisVisitor(profiles)
    module.accept(visitor)
    return visitor.bitcode()
