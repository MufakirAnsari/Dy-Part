from setuptools import setup, find_packages

setup(
    name="dypart_framework",
    version="0.1.0",
    description="Dy-Part: Dynamic Qubit Partitioning for Quantum Circuit Execution",
    author="Dy-Part Contributors",
    python_requires=">=3.10",
    packages=sorted(list(set(find_packages() + ["vqe_framework", "vqe_framework.utils"]))),
    install_requires=[
        "qiskit==1.1.0",
        "qiskit-aer==0.14.0",
        "qiskit-algorithms==0.3.0",
        "numpy>=1.24",
        "pandas>=2.0",
        "scipy>=1.10",
        "networkx>=3.0",
        "pymetis>=2023.1",
        "matplotlib>=3.7",
        "seaborn>=0.12",
    ],
)
