##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##

from typing import List

def _find_line(qir: List[str], prefix : str, err: str):
    for line in qir:
        l = line.strip()
        if l.startswith(prefix):
            return l
    assert err

def find_function(qir: List[str]):
    result = []
    state = 0
    for line in qir:
        l = line.strip()
        if state == 0 and l == "define void @main() #0 {":
            state = 1
        elif state == 1 and l == "entry:":
            state = 2
        elif state == 2 and l == "}":
            return result
        elif state == 2:
            result.append(l)
    assert "No main function found"

def check_attributes(qir: List[str], expected: int):
    attr_string = 'attributes #0 = { "EntryPoint" "requiredQubits"="'
    attr_line = _find_line(qir, attr_string, "Missing entry point attribute")
    qubit_start = len(attr_string)
    j = attr_line.find('" }', qubit_start)
    if j < 0:
        assert "Badly formatted entry point attribute"
    try:
        n = int(attr_line[qubit_start:j])
    except ValueError:
        assert f"Badly formatted qubit count in entry point attribute: {attr_line[qubit_start:j]}"
    if n != expected:
        assert f"Incorrect qubit count: {expected} expected, {n} actual"

