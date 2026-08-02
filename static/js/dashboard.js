document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const txForm = document.getElementById('tx-form');
    const txStatus = document.getElementById('tx-status');
    const qkdLog = document.getElementById('qkd-log');
    const mineBtn = document.getElementById('mine-btn');
    const mineStatus = document.getElementById('mine-status');
    const validatorsGrid = document.getElementById('validators-grid');
    const blockchainExplorer = document.getElementById('blockchain-explorer');
    const entropyVal = document.getElementById('entropy-val');
    const networkState = document.getElementById('network-state');
    
    // Fabric Elements
    const fabricStatus = document.getElementById('fabric-status');
    const fabricChannel = document.getElementById('fabric-channel');
    const fabricChaincode = document.getElementById('fabric-chaincode');
    const fabricLatestTx = document.getElementById('fabric-latest-tx');

    let currentChainLength = 0;
    let transactionData = null;
    let mineData = null;

    if (mineBtn) mineBtn.style.display = 'none'; // Not needed anymore

    // Steps
    const steps = [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3'),
        document.getElementById('step-4'),
        document.getElementById('step-5'),
        document.getElementById('step-6'),
        document.getElementById('step-7')
    ];
    
    const execBtns = [
        document.getElementById('exec-btn-1'),
        document.getElementById('exec-btn-2'),
        document.getElementById('exec-btn-3'),
        document.getElementById('exec-btn-4'),
        document.getElementById('exec-btn-5'),
        document.getElementById('exec-btn-6'),
        document.getElementById('exec-btn-7')
    ];

    function activateStep(index) {
        steps.forEach((step, i) => {
            if (i <= index && step) {
                step.classList.add('active');
            } else if (step) {
                step.classList.remove('active');
            }
        });
    }

    function resetSteps() {
        steps.forEach(step => {
            if (step) step.classList.remove('active');
        });
        execBtns.forEach((btn, i) => {
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = 'Execute';
            }
        });
        transactionData = null;
        mineData = null;
    }
    
    function enableNextButton(index) {
        if (index < execBtns.length && execBtns[index]) {
            execBtns[index].disabled = false;
        }
    }

    // Load initial data
    fetchNodes();
    fetchChain(true);
    fetchFabricStatus();

    async function fetchFabricStatus() {
        try {
            const res = await fetch('/api/fabric/status');
            const data = await res.json();
            
            if (data.connected) {
                fabricStatus.textContent = 'ONLINE';
                fabricStatus.className = 'value success';
                fabricChannel.textContent = data.channel || 'N/A';
                fabricChaincode.textContent = data.chaincode || 'N/A';
            } else {
                fabricStatus.textContent = 'OFFLINE (Simulated)';
                fabricStatus.className = 'value warning';
            }
        } catch (e) {
            fabricStatus.textContent = 'ERROR';
            fabricStatus.className = 'value danger';
        }
    }

    async function fetchNodes() {
        try {
            const res = await fetch('/api/nodes');
            const nodes = await res.json();
            
            validatorsGrid.innerHTML = '';
            nodes.forEach(node => {
                const card = document.createElement('div');
                card.className = 'validator-card';
                card.id = `val-${node}`;
                card.innerHTML = `
                    <div class="name">${node}</div>
                    <div class="status">Waiting...</div>
                `;
                validatorsGrid.appendChild(card);
            });
        } catch (e) {
            console.error(e);
        }
    }

    async function fetchChain(initialLoad = false) {
        try {
            const res = await fetch('/api/chain');
            const data = await res.json();
            
            blockchainExplorer.innerHTML = '';
            data.chain.forEach(block => {
                const blockEl = document.createElement('div');
                blockEl.className = 'block';
                // Add animation class if it's a new block being added (not on initial load)
                if (!initialLoad && block.index >= currentChainLength) {
                    blockEl.classList.add('new-block');
                }
                
                let txHtml = '';
                if(block.index === 0) {
                    txHtml = `<p><strong>Genesis Block</strong></p>`;
                } else {
                    txHtml = `<p><strong>Transactions:</strong> ${block.transactions.length}</p>`;
                    // Add details for transaction history
                    block.transactions.forEach(tx => {
                        txHtml += `<div class="tx-history-item" style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px; padding-left:10px; border-left:2px solid var(--accent);">
                            ${tx.sender} ➔ ${tx.receiver} (${tx.amount} Q-Tokens)
                        </div>`;
                    });
                }

                blockEl.innerHTML = `
                    <h3>Block #${block.index}</h3>
                    ${txHtml}
                    <p><strong>Timestamp:</strong> ${new Date(block.timestamp * 1000).toLocaleString()}</p>
                    <p class="hash"><strong>Hash:</strong><br>${block.hash.substring(0, 32)}...</p>
                    <p class="hash"><strong>Prev Hash:</strong><br>${block.previous_hash.substring(0, 32)}...</p>
                    <p class="hash"><strong>Validator:</strong> ${block.validator || 'N/A'}</p>
                    <p class="hash"><strong>Merkle Root:</strong><br>${block.merkle_root ? block.merkle_root.substring(0, 32) + '...' : 'N/A'}</p>
                    <p class="hash"><strong>Q-BFT Sigs:</strong> ${block.qbft_signatures ? block.qbft_signatures.length : 0}</p>
                    <div style="margin-top: 10px; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 4px; border-left: 3px solid #1a8bff;">
                        <p class="hash" style="margin:0;"><strong>Fabric TX ID:</strong><br>${block.fabric_tx_id || 'N/A'}</p>
                    </div>
                `;
                blockchainExplorer.appendChild(blockEl);
            });
            
            // Scroll to the end of the explorer to see the newest block
            blockchainExplorer.scrollTo({
                left: blockchainExplorer.scrollWidth,
                behavior: 'smooth'
            });
            
            currentChainLength = data.chain.length;
            
        } catch (e) {
            console.error(e);
        }
    }

    // Initiate Secure Transfer form submit
    txForm.addEventListener('submit', (e) => {
        e.preventDefault();
        resetSteps();
        
        txStatus.innerHTML = '<span style="color: var(--warning)">Transaction staged. Ready to execute Step 1.</span>';
        mineStatus.innerHTML = '';
        txStatus.className = 'status-box';
        networkState.textContent = 'STAGED';
        networkState.className = 'value warning';
        
        if (execBtns[0]) execBtns[0].disabled = false;
    });

    window.executeStep = async function(stepNum) {
        const btnIndex = stepNum - 1;
        if (!execBtns[btnIndex]) return;
        
        execBtns[btnIndex].disabled = true;
        execBtns[btnIndex].innerHTML = 'Running...';
        
        try {
            if (stepNum === 1) {
                // Phase 1: User Transaction
                activateStep(0);
                txStatus.innerHTML = '<span style="color: var(--success)">Transaction parameters locked.</span>';
                networkState.textContent = 'LOCKED';
                
                execBtns[btnIndex].innerHTML = 'Done ✓';
                enableNextButton(stepNum);
                
            } else if (stepNum === 2) {
                // Phase 2: PQC Signature
                const sender = document.getElementById('sender').value;
                const receiver = document.getElementById('receiver').value;
                const amount = document.getElementById('amount').value;

                txStatus.innerHTML = '<span style="color: var(--warning)">Generating PQC Signature...</span>';

                const res = await fetch('/api/transaction', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sender, receiver, amount: parseFloat(amount) })
                });
                const data = await res.json();
                
                if (res.ok) {
                    transactionData = data;
                    activateStep(1);
                    txStatus.innerHTML = `<span style="color: var(--success)">Success: PQC Signature Generated!</span><br><br><span style="font-size: 0.8em; word-break: break-all;">Signature: ${data.signature.substring(0, 64)}...</span>`;
                    execBtns[btnIndex].innerHTML = 'Done ✓';
                    enableNextButton(stepNum);
                } else {
                    txStatus.innerHTML = `<span style="color: var(--danger)">Error: ${data.error}</span>`;
                    execBtns[btnIndex].innerHTML = 'Failed';
                    execBtns[btnIndex].disabled = false;
                }
                
            } else if (stepNum === 3) {
                // Phase 3: BB84 QKD
                activateStep(2);
                qkdLog.innerHTML = `
> Establishing Quantum Channel...
> Node A: ${transactionData.qkd_session.node_a}
> Node B: ${transactionData.qkd_session.node_b}
> Sifting Phase Complete...
> Shared Key (Hex):
${transactionData.qkd_session.shared_key_hex}
> Key established securely.
                `;
                networkState.textContent = 'QKD COMPLETE';
                networkState.className = 'value success';
                
                execBtns[btnIndex].innerHTML = 'Done ✓';
                enableNextButton(stepNum);
                
            } else if (stepNum === 4) {
                // Phase 4: QRNG Leader Selection
                mineStatus.innerHTML = '<span style="color: var(--warning)">Requesting QRNG entropy...</span>';
                const res = await fetch('/api/mine');
                const data = await res.json();

                if (res.ok) {
                    mineData = data;
                    activateStep(3);
                    entropyVal.textContent = data.entropy.substring(0, 16) + '...';
                    
                    document.querySelectorAll('.validator-card').forEach(c => {
                        c.classList.remove('active');
                        c.querySelector('.status').textContent = 'Follower';
                    });
                    const leaderCard = document.getElementById(`val-${data.leader}`);
                    if (leaderCard) {
                        leaderCard.classList.add('active');
                        leaderCard.querySelector('.status').innerHTML = '<span style="color: var(--accent)">Leader</span>';
                    }
                    mineStatus.innerHTML = `<span style="color: var(--success)">QRNG Leader selected: ${data.leader}</span>`;
                    
                    execBtns[btnIndex].innerHTML = 'Done ✓';
                    enableNextButton(stepNum);
                } else {
                    mineStatus.innerHTML = `<span style="color: var(--danger)">Error: ${data.message}</span>`;
                    execBtns[btnIndex].innerHTML = 'Failed';
                    execBtns[btnIndex].disabled = false;
                }
                
            } else if (stepNum === 5) {
                // Phase 5: Q-BFT Consensus
                activateStep(4);
                mineStatus.innerHTML = `<span style="color: var(--success)">Consensus Reached! Approvals secured.</span>`;
                networkState.textContent = 'CONSENSUS OK';
                networkState.className = 'value success';
                
                execBtns[btnIndex].innerHTML = 'Done ✓';
                enableNextButton(stepNum);
                
            } else if (stepNum === 6) {
                // Phase 6: Commit to Fabric
                activateStep(5);
                if (mineData.block && mineData.block.fabric_tx_id) {
                    fabricLatestTx.textContent = mineData.block.fabric_tx_id;
                }
                mineStatus.innerHTML = `<span style="color: var(--success)">Block Finalized & Committed to Fabric.</span>`;
                
                fetchChain(false);
                
                execBtns[btnIndex].innerHTML = 'Done ✓';
                enableNextButton(stepNum);
                
            } else if (stepNum === 7) {
                // Phase 7: Verify Transaction
                activateStep(6);
                
                const res = await fetch('/api/chain');
                const chainData = await res.json();
                
                if (res.ok && chainData.chain.length > 0) {
                    const lastBlock = chainData.chain[chainData.chain.length - 1];
                    mineStatus.innerHTML = `<span style="color: var(--success)">Verification Passed! Block #${lastBlock.index} integrity confirmed. Fabric TX: ${lastBlock.fabric_tx_id || 'N/A'}</span>`;
                } else {
                    mineStatus.innerHTML = `<span style="color: var(--danger)">Verification Failed!</span>`;
                }
                
                networkState.textContent = 'VERIFIED';
                networkState.className = 'value success';
                
                execBtns[btnIndex].innerHTML = 'Done ✓';
            }
        } catch (e) {
            console.error(e);
            execBtns[btnIndex].innerHTML = 'Error';
            execBtns[btnIndex].disabled = false;
        }
    };
});
