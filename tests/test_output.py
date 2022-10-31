##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from qiskit_qir.translate import to_qir
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

import test_utils


def test_single_array():
    circuit = QuantumCircuit(3, 3)
    circuit.name = "test_single_array"
    circuit.h(1)
    circuit.s(2)
    circuit.t(0)
    circuit.measure([0, 1, 2], [2, 0, 1])

    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 3, 3)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 1)
    assert func[1] == test_utils.single_op_call_string("s", 2)
    assert func[2] == test_utils.single_op_call_string("t", 0)
    assert func[3] == test_utils.measure_call_string("mz", 2, 0)
    assert func[4] == test_utils.measure_call_string("mz", 0, 1)
    assert func[5] == test_utils.measure_call_string("mz", 1, 2)
    assert func[6] == test_utils.array_start_record_output_string()
    assert func[7] == test_utils.result_record_output_string(2)
    assert func[8] == test_utils.result_record_output_string(1)
    assert func[9] == test_utils.result_record_output_string(0)
    assert func[10] == test_utils.array_end_record_output_string()
    assert func[11] == test_utils.return_string()
    assert len(func) == 12

def test_no_measure_with_no_registers():
    circuit = QuantumCircuit(1, 0)
    circuit.name = "test_no_measure_with_no_registers"
    circuit.h(0)
    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.return_string()
    assert len(func) == 2

def test_no_measure_with_register():
    circuit = QuantumCircuit(1, 1)
    circuit.name = "test_no_measure_with_register"
    circuit.h(0)
    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.array_start_record_output_string()
    assert func[2] == test_utils.result_record_output_string(0)
    assert func[3] == test_utils.array_end_record_output_string()
    assert func[4] == test_utils.return_string()
    assert len(func) == 5


def test_branching_on_bit_emits_correct_ir():
    qr = QuantumRegister(1, "qreg")
    cr = ClassicalRegister(1, "creg")
    circuit = QuantumCircuit(qr, cr, name="branching_on_bit_emits_correct_ir")
    circuit.x(0)
    circuit.measure(0, 0)
    circuit.x(0).c_if(cr[0], 1)

    ir = to_qir(circuit)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("x", 0)
    assert func[1] == test_utils.measure_call_string("mz", 0, 0)
    assert func[2] == test_utils.equal("equal", 0)
    assert func[3] == f"br i1 %equal, label %then, label %else"
    assert func[4] == ''
    assert func[5] == f"then:                                             ; preds = %entry"
    assert func[6] == test_utils.single_op_call_string("x", 0)
    assert func[7] == f"br label %continue"
    assert func[8] == ''
    assert func[9] == f"else:                                             ; preds = %entry"
    assert func[10] == f"br label %continue"
    assert func[11] == ''
    assert func[12] == f"continue:                                         ; preds = %else, %then"
    assert func[13] == test_utils.array_start_record_output_string()
    assert func[14] == test_utils.result_record_output_string(0)
    assert func[15] == test_utils.array_end_record_output_string()
    assert func[16] == test_utils.return_string()

    assert len(func) == 17


def test_branching_on_register_with_one_bit_emits_correct_ir():
    qr = QuantumRegister(1, "qreg")
    cr = ClassicalRegister(1, "creg")
    circuit = QuantumCircuit(qr, cr, name="branching_on_register_with_one_bit_emits_correct_ir")
    circuit.x(0)
    circuit.measure(0, 0)
    circuit.x(0).c_if(cr, 1)

    ir = to_qir(circuit)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("x", 0)
    assert func[1] == test_utils.measure_call_string("mz", 0, 0)
    assert func[2] == test_utils.equal("equal", 0)
    assert func[3] == f"br i1 %equal, label %then, label %else"
    assert func[4] == ''
    assert func[5] == f"then:                                             ; preds = %entry"
    assert func[6] == test_utils.single_op_call_string("x", 0)
    assert func[7] == f"br label %continue"
    assert func[8] == ''
    assert func[9] == f"else:                                             ; preds = %entry"
    assert func[10] == f"br label %continue"
    assert func[11] == ''
    assert func[12] == f"continue:                                         ; preds = %else, %then"
    assert func[13] == test_utils.array_start_record_output_string()
    assert func[14] == test_utils.result_record_output_string(0)
    assert func[15] == test_utils.array_end_record_output_string()
    assert func[16] == test_utils.return_string()

    assert len(func) == 17


