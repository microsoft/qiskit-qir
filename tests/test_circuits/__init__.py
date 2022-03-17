##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from test_circuits.basic_circuits import ghz, teleport, unroll, teleport_with_subroutine
from test_circuits.control_flow_circuits import *
from test_circuits.random import *
from test_circuits.random import __all__ as random_fixtures

# All of the test fixtures
all_tests = [
    "ghz",
    "teleport",
    "unroll",
    "teleport_with_subroutine"
] + random_fixtures + cf_fixtures

# Tests we expect to fail
expected_to_fail_tests = cf_fixtures

# Tests we should run
__all__ = [test for test in all_tests if test not in expected_to_fail_tests]
