import aiosqlite
import json
from datetime import datetime
from typing import List, Optional, Dict
from contextlib import asynccontextmanager

class Database:
    def __init__(self, db_path='scam_detector.db'):
        self.db_path = db_path
    
    @asynccontextmanager
    async def get_connection(self):
        conn = await aiosqlite.connect(self.db_path)
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await conn.close()
    
    async def init_database(self):
        async with self.get_connection() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS server_config (
                    guild_id TEXT PRIMARY KEY,
                    report_channel_id TEXT,
                    default_action TEXT DEFAULT 'delete',
                    hash_threshold INTEGER DEFAULT 5,
                    use_global_hashes INTEGER DEFAULT 1,
                    scan_bot_messages INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS server_hashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    description TEXT,
                    UNIQUE(guild_id, hash)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    detected_at TEXT NOT NULL
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS false_positives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    reported_by TEXT NOT NULL,
                    reported_at TEXT NOT NULL,
                    UNIQUE(guild_id, hash)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_reputation (
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    detection_count INTEGER DEFAULT 0,
                    last_detection TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')
            
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_detections_guild ON detections(guild_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_detections_hash ON detections(guild_id, hash)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_detections_user ON detections(guild_id, user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_reputation ON user_reputation(guild_id, user_id)')
    
    async def get_server_config(self, guild_id: str) -> Optional[Dict]:
        async with self.get_connection() as conn:
            async with conn.execute('''
                SELECT report_channel_id, default_action, hash_threshold, use_global_hashes, scan_bot_messages, active
                FROM server_config WHERE guild_id = ?
            ''', (guild_id,)) as cursor:
                result = await cursor.fetchone()
        
        if result:
            return {
                'report_channel_id': result[0],
                'default_action': result[1],
                'hash_threshold': result[2],
                'use_global_hashes': result[3] if result[3] is not None else 1,
                'scan_bot_messages': result[4] if result[4] is not None else 0,
                'active': result[5] if result[5] is not None else 1
            }
        return None
    
    async def set_report_channel(self, guild_id: str, channel_id: str):
        async with self.get_connection() as conn:
            await conn.execute('''
                INSERT INTO server_config (guild_id, report_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET report_channel_id = ?
            ''', (guild_id, channel_id, channel_id))
    
    async def set_default_action(self, guild_id: str, action: str):
        async with self.get_connection() as conn:
            await conn.execute('''
                INSERT INTO server_config (guild_id, default_action)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET default_action = ?
            ''', (guild_id, action, action))
    
    async def set_hash_threshold(self, guild_id: str, threshold: int):
        async with self.get_connection() as conn:
            await conn.execute('''
                INSERT INTO server_config (guild_id, hash_threshold)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET hash_threshold = ?
            ''', (guild_id, threshold, threshold))
    
    async def set_use_global_hashes(self, guild_id: str, use_global: bool):
        async with self.get_connection() as conn:
            await conn.execute('''
                INSERT INTO server_config (guild_id, use_global_hashes)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET use_global_hashes = ?
            ''', (guild_id, 1 if use_global else 0, 1 if use_global else 0))
    
    async def set_scan_bot_messages(self, guild_id: str, scan_bots: bool):
        async with self.get_connection() as conn:
            await conn.execute('''
                INSERT INTO server_config (guild_id, scan_bot_messages)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET scan_bot_messages = ?
            ''', (guild_id, 1 if scan_bots else 0, 1 if scan_bots else 0))
    
    async def set_server_active(self, guild_id: str, active: bool):
        async with self.get_connection() as conn:
            await conn.execute('''
                INSERT INTO server_config (guild_id, active)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET active = ?
            ''', (guild_id, 1 if active else 0, 1 if active else 0))
    
    async def add_server_hash(self, guild_id: str, hash_value: str, description: str = None) -> bool:
        try:
            async with self.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO server_hashes (guild_id, hash, description)
                    VALUES (?, ?, ?)
                ''', (guild_id, hash_value, description))
            return True
        except aiosqlite.IntegrityError:
            return False
    
    async def get_server_hashes(self, guild_id: str) -> List[Dict]:
        async with self.get_connection() as conn:
            async with conn.execute('''
                SELECT hash, description
                FROM server_hashes WHERE guild_id = ?
            ''', (guild_id,)) as cursor:
                results = await cursor.fetchall()
        
        return [{'hash': row[0], 'description': row[1]} for row in results]
    
    async def delete_server_hash(self, guild_id: str, hash_value: str) -> bool:
        async with self.get_connection() as conn:
            cursor = await conn.execute('''
                DELETE FROM server_hashes
                WHERE guild_id = ? AND hash = ?
            ''', (guild_id, hash_value))
            deleted = cursor.rowcount > 0
        return deleted
    
    def get_global_hashes(self) -> List[Dict]:
        try:
            with open('global_hashes.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('hashes', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load global hashes: {e}. Continuing with server-specific hashes only.")
            return []
        except Exception as e:
            print(f"Warning: Unexpected error loading global hashes: {e}. Continuing with server-specific hashes only.")
            return []
    
    async def get_all_hashes(self, guild_id: str = None) -> List[Dict]:
        all_hashes = []
        
        use_global = True
        if guild_id:
            server_config = await self.get_server_config(guild_id)
            use_global = server_config.get('use_global_hashes', 1) == 1 if server_config else True
        
        if use_global:
            all_hashes = self.get_global_hashes()
        
        if guild_id:
            server_hashes = await self.get_server_hashes(guild_id)
            false_positives = await self.get_false_positives(guild_id)
            fp_hashes = {fp['hash'] for fp in false_positives}
            
            all_hashes = [h for h in all_hashes if h['hash'] not in fp_hashes]
            server_hashes = [h for h in server_hashes if h['hash'] not in fp_hashes]
            all_hashes.extend(server_hashes)
        
        return all_hashes
    
    async def get_stats(self, guild_id: str = None) -> Dict:
        global_count = len(self.get_global_hashes())
        
        server_count = 0
        if guild_id:
            async with self.get_connection() as conn:
                async with conn.execute('SELECT COUNT(*) FROM server_hashes WHERE guild_id = ?', (guild_id,)) as cursor:
                    result = await cursor.fetchone()
                    server_count = result[0]
        
        return {
            'global_count': global_count,
            'server_count': server_count,
            'total': global_count + server_count
        }
    
    async def increment_detection(self, guild_id: str, user_id: str, hash_value: str):
        async with self.get_connection() as conn:
            now = datetime.now()
            detection_time = now.isoformat()
            reputation_time = now.strftime("%Y-%m-%d %H:%M")
            
            await conn.execute('''
                INSERT INTO detections (guild_id, user_id, hash, detected_at)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, hash_value, detection_time))
            
            await conn.execute('''
                INSERT INTO user_reputation (guild_id, user_id, detection_count, last_detection)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET
                    detection_count = detection_count + 1,
                    last_detection = ?
            ''', (guild_id, user_id, reputation_time, reputation_time))
    
    async def get_detection_stats(self, guild_id: str) -> Dict:
        async with self.get_connection() as conn:
            async with conn.execute('SELECT COUNT(*) FROM detections WHERE guild_id = ?', (guild_id,)) as cursor:
                result = await cursor.fetchone()
                total_detections = result[0]
            
            async with conn.execute('''
                SELECT hash, COUNT(*) as count
                FROM detections
                WHERE guild_id = ?
                GROUP BY hash
                ORDER BY count DESC
                LIMIT 10
            ''', (guild_id,)) as cursor:
                results = await cursor.fetchall()
                top_hashes = [{'hash': row[0], 'count': row[1]} for row in results]
        
        return {
            'total_detections': total_detections,
            'top_hashes': top_hashes
        }
    
    async def get_user_reputation(self, guild_id: str, user_id: str) -> Optional[Dict]:
        async with self.get_connection() as conn:
            async with conn.execute('''
                SELECT detection_count, last_detection
                FROM user_reputation
                WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
        
        if result:
            return {
                'detection_count': result[0],
                'last_detection': result[1]
            }
        return None
    
    async def add_false_positive(self, guild_id: str, hash_value: str, reported_by: str) -> bool:
        try:
            async with self.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO false_positives (guild_id, hash, reported_by, reported_at)
                    VALUES (?, ?, ?, ?)
                ''', (guild_id, hash_value, reported_by, datetime.now().isoformat()))
            return True
        except aiosqlite.IntegrityError:
            return False
    
    async def get_false_positives(self, guild_id: str) -> List[Dict]:
        async with self.get_connection() as conn:
            async with conn.execute('''
                SELECT hash, reported_by, reported_at
                FROM false_positives WHERE guild_id = ?
            ''', (guild_id,)) as cursor:
                results = await cursor.fetchall()
        
        return [{'hash': row[0], 'reported_by': row[1], 'reported_at': row[2]} for row in results]
    
    async def remove_false_positive(self, guild_id: str, hash_value: str) -> bool:
        async with self.get_connection() as conn:
            cursor = await conn.execute('''
                DELETE FROM false_positives
                WHERE guild_id = ? AND hash = ?
            ''', (guild_id, hash_value))
            deleted = cursor.rowcount > 0
        return deleted
    
    async def is_false_positive(self, guild_id: str, hash_value: str) -> bool:
        async with self.get_connection() as conn:
            async with conn.execute('''
                SELECT 1 FROM false_positives
                WHERE guild_id = ? AND hash = ?
            ''', (guild_id, hash_value)) as cursor:
                result = await cursor.fetchone()
        return result is not None
    
    async def export_hashes(self, guild_id: str) -> Dict:
        server_hashes = await self.get_server_hashes(guild_id)
        false_positives = await self.get_false_positives(guild_id)
        
        return {
            'guild_id': guild_id,
            'exported_at': datetime.now().isoformat(),
            'hashes': server_hashes,
            'false_positives': [fp['hash'] for fp in false_positives]
        }
    
    async def import_hashes(self, guild_id: str, data: Dict) -> Dict[str, int]:
        added = 0
        skipped = 0
        
        for hash_item in data.get('hashes', []):
            success = await self.add_server_hash(
                guild_id,
                hash_item['hash'],
                hash_item.get('description')
            )
            if success:
                added += 1
            else:
                skipped += 1
        
        return {'added': added, 'skipped': skipped}
    
    async def reset_user_hits(self, guild_id: str, user_id: str) -> bool:
        async with self.get_connection() as conn:
            cursor = await conn.execute('''
                DELETE FROM user_reputation
                WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            
            await conn.execute('''
                DELETE FROM detections
                WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            
            deleted = cursor.rowcount > 0
        return deleted
    
    async def delete_all_server_data(self, guild_id: str):
        async with self.get_connection() as conn:
            await conn.execute('DELETE FROM server_config WHERE guild_id = ?', (guild_id,))
            await conn.execute('DELETE FROM server_hashes WHERE guild_id = ?', (guild_id,))
            await conn.execute('DELETE FROM detections WHERE guild_id = ?', (guild_id,))
            await conn.execute('DELETE FROM false_positives WHERE guild_id = ?', (guild_id,))
            await conn.execute('DELETE FROM user_reputation WHERE guild_id = ?', (guild_id,))
