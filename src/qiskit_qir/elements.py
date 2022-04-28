##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from typing import List, Union
from qiskit import ClassicalRegister, QuantumRegister
from qiskit.circuit.bit import Bit
from qiskit.circuit.quantumcircuit import QuantumCircuit, Instruction


class _QuantumCircuitElement:
    @classmethod
    def from_element_list(cls, elements):
        return [cls(elem) for elem in elements]


class _Register(_QuantumCircuitElement):
    def __init__(self, register: Union[QuantumRegister, ClassicalRegister]):
        self._register = register

    def accept(self, visitor):
        visitor.visit_register(self._register)


class _Instruction(_QuantumCircuitElement):
    def __init__(
        self,
        instruction: Instruction,
        qargs: List[Bit],
        cargs: List[Bit]
    ):
        self._instruction = instruction
        self._qargs = qargs
        self._cargs = cargs

    def accept(self, visitor):
        visitor.visit_instruction(self._instruction, self._qargs, self._cargs)


class QiskitModule:
    def __init__(self, name, num_qubits, num_clbits, reg_sizes, elements):
        self._name = name
        self._elements = elements
        self._num_qubits = num_qubits
        self._num_clbits = num_clbits
        self.reg_sizes = reg_sizes

    @property
    def name(self):
        return self._name

    @property
    def num_qubits(self):
        return self._num_qubits

    @property
    def num_clbits(self):
        return self._num_clbits

    @classmethod
    def from_quantum_circuit(cls, circuit: QuantumCircuit) -> "QiskitModule":
        """Create a new QiskitModule from a qiskit.QuantumCircuit object."""
        elements = []
        reg_sizes = [len(creg) for creg in circuit.cregs]

        # Registers
        elements.extend(_Register.from_element_list(circuit.qregs))
        elements.extend(_Register.from_element_list(circuit.cregs))

        # Instructions
        for instruction, qargs, cargs in circuit._data:
            elements.append(_Instruction(instruction, qargs, cargs))

        return cls(
            name=circuit.name,
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            reg_sizes=reg_sizes,
            elements=elements,
        )

    def accept(self, visitor):
        visitor.visit_qiskit_module(self)
        for element in self._elements:
            element.accept(visitor)
        visitor.record_output(self)
