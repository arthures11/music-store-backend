import redis.asyncio as redis
import os
from dotenv import load_dotenv
import json
from typing import List, Optional


load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 60))

redis_client = None

async def init_redis_pool():
    """Initializes the Redis connection pool."""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        await redis_client.ping() #
        print(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        redis_client = None

async def close_redis_pool():
    """Closes the Redis connection pool."""
    if redis_client:
        await redis_client.close()
        print("Redis connection closed.")

def get_redis_client() -> redis.Redis | None:
    """Returns the initialized Redis client instance."""
    return redis_client


async def get_cache(key: str):
    """Gets data from cache, handling potential errors and deserialization."""
    client = get_redis_client()
    if not client:
        return None
    try:
        cached_data = await client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        print(f"Error getting cache for key '{key}': {e}")
        return None

async def set_cache(key: str, data: any, ttl: int = CACHE_TTL):
    """Sets data in cache, handling potential errors and serialization."""
    client = get_redis_client()
    if not client:
        return
    try:
        serialized_data = json.dumps(data)
        await client.set(key, serialized_data, ex=ttl)
    except Exception as e:
        print(f"Error setting cache for key '{key}': {e}")

def generate_cache_key(prefix: str, name_filter: Optional[str]) -> str:
    """Generates a consistent cache key."""
    filter_part = f"name={name_filter.lower()}" if name_filter else "all"
    return f"{prefix}:{filter_part}"
