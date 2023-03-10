##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.translate import to_qir_module
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

import test_utils


def test_single_array():
    circuit = QuantumCircuit(3, 3)
    circuit.name = "test_single_array"
    circuit.h(1)
    circuit.s(2)
    circuit.t(0)
    circuit.measure([0, 1, 2], [2, 0, 1])

    generated_qir = str(to_qir_module(circuit)[0]).splitlines()

    test_utils.check_attributes(generated_qir, 3, 3)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 1)
    assert func[2] == test_utils.single_op_call_string("s", 2)
    assert func[3] == test_utils.single_op_call_string("t", 0)
    assert func[4] == test_utils.measure_call_string("mz", 2, 0)
    assert func[5] == test_utils.measure_call_string("mz", 0, 1)
    assert func[6] == test_utils.measure_call_string("mz", 1, 2)
    assert func[7] == test_utils.array_record_output_string(3)
    assert func[8] == test_utils.result_record_output_string(2)
    assert func[9] == test_utils.result_record_output_string(1)
    assert func[10] == test_utils.result_record_output_string(0)
    assert func[11] == test_utils.return_string()
    assert len(func) == 12


def test_no_measure_with_no_registers():
    circuit = QuantumCircuit(1, 0)
    circuit.name = "test_no_measure_with_no_registers"
    circuit.h(0)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()

    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_no_measure_with_register():
    circuit = QuantumCircuit(1, 1)
    circuit.name = "test_no_measure_with_register"
    circuit.h(0)
    generated_qir = str(to_qir_module(circuit)[0]).splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 0)
    assert func[2] == test_utils.array_record_output_string(1)
    assert func[3] == test_utils.result_record_output_string(0)
    assert func[4] == test_utils.return_string()
    assert len(func) == 5


