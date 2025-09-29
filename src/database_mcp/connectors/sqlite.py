"""
Коннектор для SQLite
"""

import asyncio
import time
import sqlite3
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from ..utils.config import DatabaseType, QueryResult, TableInfo


class SQLiteConnector(BaseConnector):
    """Коннектор для SQLite"""
    
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.connection = None
    
    async def connect(self) -> bool:
        """Подключение к SQLite"""
        try:
            # Для SQLite database - это путь к файлу
            db_path = self.config.database
            
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                None, sqlite3.connect, db_path
            )
            
            # Включаем возврат строк как словарей
            self.connection.row_factory = sqlite3.Row
            self._is_connected = True
            
            self.logger.log_connection(
                database_type="sqlite",
                host="local",
                database=db_path,
                success=True
            )
            
            return True
            
        except Exception as e:
            self.logger.log_connection(
                database_type="sqlite",
                host="local",
                database=self.config.database,
                success=False,
                error=str(e)
            )
            return False
    
    async def disconnect(self) -> bool:
        """Отключение от SQLite"""
        try:
            if self.connection:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.close)
                self.connection = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting from SQLite",
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
            
            result = await loop.run_in_executor(
                None, self._execute_select_sync, query, params
            )
            
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="sqlite",
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
                database_type="sqlite",
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
            
            affected_rows = await loop.run_in_executor(
                None, self._execute_write_sync, query, params
            )
            
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="sqlite",
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
                database_type="sqlite",
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
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        
        result = await self.execute_query(query)
        
        if result.success and result.data:
            return [row['name'] for row in result.data]
        
        return []
    
    async def get_table_schema(self, table_name: str) -> TableInfo:
        """Получение схемы таблицы"""
        query = f"PRAGMA table_info({table_name})"
        
        result = await self.execute_query(query)
        
        if not result.success:
            raise ValueError(f"Error getting schema for table {table_name}: {result.error_message}")
        
        columns = []
        for row in result.data:
            columns.append({
                'name': row['name'],
                'type': row['type'],
                'nullable': row['notnull'] == 0,
                'default': row['dflt_value'],
                'pk': row['pk'] == 1
            })
        
        return TableInfo(
            name=table_name,
            columns=columns
        )
    
    async def test_connection(self) -> bool:
        """Тестирование подключения"""
        try:
            result = await self.execute_query("SELECT 1 as test")
            return result.success
        except Exception:
            return False
    
    def _execute_select_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Синхронное выполнение SELECT запроса"""
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            # Преобразуем Row объекты в словари
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
    
    def _execute_write_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Синхронное выполнение INSERT/UPDATE/DELETE запроса"""
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            self.connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()
