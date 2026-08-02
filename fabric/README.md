# Hyperledger Fabric Local Network for Quantum Blockchain

This folder contains a complete local Hyperledger Fabric network configuration specifically designed to run seamlessly with the existing Quantum Blockchain Flask application.

**The existing python code (`app.py`, `core/fabric_service.py`, etc.) requires absolutely no changes to interact with this network.**

## Prerequisites
1. **Docker & Docker Compose** (Make sure Docker Desktop is running)
2. **Linux Environment**: The scripts are written for Linux/WSL2/Git Bash.

## Usage Guide

### 1. Start the Network
Open your terminal (WSL2, Git Bash, or Linux terminal), navigate to this `fabric/scripts` folder, and run:

```bash
cd fabric/scripts
chmod +x *.sh
./bootstrap.sh
```

**What this does:**
- Downloads Hyperledger Fabric binaries to `fabric/bin` (if they don't exist).
- Generates crypto materials and channel configurations.
- Starts the Fabric containers (Orderer, Peer, CouchDB, CLI).
- Creates the `mychannel` channel and joins the peer to it.

### 2. Deploy the Chaincode
Once the network is running successfully, deploy the `quantum-secured-cc` chaincode:

```bash
./deploy_chaincode.sh
```

**What this does:**
- Packages the Go chaincode (`chaincode.go`).
- Installs it on the peer.
- Approves and commits the chaincode definition on `mychannel`.
- Invokes the `InitLedger` function.

### 3. Run the Flask App
Leave the Fabric containers running in the background. Open a new terminal for your Python application:

```bash
cd ../../ # Back to the root project folder
python app.py
```
Check the Fabric integration status at `http://localhost:5000/api/fabric/status`. It should now report `"connected": true` and `"mode": "LIVE_GATEWAY"`.

Now when you trigger `/api/mine`, blocks are committed to the real Hyperledger Fabric ledger via CouchDB!

### 4. Teardown (Clean up)
When you are done testing, cleanly stop the network and remove generated files:

```bash
./teardown.sh
```
