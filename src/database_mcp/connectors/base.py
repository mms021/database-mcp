"""
Базовый класс для коннекторов к базам данных
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

from ..utils.config import DatabaseConnection, DatabaseType, QueryResult, TableInfo
from ..utils.logging import DatabaseLogger


class BaseConnector(ABC):
    """Базовый класс для всех коннекторов к базам данных"""
    
    def __init__(self, connection_config: DatabaseConnection):
        self.config = connection_config
        self.logger = DatabaseLogger()
        self._connection = None
        self._is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Подключение к базе данных"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Отключение от базы данных"""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Выполнение SELECT запроса"""
        pass
    
    @abstractmethod
    async def execute_write(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Выполнение INSERT/UPDATE/DELETE запроса"""
        pass
    
    @abstractmethod
    async def get_tables(self) -> List[str]:
        """Получение списка таблиц"""
        pass
    
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> TableInfo:
        """Получение схемы таблицы"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Тестирование подключения"""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Проверка статуса подключения"""
        return self._is_connected
    
    @property
    def connection_id(self) -> str:
        """Уникальный идентификатор подключения"""
        return f"{self.config.database_type}_{self.config.host}_{self.config.database}"


class ConnectionManager:
    """Менеджер для управления подключениями к базам данных"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections: Dict[str, BaseConnector] = {}
        self.logger = DatabaseLogger()
        self._lock = asyncio.Lock()
    
    async def add_connection(self, connection_id: str, connector: BaseConnector) -> bool:
        """Добавление нового подключения"""
        async with self._lock:
            if len(self.connections) >= self.max_connections:
                self.logger.logger.warning(
                    "Maximum connections reached",
                    current_count=len(self.connections),
                    max_connections=self.max_connections
                )
                return False
            
            if connection_id in self.connections:
                self.logger.logger.warning(
                    "Connection already exists",
                    connection_id=connection_id
                )
                return False
            
            self.connections[connection_id] = connector
            self.logger.logger.info(
                "Connection added",
                connection_id=connection_id,
                database_type=connector.config.database_type
            )
            return True
    
    async def get_connection(self, connection_id: str) -> Optional[BaseConnector]:
        """Получение подключения по ID"""
        async with self._lock:
            return self.connections.get(connection_id)
    
    async def remove_connection(self, connection_id: str) -> bool:
        """Удаление подключения"""
        async with self._lock:
            if connection_id in self.connections:
                connector = self.connections[connection_id]
                if connector.is_connected:
                    await connector.disconnect()
                
                del self.connections[connection_id]
                self.logger.logger.info(
                    "Connection removed",
                    connection_id=connection_id
                )
                return True
            return False
    
    async def list_connections(self) -> List[Dict[str, Any]]:
        """Получение списка всех подключений"""
        async with self._lock:
            return [
                {
                    "id": conn_id,
                    "database_type": connector.config.database_type,
                    "host": connector.config.host,
                    "database": connector.config.database,
                    "is_connected": connector.is_connected,
                }
                for conn_id, connector in self.connections.items()
            ]
    
    async def close_all_connections(self):
        """Закрытие всех подключений"""
        async with self._lock:
            for connection_id, connector in self.connections.items():
                try:
                    if connector.is_connected:
                        await connector.disconnect()
                    self.logger.logger.info(
                        "Connection closed",
                        connection_id=connection_id
                    )
                except Exception as e:
                    self.logger.logger.error(
                        "Error closing connection",
                        connection_id=connection_id,
                        error=str(e)
                    )
            
            self.connections.clear()
    
    @asynccontextmanager
    async def get_connection_context(self, connection_id: str):
        """Контекстный менеджер для получения подключения"""
        connector = await self.get_connection(connection_id)
        if not connector:
            raise ValueError(f"Connection {connection_id} not found")
        
        if not connector.is_connected:
            await connector.connect()
        
        try:
            yield connector
        except Exception as e:
            self.logger.logger.error(
                "Error in connection context",
                connection_id=connection_id,
                error=str(e)
            )
            raise


# Глобальный менеджер подключений
connection_manager = ConnectionManager()
