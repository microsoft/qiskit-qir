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

## Installation

Install the `pyqir-generator` dependency first for your platform.

```bash
# For Darwin:
pip install https://github.com/qir-alliance/pyqir/releases/download/v0.2.0a1/pyqir_generator-0.2.0a1-cp36-abi3-macosx_10_7_x86_64.whl

# For Windows:
pip install https://github.com/qir-alliance/pyqir/releases/download/v0.2.0a1/pyqir_generator-0.2.0a1-cp36-abi3-win_amd64.whl

# For Linux:
pip install https://github.com/qir-alliance/pyqir/releases/download/v0.2.0a1/pyqir_generator-0.2.0a1-cp36-abi3-linux_x86_64.whl
```

Then, install `qiskit-qir` with `pip`:

```bash
pip install qiskit-qir
```

## Development

### Install from source

To install the package from source, clone the repo onto your machine, browse to `qdk-python/qiskit-qir` and run

```bash
pip install -e .
```

### Tests

First, install the development dependencies using

```bash
pip install -r requirements_dev.txt
```

To run the tests in your local environment, run

```bash
make test
```

To run the tests in virtual environments on supported Python versions, run

```bash
make test-all
```

### Docs

To build the docs using Sphinx, run

```bash
make docs
```
