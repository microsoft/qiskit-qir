##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from typing import List, Optional, Union
from pyqir import Module, Context
from qiskit import ClassicalRegister, QuantumRegister
from qiskit.circuit.bit import Bit
from qiskit.circuit.quantumcircuit import QuantumCircuit, Instruction
from abc import ABCMeta, abstractmethod


class _QuantumCircuitElement(metaclass=ABCMeta):
    @classmethod
    def from_element_list(cls, elements):
        return [cls(elem) for elem in elements]

    @abstractmethod
    def accept(self, visitor):
        pass


class _Register(_QuantumCircuitElement):
    def __init__(self, register: Union[QuantumRegister, ClassicalRegister]):
        self._register: Union[QuantumRegister, ClassicalRegister] = register

    def accept(self, visitor):
        visitor.visit_register(self._register)


class _Instruction(_QuantumCircuitElement):
    def __init__(self, instruction: Instruction, qargs: List[Bit], cargs: List[Bit]):
        self._instruction: Instruction = instruction
        self._qargs = qargs
        self._cargs = cargs

    def accept(self, visitor):
        visitor.visit_instruction(self._instruction, self._qargs, self._cargs)


class QiskitModule:
    def __init__(
        self,
        circuit: QuantumCircuit,
        name: str,
        module: Module,
        num_qubits: int,
        num_clbits: int,
        reg_sizes: List[int],
        elements: List[_QuantumCircuitElement],
    ):
        self._circuit = circuit
        self._name = name
        self._module = module
        self._elements = elements
        self._num_qubits = num_qubits
        self._num_clbits = num_clbits
        self.reg_sizes = reg_sizes

    @property
    def circuit(self) -> QuantumCircuit:
        return self._circuit

    @property
    def name(self) -> str:
        return self._name

    @property
    def module(self) -> Module:
        return self._module

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def num_clbits(self) -> int:
        return self._num_clbits

    @classmethod
    def from_quantum_circuit(
        cls, circuit: QuantumCircuit, module: Optional[Module] = None
    ) -> "QiskitModule":
        """Create a new QiskitModule from a qiskit.QuantumCircuit object."""
        elements: List[_QuantumCircuitElement] = []
        reg_sizes = [len(creg) for creg in circuit.cregs]

        # Registers
        elements.extend(_Register.from_element_list(circuit.qregs))
        elements.extend(_Register.from_element_list(circuit.cregs))

        # Instructions
        for instruction, qargs, cargs in circuit._data:
            elements.append(_Instruction(instruction, qargs, cargs))

        if module is None:
            module = Module(Context(), circuit.name)
        return cls(
            circuit=circuit,
            name=circuit.name,
            module=module,
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
        visitor.finalize()
