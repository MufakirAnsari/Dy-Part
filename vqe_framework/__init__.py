# vqe_framework/__init__.py
"""Dy-Part: Dynamic Qubit Partitioning for Quantum Circuit Execution."""

try:
    import qiskit.circuit.library

    # Compatibility shim: qiskit-algorithms >= 0.4 requires evolved_operator_ansatz
    # which was introduced in Qiskit 1.3. For Qiskit < 1.3, alias to EvolvedOperatorAnsatz.
    if not hasattr(qiskit.circuit.library, "evolved_operator_ansatz"):
        if hasattr(qiskit.circuit.library, "EvolvedOperatorAnsatz"):
            setattr(qiskit.circuit.library, "evolved_operator_ansatz", qiskit.circuit.library.EvolvedOperatorAnsatz)
except ImportError:
    pass
