##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from enum import Flag, auto
import os
from typing import Dict, List, Union
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Qubit, Clbit
from qiskit.circuit.instruction import Instruction


class Capability(Flag):
    NONE = 0
    CONDITIONAL_BRANCHING_ON_RESULT = auto()
    QUBIT_USE_AFTER_MEASUREMENT = auto()
    ALL = CONDITIONAL_BRANCHING_ON_RESULT | QUBIT_USE_AFTER_MEASUREMENT


class CapabilityError(Exception):
    """Base class for profile validation exceptions"""

    def _get_bit_labels(
        self,
        circuit: QuantumCircuit,
    ) -> Dict[Union[Qubit, Clbit], str]:
        register_names: Dict[str, Union[QuantumRegister, ClassicalRegister]] = {}
        for registers in (circuit.qregs, circuit.cregs):
            for register in registers:
                register_names[register.name] = register
        bit_labels: Dict[Union[Qubit, Clbit], str] = {
            bit: "%s[%d]" % (name, idx)
            for name, register in register_names.items()
            for (idx, bit) in enumerate(register)
        }
        return bit_labels

    def _get_instruction_string(
        self,
        bit_labels: Dict[Union[Qubit, Clbit], str],
        instruction: Instruction,
        qargs: List[Qubit],
        cargs: List[Clbit],
    ):
        gate_params = ",".join(["param(%s)" % bit_labels[c] for c in cargs])
        qubit_params = ",".join(["%s" % bit_labels[q] for q in qargs])
        instruction_name = instruction.name
        if instruction.condition is not None:
            # condition should be a
            # - tuple (ClassicalRegister, int)
            # - tuple (Clbit, bool)
            # - tuple (Clbit, int)
            if isinstance(instruction.condition[0], Clbit):
                bit: Clbit = instruction.condition[0]
                value: Union[int, bool] = instruction.condition[1]
                instruction_name = "if(%s[%d] == %s) %s" % (
                    bit._register.name,
                    bit._index,
                    value,
                    instruction_name,
                )
            else:
                register: ClassicalRegister = instruction.condition[0]
                value: int = instruction.condition[1]
                instruction_name = "if(%s == %d) %s" % (
                    register._name,
                    value,
                    instruction_name,
                )

        if gate_params:
            return f"{instruction_name}({gate_params}) {qubit_params}"
        else:
            return f"{instruction_name} {qubit_params}"


class ConditionalBranchingOnResultError(CapabilityError):
    def __init__(
        self,
        circuit: QuantumCircuit,
        instruction: Instruction,
        qargs: List[Qubit],
        cargs: List[Clbit],
        profile: str,
    ):
        bit_labels: Dict[Union[Qubit, Clbit], str] = self._get_bit_labels(circuit)
        instruction_string = self._get_instruction_string(
            bit_labels, instruction, qargs, cargs
        )
        self.instruction_string = instruction_string
        self.msg_suffix = "Support for branching based on measurement requires Capability.CONDITIONAL_BRANCHING_ON_RESULT"
        self.msg = f"Attempted to branch on register value.{os.linesep}Instruction: {instruction_string}{os.linesep}{self.msg_suffix}"
        CapabilityError.__init__(self, self.msg)
        self.instruction = instruction
        self.qargs = qargs
        self.cargs = cargs
        self.profile = profile


class QubitUseAfterMeasurementError(CapabilityError):
    def __init__(
        self,
        circuit: QuantumCircuit,
        instruction: Instruction,
        qargs: List[Qubit],
        cargs: List[Clbit],
        profile: str,
    ):
        bit_labels: Dict[Union[Qubit, Clbit], str] = self._get_bit_labels(circuit)
        instruction_string = self._get_instruction_string(
            bit_labels, instruction, qargs, cargs
        )
        self.instruction_string = instruction_string
        self.msg_suffix = (
            "Support for qubit reuse requires Capability.QUBIT_USE_AFTER_MEASUREMENT"
        )
        self.msg = f"Qubit was used after being measured.{os.linesep}Instruction: {instruction_string}{os.linesep}{self.msg_suffix}"
        CapabilityError.__init__(self, self.msg)
        self.instruction = instruction
        self.qargs = qargs
        self.cargs = cargs
        self.profile = profile
