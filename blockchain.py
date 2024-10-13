import json
import hashlib
import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.mempool = []
        self.difficulty = 4
        self.reward = 50
        self.block_mined_count = 0
        
        self.load_chain()
        if len(self.chain) == 0:
            self.create_block(previous_hash='1', nonce=0)
        
    def save_chain(self):
        with open('blockchain.json', 'w') as f:
            json.dump(self.chain, f)
    
    def load_chain(self):
        try:
            with open('blockchain.json', 'r') as f:
                self.chain = json.load(f)
        except FileNotFoundError:
            self.chain = []

    def create_block(self, nonce, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'previous_hash': previous_hash
        }
        block['hash'] = self.hash(block)
        self.current_transactions = []
        self.chain.append(block)
        return block
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def proof_of_work(self, previous_nonce):
        nonce = 0
        while not self.valid_proof(previous_nonce, nonce):
            nonce += 1
        return nonce

    def valid_proof(self, previous_nonce, nonce):
        guess = f'{previous_nonce}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == '0' * self.difficulty

    def add_transaction(self, wallet_id, amount):
        transaction = {'wallet_id': wallet_id, 'amount': amount}
        self.mempool.append(transaction)

    def mine_block(self, wallet_id):
        if not self.mempool:
            print("ไม่สามารถขุดบล็อกได้: ไม่มีธุรกรรมใน mempool")
            return None

        last_block = self.chain[-1]
        previous_nonce = last_block['nonce']
        nonce = self.proof_of_work(previous_nonce)
        previous_hash = self.hash(last_block)
        block = self.create_block(nonce, previous_hash)

        block['transactions'] = self.mempool.copy()
        self.mempool.clear()

        # เพิ่ม index ให้กับบล็อกใหม่
        block['index'] = len(self.chain) + 1

        # ให้รางวัลแก่ผู้ขุด
        try:
            transaction_id = self.add_transaction(wallet_id, self.reward)
            update_wallet_balance(wallet_id, self.reward)
        except Exception as e:
            print("Error updating wallet:", e)
            return None

        # บันทึกบล็อกลงในฐานข้อมูล
        print("Attempting to save block:", block)
        if not save_block_to_db(block):
            print("เกิดข้อผิดพลาดในการบันทึกบล็อกลงในฐานข้อมูล")
            return None

        self.block_mined_count += 1

        if self.block_mined_count % 100 == 0:
            self.difficulty += 1
            self.reward = max(1, self.reward // 2)

        self.save_chain()

        if 'hash' in block:
            print(f"ขุดบล็อกใหม่สำเร็จ: {block['index']} | Hash: {block['hash']} | ผู้ขุด: {wallet_id} | รางวัล: {self.reward} Coins")
        else:
            print(f"ขุดบล็อกใหม่สำเร็จ: {block['index']} | Hash ไม่ถูกต้อง | ผู้ขุด: {wallet_id} | รางวัล: {self.reward} Coins")

        return block
