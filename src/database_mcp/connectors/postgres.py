"""
Коннектор для PostgreSQL
"""

import asyncio
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .base import BaseConnector
from ..utils.config import DatabaseType, QueryResult, TableInfo


class PostgreSQLConnector(BaseConnector):
    """Коннектор для PostgreSQL"""
    
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.connection = None
        self.cursor = None
    
    async def connect(self) -> bool:
        """Подключение к PostgreSQL"""
        try:
            connection_string = self._build_connection_string()
            
            # Создание подключения в отдельном потоке
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                None, psycopg2.connect, connection_string
            )
            
            self.connection.autocommit = True
            self._is_connected = True
            
            self.logger.log_connection(
                database_type="postgresql",
                host=self.config.host,
                database=self.config.database,
                success=True
            )
            
            return True
            
        except Exception as e:
            self.logger.log_connection(
                database_type="postgresql",
                host=self.config.host,
                database=self.config.database,
                success=False,
                error=str(e)
            )
            return False
    
    async def disconnect(self) -> bool:
        """Отключение от PostgreSQL"""
        try:
            if self.connection:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.close)
                self.connection = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting from PostgreSQL",
                error=str(e)
            )
            return False
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Выполнение SELECT запроса"""
        if not self._is_connected:
            return QueryResult(
                success=False,
                error_message="Not connected to database"
            )
        
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            
            # Выполнение запроса в отдельном потоке
            result = await loop.run_in_executor(
                None, self._execute_select_sync, query, params
            )
            
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="postgresql",
                execution_time=execution_time,
                success=True,
                row_count=len(result) if result else 0
            )
            
            return QueryResult(
                success=True,
                data=result,
                columns=list(result[0].keys()) if result else [],
                row_count=len(result) if result else 0,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="postgresql",
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
            
            return QueryResult(
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def execute_write(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Выполнение INSERT/UPDATE/DELETE запроса"""
        if not self._is_connected:
            return QueryResult(
                success=False,
                error_message="Not connected to database"
            )
        
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            
            # Выполнение запроса в отдельном потоке
            affected_rows = await loop.run_in_executor(
                None, self._execute_write_sync, query, params
            )
            
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="postgresql",
                execution_time=execution_time,
                success=True,
                row_count=affected_rows
            )
            
            return QueryResult(
                success=True,
                row_count=affected_rows,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="postgresql",
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
            
            return QueryResult(
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def get_tables(self) -> List[str]:
        """Получение списка таблиц"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name
        """
        
        schema = self.config.schema or 'public'
        result = await self.execute_query(query, {'table_schema': schema})
        
        if result.success and result.data:
            return [row['table_name'] for row in result.data]
        
        return []
    
    async def get_table_schema(self, table_name: str) -> TableInfo:
        """Получение схемы таблицы"""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """
        
        schema = self.config.schema or 'public'
        result = await self.execute_query(query, {'table_schema': schema, 'table_name': table_name})
        
        if not result.success:
            raise ValueError(f"Error getting schema for table {table_name}: {result.error_message}")
        
        columns = []
        for row in result.data:
            columns.append({
                'name': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable'] == 'YES',
                'default': row['column_default'],
                'max_length': row['character_maximum_length']
            })
        
        return TableInfo(
            name=table_name,
            schema=schema,
            columns=columns
        )
    
    async def test_connection(self) -> bool:
        """Тестирование подключения"""
        try:
            result = await self.execute_query("SELECT 1 as test")
            return result.success
        except Exception:
            return False
    
    def _build_connection_string(self) -> str:
        """Построение строки подключения"""
        params = {
            'host': self.config.host,
            'port': self.config.port,
            'dbname': self.config.database,
            'user': self.config.username,
            'password': self.config.password,
            'connect_timeout': self.config.connection_timeout,
        }
        
        if self.config.schema:
            params['options'] = f'-c search_path={self.config.schema}'
        
        if self.config.ssl_mode:
            params['sslmode'] = self.config.ssl_mode
        
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}
        
        # Построение строки подключения
        conn_parts = []
        for key, value in params.items():
            if key == 'options':
                conn_parts.append(f"{key}={value}")
            else:
                conn_parts.append(f"{key}={value}")
        
        return " ".join(conn_parts)
    
    def _execute_select_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Синхронное выполнение SELECT запроса"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            if params:
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _execute_write_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Синхронное выполнение INSERT/UPDATE/DELETE запроса"""
        with self.connection.cursor() as cursor:
            if params:
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            return cursor.rowcount
