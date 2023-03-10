##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##

from typing import List
from pyqir import is_entry_point, Context, Module, Function


def _qubit_string(qubit: int) -> str:
    if qubit == 0:
        return "%Qubit* null"
    else:
        return f"%Qubit* inttoptr (i64 {qubit} to %Qubit*)"


def _result_string(res: int) -> str:
    if res == 0:
        return "%Result* null"
    else:
        return f"%Result* inttoptr (i64 {res} to %Result*)"


def initialize_call_string() -> str:
    return "call void @__quantum__rt__initialize(i8* null)"


def single_op_call_string(name: str, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb)})"


def adj_op_call_string(name: str, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__adj({_qubit_string(qb)})"


def double_op_call_string(name: str, qb1: int, qb2: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb1)}, {_qubit_string(qb2)})"


def rotation_call_string(name: str, theta: float, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__body(double {theta:#e}, {_qubit_string(qb)})"


def measure_call_string(name: str, res: str, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb)}, {_result_string(res)})"


def equal(var: str, res: str):
    return f"%{var} = call i1 @__quantum__qis__read_result__body({_result_string(res)})"


def generic_op_call_string(name: str, qbs: List[int]) -> str:
    args = ", ".join(_qubit_string(qb) for qb in qbs)
    return f"call void @__quantum__qis__{name}__body({args})"


def return_string() -> str:
    return "ret void"


def array_record_output_string(num_elements: int) -> str:
    return (
        f"call void @__quantum__rt__array_record_output(i64 {num_elements}, i8* null)"
    )


def result_record_output_string(res: str) -> str:
    return f"call void @__quantum__rt__result_record_output({_result_string(res)}, i8* null)"


# Returns the method body with:
# - leading spaces trimmed
# - first label skipped
# - signature and closing braces removed
def get_entry_point_body(qir: List[str]) -> List[str]:
    joined = "\n".join(qir)
    mod = Module.from_ir(Context(), joined)
    func = next(filter(is_entry_point, mod.functions))
    assert func is not None, "No main function found"
    lines = str(func).splitlines()[2:-1]
    return list(map(lambda line: line.strip(), lines))


def get_entry_point(mod: Module) -> Function:
    func = next(filter(is_entry_point, mod.functions))
    assert func is not None, "No main function found"
    return func


def check_attributes(
    qir: List[str], expected_qubits: int = 0, expected_results: int = 0
) -> None:
    x = "\n".join(qir)
    mod = Module.from_ir(Context(), x)
    func = next(filter(is_entry_point, mod.functions))

    check_attributes_on_entrypoint(func, expected_qubits, expected_results)


def check_attributes_on_entrypoint(
    func: Function, expected_qubits: int = 0, expected_results: int = 0
) -> None:
    actual_qubits = -1
    actual_results = -1
    from pyqir import required_num_qubits, required_num_results

    actual_qubits = required_num_qubits(func)
    actual_results = required_num_results(func)
    assert (
        expected_qubits == actual_qubits
    ), f"Incorrect qubit count: {expected_qubits} expected, {actual_qubits} actual"

    assert (
        expected_results == actual_results
    ), f"Incorrect result count: {expected_results} expected, {actual_results} actual"
