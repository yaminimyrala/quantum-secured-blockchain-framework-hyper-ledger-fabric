from flask import Flask, jsonify, request, render_template
from core.blockchain import Blockchain
from core.network import QuantumNetwork
from core.qbft import QBFTSimulator
from core.qrng import QRNGSimulator
from core.pqc import PQCSimulator
from core.qkd import QKDSimulator
import time

app = Flask(__name__)

# Initialize system
blockchain = Blockchain()
network = QuantumNetwork()
qbft = QBFTSimulator(network.validators)
simulated_users = {
    "Alice": PQCSimulator.generate_keypair(),
    "Bob": PQCSimulator.generate_keypair()
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({
        "Alice": simulated_users["Alice"]["public_key"],
        "Bob": simulated_users["Bob"]["public_key"]
    })

@app.route('/api/transaction', methods=['POST'])
def new_transaction():
    data = request.get_json()
    sender = data.get('sender')
    receiver = data.get('receiver')
    amount = data.get('amount')
    
    if sender not in simulated_users:
        return jsonify({"error": "Unknown sender"}), 400
        
    sender_keys = simulated_users[sender]
    
    # 1. PQC Signature
    tx_data = {
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "timestamp": time.time(),
        "public_key": sender_keys["public_key"]
    }
    signature = PQCSimulator.sign(tx_data, sender_keys["private_key"])
    
    # Add to mempool
    try:
        index = blockchain.add_transaction(sender, receiver, amount, sender_keys["public_key"], signature, tx_data["timestamp"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # 2. BB84 QKD Simulation (just for logs/dashboard)
    qkd_session = QKDSimulator.exchange_keys("User", "Validator-Alpha")
    
    return jsonify({
        "message": f"Transaction will be added to Block {index}",
        "signature": signature,
        "qkd_session": qkd_session
    }), 201

@app.route('/api/mine', methods=['GET'])
def mine():
    # 3. QRNG Leader Selection
    leader = QRNGSimulator.select_leader(network.validators)
    entropy = QRNGSimulator.generate_entropy()
    
    # 4. Q-BFT Consensus
    block_proposal = {
        "transactions": blockchain.pending_transactions,
        "previous_hash": blockchain.get_last_block().hash
    }
    success, signatures = qbft.run_consensus(block_proposal, leader)
    
    if success:
        # 5. Block Creation
        block = blockchain.create_block(signatures, leader.name)
        
        # Print to terminal
        print("\n" + "="*60)
        print(" NEW BLOCK CREATED AND ADDED TO QUANTUM BLOCKCHAIN ")
        print("="*60)
        import json
        print(json.dumps(block.to_dict(), indent=4))
        print("="*60 + "\n")

        return jsonify({
            "message": "New block mined and added to the Quantum Blockchain!",
            "leader": leader.name,
            "entropy": entropy,
            "block": block.to_dict()
        }), 200
    else:
        return jsonify({"message": "Consensus failed!"}), 500

@app.route('/api/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': [b.to_dict() for b in blockchain.chain],
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    return jsonify([v.name for v in network.validators]), 200

@app.route('/api/fabric/status', methods=['GET'])
def fabric_status():
    return jsonify(blockchain.fabric.get_fabric_status()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