def test_branching_on_bit_emits_correct_ir():
    qr = QuantumRegister(1, "qreg")
    cr = ClassicalRegister(1, "creg")
    circuit = QuantumCircuit(qr, cr, name="branching_on_bit_emits_correct_ir")
    circuit.x(0)
    circuit.measure(0, 0)
    circuit.x(0).c_if(cr[0], 1)

    ir = str(to_qir_module(circuit)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("x", 0)
    assert func[2] == test_utils.measure_call_string("mz", 0, 0)
    assert func[3] == test_utils.equal("0", 0)
    assert func[4] == f"br i1 %0, label %then, label %else"
    assert func[5] == ""
    assert (
        func[6] == f"then:                                             ; preds = %entry"
    )
    assert func[7] == test_utils.single_op_call_string("x", 0)
    assert func[8] == f"br label %continue"
    assert func[9] == ""
    assert (
        func[10]
        == f"else:                                             ; preds = %entry"
    )
    assert func[11] == f"br label %continue"
    assert func[12] == ""
    assert (
        func[13]
        == f"continue:                                         ; preds = %else, %then"
    )
    assert func[14] == test_utils.array_record_output_string(1)
    assert func[15] == test_utils.result_record_output_string(0)
    assert func[16] == test_utils.return_string()

    assert len(func) == 17


def test_branching_on_register_with_one_bit_emits_correct_ir():
    qr = QuantumRegister(1, "qreg")
    cr = ClassicalRegister(1, "creg")
    circuit = QuantumCircuit(
        qr, cr, name="branching_on_register_with_one_bit_emits_correct_ir"
    )
    circuit.x(0)
    circuit.measure(0, 0)
    circuit.x(0).c_if(cr, 1)

    ir = str(to_qir_module(circuit)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("x", 0)
    assert func[2] == test_utils.measure_call_string("mz", 0, 0)
    assert func[3] == test_utils.equal("0", 0)
    assert func[4] == f"br i1 %0, label %then, label %else"
    assert func[5] == ""
    assert (
        func[6] == f"then:                                             ; preds = %entry"
    )
    assert func[7] == test_utils.single_op_call_string("x", 0)
    assert func[8] == f"br label %continue"
    assert func[9] == ""
    assert (
        func[10]
        == f"else:                                             ; preds = %entry"
    )
    assert func[11] == f"br label %continue"
    assert func[12] == ""
    assert (
        func[13]
        == f"continue:                                         ; preds = %else, %then"
    )
    assert func[14] == test_utils.array_record_output_string(1)
    assert func[15] == test_utils.result_record_output_string(0)
    assert func[16] == test_utils.return_string()

    assert len(func) == 17


def test_no_measure_without_registers():
    circuit = QuantumCircuit(1)
    circuit.name = "test_no_measure_no_registers"
    circuit.h(0)

    generated_qir = str(to_qir_module(circuit)[0]).splitlines()

    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_measurement_into_multiple_registers_is_mapped_correctly():
    cr0 = ClassicalRegister(2, "first")
    cr1 = ClassicalRegister(3, "second")
    circuit = QuantumCircuit(5)
    circuit.add_register(cr0)
    circuit.add_register(cr1)
    circuit.name = "measurement_into_multiple_registers"
    circuit.h(0)

    circuit.measure([0, 0], [0, 2])

    generated_qir = str(to_qir_module(circuit)[0]).splitlines()

    test_utils.check_attributes(generated_qir, 5, 5)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 0)
    assert func[2] == test_utils.measure_call_string("mz", 0, 0)
    assert func[3] == test_utils.measure_call_string("mz", 2, 0)
    assert func[4] == test_utils.array_record_output_string(2)
    assert func[5] == test_utils.result_record_output_string(1)
    assert func[6] == test_utils.result_record_output_string(0)
    assert func[7] == test_utils.array_record_output_string(3)
    assert func[8] == test_utils.result_record_output_string(4)
    assert func[9] == test_utils.result_record_output_string(3)
    assert func[10] == test_utils.result_record_output_string(2)
    assert func[11] == test_utils.return_string()
    assert len(func) == 12


def test_using_static_allocation_is_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = str(to_qir_module(circuit)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 0)
    assert func[2] == test_utils.measure_call_string("mz", 0, 0)
    assert func[3] == test_utils.array_record_output_string(1)
    assert func[4] == test_utils.result_record_output_string(0)
    assert func[5] == test_utils.return_string()
    assert len(func) == 6


def test_record_output_when_true_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = str(to_qir_module(circuit, record_output=True)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 0)
    assert func[2] == test_utils.measure_call_string("mz", 0, 0)
    assert func[3] == test_utils.array_record_output_string(1)
    assert func[4] == test_utils.result_record_output_string(0)
    assert func[5] == test_utils.return_string()
    assert len(func) == 6


def test_record_output_when_false_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = str(to_qir_module(circuit, record_output=False)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("h", 0)
    assert func[2] == test_utils.measure_call_string("mz", 0, 0)
    assert func[3] == test_utils.return_string()
    assert len(func) == 4


def test_barrier_default_bypass():
    circuit = QuantumCircuit(1)
    circuit.barrier()
    circuit.x(0)

    ir = str(to_qir_module(circuit)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("x", 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_barrier_with_qubits_default_bypass():
    circuit = QuantumCircuit(3)
    circuit.barrier([2, 0, 1])
    circuit.x(0)

    ir = str(to_qir_module(circuit)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 3, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string("x", 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_barrier_with_override():
    circuit = QuantumCircuit(1)
    circuit.barrier()

    ir = str(to_qir_module(circuit, emit_barrier_calls=True)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.generic_op_call_string("barrier", [])
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_barrier_with_qubits_with_override():
    circuit = QuantumCircuit(3)
    circuit.barrier([2, 0, 1])

    ir = str(to_qir_module(circuit, emit_barrier_calls=True)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 3, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.generic_op_call_string("barrier", [])
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_swap():
    circuit = QuantumCircuit(3)
    circuit.swap(2, 0)

    ir = str(to_qir_module(circuit)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 3, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.double_op_call_string("swap", 2, 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_ccx():
    circuit = QuantumCircuit(3)
    circuit.ccx(2, 0, 1)

    ir = str(to_qir_module(circuit)[0])
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 3, 0)
    func = test_utils.get_entry_point_body(generated_qir)

    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.generic_op_call_string("ccx", [2, 0, 1])
    assert func[2] == test_utils.return_string()
    assert len(func) == 3
