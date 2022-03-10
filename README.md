# qiskit-qir

Qiskit to QIR translator.

## Example

```python
from qiskit import QuantumCircuit
from qiskit_qir import to_qir

circuit = QuantumCircuit(3, 3, name="my-circuit")
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure([0,1,2], [0, 1, 2])

qir = to_qir(circuit)
```

## Install from source

To install the package from source, clone the repo onto your machine, browse to `qdk-python/qiskit-qir` and run

```bash
pip install -e .
```

To install with all test requirements, run

```bash
pip install -e .[test]
```

## Running tests

To run the tests in your local environment, run

```bash
pytest
```

To run tests on all supported Python versions, install `tox` using `pip install tox` and run

```bash
tox
```
