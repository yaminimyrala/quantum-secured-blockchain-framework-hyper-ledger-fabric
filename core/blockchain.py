import hashlib
import json
import time
from typing import List
from .transaction import Transaction
from .pqc import PQCSimulator
from .fabric_service import FabricGatewayService

class Block:
    def __init__(self, index, transactions, previous_hash, validator=None):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.validator = validator
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()
        self.qbft_signatures = [] # Store validator signatures for consensus
        self.fabric_tx_id = "" # Will be populated upon commit

    def calculate_merkle_root(self):
        if not self.transactions:
            return ""
        
        tx_hashes = [hashlib.sha256(json.dumps(tx).encode()).hexdigest() for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            new_level = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i+1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            tx_hashes = new_level
            
        return tx_hashes[0]

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        
        # Use quantum-resistant hash in a real scenario (e.g. SHA3)
        return hashlib.sha3_256(block_string).hexdigest()
        
    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "merkle_root": self.merkle_root,
            "hash": self.hash,
            "qbft_signatures": self.qbft_signatures,
            "fabric_tx_id": self.fabric_tx_id
        }

class Blockchain:
    def __init__(self):
        self.fabric = FabricGatewayService()
        self.pending_transactions = []
        self._local_chain = []  # In-memory fallback for when Fabric chain is empty
        self.create_genesis_block()

    @property
    def chain(self) -> List[Block]:
        fabric_chain = self.fabric.get_chain()
        if fabric_chain:
            blocks = []
            for f_block in fabric_chain:
                b = Block(
                    index=f_block["index"],
                    transactions=f_block["transactions"],
                    previous_hash=f_block["previous_hash"],
                    validator=f_block["validator"]
                )
                b.hash = f_block["hash"]
                b.timestamp = f_block["timestamp"]
                # Restore Fabric-specific fields that Block.__init__ doesn't set
                b.fabric_tx_id = f_block.get("fabric_tx_id", "")
                b.merkle_root = f_block.get("merkle_root", b.merkle_root)
                blocks.append(b)
            # Keep local chain in sync so fallback stays current
            self._local_chain = blocks
            return blocks
        # Fabric chain is empty or unreachable — use local in-memory chain
        return self._local_chain

    def create_genesis_block(self):
        # Only create genesis if both Fabric and local chain are empty
        if not self.fabric.get_chain() and not self._local_chain:
            genesis_block = Block(0, [], "0", "System")
            self._local_chain.append(genesis_block)  # Add to local fallback immediately
            tx_id = "GENESIS"
            tx_data = json.dumps([])
            self.fabric.create_transaction(
                tx_id=tx_id,
                tx_type="GENESIS",
                tx_data=tx_data,
                pqc_status="N/A",
                bb84_status="N/A",
                leader="System",
                consensus_result="N/A",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(genesis_block.timestamp)),
                prev_hash="0",
                curr_hash=genesis_block.hash,
                block_num=0,
                tx_status="COMMITTED"
            )

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, sender, receiver, amount, public_key, signature, timestamp=None):
        tx = Transaction(sender, receiver, amount, public_key, signature, timestamp)
        
        # Verify transaction signature using PQC Simulator
        if not PQCSimulator.verify(tx.to_dict(), signature, public_key):
            raise ValueError("Invalid PQC Signature!")
            
        self.pending_transactions.append(tx.to_json())
        return self.get_last_block().index + 1

    def create_block(self, qbft_signatures, validator_name):
        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.pending_transactions,
            previous_hash=last_block.hash,
            validator=validator_name
        )
        new_block.qbft_signatures = qbft_signatures
        
        # Add to local chain immediately so get_last_block() works even before Fabric commit
        self._local_chain.append(new_block)
        
        # Commit to Fabric Ledger
        # Strip public_key from transactions before storing: PEM keys contain literal
        # newline characters which break JSON round-trips through Fabric's world state.
        safe_txs = [
            {k: v for k, v in tx.items() if k != "public_key"}
            if isinstance(tx, dict) else tx
            for tx in self.pending_transactions
        ]
        tx_data = json.dumps(safe_txs)
        tx_id = f"TX_FABRIC_{new_block.index:04d}_{new_block.hash[:8]}"
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(new_block.timestamp))
        
        self.fabric.create_transaction(
            tx_id=tx_id,
            tx_type="QUANTUM_DATA_PAYLOAD",
            tx_data=tx_data,
            pqc_status="VERIFIED_DILITHIUM",
            bb84_status="ESTABLISHED",
            leader=validator_name,
            consensus_result="Q-BFT_APPROVED",
            timestamp=timestamp_str,
            prev_hash=new_block.previous_hash,
            curr_hash=new_block.hash,
            block_num=new_block.index,
            tx_status="COMMITTED"
        )
        new_block.fabric_tx_id = tx_id
        
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self):
        current_chain = self.chain
        for i in range(1, len(current_chain)):
            current_block = current_chain[i]
            previous_block = current_chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True
