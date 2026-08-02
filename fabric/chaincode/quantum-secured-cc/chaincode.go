package main

import (
	"encoding/json"
	"fmt"
	"log"
	"strconv"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing a QuantumTransaction
type SmartContract struct {
	contractapi.Contract
}

// QuantumTransaction describes basic details of what makes up a simple quantum secured transaction
type QuantumTransaction struct {
	TransactionID           string `json:"transactionID"`
	TransactionType         string `json:"transactionType"`
	TransactionData         string `json:"transactionData"` // Stored as a JSON string
	PQCVerificationStatus   string `json:"pqcVerificationStatus"`
	BB84CommunicationStatus string `json:"bb84CommunicationStatus"`
	QRNGSelectedLeader      string `json:"qrngSelectedLeader"`
	QBFTConsensusResult     string `json:"qbftConsensusResult"`
	Timestamp               string `json:"timestamp"` // Could be float representation as string or ISO string
	PreviousHash            string `json:"previousHash"`
	CurrentHash             string `json:"currentHash"`
	BlockNumber             int    `json:"blockNumber"`
	TransactionStatus       string `json:"transactionStatus"`
}

// InitLedger adds a base set of transactions to the ledger
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	// Usually left empty or adds some genesis data
	return nil
}

// CreateTransaction issues a new transaction to the world state with given details.
func (s *SmartContract) CreateTransaction(ctx contractapi.TransactionContextInterface,
	txID string,
	txType string,
	txData string,
	pqcStatus string,
	bb84Status string,
	leader string,
	consensusResult string,
	timestamp string,
	prevHash string,
	currHash string,
	blockNumStr string,
	txStatus string) error {

	exists, err := s.TransactionExists(ctx, txID)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the transaction %s already exists", txID)
	}

	blockNum, err := strconv.Atoi(blockNumStr)
	if err != nil {
		return fmt.Errorf("invalid block number %s: %v", blockNumStr, err)
	}

	tx := QuantumTransaction{
		TransactionID:           txID,
		TransactionType:         txType,
		TransactionData:         txData,
		PQCVerificationStatus:   pqcStatus,
		BB84CommunicationStatus: bb84Status,
		QRNGSelectedLeader:      leader,
		QBFTConsensusResult:     consensusResult,
		Timestamp:               timestamp,
		PreviousHash:            prevHash,
		CurrentHash:             currHash,
		BlockNumber:             blockNum,
		TransactionStatus:       txStatus,
	}

	txJSON, err := json.Marshal(tx)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(txID, txJSON)
}

// GetTransaction returns the transaction stored in the world state with given id.
func (s *SmartContract) GetTransaction(ctx contractapi.TransactionContextInterface, id string) (*QuantumTransaction, error) {
	txJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if txJSON == nil {
		return nil, fmt.Errorf("the transaction %s does not exist", id)
	}

	var tx QuantumTransaction
	err = json.Unmarshal(txJSON, &tx)
	if err != nil {
		return nil, err
	}

	return &tx, nil
}

// TransactionExists returns true when asset with given ID exists in world state
func (s *SmartContract) TransactionExists(ctx contractapi.TransactionContextInterface, id string) (bool, error) {
	txJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return txJSON != nil, nil
}

// GetAllTransactions returns all transactions found in world state
func (s *SmartContract) GetAllTransactions(ctx contractapi.TransactionContextInterface) ([]*QuantumTransaction, error) {
	// range query with empty string for startKey and endKey does an
	// open-ended query of all assets in the chaincode namespace.
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var transactions []*QuantumTransaction
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var tx QuantumTransaction
		err = json.Unmarshal(queryResponse.Value, &tx)
		if err != nil {
			return nil, err
		}
		transactions = append(transactions, &tx)
	}

	return transactions, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		log.Panicf("Error creating quantum-secured-cc chaincode: %v", err)
	}

	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting quantum-secured-cc chaincode: %v", err)
	}
}
