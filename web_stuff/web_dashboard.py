from flask import Flask, jsonify, render_template
import sqlite3
from datetime import datetime
import os
import threading

TEMPLATE_FOLDER = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=TEMPLATE_FOLDER)

DB_PATH = 'scam_detector.db'

_bot_instance = None

def init_dashboard(bot):
    global _bot_instance
    _bot_instance = bot
    _bot_instance = bot

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
    
    cursor.execute('SELECT DISTINCT guild_id FROM server_config')
    guild_ids = [row[0] for row in cursor.fetchall()]
    
    guilds_info = []
    if _bot_instance:
        for guild_id in guild_ids:
            try:
                guild = _bot_instance.get_guild(int(guild_id))
                if guild:
                    guilds_info.append({
                        'guild_id': guild_id,
                        'name': guild.name,
                        'member_count': guild.member_count,
                        'icon_url': str(guild.icon.url) if guild.icon else None
                    })
            except Exception as e:
                print(f"Error fetching guild {guild_id}: {e}")
    
    cursor.execute('''
        SELECT guild_id, COUNT(*) as count
        FROM detections
        GROUP BY guild_id
        ORDER BY count DESC
        LIMIT 10
    ''')
    top_servers = cursor.fetchall()
    
    top_servers_enriched = []
    for row in top_servers:
        guild_id = row['guild_id']
        guild_info = next((g for g in guilds_info if g['guild_id'] == guild_id), None)
        top_servers_enriched.append({
            'guild_id': guild_id,
            'count': row['count'],
            'name': guild_info['name'] if guild_info else 'Unknown',
            'member_count': guild_info['member_count'] if guild_info else None
        })
    
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
    
    cursor.execute('SELECT DISTINCT guild_id FROM server_config')
    all_guild_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('''
        SELECT guild_id, COUNT(*) as hash_count
        FROM server_hashes
        GROUP BY guild_id
    ''')
    hashes_per_server_raw = cursor.fetchall()
    hash_dict = {row['guild_id']: row['hash_count'] for row in hashes_per_server_raw}
    
    cursor.execute('''
        SELECT guild_id, COUNT(*) as fp_count
        FROM false_positives
        GROUP BY guild_id
    ''')
    false_positives_per_server_raw = cursor.fetchall()
    fp_dict = {row['guild_id']: row['fp_count'] for row in false_positives_per_server_raw}
    
    hashes_per_server = []
    for guild_id in all_guild_ids:
        hash_count = hash_dict.get(guild_id, 0)
        fp_count = fp_dict.get(guild_id, 0)
        guild_info = next((g for g in guilds_info if g['guild_id'] == guild_id), None)
        
        hashes_per_server.append({
            'guild_id': guild_id,
            'name': guild_info['name'] if guild_info else 'Unknown',
            'member_count': guild_info['member_count'] if guild_info else None,
            'hash_count': hash_count,
            'fp_count': fp_count if fp_count > 0 else None
        })
    
    hashes_per_server.sort(key=lambda x: x['hash_count'], reverse=True)
    
    total_members = sum(g['member_count'] for g in guilds_info if g['member_count'])
    
    conn.close()
    
    return {
        'total_servers': total_servers,
        'total_members': total_members,
        'total_detections': total_detections,
        'total_server_hashes': total_server_hashes,
        'total_false_positives': total_false_positives,
        'guilds_info': guilds_info,
        'top_servers': top_servers_enriched,
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

def start_dashboard(host='localhost', port=5011):
    def run():
        import logging
        # Disable Flask/Werkzeug logs to suppress output from this thread
        logging.getLogger('werkzeug').disabled = True
        app.run(debug=False, host=host, port=port, use_reloader=False, threaded=True)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"Dashboard started on http://{host}:{port}")
    return thread

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found!")
        print(f"Expected path: {DB_PATH}")
        exit(1)
    
    print("Warning: Running without bot instance. Guild names and member counts will not be available.")
    print(f"Using database: {DB_PATH}")
    app.run(debug=True, host='localhost', port=5011)
