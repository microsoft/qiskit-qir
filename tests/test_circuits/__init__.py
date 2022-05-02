##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##

from .random import *
from .basic_circuits import *

# Core test fixtures
core_tests = [
    "ghz",
    "teleport",
    "unroll",
    "teleport_with_subroutine",
    "bernstein_vazirani_with_barriers"
] + random_fixtures
