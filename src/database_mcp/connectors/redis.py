"""
Коннектор для Redis
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from ..utils.config import DatabaseType, QueryResult, TableInfo


class RedisConnector(BaseConnector):
    """Коннектор для Redis"""
    
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.redis_client = None
    
    async def connect(self) -> bool:
        """Подключение к Redis"""
        try:
            # Импорт redis только при необходимости
            import redis
            
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=0,  # Redis использует числовые БД
                socket_timeout=self.config.connection_timeout,
                socket_connect_timeout=self.config.connection_timeout
            )
            
            # Тестируем подключение
            self.redis_client.ping()
            self._is_connected = True
            
            self.logger.log_connection(
                database_type="redis",
                host=self.config.host,
                database="redis",
                success=True
            )
            
            return True
            
        except Exception as e:
            self.logger.log_connection(
                database_type="redis",
                host=self.config.host,
                database="redis",
                success=False,
                error=str(e)
            )
            return False
    
    async def disconnect(self) -> bool:
        """Отключение от Redis"""
        try:
            if self.redis_client:
                self.redis_client.close()
                self.redis_client = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting from Redis",
                error=str(e)
            )
            return False
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Выполнение запроса к Redis"""
        if not self._is_connected:
            return QueryResult(
                success=False,
                error_message="Not connected to database"
            )
        
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            
            result = await loop.run_in_executor(
                None, self._execute_redis_command, query, params
            )
            
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="redis",
                execution_time=execution_time,
                success=True,
                row_count=len(result) if isinstance(result, list) else 1
            )
            
            return QueryResult(
                success=True,
                data=result,
                columns=["key", "value", "type"],
                row_count=len(result) if isinstance(result, list) else 1,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.log_query(
                query=query,
                database_type="redis",
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
        """Выполнение операций записи в Redis"""
        # TODO: Реализовать операции записи для Redis
        return QueryResult(
            success=False,
            error_message="Redis write operations not implemented yet"
        )
    
    async def get_tables(self) -> List[str]:
        """Получение списка ключей (аналог таблиц в Redis)"""
        try:
            loop = asyncio.get_event_loop()
            keys = await loop.run_in_executor(
                None, self.redis_client.keys, "*"
            )
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys[:100]]  # Ограничиваем количество
        except Exception as e:
            self.logger.logger.error(f"Error getting Redis keys: {e}")
            return []
    
    async def get_table_schema(self, table_name: str) -> TableInfo:
        """Получение информации о ключе Redis"""
        try:
            loop = asyncio.get_event_loop()
            
            # Получаем тип ключа
            key_type = await loop.run_in_executor(
                None, self.redis_client.type, table_name
            )
            
            # Получаем TTL
            ttl = await loop.run_in_executor(
                None, self.redis_client.ttl, table_name
            )
            
            columns = [
                {
                    'name': 'key',
                    'type': 'string',
                    'nullable': False,
                    'description': 'Redis key name'
                },
                {
                    'name': 'type',
                    'type': key_type.decode('utf-8') if isinstance(key_type, bytes) else key_type,
                    'nullable': False,
                    'description': 'Redis data type'
                },
                {
                    'name': 'ttl',
                    'type': 'integer',
                    'nullable': True,
                    'description': 'Time to live in seconds (-1 if no expiration)',
                    'sample_value': str(ttl)
                }
            ]
            
            return TableInfo(
                name=table_name,
                columns=columns
            )
            
        except Exception as e:
            raise ValueError(f"Error getting schema for Redis key {table_name}: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Тестирование подключения"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
            return False
        except Exception:
            return False
    
    def _execute_redis_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Выполнение Redis команды"""
        if command.upper() == "KEYS":
            pattern = params.get('pattern', '*') if params else '*'
            keys = self.redis_client.keys(pattern)
            
            result = []
            for key in keys[:100]:  # Ограничиваем количество результатов
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                key_type = self.redis_client.type(key)
                ttl = self.redis_client.ttl(key)
                
                result.append({
                    'key': key_str,
                    'type': key_type.decode('utf-8') if isinstance(key_type, bytes) else key_type,
                    'ttl': ttl
                })
            
            return result
        
        elif command.upper() == "GET":
            if not params or 'key' not in params:
                raise ValueError("GET command requires 'key' parameter")
            
            key = params['key']
            value = self.redis_client.get(key)
            
            if value is None:
                return []
            
            return [{
                'key': key,
                'value': value.decode('utf-8') if isinstance(value, bytes) else str(value),
                'type': 'string'
            }]
        
        else:
            raise ValueError(f"Unsupported Redis command: {command}")
