from flask import Flask, jsonify, render_template
import sqlite3
from datetime import datetime
import os

TEMPLATE_FOLDER = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=TEMPLATE_FOLDER)

DB_PATH = 'scam_detector.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(DISTINCT guild_id) FROM server_config')
    total_servers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM detections')
    total_detections = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM server_hashes')
    total_server_hashes = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM false_positives')
    total_false_positives = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT guild_id, COUNT(*) as count
        FROM detections
        GROUP BY guild_id
        ORDER BY count DESC
        LIMIT 10
    ''')
    top_servers = cursor.fetchall()
    
    cursor.execute('''
        SELECT hash, COUNT(*) as count
        FROM detections
        GROUP BY hash
        ORDER BY count DESC
        LIMIT 10
    ''')
    top_hashes = cursor.fetchall()
    
    cursor.execute('''
        SELECT guild_id, user_id, hash, detected_at
        FROM detections
        ORDER BY detected_at DESC
        LIMIT 20
    ''')
    recent_detections = cursor.fetchall()
    
    cursor.execute('''
        SELECT guild_id, COUNT(*) as hash_count
        FROM server_hashes
        GROUP BY guild_id
        ORDER BY hash_count DESC
    ''')
    hashes_per_server_raw = cursor.fetchall()
    
    cursor.execute('''
        SELECT guild_id, COUNT(*) as fp_count
        FROM false_positives
        GROUP BY guild_id
        ORDER BY fp_count DESC
    ''')
    false_positives_per_server_raw = cursor.fetchall()
    
    fp_dict = {row['guild_id']: row['fp_count'] for row in false_positives_per_server_raw}
    hashes_per_server = []
    for row in hashes_per_server_raw:
        guild_id = row['guild_id']
        fp_count = fp_dict.get(guild_id, 0)
        hashes_per_server.append({
            'guild_id': guild_id,
            'hash_count': row['hash_count'],
            'fp_count': fp_count if fp_count > 0 else None
        })
    
    conn.close()
    
    return {
        'total_servers': total_servers,
        'total_detections': total_detections,
        'total_server_hashes': total_server_hashes,
        'total_false_positives': total_false_positives,
        'top_servers': [dict(row) for row in top_servers],
        'top_hashes': [dict(row) for row in top_hashes],
        'recent_detections': [dict(row) for row in recent_detections],
        'hashes_per_server': hashes_per_server
    }

@app.route('/')
def index():
    stats = get_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found!")
        exit(1)
    
    print("Starting dashboard on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
