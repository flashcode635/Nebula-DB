import wiredtiger
import json
import time
import os

class WiredTigerCache:
    def __init__(self, cache_dir="./wiredtiger_cache", cache_size="100MB"):
        """
        Initialize WiredTiger cache
        
        Args:
            cache_dir: Directory where cache files will be stored
            cache_size: Max memory cache size (e.g., "100MB", "1GB")
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Open WiredTiger connection
        self.conn = wiredtiger.wiredtiger_open(
            cache_dir,
            f"create,cache_size={cache_size}"
        )
        
        # Create session
        self.session = self.conn.open_session()
        
        # Create table for cache
        # key_format=S means string key
        # value_format=u means raw bytes value
        self.session.create(
            "table:cache",
            "key_format=S,value_format=u"
        )
        
        # Open cursor for operations
        self.cursor = self.session.open_cursor("table:cache")
    
    def set(self, key, value, ttl_seconds=None):
        """
        Store value in cache
        
        Args:
            key: Cache key (string)
            value: Value to cache (any JSON serializable type)
            ttl_seconds: Time to live in seconds (optional)
        """
        # Convert value to bytes
        if isinstance(value, (dict, list)):
            value_bytes = json.dumps(value).encode('utf-8')
        elif isinstance(value, str):
            value_bytes = value.encode('utf-8')
        elif isinstance(value, bytes):
            value_bytes = value
        else:
            value_bytes = str(value).encode('utf-8')
        
        # Store main value
        self.cursor.set_key(key)
        self.cursor.set_value(value_bytes)
        self.cursor.insert()
        
        # Store TTL if provided
        if ttl_seconds:
            expiry_key = f"{key}__ttl"
            expiry_time = time.time() + ttl_seconds
            self.cursor.set_key(expiry_key)
            self.cursor.set_value(str(expiry_time).encode('utf-8'))
            self.cursor.insert()
        
        self.cursor.reset()
    
    def get(self, key):
        """
        Retrieve value from cache
        
        Returns:
            Cached value or None if not found/expired
        """
        # Check TTL first
        expiry_key = f"{key}__ttl"
        self.cursor.set_key(expiry_key)
        
        if self.cursor.search() == 0:
            expiry_time = float(self.cursor.get_value().decode('utf-8'))
            if time.time() > expiry_time:
                # Expired - delete both entries
                self.delete(key)
                return None
            self.cursor.reset()
        
        # Get actual value
        self.cursor.set_key(key)
        if self.cursor.search() == 0:
            value_bytes = self.cursor.get_value()
            self.cursor.reset()
            
            # Try to decode as JSON
            try:
                return json.loads(value_bytes.decode('utf-8'))
            except:
                return value_bytes.decode('utf-8')
        
        self.cursor.reset()
        return None
    
    def delete(self, key):
        """Delete key from cache"""
        # Delete main value
        self.cursor.set_key(key)
        self.cursor.remove()
        
        # Delete TTL if exists
        expiry_key = f"{key}__ttl"
        self.cursor.set_key(expiry_key)
        self.cursor.remove()
        
        self.cursor.reset()
    
    def exists(self, key):
        """Check if key exists in cache (and not expired)"""
        return self.get(key) is not None
    
    def clear(self):
        """Clear entire cache"""
        self.session.drop("table:cache")
        self.session.create(
            "table:cache",
            "key_format=S,value_format=u"
        )
        self.cursor = self.session.open_cursor("table:cache")
    
    def get_stats(self):
        """Get cache statistics"""
        stats = self.session.get_stats()
        return stats
    
    def close(self):
        """Close WiredTiger connections"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'session') and self.session:
            self.session.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
