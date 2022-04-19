##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from enum import Flag, auto


class Capability(Flag):
    NONE = 0
    CONDITIONAL_BRANCHING_ON_RESULT = auto()
    QUBIT_USE_AFTER_MEASUREMENT = auto()
