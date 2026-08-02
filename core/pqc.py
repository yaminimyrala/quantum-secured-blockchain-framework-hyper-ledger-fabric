import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

class PQCSimulator:
    """
    Simulates CRYSTALS-Dilithium Post-Quantum Cryptography for digital signatures.
    Uses ECDSA as a stand-in for the simulation to provide verifiable signatures.
    """
    @staticmethod
    def generate_keypair():
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()
        
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return {"private_key": priv_pem, "public_key": pub_pem}

    @staticmethod
    def sign(message_dict, private_key_pem):
        message_str = json.dumps(message_dict, sort_keys=True)
        
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
        )
        
        signature = private_key.sign(
            message_str.encode('utf-8'),
            ec.ECDSA(hashes.SHA3_256())
        )
        return signature.hex()

    @staticmethod
    def verify(message_dict, signature_hex, public_key_pem):
        message_str = json.dumps(message_dict, sort_keys=True)
        
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )
            
            public_key.verify(
                bytes.fromhex(signature_hex),
                message_str.encode('utf-8'),
                ec.ECDSA(hashes.SHA3_256())
            )
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False
