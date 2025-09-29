"""
Коннектор для ClickHouse
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from ..utils.config import DatabaseType, QueryResult, TableInfo


class ClickHouseConnector(BaseConnector):
    """Коннектор для ClickHouse"""
    
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.connection = None
    
    async def connect(self) -> bool:
        """Подключение к ClickHouse"""
        try:
            # Импорт clickhouse-driver только при необходимости
            from clickhouse_driver import Client
            
            self.connection = Client(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                connect_timeout=self.config.connection_timeout
            )
            
            self._is_connected = True
            
            self.logger.log_connection(
                database_type="clickhouse",
                host=self.config.host,
                database=self.config.database,
                success=True
            )
            
            return True
            
        except Exception as e:
            self.logger.log_connection(
                database_type="clickhouse",
                host=self.config.host,
                database=self.config.database,
                success=False,
                error=str(e)
            )
            return False
    
    async def disconnect(self) -> bool:
        """Отключение от ClickHouse"""
        try:
            if self.connection:
                self.connection.disconnect()
                self.connection = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting from ClickHouse",
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
                database_type="clickhouse",
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
                database_type="clickhouse",
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
            
            result = await loop.run_in_executor(
                None, self._execute_write_sync, query, params
            )
            
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="clickhouse",
                execution_time=execution_time,
                success=True,
                row_count=result
            )
            
            return QueryResult(
                success=True,
                row_count=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="clickhouse",
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
        query = "SHOW TABLES"
        
        result = await self.execute_query(query)
        
        if result.success and result.data:
            return [list(row.values())[0] for row in result.data]
        
        return []
    
    async def get_table_schema(self, table_name: str) -> TableInfo:
        """Получение схемы таблицы"""
        query = f"DESCRIBE TABLE {table_name}"
        
        result = await self.execute_query(query)
        
        if not result.success:
            raise ValueError(f"Error getting schema for table {table_name}: {result.error_message}")
        
        columns = []
        for row in result.data:
            columns.append({
                'name': row['name'],
                'type': row['type'],
                'default_type': row.get('default_type', ''),
                'default_expression': row.get('default_expression', ''),
                'comment': row.get('comment', ''),
                'codec_expression': row.get('codec_expression', ''),
                'ttl_expression': row.get('ttl_expression', '')
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
        if params:
            result = self.connection.execute(query, params)
        else:
            result = self.connection.execute(query)
        
        # Получаем имена колонок
        columns = [desc[0] for desc in result.column_descriptions]
        
        # Преобразуем результат в список словарей
        return [dict(zip(columns, row)) for row in result.result_rows]
    
    def _execute_write_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Синхронное выполнение INSERT/UPDATE/DELETE запроса"""
        if params:
            result = self.connection.execute(query, params)
        else:
            result = self.connection.execute(query)
        
        return len(result.result_rows) if hasattr(result, 'result_rows') else 0
