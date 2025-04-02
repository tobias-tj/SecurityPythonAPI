import psycopg2
from psycopg2 import pool
import logging

logger = logging.getLogger(__name__)


class DynamicDbConnection:
    _connection_pool = None

    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.conn = None

    def initialize_pool(self):
        try:
            if not DynamicDbConnection._connection_pool:
                DynamicDbConnection._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 5,  # minconn, maxconn
                    self.connection_string,
                    sslmode='require'
                )
                logger.info("Dynamic connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing dynamic pool: {str(e)}")
            raise

    def get_connection(self):
        if not DynamicDbConnection._connection_pool:
            self.initialize_pool()

        try:
            self.conn = DynamicDbConnection._connection_pool.getconn()
            with self.conn.cursor() as cursor:
                cursor.execute("SET TIME ZONE 'America/Asuncion';")
            return self.conn
        except Exception as e:
            logger.error(f"Error getting connection from pool: {str(e)}")
            raise

    def execute_query(self, query, params=None):
        try:
            if not self.conn:
                self.get_connection()

            with self.conn.cursor() as cursor:
                logger.info(f"Executing query: {query}")
                cursor.execute(query, params or ())
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                self.conn.commit()
                return True
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Error executing query: {str(e)}")
            raise

    def close(self):
        try:
            if self.conn:
                DynamicDbConnection._connection_pool.putconn(self.conn)
                self.conn = None
        except Exception as e:
            logger.error(f"Error returning connection to pool: {str(e)}")
            raise

    @classmethod
    def close_all(cls):
        try:
            if cls._connection_pool:
                cls._connection_pool.closeall()
                logger.info("All dynamic connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing all connections: {str(e)}")
            raise