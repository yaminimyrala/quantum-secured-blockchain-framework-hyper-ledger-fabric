import random

class QKDSimulator:
    """
    Simulates BB84 Quantum Key Distribution.
    """
    @staticmethod
    def generate_shared_key(length=256):
        # Simulate Alice generating random bits and bases
        alice_bits = [random.choice([0, 1]) for _ in range(length * 2)]
        alice_bases = [random.choice(['+', 'x']) for _ in range(length * 2)]
        
        # Simulate Bob choosing random bases
        bob_bases = [random.choice(['+', 'x']) for _ in range(length * 2)]
        
        # Simulate Bob measuring
        bob_bits = []
        for i in range(length * 2):
            if alice_bases[i] == bob_bases[i]:
                bob_bits.append(alice_bits[i])
            else:
                bob_bits.append(random.choice([0, 1]))
                
        # Sifting phase
        shared_key = []
        for i in range(length * 2):
            if alice_bases[i] == bob_bases[i]:
                shared_key.append(str(alice_bits[i]))
                if len(shared_key) == length:
                    break
                    
        return "".join(shared_key)
        
    @staticmethod
    def exchange_keys(node_a, node_b):
        # Simulate establishing a QKD secure channel between two nodes
        shared_key = QKDSimulator.generate_shared_key(256)
        return {
            "node_a": node_a,
            "node_b": node_b,
            "shared_key_hex": hex(int(shared_key, 2))[2:].zfill(64)
        }
