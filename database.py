import sqlite3

def init_db():
    with sqlite3.connect('pubachain.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY,
            wallet_id TEXT UNIQUE,
            password TEXT,
            wallet_address TEXT,
            balance REAL DEFAULT 0
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            wallet_id TEXT,
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS blocks (
            block_index INTEGER PRIMARY KEY,
            previous_hash TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            nonce INTEGER,
            transactions TEXT
        )''')
        conn.commit()

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
        
        cursor.execute("SELECT * FROM blocks WHERE block_index = ?", (block['index'],))
        if cursor.fetchone() is not None:
            print(f"Block index {block['index']} already exists.")
            return False

        cursor.execute("INSERT INTO blocks (block_index, timestamp, transactions, nonce, previous_hash) VALUES (?, ?, ?, ?, ?)",
                       (block['index'], block['timestamp'], str(block['transactions']), block['nonce'], block['previous_hash']))

        conn.commit()
    except Exception as e:
        print(f"Error saving block to database: {str(e)}")
    finally:
        conn.close()

    return True
