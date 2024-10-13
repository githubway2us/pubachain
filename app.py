from flask import Flask, request, jsonify, render_template
from flask_session import Session
from dotenv import load_dotenv
import os
from blockchain import Blockchain
from database import init_db, update_wallet_balance, save_block_to_db

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize the blockchain and database
blockchain = Blockchain()
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/blocks/search', methods=['GET'])
def search_block_by_hash():
    hash_to_search = request.args.get('hash')

    for block in blockchain.chain:
        if 'hash' in block and block['hash'] == hash_to_search:
            return jsonify({'success': True, 'block': block, 'transactions': block['transactions']})

    return jsonify({'success': False, 'message': 'Block not found'})

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

# Other routes...

if __name__ == '__main__':
    app.run(debug=True)
