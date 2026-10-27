from flask import Flask, request, jsonify, render_template
from pathlib import Path
from werkzeug.utils import secure_filename
from uuid import uuid4
import sqlite3
import os
from datetime import datetime

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
DB = ROOT / 'findly.db'
UPLOADS = ROOT / 'static' / 'uploads'
UPLOADS.mkdir(parents=True, exist_ok=True)
ALLOWED = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
CATEGORIES = {'Bags', 'Electronics', 'Keys', 'Wallets', 'Bottles', 'IDs', 'Books', 'Clothing', 'Other'}

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def setup():
    with connect() as con:
        con.executescript('''CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,type TEXT NOT NULL,category TEXT NOT NULL,location TEXT NOT NULL,date TEXT NOT NULL,description TEXT NOT NULL,image TEXT DEFAULT '',status TEXT NOT NULL DEFAULT 'Open');
        CREATE TABLE IF NOT EXISTS claims(id INTEGER PRIMARY KEY AUTOINCREMENT,item_id INTEGER NOT NULL,proof TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'Pending',date TEXT NOT NULL,FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY AUTOINCREMENT,text TEXT NOT NULL,date TEXT NOT NULL);''')

def error(message, status=400):
    return jsonify(error=message), status

@app.get('/')
def home():
    return render_template('index.html')

@app.get('/api/state')
def state():
    with connect() as con:
        items = [dict(x) for x in con.execute('SELECT * FROM items ORDER BY id DESC')]
        claims = [dict(x) for x in con.execute('SELECT claims.*,items.title FROM claims JOIN items ON items.id=claims.item_id ORDER BY claims.id DESC')]
        notices = [dict(x) for x in con.execute('SELECT * FROM notices ORDER BY id DESC LIMIT 30')]
    return jsonify(items=items, claims=claims, notices=notices)

@app.post('/api/items')
def create_item():
    data = request.form
    title = data.get('title', '').strip()
    kind = data.get('type', '')
    category = data.get('category', '')
    location = data.get('location', '').strip()
    date = data.get('date', '').strip()
    description = data.get('description', '').strip()
    
    if not title or not location or not date or not description or kind not in {'Lost', 'Found'} or category not in CATEGORIES:
        return error('Complete all required fields.')
        
    uploaded = request.files.get('image')
    if not uploaded or not uploaded.filename:
        return error('Please upload a photo of the item. Photos are required for both Lost and Found reports.')
        
    name = secure_filename(uploaded.filename)
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if ext not in ALLOWED:
        return error('Upload JPG, PNG, WEBP or GIF images only.')
    if not (uploaded.mimetype or '').startswith('image/'):
        return error('Selected file must be an image.')
        
    filename = f'{uuid4().hex}.{ext}'
    uploaded.save(UPLOADS / filename)
    image = '/static/uploads/' + filename

    with connect() as con:
        con.execute('INSERT INTO items(title,type,category,location,date,description,image) VALUES(?,?,?,?,?,?,?)', (title, kind, category, location, date, description, image))
        con.execute('INSERT INTO notices(text,date) VALUES(?,?)', (f'{kind} report created: {title}', datetime.now().strftime('%Y-%m-%d %H:%M')))
    return jsonify(ok=True), 201

@app.delete('/api/items/<int:item_id>')
def delete_item(item_id):
    with connect() as con:
        item = con.execute('SELECT * FROM items WHERE id=?', (item_id,)).fetchone()
        if not item:
            return error('Item not found.', 404)
        
        # Remove uploaded image file if it exists
        if item['image'] and item['image'].startswith('/static/uploads/'):
            filename = item['image'].replace('/static/uploads/', '')
            file_path = UPLOADS / filename
            if file_path.exists():
                try:
                    os.remove(file_path)
                except OSError:
                    pass

        # Delete associated claims and the item itself
        con.execute('DELETE FROM claims WHERE item_id=?', (item_id,))
        con.execute('DELETE FROM items WHERE id=?', (item_id,))
        con.execute('INSERT INTO notices(text,date) VALUES(?,?)', (f'Report deleted: {item["title"]}', datetime.now().strftime('%Y-%m-%d %H:%M')))
    return jsonify(ok=True)

@app.post('/api/claims')
def create_claim():
    data = request.get_json(silent=True) or {}
    try:
        item_id = int(data.get('itemId'))
    except (TypeError, ValueError):
        return error('Invalid item ID')
        
    proof = str(data.get('proof', '')).strip()
    if len(proof) < 8:
        return error('Provide at least 8 characters of ownership proof.')
        
    with connect() as con:
        item = con.execute('SELECT * FROM items WHERE id=?', (item_id,)).fetchone()
        if not item:
            return error('Item not found.', 404)
        if item['type'] != 'Found':
            return error('Claims can only be submitted for Found reports.')
        if item['status'] == 'Recovered':
            return error('This item has already been recovered.')
            
        con.execute('INSERT INTO claims(item_id,proof,date) VALUES(?,?,?)', (item_id, proof, datetime.now().strftime('%Y-%m-%d %H:%M')))
        con.execute('INSERT INTO notices(text,date) VALUES(?,?)', (f'Claim submitted for {item["title"]}', datetime.now().strftime('%Y-%m-%d %H:%M')))
    return jsonify(ok=True), 201

@app.post('/api/claims/<int:claim_id>/review')
def review(claim_id):
    data = request.get_json(silent=True) or {}
    status = data.get('status')
    if status not in {'Approved', 'Rejected'}:
        return error('Invalid review decision.')
        
    with connect() as con:
        claim = con.execute('SELECT * FROM claims WHERE id=?', (claim_id,)).fetchone()
        if not claim:
            return error('Claim not found.', 404)
        if claim['status'] != 'Pending':
            return error('Claim has already been reviewed.')
            
        con.execute('UPDATE claims SET status=? WHERE id=?', (status, claim_id))
        if status == 'Approved':
            con.execute("UPDATE items SET status='Recovered' WHERE id=?", (claim['item_id'],))
        con.execute('INSERT INTO notices(text,date) VALUES(?,?)', (f'Claim #{claim_id}: {status}', datetime.now().strftime('%Y-%m-%d %H:%M')))
    return jsonify(ok=True)

@app.errorhandler(413)
def too_large(_):
    return error('Image must be smaller than 5 MB.', 413)

setup()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)