def test_no_measure_without_registers():
    circuit = QuantumCircuit(1)
    circuit.name = "test_no_measure_no_registers"
    circuit.h(0)

    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 1, 0)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.return_string()
    assert len(func) == 2


def test_measurement_into_multiple_registers_is_mapped_correctly():
    cr0 = ClassicalRegister(2, "first")
    cr1 = ClassicalRegister(3, "second")
    circuit = QuantumCircuit(5)
    circuit.add_register(cr0)
    circuit.add_register(cr1)
    circuit.name = "measurement_into_multiple_registers"
    circuit.h(0)

    circuit.measure([0, 0], [0, 2])

    generated_qir = to_qir(circuit).splitlines()

    test_utils.check_attributes(generated_qir, 5, 5)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.measure_call_string("mz", 0, 0)
    assert func[2] == test_utils.measure_call_string("mz", 2, 0)
    assert func[3] == test_utils.array_start_record_output_string()
    assert func[4] == test_utils.result_record_output_string(1)
    assert func[5] == test_utils.result_record_output_string(0)
    assert func[6] == test_utils.array_end_record_output_string()
    assert func[7] == test_utils.array_start_record_output_string()
    assert func[8] == test_utils.result_record_output_string(4)
    assert func[9] == test_utils.result_record_output_string(3)
    assert func[10] == test_utils.result_record_output_string(2)
    assert func[11] == test_utils.array_end_record_output_string()
    assert func[12] == test_utils.return_string()
    assert len(func) == 13


def test_use_static_qubit_alloc_is_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = to_qir(circuit, use_static_qubit_alloc=False)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, -1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.allocate_qubit(0)
    assert func[1] == test_utils.single_op_call_string("h", 0, static_alloc=False)
    assert func[2] == test_utils.measure_call_string("mz", 0, 0, static_qubit_alloc=False)
    assert func[3] == test_utils.array_start_record_output_string()
    assert func[4] == test_utils.result_record_output_string(0)
    assert func[5] == test_utils.array_end_record_output_string()
    assert func[6] == test_utils.release_qubit(0)
    assert func[7] == test_utils.return_string()
    assert len(func) == 8


def test_use_static_result_alloc_is_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = to_qir(circuit, use_static_result_alloc=False)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, -1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.measure_call_string("m", 0, 0, static_result_alloc=False)
    assert func[2] == test_utils.array_start_record_output_string()
    assert func[3] == test_utils.result_record_output_string(0, static_alloc=False)
    assert func[4] == test_utils.array_end_record_output_string()
    assert func[5] == test_utils.return_string()
    assert len(func) == 6


def test_using_both_static_allocs_false_is_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = to_qir(circuit, use_static_qubit_alloc=False, use_static_result_alloc=False)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, -1, -1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.allocate_qubit(0)
    assert func[1] == test_utils.single_op_call_string("h", 0, static_alloc=False)
    assert func[2] == test_utils.measure_call_string("m", 0, 0, static_qubit_alloc=False, static_result_alloc=False)
    assert func[3] == test_utils.array_start_record_output_string()
    assert func[4] == test_utils.result_record_output_string(0, static_alloc=False)
    assert func[5] == test_utils.array_end_record_output_string()
    assert func[6] == test_utils.release_qubit(0)
    assert func[7] == test_utils.return_string()
    assert len(func) == 8


def test_using_both_static_allocs_true_is_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = to_qir(circuit, use_static_qubit_alloc=True, use_static_result_alloc=True)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.measure_call_string("mz", 0, 0)
    assert func[2] == test_utils.array_start_record_output_string()
    assert func[3] == test_utils.result_record_output_string(0)
    assert func[4] == test_utils.array_end_record_output_string()
    assert func[5] == test_utils.return_string()
    assert len(func) == 6


def test_record_output_when_true_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = to_qir(circuit, record_output=True)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.measure_call_string("mz", 0, 0)
    assert func[2] == test_utils.array_start_record_output_string()
    assert func[3] == test_utils.result_record_output_string(0)
    assert func[4] == test_utils.array_end_record_output_string()
    assert func[5] == test_utils.return_string()
    assert len(func) == 6


def test_record_output_when_false_mapped_correctly():
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    ir = to_qir(circuit, record_output=False)
    generated_qir = ir.splitlines()

    test_utils.check_attributes(generated_qir, 1, 1)
    func = test_utils.find_function(generated_qir)
    assert func[0] == test_utils.single_op_call_string("h", 0)
    assert func[1] == test_utils.measure_call_string("mz", 0, 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3
