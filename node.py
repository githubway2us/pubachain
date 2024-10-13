from flask import Flask, request, jsonify, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import hashlib
import time
import sqlite3
from flask_session import Session
import uuid
from functools import wraps
from dotenv import load_dotenv  # นำเข้า load_dotenv จาก dotenv
import os  # นำเข้าโมดูล os

load_dotenv()  # โหลดตัวแปรจากไฟล์ .env
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # ใช้คีย์จากไฟล์ .env
app.config['SESSION_TYPE'] = 'filesystem'  # ตั้งค่าประเภทเซสชัน
Session(app)  # เริ่มต้นเซสชัน
# Database setup
def init_db():
    with sqlite3.connect('pubachain.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY,
                wallet_id TEXT UNIQUE,
                password TEXT,
                wallet_address TEXT,
                balance REAL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                wallet_id TEXT,
                amount REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                previous_hash TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                nonce INTEGER,
                transactions TEXT
            )
        ''')
        #cursor.execute('''
            #CREATE TABLE IF NOT EXISTS scores (
                #id INTEGER PRIMARY KEY,
                #wallet_id TEXT,
                #coins_mined INTEGER,
                #timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            #)
        #''')
        conn.commit()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.mempool = []
        self.difficulty = 4
        self.reward = 50
        self.block_mined_count = 0
        
        # ลองโหลดสถานะบล็อกเชนจากไฟล์ก่อน
        self.load_chain()
        if len(self.chain) == 0:  # ถ้าไม่มีบล็อกให้สร้าง Genesis block
            self.create_block(previous_hash='1', nonce=0)
        
    def save_chain(self):
        # บันทึกบล็อกเชนลงในไฟล์
        with open('blockchain.json', 'w') as f:
            json.dump(self.chain, f)
    
    def load_chain(self):
        # ลองโหลดบล็อกเชนจากไฟล์
        try:
            with open('blockchain.json', 'r') as f:
                self.chain = json.load(f)
        except FileNotFoundError:
            self.chain = []  # ถ้าไฟล์ไม่มี ให้เริ่มบล็อกเชนใหม่

    def create_block(self, nonce, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'previous_hash': previous_hash
        }
        block['hash'] = self.hash(block)  # ตรวจสอบว่าได้คำนวณ hash และเพิ่มไปในบล็อก
        self.current_transactions = []  # รีเซ็ตธุรกรรมในบล็อกใหม่
        self.chain.append(block)  # เพิ่มบล็อกใหม่ในเชน
        return block
    
    def hash(self, block):
        """
        สร้างแฮชของบล็อก
        """
        encoded_block = json.dumps(block, sort_keys=True).encode()  # เข้ารหัสบล็อก
        return hashlib.sha256(encoded_block).hexdigest()  # คืนค่าแฮชของบล็อก
    
    def proof_of_work(self, previous_nonce):
        """
        หาค่า nonce ที่ถูกต้องโดยใช้ Proof of Work
        """
        nonce = 0
        while not self.valid_proof(previous_nonce, nonce):
            nonce += 1
        return nonce

    def valid_proof(self, previous_nonce, nonce):
        """
        ตรวจสอบความถูกต้องของ nonce
        """
        guess = f'{previous_nonce}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == '0' * self.difficulty

    def add_transaction(self, wallet_id, amount):
        """
        เพิ่มธุรกรรมใหม่ไปยัง mempool
        """
        transaction = {'wallet_id': wallet_id, 'amount': amount}
        self.mempool.append(transaction)


    def mine_block(self, wallet_id):
        """
        ฟังก์ชันสำหรับการขุดบล็อกใหม่และให้รางวัลแก่ผู้ขุด
        """
        if not self.mempool:  # ตรวจสอบว่ามีธุรกรรมใน mempool หรือไม่
            print("ไม่สามารถขุดบล็อกได้: ไม่มีธุรกรรมใน mempool")
            return None

        # รับข้อมูลบล็อกสุดท้าย
        last_block = self.chain[-1]
        previous_nonce = last_block['nonce']

        # คำนวณ nonce ใหม่โดยใช้ proof of work
        nonce = self.proof_of_work(previous_nonce)
        previous_hash = self.hash(last_block)

        # สร้างบล็อกใหม่
        block = self.create_block(nonce, previous_hash)

        # ใช้ธุรกรรมจาก mempool ในการสร้างบล็อกใหม่
        block['transactions'] = self.mempool.copy()  # ใช้ copy ของ mempool
        self.mempool.clear()  # เคลียร์ mempool หลังจากขุดบล็อกใหม่
        # เพิ่ม index ให้กับบล็อกใหม่
        block['index'] = len(self.chain) + 1

        # ให้รางวัลแก่ผู้ขุด
        try:
            transaction_id = self.add_transaction(wallet_id, self.reward)  # เพิ่มรางวัลให้กับกระเป๋า
            update_wallet_balance(wallet_id, self.reward)  # อัปเดตยอดเงินในกระเป๋า
        except Exception as e:
            print("Error updating wallet:", e)
            return None

        # บันทึกบล็อกลงในฐานข้อมูล
        print("Attempting to save block:", block)
        if not save_block_to_db(block):
            print("เกิดข้อผิดพลาดในการบันทึกบล็อกลงในฐานข้อมูล")
            return None

        # เพิ่มจำนวนบล็อกที่ขุดแล้ว
        self.block_mined_count += 1

        # ปรับความยากและรางวัลตามจำนวนบล็อกที่ขุดแล้ว
        if self.block_mined_count % 100 == 0:  # ปรับทุก ๆ 100 บล็อก
            self.difficulty += 1  # เพิ่มความยาก
            self.reward = max(1, self.reward // 2)  # ลดรางวัลโดยไม่ให้ต่ำกว่า 1

        # บันทึกบล็อกเชนหลังจากขุดสำเร็จ
        self.save_chain()

        if 'hash' in block:
            print(f"ขุดบล็อกใหม่สำเร็จ: {block['index']} | Hash: {block['hash']} | ผู้ขุด: {wallet_id} | รางวัล: {self.reward} Coins")
        else:
            print(f"ขุดบล็อกใหม่สำเร็จ: {block['index']} | Hash ไม่ถูกต้อง | ผู้ขุด: {wallet_id} | รางวัล: {self.reward} Coins")

        return block


def verify_and_update_balance(wallet_id):
    # ดึงข้อมูลยอดจากฐานข้อมูล
    with sqlite3.connect('pubachain.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM wallets WHERE wallet_id = ?', (wallet_id,))
        db_balance = cursor.fetchone()[0]

    # ดึงยอดจากบล็อกเชน
    blockchain_balance = get_balance_from_blockchain(wallet_id)

    # ตรวจสอบยอดว่าตรงกันหรือไม่
    if db_balance != blockchain_balance:
        # ถ้ายอดไม่ตรงกัน ทำการอัปเดตยอดตามบล็อกเชน
        with sqlite3.connect('pubachain.db') as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE wallets SET balance = ? WHERE wallet_id = ?', (blockchain_balance, wallet_id))
            conn.commit()
        return f"ยอดในกระเป๋า {wallet_id} ไม่ตรงกัน ถูกแก้ไขแล้วเป็น {blockchain_balance} เหรียญ"
    else:
        return "ยอดตรงกัน ไม่มีการแก้ไข"


@app.route('/blocks/search', methods=['GET'])
def search_block_by_hash():
    hash_to_search = request.args.get('hash')

    # ค้นหาบล็อกจาก hash
    for block in blockchain['chain']:
        if 'hash' in block and block['hash'] == hash_to_search:
            # ส่งข้อมูลบล็อกพร้อมกับธุรกรรม
            return jsonify({'success': True, 'block': block, 'transactions': block['transactions']})

    return jsonify({'success': False, 'message': 'Block not found'})




def update_wallet_balance(wallet_id, amount):
    try:
        conn = sqlite3.connect('pubachain.db', timeout=5)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM wallets WHERE wallet_id = ?', (wallet_id,))
        wallet = cursor.fetchone()
        
        if wallet:
            cursor.execute('UPDATE wallets SET balance = balance + ? WHERE wallet_id = ?', (amount, wallet_id))
        else:
            cursor.execute('INSERT INTO wallets (wallet_id, balance) VALUES (?, ?)', (wallet_id, amount))

        cursor.execute('INSERT INTO transactions (wallet_id, amount) VALUES (?, ?)', (wallet_id, amount))

        conn.commit()
    except Exception as e:
        print(f"Error updating wallet balance: {str(e)}")
    finally:
        conn.close()

def save_block_to_db(block):
    try:
        conn = sqlite3.connect('pubachain.db', timeout=5)
        cursor = conn.cursor()
        
        # ตรวจสอบว่าบล็อกมี index ซ้ำซ้อนหรือไม่
        cursor.execute("SELECT * FROM blocks WHERE block_index = ?", (block['index'],))
        if cursor.fetchone() is not None:
            print(f"Block index {block['index']} already exists.")
            return False

        # บันทึกบล็อกใหม่
        cursor.execute("INSERT INTO blocks (block_index, timestamp, transactions, nonce, previous_hash) VALUES (?, ?, ?, ?, ?)",
                       (block['index'], block['timestamp'], str(block['transactions']), block['nonce'], block['previous_hash']))

        conn.commit()
    except Exception as e:
        print(f"Error saving block to database: {str(e)}")
    finally:
        conn.close()

    return True


@app.route('/check_blocks', methods=['GET'])
def check_blocks():
    try:
        with sqlite3.connect('pubachain.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM blocks')
            blocks = cursor.fetchall()
            return jsonify({
                "success": True,
                "blocks": blocks
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


    
# Route สำหรับดึงข้อมูลบล็อกทั้งหมด
@app.route('/blocks', methods=['GET'])
def get_blocks():
    try:
        blocks = blockchain.chain
        return jsonify({
            "success": True,
            "blocks": blocks
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

# Route สำหรับดึงบล็อกล่าสุด
@app.route('/blocks/latest', methods=['GET'])
def get_latest_block():
    try:
        latest_block = blockchain.chain[-1]
        return jsonify({
            "success": True,
            "block": latest_block
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    
def save_wallet_to_db(wallet):
    # โค้ดที่ใช้ในการบันทึกยอดเงินในฐานข้อมูล
    connection = sqlite3.connect('pubachain.db')
    cursor = connection.cursor()
    
    cursor.execute('''
        UPDATE wallets SET balance = ? WHERE wallet_id = ?
    ''', (wallet['balance'], wallet['wallet_id']))
    
    connection.commit()
    connection.close()


# Initialize the blockchain
blockchain = Blockchain()
init_db()

@app.route('/')
def index():
    return render_template('index.html')



def fetch_transfer_history_from_database(wallet_id):
    import sqlite3

    # เชื่อมต่อกับฐานข้อมูล
    conn = sqlite3.connect('pubachain.db')  # ชื่อฐานข้อมูลของคุณ
    cursor = conn.cursor()

    # สร้างคำสั่ง SQL เพื่อดึงประวัติการโอนเหรียญ
    cursor.execute('''
        SELECT recipient_wallet_id, amount, timestamp
        FROM transfer_history
        WHERE sender_wallet_id = ?
        ORDER BY timestamp DESC
    ''', (wallet_id,))

    # ดึงข้อมูลทั้งหมด
    transfers = cursor.fetchall()
    conn.close()

    # แปลงข้อมูลให้อยู่ในรูปแบบที่ใช้งานได้
    transfer_history = [
        {
            'recipient_wallet_id': transfer[0],
            'amount': transfer[1],
            'timestamp': transfer[2]
        } for transfer in transfers
    ]

    return transfer_history


@app.route('/wallet/transfer/history', methods=['GET'])
def get_transfer_history():
    wallet_id = request.args.get('wallet_id')  # รับ wallet_id จาก query string
    if not wallet_id:
        return jsonify({'success': False, 'message': 'กรุณาล็อกอินเพื่อดูประวัติการโอนเหรียญ'}), 403

    try:
        history = fetch_transfer_history_from_database(wallet_id)
        return jsonify(history), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



@app.route('/wallet')
def wallet():
    return render_template('transfer.html')

@app.route('/wallet.html')
def wallet_page():
    return render_template('wallet.html')

@app.route('/transactions.html')
def transactions_page():
    return render_template('transactions.html')

@app.route('/game.html')
def game_page():
    return render_template('game.html')

@app.route('/mine_coins.html')
def mine_coins_page():
    return render_template('mine_coins.html')

@app.route('/wallet/transfer', methods=['POST'])
def transfer_coins():
    if 'wallet_id' not in session:
        return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบก่อนทำการโอนเหรียญ!"})
    
    data = request.json
    recipient_wallet_id = data.get('recipient_wallet_id')
    amount = data.get('amount')

    # ตรวจสอบว่าจำนวนเงินเป็นบวก
    if amount <= 0:
        return jsonify({"success": False, "message": "จำนวนเงินต้องมากกว่าศูนย์!"})

    # ตรวจสอบยอดเงินในกระเป๋าของผู้โอน
    sender_wallet_id = session['wallet_id']
    with sqlite3.connect('pubachain.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM wallets WHERE wallet_id = ?', (sender_wallet_id,))
        sender_balance = cursor.fetchone()

        if sender_balance and sender_balance[0] >= amount:
            # เพิ่มธุรกรรมลงใน mempool
            blockchain.add_transaction(sender_wallet_id, -amount)
            blockchain.add_transaction(recipient_wallet_id, amount)

            # ลดยอดเงินของผู้โอน
            cursor.execute('UPDATE wallets SET balance = balance - ? WHERE wallet_id = ?', (amount, sender_wallet_id))
            # เพิ่มยอดเงินในกระเป๋าของผู้รับ
            cursor.execute('UPDATE wallets SET balance = balance + ? WHERE wallet_id = ?', (amount, recipient_wallet_id))
            # บันทึกการโอนในตาราง transactions
            cursor.execute('INSERT INTO transactions (wallet_id, amount) VALUES (?, ?)', (sender_wallet_id, -amount))
            cursor.execute('INSERT INTO transactions (wallet_id, amount) VALUES (?, ?)', (recipient_wallet_id, amount))
            conn.commit()

            return jsonify({"success": True, "message": "โอนเหรียญเรียบร้อยแล้ว!"})
            
        else:
            return jsonify({"success": False, "message": "ยอดเงินไม่เพียงพอหรือตรวจไม่พบกระเป๋าผู้รับ!"})



@app.route('/wallet/create', methods=['POST'])
def create_wallet():
    data = request.json
    wallet_id = data.get('wallet_id')
    password = data.get('password')

    # รหัสผ่านจะต้องถูกเข้ารหัสที่นี่
    hashed_password = generate_password_hash(password)

    # สร้างที่อยู่กระเป๋าใหม่
    wallet_address = str(uuid.uuid4())  # สร้างที่อยู่กระเป๋าแบบสุ่ม

    with sqlite3.connect('pubachain.db') as conn:
        cursor = conn.cursor()
        # ตรวจสอบว่ามีกระเป๋าที่มี ID นี้อยู่แล้วหรือไม่
        cursor.execute('SELECT * FROM wallets WHERE wallet_id = ?', (wallet_id,))
        row = cursor.fetchone()
        
        if row:  # ถ้ามีกระเป๋าอยู่แล้ว
            return jsonify({"success": False, "message": "ID กระเป๋านี้มีอยู่แล้ว กรุณาใช้ ID อื่น!"})

        # ถ้าไม่มี กระเป๋าให้สร้างใหม่
        cursor.execute('INSERT INTO wallets (wallet_id, password, balance, wallet_address) VALUES (?, ?, ?, ?)',
                       (wallet_id, hashed_password, 0.0, wallet_address))  # เริ่มต้นยอดเงินที่ 0
        conn.commit()

    return jsonify({"success": True, "message": "สร้างกระเป๋าเรียบร้อยแล้ว!", "wallet_id": wallet_id, "wallet_address": wallet_address, "balance": 0.0})

@app.route('/wallet/login', methods=['POST'])
def login_wallet():
    data = request.json
    wallet_id = data.get('wallet_id')
    password = data.get('password')

    with sqlite3.connect('pubachain.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password, balance FROM wallets WHERE wallet_id = ?', (wallet_id,))
        row = cursor.fetchone()

        if row and check_password_hash(row[0], password):
            # บันทึก ID กระเป๋าและยอดเงินในเซสชัน
            session['wallet_id'] = wallet_id
            session['balance'] = row[1]
            return jsonify({"success": True, "wallet_id": wallet_id, "balance": row[1]})
        else:
            return jsonify({"success": False, "message": "ID กระเป๋าหรือรหัสผ่านไม่ถูกต้อง!"})

@app.route('/wallet/logout', methods=['POST'])
def logout_wallet():
    session.clear()  # ลบข้อมูลเซสชัน
    return jsonify({"success": True, "message": "ออกจากระบบเรียบร้อยแล้ว!"})

# ฟังก์ชันเพื่อใช้ในการตรวจสอบสถานะการเข้าสู่ระบบ
@app.route('/wallet/status', methods=['GET'])
def wallet_status():
    if 'wallet_id' not in session:
        return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบ!"})

    return jsonify({
        "success": True,
        "wallet_id": session['wallet_id'],
        "balance": session['balance']
    })

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'wallet_id' not in session:
            return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบ!"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/some_protected_route')
@login_required
def protected_route():
    # เส้นทางนี้ต้องการให้ผู้ใช้เข้าสู่ระบบก่อน
    return jsonify({"success": True, "message": "คุณสามารถเข้าถึงเส้นทางนี้ได้!"})






@app.route('/wallet/transfer.html')
def transfer_page():
    return render_template('transfer.html')


@app.route('/transactions', methods=['GET'])
def get_transactions():
    with sqlite3.connect('pubachain.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions ORDER BY timestamp DESC')
        
        # ดึงข้อมูลทั้งหมด
        transactions = cursor.fetchall()
        
        # แปลงข้อมูลให้เป็นรายการของ dictionary
        transaction_list = []
        for transaction in transactions:
            transaction_list.append({
                'id': transaction[0],            # หรือใช้ชื่อคอลัมน์แทน
                'wallet_id': transaction[1],     # หรือใช้ชื่อคอลัมน์แทน
                'amount': transaction[2],        # หรือใช้ชื่อคอลัมน์แทน
                'timestamp': transaction[3]      # หรือใช้ชื่อคอลัมน์แทน
            })
    
    return jsonify(transaction_list)


def get_db_connection():
    conn = sqlite3.connect('pubachain.db')
    conn.row_factory = sqlite3.Row
    return conn



@app.route('/mine/start', methods=['POST'])
def start_mining():
    wallet_id = request.json.get('wallet_id')
    block = blockchain.mine_block(wallet_id)  # เรียกใช้ฟังก์ชัน mine_block
    
    if not wallet_id:
        return jsonify({
            "success": False,
            "message": "กรุณาระบุ wallet_id"
        }), 400  # ส่งกลับสถานะ 400 ถ้าข้อมูลไม่ครบถ้วน

    try:
        # ขุดบล็อกใหม่
        block = blockchain.mine_block(wallet_id)

        # บันทึกบล็อกใหม่ลงในฐานข้อมูล
        save_block_to_db(block)

        return jsonify({
            "success": True,
            "message": "ขุดบล็อกสำเร็จ!",
            "hash": block['hash'],  # ส่งกลับ hash ของบล็อกที่ขุด
            "transactions": block['transactions']  # ส่งกลับธุรกรรมที่บันทึกในบล็อก
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500  # ส่งกลับสถานะ 500 ถ้ามีข้อผิดพลาดเกิดขึ้น

def update_wallet(wallet_id, reward_amount):
    try:
        # เชื่อมต่อกับฐานข้อมูล
        conn = sqlite3.connect('pubachain.db')
        cursor = conn.cursor()

        # ตรวจสอบว่ากระเป๋านี้มีอยู่ในฐานข้อมูลหรือไม่
        cursor.execute("SELECT balance FROM wallets WHERE wallet_id = ?", (wallet_id,))
        result = cursor.fetchone()

        if result:
            # อัปเดตยอดเหรียญในกระเป๋า
            current_balance = result[0]
            new_balance = current_balance + reward_amount
            cursor.execute("UPDATE wallets SET balance = ? WHERE wallet_id = ?", (new_balance, wallet_id))
            conn.commit()
            print(f"อัปเดตกระเป๋า {wallet_id} เป็นยอดเงินใหม่: {new_balance}")
        else:
            print(f"ไม่พบกระเป๋าที่ต้องการอัปเดตสำหรับ ID: {wallet_id}")
            raise ValueError("ไม่พบกระเป๋าที่ต้องการอัปเดต")

    except sqlite3.Error as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับฐานข้อมูล: {e}")
        raise

    finally:
        # ปิดการเชื่อมต่อฐานข้อมูล
        if conn:
            conn.close()




@app.route('/check_wallet')
def check_wallet_page():
    return render_template('wallet_status.html')


if __name__ == '__main__':
    app.run(debug=True)
