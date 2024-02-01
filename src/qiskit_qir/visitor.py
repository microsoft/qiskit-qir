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
from qiskit.circuit.bit import Bit
import pyqir.qis as qis
import pyqir.rt as rt
import pyqir
from pyqir import (
    BasicBlock,
    Builder,
    Constant,
    Function,
    FunctionType,
    IntType,
    Linkage,
    Module,
    PointerType,
    const,
    entry_point,
    qubit_id,
)
from typing import List, Union

from qiskit_qir.capability import (
    Capability,
    ConditionalBranchingOnResultError,
    QubitUseAfterMeasurementError,
)
from qiskit_qir.elements import QiskitModule

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
        self._qiskitModule: QiskitModule | None = None
        self._builder = None
        self._entry_point = None
        self._qubit_labels = {}
        self._clbit_labels = {}
        self._profile = profile
        self._capabilities = self._map_profile_to_capabilities(profile)
        self._measured_qubits = {}
        self._emit_barrier_calls = kwargs.get("emit_barrier_calls", False)
        self._record_output = kwargs.get("record_output", True)

    def visit_qiskit_module(self, module: QiskitModule):
        _log.debug(
            f"Visiting Qiskit module '{module.name}' ({module.num_qubits}, {module.num_clbits})"
        )
        self._module = module.module
        self._qiskitModule = module
        context = self._module.context
        entry = entry_point(
            self._module, module.name, module.num_qubits, module.num_clbits
        )

        self._entry_point = entry.name
        self._builder = Builder(context)
        self._builder.insert_at_end(BasicBlock(context, "entry", entry))

        i8p = PointerType(IntType(context, 8))
        nullptr = Constant.null(i8p)
        rt.initialize(self._builder, nullptr)

    @property
    def entry_point(self) -> str:
        return self._entry_point

    def finalize(self):
        self._builder.ret(None)

    def record_output(self, module: QiskitModule):
        if self._record_output == False:
            return

        i8p = PointerType(IntType(self._module.context, 8))

        # qiskit inverts the ordering of the results within each register
        # but keeps the overall register ordering
        # here we logically loop from n-1 to 0, decrementing in order to
        # invert the register output. The second parameter is an exclusive
        # range so we need to go to -1 instead of 0
        logical_id_base = 0
        for size in module.reg_sizes:
            rt.array_record_output(
                self._builder,
                const(IntType(self._module.context, 64), size),
                Constant.null(i8p),
            )
            for index in range(size - 1, -1, -1):
                result_ref = pyqir.result(self._module.context, logical_id_base + index)
                rt.result_record_output(self._builder, result_ref, Constant.null(i8p))
            logical_id_base += size

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
        for inst, i_qargs, i_cargs in subcircuit.data:
            mapped_qbits = [qargs[subcircuit.qubits.index(i)] for i in i_qargs]
            mapped_clbits = [cargs[subcircuit.clbits.index(i)] for i in i_cargs]
            _log.debug(
                f"Processing sub-instruction {inst.name} with mapped qubits {mapped_qbits}"
            )
            self.visit_instruction(inst, mapped_qbits, mapped_clbits)

    def visit_instruction(
        self,
        instruction: Instruction,
        qargs: List[Bit],
        cargs: List[Bit],
        skip_condition=False,
    ):
        qlabels = [self._qubit_labels.get(bit) for bit in qargs]
        clabels = [self._clbit_labels.get(bit) for bit in cargs]
        qubits = [pyqir.qubit(self._module.context, n) for n in qlabels]
        results = [pyqir.result(self._module.context, n) for n in clabels]

        if (
            instruction.condition is not None
        ) and not self._capabilities & Capability.CONDITIONAL_BRANCHING_ON_RESULT:
            raise ConditionalBranchingOnResultError(
                self._qiskitModule.circuit, instruction, qargs, cargs, self._profile
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
                conditions = [pyqir.result(self._module.context, bit_label)]
            else:
                conditions = [
                    pyqir.result(self._module.context, self._clbit_labels.get(bit))
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
                        qis.if_result(
                            self._builder,
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
                qis.mz(self._builder, qubit, result)
        else:
            if not self._capabilities & Capability.QUBIT_USE_AFTER_MEASUREMENT:
                # If we have a supported instruction, apply the capability
                # check. If we have a composite instruction then it will call
                # back into this function with a supported name and we'll
                # verify at that time
                if instruction.name in _SUPPORTED_INSTRUCTIONS:
                    if any(map(self._measured_qubits.get, map(qubit_id, qubits))):
                        raise QubitUseAfterMeasurementError(
                            self._qiskitModule.circuit,
                            instruction,
                            qargs,
                            cargs,
                            self._profile,
                        )
            if "barrier" == instruction.name:
                if self._emit_barrier_calls:
                    qis.barrier(self._builder)
            elif "delay" == instruction.name:
                pass
            elif "swap" == instruction.name:
                qis.swap(self._builder, *qubits)
            elif "ccx" == instruction.name:
                qis.ccx(self._builder, *qubits)
            elif "cx" == instruction.name:
                qis.cx(self._builder, *qubits)
            elif "cz" == instruction.name:
                qis.cz(self._builder, *qubits)
            elif "h" == instruction.name:
                qis.h(self._builder, *qubits)
            elif "reset" == instruction.name:
                qis.reset(self._builder, qubits[0])
            elif "rx" == instruction.name:
                qis.rx(self._builder, *instruction.params, *qubits)
            elif "ry" == instruction.name:
                qis.ry(self._builder, *instruction.params, *qubits)
            elif "rz" == instruction.name:
                qis.rz(self._builder, *instruction.params, *qubits)
            elif "s" == instruction.name:
                qis.s(self._builder, *qubits)
            elif "sdg" == instruction.name:
                qis.s_adj(self._builder, *qubits)
            elif "t" == instruction.name:
                qis.t(self._builder, *qubits)
            elif "tdg" == instruction.name:
                qis.t_adj(self._builder, *qubits)
            elif "x" == instruction.name:
                qis.x(self._builder, *qubits)
            elif "y" == instruction.name:
                qis.y(self._builder, *qubits)
            elif "z" == instruction.name:
                qis.z(self._builder, *qubits)
            elif "id" == instruction.name:
                # See: https://github.com/qir-alliance/pyqir/issues/74
                qubit = pyqir.qubit(self._module.context, qubit_id(*qubits))
                qis.x(self._builder, qubit)
                qis.x(self._builder, qubit)
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
