"""
Коннектор для MongoDB
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from ..utils.config import DatabaseType, QueryResult, TableInfo


class MongoDBConnector(BaseConnector):
    """Коннектор для MongoDB"""
    
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.client = None
        self.database = None
    
    async def connect(self) -> bool:
        """Подключение к MongoDB"""
        try:
            # Импорт pymongo только при необходимости
            from pymongo import MongoClient
            
            connection_string = self._build_connection_string()
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=self.config.connection_timeout * 1000)
            
            # Тестируем подключение
            self.client.server_info()
            
            self.database = self.client[self.config.database]
            self._is_connected = True
            
            self.logger.log_connection(
                database_type="mongodb",
                host=self.config.host,
                database=self.config.database,
                success=True
            )
            
            return True
            
        except Exception as e:
            self.logger.log_connection(
                database_type="mongodb",
                host=self.config.host,
                database=self.config.database,
                success=False,
                error=str(e)
            )
            return False
    
    async def disconnect(self) -> bool:
        """Отключение от MongoDB"""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.database = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting from MongoDB",
                error=str(e)
            )
            return False
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Выполнение SELECT запроса (find в MongoDB)"""
        if not self._is_connected:
            return QueryResult(
                success=False,
                error_message="Not connected to database"
            )
        
        start_time = time.time()
        
        try:
            # Для MongoDB query должен содержать collection и filter
            if not params or 'collection' not in params:
                return QueryResult(
                    success=False,
                    error_message="MongoDB queries require 'collection' parameter"
                )
            
            collection_name = params['collection']
            filter_query = params.get('filter', {})
            limit = params.get('limit', 1000)
            
            loop = asyncio.get_event_loop()
            
            result = await loop.run_in_executor(
                None, self._execute_find_sync, collection_name, filter_query, limit
            )
            
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=f"find({collection_name}, {filter_query})",
                database_type="mongodb",
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
                database_type="mongodb",
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
        # TODO: Реализовать операции записи для MongoDB
        return QueryResult(
            success=False,
            error_message="MongoDB write operations not implemented yet"
        )
    
    async def get_tables(self) -> List[str]:
        """Получение списка коллекций"""
        try:
            loop = asyncio.get_event_loop()
            collections = await loop.run_in_executor(
                None, self.database.list_collection_names
            )
            return collections
        except Exception as e:
            self.logger.logger.error(f"Error getting MongoDB collections: {e}")
            return []
    
    async def get_table_schema(self, table_name: str) -> TableInfo:
        """Получение схемы коллекции (примерная структура)"""
        try:
            collection = self.database[table_name]
            
            # Получаем один документ для анализа структуры
            sample_doc = collection.find_one()
            
            columns = []
            if sample_doc:
                for key, value in sample_doc.items():
                    columns.append({
                        'name': key,
                        'type': type(value).__name__,
                        'nullable': True,
                        'sample_value': str(value)[:100]  # Ограничиваем длину
                    })
            
            return TableInfo(
                name=table_name,
                columns=columns
            )
            
        except Exception as e:
            raise ValueError(f"Error getting schema for collection {table_name}: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Тестирование подключения"""
        try:
            if self.client:
                self.client.server_info()
                return True
            return False
        except Exception:
            return False
    
    def _build_connection_string(self) -> str:
        """Построение строки подключения MongoDB"""
        if self.config.username and self.config.password:
            auth = f"{self.config.username}:{self.config.password}@"
        else:
            auth = ""
        
        return f"mongodb://{auth}{self.config.host}:{self.config.port}/{self.config.database}"
    
    def _execute_find_sync(self, collection_name: str, filter_query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Синхронное выполнение find запроса"""
        collection = self.database[collection_name]
        cursor = collection.find(filter_query).limit(limit)
        
        # Преобразуем ObjectId в строки для JSON сериализации
        result = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            result.append(doc)
        
        return result
