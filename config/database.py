import os
import aiomysql
from dotenv import load_dotenv

load_dotenv()

pool = None

async def get_db_pool():
    global pool
    if pool is None:
        pool = await aiomysql.create_pool(
            host=os.getenv("DB_HOST"),
            port=3306,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_DATABASE"),
            autocommit=True 
        )
    return pool
