# vqe_framework/qpu_interface.py

from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error, ReadoutError
from qiskit_aer.primitives import Estimator as AerEstimator

class NoisyQPU:
    """
    A class to simulate a Noisy Quantum Processing Unit (QPU).
    
    This class wraps the Qiskit AerSimulator and applies a configurable
    noise model to mimic the behavior of real NISQ hardware.
    """
    def __init__(self, n_qubits, gate_error_rate=1e-3, readout_error_rate=1e-2):
        """
        Initializes the noisy QPU simulator.
        
        Args:
            n_qubits (int): The number of qubits for the noise model.
            gate_error_rate (float): The probability of a depolarizing error on each 2-qubit gate.
            readout_error_rate (float): The probability of a bit-flip error during measurement.
        """
        self.n_qubits = n_qubits
        self.gate_error_rate = gate_error_rate
        self.readout_error_rate = readout_error_rate
        
        self.noise_model = self._create_noise_model()
        self.backend = AerSimulator(noise_model=self.noise_model)

    def _create_noise_model(self):
        """
        Creates a simple Qiskit NoiseModel with depolarizing and readout errors.
        """
        # 1. Depolarizing error on two-qubit gates (e.g., CNOT, CZ)
        # This error model applies a random Pauli gate (X, Y, or Z) after a gate
        # with a certain probability.
        two_qubit_error = depolarizing_error(self.gate_error_rate, 2)
        
        # 2. Readout error on measurements
        # This simulates errors in correctly reading the final state of the qubit.
        readout_errors = []
        for i in range(self.n_qubits):
            # P(1|0) is the probability of measuring 1 when the state was 0
            # P(0|1) is the probability of measuring 0 when the state was 1
            error = ReadoutError([[1 - self.readout_error_rate, self.readout_error_rate],
                                  [self.readout_error_rate, 1 - self.readout_error_rate]])
            readout_errors.append((i, error))

        noise_model = NoiseModel()
        
        # Apply the depolarizing error to all 2-qubit gates
        noise_model.add_all_qubit_quantum_error(two_qubit_error, ['cx', 'cz'])
        
        # Apply the readout error
        for qubit_index, error_object in readout_errors:
             noise_model.add_readout_error(error_object, [qubit_index])
        
        print(f"Noise Model Created: Gate Error Rate = {self.gate_error_rate}, Readout Error Rate = {self.readout_error_rate}")
        return noise_model

    # NEW, UPGRADED VERSION
    def get_estimator(self, shots=None): # Add a shots parameter, default to None
        """
        Returns a Qiskit AerEstimator configured with this QPU's noise model.
        This is used by VQE to calculate expectation values.
        
        Args:
            shots (int, optional): The number of shots to use for expectation value
                                   estimation. If None, Qiskit's default is used.
        """
        from qiskit_aer.primitives import Estimator as AerEstimator
        
        # Build the options dictionary
        estimator_options = {
            "backend_options": {"noise_model": self.noise_model}
        }
        # Only add the shots option if it's provided by the caller
        if shots is not None:
            estimator_options["run_options"] = {"shots": shots}
            
        return AerEstimator(**estimator_options)



    def get_sampler(self):
        """
        Returns a Qiskit Sampler configured with this QPU's noise model.
        This is used for sampling the final circuit to get the solution bitstring.
        """
        from qiskit.primitives import Sampler
        # Note: The base Sampler primitive does not directly accept a noise model.
        # We use the AerSimulator as a backend for a generic Sampler.
        # This is a bit of a workaround for the Primitives API.
        # A more direct way is to build a noisy backend and use it for sampling,
        # but the primitives are the modern approach. Let's build a noisy backend
        # for the sampler.
        noisy_backend = AerSimulator(noise_model=self.noise_model)
        
        # The Sampler implementation will use this backend. This part is a bit
        # tricky with the new Primitives. Let's do it the robust way.
        # We'll stick to running the circuit directly on the backend for sampling.
        return noisy_backend