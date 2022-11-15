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
from pyqir import (
    BasicBlock,
    BasicQisBuilder,
    Builder,
    Context,
    Function,
    FunctionType,
    Linkage,
    Module,
    Type,
    entry_point,
    qubit_type,
    qubit as get_qubit,
    qubit_id,
    result_type,
    result as get_result,
)
from typing import List, Union

from qiskit_qir.capability import (
    Capability,
    ConditionalBranchingOnResultError,
    QubitUseAfterMeasurementError,
)

_log = logging.getLogger(name=__name__)

# This list cannot change as existing clients hardcoded to it
# when it wasn't designed to be externally used.
# To work around this we are using an additional list to replace
# this list which contains the instructions that we can process.
# This following three variables can be removed in a future
# release after dependency version restrictions have been applied.
SUPPORTED_INSTRUCTIONS = [
    "barrier",
    "delay",
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
    "id",
]

_QUANTUM_INSTRUCTIONS = [
    "barrier",
    "ccx",
    "cx",
    "cz",
    "h",
    "id",
    "m",
    "measure",
    "reset",
    "rx",
    "ry",
    "rz",
    "s",
    "sdg",
    "swap",
    "t",
    "tdg",
    "x",
    "y",
    "z",
]

_NOOP_INSTRUCTIONS = ["delay"]

_SUPPORTED_INSTRUCTIONS = _QUANTUM_INSTRUCTIONS + _NOOP_INSTRUCTIONS


class QuantumCircuitElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, register):
        raise NotImplementedError

    @abstractmethod
    def visit_instruction(self, instruction):
        raise NotImplementedError


