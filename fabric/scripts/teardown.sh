#!/bin/bash

cd "$(dirname "$0")/../network"

echo "Bringing down Docker containers..."
docker compose down -v

echo "Removing crypto materials and channel artifacts..."
rm -rf crypto-config channel-artifacts

echo "Removing old chaincode docker containers and images..."
docker rm -f $(docker ps -aq --filter name=dev-peer0.org1.example.com) 2>/dev/null || true
docker rmi -f $(docker images -q --filter reference=dev-peer0.org1.example.com*) 2>/dev/null || true

echo "Network teardown complete."
