"""
Инструменты управления подключениями к базам данных
"""

from typing import Dict, Any, Optional
import uuid

from ..connectors import (
    PostgreSQLConnector,
    MySQLConnector,
    ClickHouseConnector,
    SQLiteConnector,
    MongoDBConnector,
    RedisConnector,
    OracleConnector,
    connection_manager
)
from ..utils.config import DatabaseConnection, DatabaseType
from ..utils.logging import DatabaseLogger


class ManagementTool:
    """Инструменты для управления подключениями к БД"""
    
    def __init__(self):
        self.logger = DatabaseLogger()
    
    async def connect_database(
        self,
        database_type: str,
        host: str,
        database: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        port: Optional[int] = None,
        schema: Optional[str] = None,
        charset: Optional[str] = None,
        ssl_mode: Optional[str] = None,
        connection_timeout: int = 30,
        allow_write: bool = False,
        allow_ddl: bool = False,
        allow_raw_sql: bool = False,
        max_query_time: int = 30,
        max_result_rows: int = 1000,
        connection_type: str = "local",
        container_name: Optional[str] = None,
        docker_image: Optional[str] = None,
        docker_ports: Optional[Dict[str, str]] = None,
        docker_volumes: Optional[list] = None,
        docker_env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Подключение к базе данных
        
        Args:
            database_type: Тип БД (postgresql, mysql, clickhouse, sqlite, mongodb, redis, oracle)
            host: Хост БД
            database: Имя базы данных
            username: Имя пользователя
            password: Пароль
            port: Порт БД
            schema: Схема (для PostgreSQL)
            charset: Кодировка (для MySQL)
            ssl_mode: Режим SSL
            connection_timeout: Таймаут подключения
            allow_write: Разрешить операции записи
            allow_ddl: Разрешить DDL операции
            allow_raw_sql: Разрешить произвольные SQL
            max_query_time: Максимальное время выполнения запроса
            max_result_rows: Максимальное количество строк в результате
            connection_type: Тип подключения (local, docker, remote, cloud)
            container_name: Имя Docker контейнера
            docker_image: Docker образ
            docker_ports: Маппинг портов Docker
            docker_volumes: Volumes Docker
            docker_env: Переменные окружения Docker
        
        Returns:
            Результат подключения с connection_id
        """
        
        try:
            # Создание конфигурации подключения
            config = DatabaseConnection(
                database_type=DatabaseType(database_type),
                connection_type=connection_type,
                host=host,
                port=port,
                database=database,
                username=username,
                password=password,
                schema=schema,
                charset=charset,
                ssl_mode=ssl_mode,
                connection_timeout=connection_timeout,
                container_name=container_name,
                docker_image=docker_image,
                docker_ports=docker_ports,
                docker_volumes=docker_volumes,
                docker_env=docker_env,
                permissions={
                    'allow_write': allow_write,
                    'allow_ddl': allow_ddl,
                    'allow_raw_sql': allow_raw_sql,
                    'max_query_time': max_query_time,
                    'max_result_rows': max_result_rows
                }
            )
            
            # Создание коннектора в зависимости от типа БД
            connector = self._create_connector(config)
            
            # Попытка подключения
            success = await connector.connect()
            
            if not success:
                return {
                    "success": False,
                    "error": "Failed to connect to database",
                    "connection_id": None
                }
            
            # Генерация уникального ID подключения
            connection_id = f"{database_type}_{uuid.uuid4().hex[:8]}"
            
            # Добавление подключения в менеджер
            await connection_manager.add_connection(connection_id, connector)
            
            self.logger.log_connection(
                database_type=database_type,
                host=host,
                database=database,
                success=True
            )
            
            return {
                "success": True,
                "connection_id": connection_id,
                "database_type": database_type,
                "host": host,
                "database": database,
                "is_connected": True
            }
            
        except Exception as e:
            self.logger.log_connection(
                database_type=database_type,
                host=host,
                database=database,
                success=False,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "connection_id": None
            }
    
    async def disconnect_database(self, connection_id: str) -> Dict[str, Any]:
        """
        Отключение от базы данных
        
        Args:
            connection_id: ID подключения для отключения
        
        Returns:
            Результат отключения
        """
        
        try:
            success = await connection_manager.remove_connection(connection_id)
            
            if success:
                self.logger.logger.info(
                    "Database disconnected",
                    connection_id=connection_id
                )
                
                return {
                    "success": True,
                    "message": f"Disconnected from {connection_id}",
                    "connection_id": connection_id
                }
            else:
                return {
                    "success": False,
                    "error": f"Connection {connection_id} not found",
                    "connection_id": connection_id
                }
                
        except Exception as e:
            self.logger.logger.error(
                "Error disconnecting database",
                connection_id=connection_id,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "connection_id": connection_id
            }
    
    async def list_connections(self) -> Dict[str, Any]:
        """
        Получение списка всех подключений
        
        Returns:
            Список активных подключений
        """
        
        try:
            connections = await connection_manager.list_connections()
            
            return {
                "success": True,
                "connections": connections,
                "total_count": len(connections)
            }
            
        except Exception as e:
            self.logger.logger.error(
                "Error listing connections",
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "connections": []
            }
    
    def _create_connector(self, config: DatabaseConnection):
        """Создание коннектора в зависимости от типа БД"""
        
        db_type = config.database_type
        
        if db_type == DatabaseType.POSTGRESQL:
            return PostgreSQLConnector(config)
        elif db_type == DatabaseType.MYSQL:
            return MySQLConnector(config)
        elif db_type == DatabaseType.CLICKHOUSE:
            return ClickHouseConnector(config)
        elif db_type == DatabaseType.SQLITE:
            return SQLiteConnector(config)
        elif db_type == DatabaseType.MONGODB:
            return MongoDBConnector(config)
        elif db_type == DatabaseType.REDIS:
            return RedisConnector(config)
        elif db_type == DatabaseType.ORACLE:
            return OracleConnector(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
