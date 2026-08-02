import os
import random

class QRNGSimulator:
    """
    Simulates a Quantum Random Number Generator for entropy and leader selection.
    """
    @staticmethod
    def generate_entropy(bytes_length=32):
        # Simulate high entropy quantum randomness
        return os.urandom(bytes_length).hex()
        
    @staticmethod
    def select_leader(validators):
        """
        Uses simulated quantum randomness to fairly select a leader 
        from the list of validators for the Q-BFT consensus.
        """
        if not validators:
            return None
        # In a real QRNG, this would use quantum measurements.
        # Here we use SystemRandom which uses os.urandom (cryptographically secure).
        secure_random = random.SystemRandom()
        return secure_random.choice(validators)
