import time

class Transaction:
    def __init__(self, sender, receiver, amount, public_key, signature=None, timestamp=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp if timestamp else time.time()
        self.public_key = public_key
        self.signature = signature

    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "public_key": self.public_key
        }
        
    def to_json(self):
        d = self.to_dict()
        d["signature"] = self.signature
        return d
