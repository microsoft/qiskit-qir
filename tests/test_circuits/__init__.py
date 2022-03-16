##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from test_circuits.basic_circuits import ghz, teleport, unroll
from test_circuits.control_flow_circuits import *
from test_circuits.random import *
from test_circuits.random import __all__ as random_fixtures

# All of the test fixtures
__all__ = [
    "ghz",
    "teleport",
    "unroll"
] + random_fixtures + cf_fixtures

# Tests we expect to fail
__fail__ = cf_fixtures
