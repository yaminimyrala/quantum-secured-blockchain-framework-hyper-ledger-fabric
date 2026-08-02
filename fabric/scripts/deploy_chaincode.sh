#!/bin/bash

# Change to scripts directory
cd "$(dirname "$0")"

GREEN='\033[0;32m'
NC='\033[0m'

CC_NAME="quantum-secured-cc"
CC_SRC_PATH="/opt/gopath/src/github.com/chaincode/quantum-secured-cc"
CC_VERSION="1.0"
CC_SEQUENCE="1"

echo -e "${GREEN}1. Vendoring Go dependencies...${NC}"
cd ../chaincode/quantum-secured-cc
go mod vendor
cd ../../scripts

echo -e "${GREEN}2. Packaging chaincode...${NC}"
docker exec cli peer lifecycle chaincode package ${CC_NAME}.tar.gz --path ${CC_SRC_PATH} --lang golang --label ${CC_NAME}_${CC_VERSION}

echo -e "${GREEN}3. Installing chaincode...${NC}"
docker exec cli peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo -e "${GREEN}4. Querying installed chaincode to get Package ID...${NC}"
docker exec cli peer lifecycle chaincode queryinstalled > log.txt
PACKAGE_ID=$(sed -n "/${CC_NAME}_${CC_VERSION}/{s/^Package ID: //; s/, Label:.*$//; p;}" log.txt)
echo "Package ID: ${PACKAGE_ID}"
rm log.txt

echo -e "${GREEN}5. Approving for Org1...${NC}"
docker exec cli peer lifecycle chaincode approveformyorg -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --channelID mychannel --name ${CC_NAME} --version ${CC_VERSION} --package-id ${PACKAGE_ID} --sequence ${CC_SEQUENCE} --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt

echo -e "${GREEN}6. Checking commit readiness...${NC}"
docker exec cli peer lifecycle chaincode checkcommitreadiness --channelID mychannel --name ${CC_NAME} --version ${CC_VERSION} --sequence ${CC_SEQUENCE} --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt --output json

echo -e "${GREEN}7. Committing the chaincode definition...${NC}"
docker exec cli peer lifecycle chaincode commit -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --channelID mychannel --name ${CC_NAME} --version ${CC_VERSION} --sequence ${CC_SEQUENCE} --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo -e "${GREEN}8. Initializing the chaincode (InitLedger)...${NC}"
sleep 3
docker exec cli peer chaincode invoke -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --channelID mychannel --name ${CC_NAME} --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt -c '{"function":"InitLedger","Args":[]}'

echo -e "${GREEN}Chaincode deployed successfully! You can now run the Flask app.${NC}"
