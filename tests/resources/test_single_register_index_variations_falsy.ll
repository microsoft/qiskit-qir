; ModuleID = 'test_single_register_index_variations_falsy'
source_filename = "test_single_register_index_variations"

%Qubit = type opaque
%Result = type opaque

define void @test_single_register_index_variations() #0 {
entry:
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  %0 = call i1 @__quantum__qis__read_result__body(%Result* null)
  br i1 %0, label %then, label %else

then:                                             ; preds = %entry
  br label %continue

else:                                             ; preds = %entry
  call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Result* inttoptr (i64 1 to %Result*))
  br label %continue

continue:                                         ; preds = %else, %then
  ret void
}

declare void @__quantum__qis__mz__body(%Qubit*, %Result* writeonly) #1

declare i1 @__quantum__qis__read_result__body(%Result*)

attributes #0 = { "entry_point" "num_required_qubits"="2" "num_required_results"="2" "output_labeling_schema" "qir_profiles"="custom" }
attributes #1 = { "irreversible" }
