##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from enum import Flag, auto
import os
from typing import List, Union
from qiskit import ClassicalRegister
from qiskit.circuit import Qubit, Clbit
from qiskit.circuit.instruction import Instruction


class Capability(Flag):
    NONE = 0
    CONDITIONAL_BRANCHING_ON_RESULT = auto()
    QUBIT_USE_AFTER_MEASUREMENT = auto()
    ALL = CONDITIONAL_BRANCHING_ON_RESULT | \
          QUBIT_USE_AFTER_MEASUREMENT


class CapabilityError(Exception):
    """Base class for profile validation exceptions"""
    pass


class ConditionalBranchingOnResultError(CapabilityError):
    def __init__(self, instruction: Instruction, qargs: List[Qubit], cargs: List[Clbit], profile: str):
        instruction_string = _get_instruction_string(instruction, qargs, cargs)
        self.instruction_string = instruction_string
        self.msg_suffix = "Support for branching based on measurement requires Capability.CONDITIONAL_BRANCHING_ON_RESULT"
        self.msg = f"Attempted to branch on register value.{os.linesep}Instruction: {instruction_string}{os.linesep}{self.msg_suffix}"
        CapabilityError.__init__(self, self.msg)
        self.instruction = instruction
        self.qargs = qargs
        self.cargs = cargs
        self.profile = profile


class QubitUseAfterMeasurementError(CapabilityError):
    def __init__(self, instruction: Instruction, qargs: List[Qubit], cargs: List[Clbit], profile: str):
        instruction_string = _get_instruction_string(instruction, qargs, cargs)
        self.instruction_string = instruction_string
        self.msg_suffix = "Support for qubit reuse requires Capability.QUBIT_USE_AFTER_MEASUREMENT"
        self.msg = f"Qubit was used after being measured.{os.linesep}Instruction: {instruction_string}{os.linesep}{self.msg_suffix}"
        CapabilityError.__init__(self, self.msg)
        self.instruction = instruction
        self.qargs = qargs
        self.cargs = cargs
        self.profile = profile


def _get_instruction_string(instruction: Instruction, qargs: List[Qubit], cargs: List[Clbit]):
    gate_params = ",".join(
        ["param(%s[%i])" % (c.register.name, c.index) for c in cargs])
    qubit_params = ",".join(
        ["%s[%i]" % (q.register.name, q.index) for q in qargs])
    instruction_name = instruction.name
    if instruction.condition is not None:
        # condition should be a
        # - tuple (ClassicalRegister, int)
        # - tuple (Clbit, bool)
        # - tuple (Clbit, int)
        if isinstance(instruction.condition[0], Clbit):
            bit : Clbit = instruction.condition[0]
            value : Union[int, bool] = instruction.condition[1]
            instruction_name = "if(%s[%d] == %s) %s" % (
                bit._register.name,
                bit._index,
                value,
                instruction_name
            )
        else:
            register : ClassicalRegister = instruction.condition[0]
            value : int = instruction.condition[1]
            instruction_name = "if(%s == %d) %s" % (
                register._name,
                value,
                instruction_name
            )

    if gate_params:
        return f"{instruction_name}({gate_params}) {qubit_params}"
    else:
        return f"{instruction_name} {qubit_params}"
