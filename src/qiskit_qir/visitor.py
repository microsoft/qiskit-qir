##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from io import UnsupportedOperation
import logging
from abc import ABCMeta, abstractmethod
from qiskit import ClassicalRegister, QuantumRegister
from qiskit.circuit import Qubit, Clbit
from qiskit.circuit.instruction import Instruction
from pyqir.generator import SimpleModule, BasicQisBuilder, types
from typing import List, Union

from qiskit_qir.capability import Capability, ConditionalBranchingOnResultError, QubitUseAfterMeasurementError

_log = logging.getLogger(name=__name__)

QUANTUM_INSTRUCTIONS = [
    "measure",
    "m",
    "cx",
    "cz",
    "h",
    "reset",
    "rx",
    "ry",
    "rz",
    "s",
    "sdg",
    "t",
    "tdg",
    "x",
    "y",
    "z",
    "id"
]

NOOP_INSTRUCTIONS = [
    "barrier",
    "delay",
]

SUPPORTED_INSTRUCTIONS = QUANTUM_INSTRUCTIONS + NOOP_INSTRUCTIONS


class QuantumCircuitElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, register):
        raise NotImplementedError

    @abstractmethod
    def visit_instruction(self, instruction):
        raise NotImplementedError


class BasicQisVisitor(QuantumCircuitElementVisitor):
    def __init__(self, profile: str = "AdaptiveExecution", kwargs = {}):
        self._module = None
        self._builder = None
        self._qubit_labels = {}
        self._clbit_labels = {}
        self._profile = profile
        self._capabilities = self._map_profile_to_capabilities(profile)
        self._measured_qubits = {}
        self._use_static_qubit_alloc = kwargs.get("use_static_qubit_alloc", True)
        self._use_static_result_alloc = kwargs.get("use_static_result_alloc", True)
        self._record_output = kwargs.get("record_output", True)

    def visit_qiskit_module(self, module):
        _log.debug(
            f"Visiting Qiskit module '{module.name}' ({module.num_qubits}, {module.num_clbits})")
        self._module = SimpleModule(
            name=module.name,
            num_qubits=module.num_qubits,
            num_results=module.num_clbits,
        )
        self._module.use_static_qubit_alloc(self._use_static_qubit_alloc)
        self._module.use_static_result_alloc(self._use_static_result_alloc)

        self._builder = BasicQisBuilder(self._module.builder)

    def record_output(self, module):
        if self._record_output == False:
            return

        # produces output records of exactly "RESULT ARRAY_START"
        array_start_record_output = self._module.add_external_function(
            "__quantum__rt__array_start_record_output", types.Function(
                [], types.VOID)
        )

        # produces output records of exactly "RESULT ARRAY_END"
        array_end_record_output = self._module.add_external_function(
            "__quantum__rt__array_end_record_output", types.Function(
                [], types.VOID)
        )

        # produces output records of exactly "RESULT 0" or "RESULT 1"
        result_record_output = self._module.add_external_function(
            "__quantum__rt__result_record_output", types.Function(
                [types.RESULT], types.VOID)
        )

        # qiskit inverts the ordering of the results within each register
        # but keeps the overall register ordering
        # here we logically loop from n-1 to 0, decrementing in order to
        # invert the register output. The second parameter is an exclusive
        # range so we need to go to -1 instead of 0
        logical_id_base = 0
        for size in module.reg_sizes:
            self._module.builder.call(array_start_record_output, [])
            for index in range(size - 1, -1, -1):
                result_ref = self._module.results[logical_id_base + index]
                self._module.builder.call(result_record_output, [result_ref])
            logical_id_base += size
            self._module.builder.call(array_end_record_output, [])

    def visit_register(self, register):
        _log.debug(f"Visiting register '{register.name}'")
        if isinstance(register, QuantumRegister):
            self._qubit_labels.update({
                bit: n + len(self._qubit_labels) for n, bit in enumerate(register)
            })
            _log.debug(
                f"Added labels for qubits {[bit for n, bit in enumerate(register)]}")
        elif isinstance(register, ClassicalRegister):
            self._clbit_labels.update({
                bit: n + len(self._clbit_labels) for n, bit in enumerate(register)
            })
        else:
            raise ValueError(
                f"Register of type {type(register)} not supported.")

    def process_composite_instruction(self, instruction: Instruction, qargs: List[Qubit], cargs: List[Clbit]):
        subcircuit = instruction.definition
        _log.debug(
            f"Processing composite instruction {instruction.name} with qubits {qargs}")
        if len(qargs) != subcircuit.num_qubits:
            raise ValueError(f"Composite instruction {instruction.name} called with the wrong number of qubits; \
{subcircuit.num_qubits} expected, {len(qargs)} provided")
        if len(cargs) != subcircuit.num_clbits:
            raise ValueError(f"Composite instruction {instruction.name} called with the wrong number of classical bits; \
{subcircuit.num_clbits} expected, {len(cargs)} provided")
        for (inst, i_qargs, i_cargs) in subcircuit.data:
            mapped_qbits = [qargs[subcircuit.qubits.index(i)] for i in i_qargs]
            mapped_clbits = [cargs[subcircuit.clbits.index] for i in i_cargs]
            _log.debug(
                f"Processing sub-instruction {inst.name} with mapped qubits {mapped_qbits}")
            self.visit_instruction(inst, mapped_qbits, mapped_clbits)

    def visit_instruction(self, instruction, qargs, cargs, skip_condition=False):
        qlabels = [self._qubit_labels.get(bit) for bit in qargs]
        clabels = [self._clbit_labels.get(bit) for bit in cargs]
        qubits = [self._module.qubits[n] for n in qlabels]
        results = [self._module.results[n] for n in clabels]

        if (instruction.condition is not None) and not self._capabilities & Capability.CONDITIONAL_BRANCHING_ON_RESULT:
            raise ConditionalBranchingOnResultError(instruction, qargs, cargs, self._profile)

        labels = ", ".join([str(l) for l in qlabels + clabels])
        if instruction.condition is None or skip_condition:
            _log.debug(f"Visiting instruction '{instruction.name}' ({labels})")

        if instruction.condition is not None and skip_condition is False:
            _log.debug(
                f"Visiting condition for instruction '{instruction.name}' ({labels})")

            if isinstance(instruction.condition[0], Clbit):
                bit_label = self._clbit_labels.get(instruction.condition[0])
                conditions = [self._module.results[bit_label]]
            else:
                conditions = [self._module.results[self._clbit_labels.get(
                    bit)] for bit in instruction.condition[0]]

            # Convert value into a bitstring of the same length as classical register
            # condition should be a
            # - tuple (ClassicalRegister, int)
            # - tuple (Clbit, bool)
            # - tuple (Clbit, int)
            if isinstance(instruction.condition[0], Clbit):
                bit : Clbit = instruction.condition[0]
                value : Union[int, bool] = instruction.condition[1]
                if value:
                    values = '1'
                else:
                    values = '0'
            else:
                register : ClassicalRegister = instruction.condition[0]
                value : int = instruction.condition[1]
                values = format(value, f'0{register.size}b')

            # Add branches recursively for each bit in the bitstring
            def __visit():
                self.visit_instruction(
                    instruction, qargs, cargs, skip_condition=True)

            def _branch(conditions_values):
                try:
                    result, val = next(conditions_values)

                    def __branch():
                        self._builder.if_result(
                            result=result,
                            one=_branch(
                                conditions_values) if val == "1" else None,
                            zero=_branch(
                                conditions_values) if val == "0" else None
                        )
                except StopIteration:
                    return __visit
                else:
                    return __branch

            if len(conditions) < len(values):
                raise ValueError(f"Value {value} is larger than register width {len(conditions)}.")

            # qiskit has the most significant bit on the right, so we
            # must reverse the bit array for comparisons.
            _branch(zip(conditions, values[::-1]))()
        elif "measure" == instruction.name or "m" == instruction.name or "mz" == instruction.name:
            for qubit, result in zip(qubits, results):
                self._measured_qubits[qubit] = True
                self._builder.m(qubit, result)
        else:
            if not self._capabilities & Capability.QUBIT_USE_AFTER_MEASUREMENT:
                # If we have a supported instruction, apply the capability
                # check. If we have a composite instruction then it will call
                # back into this function with a supported name and we'll
                # verify at that time
                if instruction.name in SUPPORTED_INSTRUCTIONS:
                    if any(map(self._measured_qubits.get, qubits)):
                        raise QubitUseAfterMeasurementError(instruction, qargs, cargs, self._profile)
            if "barrier" == instruction.name:
                pass
            elif "delay" == instruction.name:
                pass
            elif "cx" == instruction.name:
                self._builder.cx(*qubits)
            elif "cz" == instruction.name:
                self._builder.cz(*qubits)
            elif "h" == instruction.name:
                self._builder.h(*qubits)
            elif "reset" == instruction.name:
                self._builder.reset(qubits[0])
            elif "rx" == instruction.name:
                self._builder.rx(*instruction.params, *qubits)
            elif "ry" == instruction.name:
                self._builder.ry(*instruction.params, *qubits)
            elif "rz" == instruction.name:
                self._builder.rz(*instruction.params, *qubits)
            elif "s" == instruction.name:
                self._builder.s(*qubits)
            elif "sdg" == instruction.name:
                self._builder.s_adj(*qubits)
            elif "t" == instruction.name:
                self._builder.t(*qubits)
            elif "tdg" == instruction.name:
                self._builder.t_adj(*qubits)
            elif "x" == instruction.name:
                self._builder.x(*qubits)
            elif "y" == instruction.name:
                self._builder.y(*qubits)
            elif "z" == instruction.name:
                self._builder.z(*qubits)
            elif "id" == instruction.name:
                # See: https://github.com/qir-alliance/pyqir/issues/74
                self._builder.x(self._module.qubits[0])
                self._builder.x(self._module.qubits[0])
            elif instruction.definition:
                _log.debug(
                    f"About to process composite instruction {instruction.name} with qubits {qargs}")
                self.process_composite_instruction(instruction, qargs, cargs)
            else:
                raise ValueError(f"Gate {instruction.name} is not supported. \
    Please transpile using the list of supported gates: {SUPPORTED_INSTRUCTIONS}.")

    def ir(self) -> str:
        return self._module.ir()

    def bitcode(self) -> bytes:
        return self._module.bitcode()

    def _map_profile_to_capabilities(self, profile: str):
        value = profile.strip().lower()
        if "BasicExecution".lower() == value:
            return Capability.NONE
        elif "AdaptiveExecution".lower() == value:
            return Capability.ALL
        else:
            raise UnsupportedOperation(f"The supplied profile is not supported: {profile}.")
