#!/bin/bash

export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../network

# Change to scripts directory
cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}1. Downloading Fabric binaries if not exist...${NC}"
if [ ! -d "../bin" ]; then
    cd ..
    curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh
    ./install-fabric.sh binary
    rm install-fabric.sh
    cd scripts
fi

cd ../network

echo -e "${GREEN}2. Generating crypto materials...${NC}"
rm -rf crypto-config
../bin/cryptogen generate --config=./crypto-config.yaml --output="crypto-config"

echo -e "${GREEN}3. Generating channel artifacts...${NC}"
rm -rf channel-artifacts
mkdir channel-artifacts

../bin/configtxgen -profile OneOrgOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block
../bin/configtxgen -profile OneOrgChannel -outputCreateChannelTx ./channel-artifacts/mychannel.tx -channelID mychannel

echo -e "${GREEN}4. Starting the network...${NC}"
docker compose up -d

echo -e "${GREEN}Waiting for containers to start...${NC}"
sleep 5

echo -e "${GREEN}5. Creating the channel...${NC}"
docker exec cli peer channel create -o orderer.example.com:7050 -c mychannel -f ./channel-artifacts/mychannel.tx --outputBlock ./channel-artifacts/mychannel.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt

echo -e "${GREEN}6. Joining peer to the channel...${NC}"
docker exec cli peer channel join -b ./channel-artifacts/mychannel.block

echo -e "${GREEN}Fabric network successfully bootstrapped!${NC}"