class BasicQisVisitor(QuantumCircuitElementVisitor):
    def __init__(self, profile: str = "AdaptiveExecution", **kwargs):
        self._module = None
        self._builder = None
        self._qir = None
        self._qubit_labels = {}
        self._clbit_labels = {}
        self._profile = profile
        self._capabilities = self._map_profile_to_capabilities(profile)
        self._measured_qubits = {}
        self._emit_barrier_calls = kwargs.get("emit_barrier_calls", False)
        self._record_output = kwargs.get("record_output", True)
        self._barrier = None
        self._ccx = None
        self._swap = None

    def visit_qiskit_module(self, module):
        _log.debug(
            f"Visiting Qiskit module '{module.name}' ({module.num_qubits}, {module.num_clbits})"
        )
        self._module = module.module
        context = self._module.context
        entry = entry_point(
            self._module, module.name, module.num_qubits, module.num_clbits
        )
        self._builder = Builder(context)
        self._builder.insert_from_end(BasicBlock(context, "entry", entry))
        self._qis = BasicQisBuilder(self._builder)

        void_type = Type.void(context)
        qtype = qubit_type(context)

        self._barrier = Function(
            FunctionType(void_type, []),
            Linkage.EXTERNAL,
            "__quantum__qis__barrier__body",
            self._module,
        )
        self._ccx = Function(
            FunctionType(void_type, [qtype, qtype, qtype]),
            Linkage.EXTERNAL,
            "__quantum__qis__ccnot__body",
            self._module,
        )
        self._swap = Function(
            FunctionType(void_type, [qtype, qtype]),
            Linkage.EXTERNAL,
            "__quantum__qis__swap__body",
            self._module,
        )

    def finalize(self):
        self._builder.ret(None)

    def record_output(self, module):
        if self._record_output == False:
            return

        void_type = Type.void(self._module.context)
        rtype = result_type(self._module.context)

        # produces output records of exactly "RESULT ARRAY_START"

        array_start_record_output = Function(
            FunctionType(void_type, []),
            Linkage.EXTERNAL,
            "__quantum__rt__array_start_record_output",
            self._module,
        )

        # produces output records of exactly "RESULT ARRAY_END"
        array_end_record_output = Function(
            FunctionType(void_type, []),
            Linkage.EXTERNAL,
            "__quantum__rt__array_end_record_output",
            self._module,
        )

        # produces output records of exactly "RESULT 0" or "RESULT 1"
        result_record_output = Function(
            FunctionType(void_type, [rtype]),
            Linkage.EXTERNAL,
            "__quantum__rt__result_record_output",
            self._module,
        )
        # qiskit inverts the ordering of the results within each register
        # but keeps the overall register ordering
        # here we logically loop from n-1 to 0, decrementing in order to
        # invert the register output. The second parameter is an exclusive
        # range so we need to go to -1 instead of 0
        logical_id_base = 0
        for size in module.reg_sizes:
            self._builder.call(array_start_record_output, [])
            for index in range(size - 1, -1, -1):
                result_ref = get_result(self._module.context, logical_id_base + index)
                self._builder.call(result_record_output, [result_ref])
            logical_id_base += size
            self._builder.call(array_end_record_output, [])

    def visit_register(self, register):
        _log.debug(f"Visiting register '{register.name}'")
        if isinstance(register, QuantumRegister):
            self._qubit_labels.update(
                {bit: n + len(self._qubit_labels) for n, bit in enumerate(register)}
            )
            _log.debug(
                f"Added labels for qubits {[bit for n, bit in enumerate(register)]}"
            )
        elif isinstance(register, ClassicalRegister):
            self._clbit_labels.update(
                {bit: n + len(self._clbit_labels) for n, bit in enumerate(register)}
            )
        else:
            raise ValueError(f"Register of type {type(register)} not supported.")

    def process_composite_instruction(
        self, instruction: Instruction, qargs: List[Qubit], cargs: List[Clbit]
    ):
        subcircuit = instruction.definition
        _log.debug(
            f"Processing composite instruction {instruction.name} with qubits {qargs}"
        )
        if len(qargs) != subcircuit.num_qubits:
            raise ValueError(
                f"Composite instruction {instruction.name} called with the wrong number of qubits; \
{subcircuit.num_qubits} expected, {len(qargs)} provided"
            )
        if len(cargs) != subcircuit.num_clbits:
            raise ValueError(
                f"Composite instruction {instruction.name} called with the wrong number of classical bits; \
{subcircuit.num_clbits} expected, {len(cargs)} provided"
            )
        for (inst, i_qargs, i_cargs) in subcircuit.data:
            mapped_qbits = [qargs[subcircuit.qubits.index(i)] for i in i_qargs]
            mapped_clbits = [cargs[subcircuit.clbits.index] for i in i_cargs]
            _log.debug(
                f"Processing sub-instruction {inst.name} with mapped qubits {mapped_qbits}"
            )
            self.visit_instruction(inst, mapped_qbits, mapped_clbits)

    def visit_instruction(self, instruction, qargs, cargs, skip_condition=False):
        qlabels = [self._qubit_labels.get(bit) for bit in qargs]
        clabels = [self._clbit_labels.get(bit) for bit in cargs]
        qubits = [get_qubit(self._module.context, n) for n in qlabels]
        results = [get_result(self._module.context, n) for n in clabels]

        if (
            instruction.condition is not None
        ) and not self._capabilities & Capability.CONDITIONAL_BRANCHING_ON_RESULT:
            raise ConditionalBranchingOnResultError(
                instruction, qargs, cargs, self._profile
            )

        labels = ", ".join([str(l) for l in qlabels + clabels])
        if instruction.condition is None or skip_condition:
            _log.debug(f"Visiting instruction '{instruction.name}' ({labels})")

        if instruction.condition is not None and skip_condition is False:
            _log.debug(
                f"Visiting condition for instruction '{instruction.name}' ({labels})"
            )

            if isinstance(instruction.condition[0], Clbit):
                bit_label = self._clbit_labels.get(instruction.condition[0])
                conditions = [get_result(self._module.context, bit_label)]
            else:
                conditions = [
                    get_result(self._module.context, self._clbit_labels.get(bit))
                    for bit in instruction.condition[0]
                ]

            # Convert value into a bitstring of the same length as classical register
            # condition should be a
            # - tuple (ClassicalRegister, int)
            # - tuple (Clbit, bool)
            # - tuple (Clbit, int)
            if isinstance(instruction.condition[0], Clbit):
                bit: Clbit = instruction.condition[0]
                value: Union[int, bool] = instruction.condition[1]
                if value:
                    values = "1"
                else:
                    values = "0"
            else:
                register: ClassicalRegister = instruction.condition[0]
                value: int = instruction.condition[1]
                values = format(value, f"0{register.size}b")

            # Add branches recursively for each bit in the bitstring
            def __visit():
                self.visit_instruction(instruction, qargs, cargs, skip_condition=True)

            def _branch(conditions_values):
                try:
                    cond, val = next(conditions_values)

                    def __branch():
                        self._qis.if_result(
                            cond,
                            one=_branch(conditions_values) if val == "1" else None,
                            zero=_branch(conditions_values) if val == "0" else None,
                        )

                except StopIteration:
                    return __visit
                else:
                    return __branch

            if len(conditions) < len(values):
                raise ValueError(
                    f"Value {value} is larger than register width {len(conditions)}."
                )

            # qiskit has the most significant bit on the right, so we
            # must reverse the bit array for comparisons.
            _branch(zip(conditions, values[::-1]))()
        elif (
            "measure" == instruction.name
            or "m" == instruction.name
            or "mz" == instruction.name
        ):
            for qubit, result in zip(qubits, results):
                self._measured_qubits[qubit_id(qubit)] = True
                self._qis.mz(qubit, result)
        else:
            if not self._capabilities & Capability.QUBIT_USE_AFTER_MEASUREMENT:
                # If we have a supported instruction, apply the capability
                # check. If we have a composite instruction then it will call
                # back into this function with a supported name and we'll
                # verify at that time
                if instruction.name in _SUPPORTED_INSTRUCTIONS:
                    if any(map(self._measured_qubits.get, map(qubit_id, qubits))):
                        raise QubitUseAfterMeasurementError(
                            instruction, qargs, cargs, self._profile
                        )
            if "barrier" == instruction.name:
                if self._emit_barrier_calls:
                    self._builder.call(self._barrier, [])
            elif "delay" == instruction.name:
                pass
            elif "swap" == instruction.name:
                self._builder.call(self._swap, qubits)
            elif "ccx" == instruction.name:
                self._builder.call(self._ccx, qubits)
            elif "cx" == instruction.name:
                self._qis.cx(*qubits)
            elif "cz" == instruction.name:
                self._qis.cz(*qubits)
            elif "h" == instruction.name:
                self._qis.h(*qubits)
            elif "reset" == instruction.name:
                self._qis.reset(qubits[0])
            elif "rx" == instruction.name:
                self._qis.rx(*instruction.params, *qubits)
            elif "ry" == instruction.name:
                self._qis.ry(*instruction.params, *qubits)
            elif "rz" == instruction.name:
                self._qis.rz(*instruction.params, *qubits)
            elif "s" == instruction.name:
                self._qis.s(*qubits)
            elif "sdg" == instruction.name:
                self._qis.s_adj(*qubits)
            elif "t" == instruction.name:
                self._qis.t(*qubits)
            elif "tdg" == instruction.name:
                self._qis.t_adj(*qubits)
            elif "x" == instruction.name:
                self._qis.x(*qubits)
            elif "y" == instruction.name:
                self._qis.y(*qubits)
            elif "z" == instruction.name:
                self._qis.z(*qubits)
            elif "id" == instruction.name:
                # See: https://github.com/qir-alliance/pyqir/issues/74
                self._qis.x(get_qubit(self._module.context, 0))
                self._qis.x(get_qubit(self._module.context, 0))
            elif instruction.definition:
                _log.debug(
                    f"About to process composite instruction {instruction.name} with qubits {qargs}"
                )
                self.process_composite_instruction(instruction, qargs, cargs)
            else:
                raise ValueError(
                    f"Gate {instruction.name} is not supported. \
    Please transpile using the list of supported gates: {_SUPPORTED_INSTRUCTIONS}."
                )

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()

    def _map_profile_to_capabilities(self, profile: str):
        value = profile.strip().lower()
        if "BasicExecution".lower() == value:
            return Capability.NONE
        elif "AdaptiveExecution".lower() == value:
            return Capability.ALL
        else:
            raise UnsupportedOperation(
                f"The supplied profile is not supported: {profile}."
            )
