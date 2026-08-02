import hashlib
import json
import socket
import subprocess
import time
import logging

# Simple fallback logger if no config exists
logging.basicConfig(level=logging.INFO)
fabric_logger = logging.getLogger("fabric")

class FabricConnectionError(Exception):
    """Raised when Hyperledger Fabric peer endpoint or gateway is unreachable."""
    pass

class FabricGatewayService:
    """
    Hyperledger Fabric Gateway & Service Layer:
    Direct production interface for the application to interact with
    the Hyperledger Fabric network (Gateway API, Chaincode, and CouchDB state database).
    Includes a fallback simulation adapter if Fabric is unreachable.
    """
    def __init__(self, peer_host="localhost", peer_port=7051, channel="mychannel", chaincode="quantum-secured-cc"):
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.channel = channel
        self.chaincode = chaincode
        self._fallback_chain = [] # Store local chain when fabric is offline

    def check_live_network(self) -> bool:
        """Check if live Hyperledger Fabric peer container endpoint is reachable and docker cli is running."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5)
            res = sock.connect_ex((self.peer_host, self.peer_port))
            sock.close()
            if res != 0:
                return False
                
            # Verify if cli container exists and is running
            docker_check = subprocess.run(
                ["docker", "ps", "--filter", "name=cli", "--format", "{{.Names}}"],
                capture_output=True, text=True, check=True
            )
            if "cli" not in docker_check.stdout:
                return False
                
            return True
        except Exception:
            return False

    def get_fabric_status(self) -> dict:
        """Return live status of Fabric Gateway Connection."""
        is_live = self.check_live_network()
        return {
            "connected": is_live,
            "mode": "LIVE_GATEWAY" if is_live else "SIMULATION_FALLBACK",
            "status": "Connected to Hyperledger Fabric Network" if is_live else "Fabric Offline - Using Local Simulation",
            "channel": self.channel,
            "chaincode": self.chaincode,
            "peer_endpoint": f"{self.peer_host}:{self.peer_port}"
        }

    def _build_invoke_script(self, args: list) -> str:
        """Build a bash script string for chaincode invoke. Routes through WSL to avoid
        Windows PowerShell JSON escaping that corrupts the -c argument."""
        ctor = json.dumps({"Args": args})
        # Use single-quotes in bash to pass JSON safely
        escaped = ctor.replace("'", "'\"'\"'")
        script = (
            "docker exec cli peer chaincode invoke "
            "-o orderer.example.com:7050 "
            "--ordererTLSHostnameOverride orderer.example.com "
            f"--channelID {self.channel} "
            f"--name {self.chaincode} "
            "--tls "
            "--cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/"
            "ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt "
            "--peerAddresses peer0.org1.example.com:7051 "
            "--tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/"
            "peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt "
            "--peerAddresses peer0.org2.example.com:9051 "
            "--tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/"
            "peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt "
            f"-c '{escaped}'"
        )
        return script

    def _build_query_script(self, args: list) -> str:
        """Build a bash script string for chaincode query. Routes through WSL."""
        ctor = json.dumps({"Args": args})
        escaped = ctor.replace("'", "'\"'\"'")
        script = (
            "docker exec cli peer chaincode query "
            f"-C {self.channel} "
            f"-n {self.chaincode} "
            f"-c '{escaped}'"
        )
        return script

    def _execute_chaincode_invoke(self, args: list) -> str:
        """Execute chaincode invoke via Fabric CLI container through WSL."""
        if not self.check_live_network():
            raise FabricConnectionError(f"Hyperledger Fabric network is unreachable at {self.peer_host}:{self.peer_port}. Please start the Fabric Docker network.")

        script = self._build_invoke_script(args)
        cmd = ["wsl", "-d", "Ubuntu-22.04", "--", "bash", "-c", script]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return res.stdout
        except subprocess.CalledProcessError as e:
            error_output = e.stderr or e.stdout or str(e)
            raise FabricConnectionError(f"Fabric Chaincode Invoke Failed: {error_output.strip()}")
        except Exception as e:
            raise FabricConnectionError(f"Fabric Gateway Execution Error: {str(e)}")

    def _execute_chaincode_query(self, args: list):
        """Execute chaincode query via Fabric CLI container through WSL."""
        if not self.check_live_network():
            raise FabricConnectionError(f"Hyperledger Fabric network is unreachable at {self.peer_host}:{self.peer_port}. Please start the Fabric Docker network.")

        script = self._build_query_script(args)
        cmd = ["wsl", "-d", "Ubuntu-22.04", "--", "bash", "-c", script]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = res.stdout.strip()
            if not output:
                return []
            return json.loads(output)
        except subprocess.CalledProcessError as e:
            error_output = e.stderr or e.stdout or str(e)
            fabric_logger.warning(f"Fabric Chaincode Query Failed: {error_output.strip()}")
            return []
        except json.JSONDecodeError:
            fabric_logger.warning(f"Fabric returned non-JSON output: {output}")
            return []
        except Exception as e:
            fabric_logger.warning(f"Fabric Gateway Query Error: {str(e)}")
            return []

    def create_transaction(self, tx_id, tx_type, tx_data, pqc_status, bb84_status, leader, consensus_result, timestamp, prev_hash, curr_hash, block_num, tx_status):
        """Creates and commits a new transaction to the Hyperledger Fabric ledger."""
        args = [
            "CreateTransaction",
            str(tx_id),
            str(tx_type),
            str(tx_data),
            str(pqc_status),
            str(bb84_status),
            str(leader),
            str(consensus_result),
            str(timestamp),
            str(prev_hash),
            str(curr_hash),
            str(block_num),
            str(tx_status)
        ]
        
        is_live = self.check_live_network()
        
        if is_live:
            self._execute_chaincode_invoke(args)
            return {
                "transactionID": tx_id,
                "transactionType": tx_type,
                "transactionData": tx_data,
                "pqcVerificationStatus": pqc_status,
                "bb84CommunicationStatus": bb84_status,
                "qrngSelectedLeader": leader,
                "qbftConsensusResult": consensus_result,
                "timestamp": timestamp,
                "previousHash": prev_hash,
                "currentHash": curr_hash,
                "blockNumber": block_num,
                "transactionStatus": tx_status,
                "liveFabricCommitted": True
            }
        else:
            # Fallback local chain
            block_dict = {
                "transactionID": tx_id,
                "transactionType": tx_type,
                "transactionData": tx_data,
                "pqcVerificationStatus": pqc_status,
                "bb84CommunicationStatus": bb84_status,
                "qrngSelectedLeader": leader,
                "qbftConsensusResult": consensus_result,
                "timestamp": timestamp,
                "previousHash": prev_hash,
                "currentHash": curr_hash,
                "blockNumber": block_num,
                "transactionStatus": tx_status,
                "liveFabricCommitted": False
            }
            self._fallback_chain.append(block_dict)
            return block_dict

    def get_all_transactions(self):
        """Query all transactions stored in Hyperledger Fabric World State (CouchDB)."""
        is_live = self.check_live_network()
        if is_live:
            return self._execute_chaincode_query(["GetAllTransactions"])
        else:
            return self._fallback_chain

    def get_chain(self):
        """Queries all Fabric transactions and builds the block visualization chain."""
        all_txs = self.get_all_transactions()
        if not isinstance(all_txs, list):
            return []

        chain = []
        # Sort transactions by block number
        sorted_txs = sorted(all_txs, key=lambda x: x.get("blockNumber", 0) if isinstance(x, dict) else 0)

        for tx in sorted_txs:
            if not isinstance(tx, dict):
                continue
            
            # Safely parse transactions, as it might be a JSON string from Fabric.
            # Use strict=False to tolerate PEM newline control chars in older records.
            try:
                raw_td = tx.get("transactionData", "[]")
                txs = json.loads(raw_td, strict=False) if raw_td else []
            except:
                txs = []
                
            # Safely parse timestamp
            ts_val = tx.get("timestamp", time.time())
            try:
                ts_float = float(ts_val)
            except ValueError:
                try:
                    ts_float = time.mktime(time.strptime(str(ts_val), "%Y-%m-%dT%H:%M:%SZ"))
                except:
                    ts_float = time.time()
                    
            chain.append({
                "index": tx.get("blockNumber", 0),
                "transactions": txs,
                "validator": tx.get("qrngSelectedLeader", ""),
                "hash": tx.get("currentHash", ""),
                "previous_hash": tx.get("previousHash", ""),
                "timestamp": ts_float,
                "fabric_tx_id": tx.get("transactionID", ""),
                "merkle_root": "" # Optional field if needed
            })

        return chain
