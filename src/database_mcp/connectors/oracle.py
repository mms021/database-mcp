"""
Коннектор для Oracle
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from ..utils.config import DatabaseType, QueryResult, TableInfo


class OracleConnector(BaseConnector):
    """Коннектор для Oracle"""
    
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.connection = None
    
    async def connect(self) -> bool:
        """Подключение к Oracle"""
        try:
            # Импорт cx_Oracle только при необходимости
            import cx_Oracle
            
            # Построение DSN
            dsn = cx_Oracle.makedsn(
                self.config.host,
                self.config.port,
                service_name=self.config.database
            )
            
            self.connection = cx_Oracle.connect(
                user=self.config.username,
                password=self.config.password,
                dsn=dsn,
                encoding="UTF-8"
            )
            
            self._is_connected = True
            
            self.logger.log_connection(
                database_type="oracle",
                host=self.config.host,
                database=self.config.database,
                success=True
            )
            
            return True
            
        except Exception as e:
            self.logger.log_connection(
                database_type="oracle",
                host=self.config.host,
                database=self.config.database,
                success=False,
                error=str(e)
            )
            return False
    
    async def disconnect(self) -> bool:
        """Отключение от Oracle"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting from Oracle",
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
                database_type="oracle",
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
                database_type="oracle",
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
                database_type="oracle",
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
                database_type="oracle",
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
        FROM user_tables 
        ORDER BY table_name
        """
        
        result = await self.execute_query(query)
        
        if result.success and result.data:
            return [row['TABLE_NAME'] for row in result.data]
        
        return []
    
    async def get_table_schema(self, table_name: str) -> TableInfo:
        """Получение схемы таблицы"""
        query = """
        SELECT 
            column_name,
            data_type,
            data_length,
            data_precision,
            data_scale,
            nullable,
            data_default
        FROM user_tab_columns 
        WHERE table_name = UPPER(:table_name)
        ORDER BY column_id
        """
        
        result = await self.execute_query(query, {'table_name': table_name})
        
        if not result.success:
            raise ValueError(f"Error getting schema for table {table_name}: {result.error_message}")
        
        columns = []
        for row in result.data:
            columns.append({
                'name': row['COLUMN_NAME'],
                'type': row['DATA_TYPE'],
                'length': row['DATA_LENGTH'],
                'precision': row['DATA_PRECISION'],
                'scale': row['DATA_SCALE'],
                'nullable': row['NULLABLE'] == 'Y',
                'default': row['DATA_DEFAULT']
            })
        
        return TableInfo(
            name=table_name,
            columns=columns
        )
    
    async def test_connection(self) -> bool:
        """Тестирование подключения"""
        try:
            result = await self.execute_query("SELECT 1 as test FROM dual")
            return result.success
        except Exception:
            return False
    
    def _execute_select_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Синхронное выполнение SELECT запроса"""
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Получаем имена колонок
            columns = [desc[0] for desc in cursor.description]
            
            # Преобразуем результат в список словарей
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()
    
    def _execute_write_sync(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Синхронное выполнение INSERT/UPDATE/DELETE запроса"""
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()
