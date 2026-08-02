class QBFTSimulator:
    def __init__(self, validators):
        self.validators = validators

    def run_consensus(self, block_proposal, leader):
        print(f"Starting Q-BFT Consensus with leader {leader.name}")
        signatures = []
        approvals = 0
        
        # In a real Q-BFT, validators would exchange messages secured by QKD
        # and signed by PQC. We simulate this by having validators "approve".
        for validator in self.validators:
            # Simulate QKD secure channel by validating the proposal
            if validator.validate_proposal(block_proposal):
                approvals += 1
                signatures.append({
                    "validator": validator.name,
                    "signature": validator.sign_approval(block_proposal)
                })
                
        # Q-BFT requires > 2/3 approvals (e.g. 3 out of 4)
        required_approvals = (2 * len(self.validators)) // 3 + 1
        
        if approvals >= required_approvals:
            return True, signatures
        else:
            return False, []
