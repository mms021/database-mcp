"""
Коннектор для MySQL
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
import pymysql
from pymysql.cursors import DictCursor

from .base import BaseConnector
from ..utils.config import DatabaseType, QueryResult, TableInfo


class MySQLConnector(BaseConnector):
    """Коннектор для MySQL"""
    
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.connection = None
    
    async def connect(self) -> bool:
        """Подключение к MySQL"""
        try:
            connection_params = self._build_connection_params()
            
            # Создание подключения в отдельном потоке
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                None, pymysql.connect, **connection_params
            )
            
            self._is_connected = True
            
            self.logger.log_connection(
                database_type="mysql",
                host=self.config.host,
                database=self.config.database,
                success=True
            )
            
            return True
            
        except Exception as e:
            self.logger.log_connection(
                database_type="mysql",
                host=self.config.host,
                database=self.config.database,
                success=False,
                error=str(e)
            )
            return False
    
    async def disconnect(self) -> bool:
        """Отключение от MySQL"""
        try:
            if self.connection:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.close)
                self.connection = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting from MySQL",
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
                database_type="mysql",
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
                database_type="mysql",
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
                database_type="mysql",
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
                database_type="mysql",
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
        
        result = await self.execute_query(query, {'table_schema': self.config.database})
        
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
            character_maximum_length,
            column_key,
            extra
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """
        
        result = await self.execute_query(query, {'table_schema': self.config.database, 'table_name': table_name})
        
        if not result.success:
            raise ValueError(f"Error getting schema for table {table_name}: {result.error_message}")
        
        columns = []
        for row in result.data:
            columns.append({
                'name': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable'] == 'YES',
                'default': row['column_default'],
                'max_length': row['character_maximum_length'],
                'key': row['column_key'],
                'extra': row['extra']
            })
        
        return TableInfo(
            name=table_name,
            schema=self.config.database,
            columns=columns
        )
    
    async def test_connection(self) -> bool:
        """Тестирование подключения"""
        try:
            result = await self.execute_query("SELECT 1 as test")
            return result.success
        except Exception:
            return False
    
    def _build_connection_params(self) -> Dict[str, Any]:
        """Построение параметров подключения"""
        params = {
            'host': self.config.host,
            'port': self.config.port,
            'user': self.config.username,
            'password': self.config.password,
            'database': self.config.database,
            'charset': self.config.charset or 'utf8mb4',
            'connect_timeout': self.config.connection_timeout,
            'autocommit': True,
        }
        
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}
        
        return params
    
    def _execute_select_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Синхронное выполнение SELECT запроса"""
        with self.connection.cursor(DictCursor) as cursor:
            if params:
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            return cursor.fetchall()
    
    def _execute_write_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Синхронное выполнение INSERT/UPDATE/DELETE запроса"""
        with self.connection.cursor() as cursor:
            if params:
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            return cursor.rowcount
