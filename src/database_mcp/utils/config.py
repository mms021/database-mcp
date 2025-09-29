"""
Конфигурация и модели данных для Database MCP
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class DatabaseType(str, Enum):
    """Поддерживаемые типы баз данных"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    CLICKHOUSE = "clickhouse"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"
    ORACLE = "oracle"


class ConnectionType(str, Enum):
    """Типы подключения"""
    LOCAL = "local"
    DOCKER = "docker"
    REMOTE = "remote"
    CLOUD = "cloud"


class DatabasePermissions(BaseModel):
    """Права доступа к базе данных"""
    allow_write: bool = Field(default=False, description="Разрешить INSERT/UPDATE/DELETE")
    allow_ddl: bool = Field(default=False, description="Разрешить DDL операции")
    allow_raw_sql: bool = Field(default=False, description="Разрешить произвольные SQL")
    max_query_time: int = Field(default=30, description="Максимальное время выполнения запроса (сек)")
    max_result_rows: int = Field(default=1000, description="Максимальное количество строк в результате")


class DatabaseConnection(BaseModel):
    """Конфигурация подключения к базе данных"""
    database_type: DatabaseType
    connection_type: ConnectionType = ConnectionType.LOCAL
    
    # Основные параметры подключения
    host: Optional[str] = Field(default="localhost", description="Хост базы данных")
    port: Optional[int] = Field(default=None, description="Порт базы данных")
    database: str = Field(description="Имя базы данных")
    username: Optional[str] = Field(default=None, description="Имя пользователя")
    password: Optional[str] = Field(default=None, description="Пароль")
    
    # Дополнительные параметры
    schema: Optional[str] = Field(default=None, description="Схема (для PostgreSQL)")
    charset: Optional[str] = Field(default="utf8mb4", description="Кодировка (для MySQL)")
    ssl_mode: Optional[str] = Field(default=None, description="Режим SSL")
    connection_timeout: int = Field(default=30, description="Таймаут подключения (сек)")
    
    # Docker параметры
    container_name: Optional[str] = Field(default=None, description="Имя Docker контейнера")
    docker_image: Optional[str] = Field(default=None, description="Docker образ")
    docker_ports: Optional[Dict[str, str]] = Field(default=None, description="Маппинг портов")
    docker_volumes: Optional[List[str]] = Field(default=None, description="Volumes")
    docker_env: Optional[Dict[str, str]] = Field(default=None, description="Переменные окружения")
    
    # Права доступа
    permissions: DatabasePermissions = Field(default_factory=DatabasePermissions)
    
    @validator('port')
    def validate_port(cls, v, values):
        """Валидация порта в зависимости от типа БД"""
        if v is None and 'database_type' in values:
            db_type = values['database_type']
            default_ports = {
                DatabaseType.POSTGRESQL: 5432,
                DatabaseType.MYSQL: 3306,
                DatabaseType.CLICKHOUSE: 9000,
                DatabaseType.MONGODB: 27017,
                DatabaseType.REDIS: 6379,
                DatabaseType.ORACLE: 1521,
            }
            return default_ports.get(db_type, 5432)
        return v
    
    @validator('docker_image')
    def validate_docker_image(cls, v, values):
        """Валидация Docker образа в зависимости от типа БД"""
        if v is None and 'database_type' in values and values.get('connection_type') == ConnectionType.DOCKER:
            db_type = values['database_type']
            default_images = {
                DatabaseType.POSTGRESQL: "postgres:15",
                DatabaseType.MYSQL: "mysql:8.0",
                DatabaseType.CLICKHOUSE: "clickhouse/clickhouse-server:latest",
                DatabaseType.MONGODB: "mongo:7",
                DatabaseType.REDIS: "redis:7-alpine",
            }
            return default_images.get(db_type, "postgres:15")
        return v


class DatabaseConfig(BaseModel):
    """Основная конфигурация Database MCP"""
    
    # Настройки логирования
    log_level: str = Field(default="INFO", description="Уровень логирования")
    log_format: str = Field(default="json", description="Формат логов (json/text)")
    
    # Настройки подключений
    max_connections: int = Field(default=10, description="Максимальное количество подключений")
    connection_pool_timeout: int = Field(default=30, description="Таймаут пула подключений")
    
    # Docker настройки
    docker_network: str = Field(default="database_mcp_network", description="Docker сеть")
    docker_prefix: str = Field(default="database_mcp", description="Префикс для Docker контейнеров")
    
    # Безопасность
    enable_query_logging: bool = Field(default=True, description="Логирование запросов")
    enable_metrics: bool = Field(default=True, description="Включение метрик")
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Создание конфигурации из переменных окружения"""
        import os
        
        return cls(
            log_level=os.getenv("DATABASE_MCP_LOG_LEVEL", "INFO"),
            log_format=os.getenv("DATABASE_MCP_LOG_FORMAT", "json"),
            max_connections=int(os.getenv("DATABASE_MCP_MAX_CONNECTIONS", "10")),
            connection_pool_timeout=int(os.getenv("DATABASE_MCP_POOL_TIMEOUT", "30")),
            docker_network=os.getenv("DATABASE_MCP_DOCKER_NETWORK", "database_mcp_network"),
            docker_prefix=os.getenv("DATABASE_MCP_DOCKER_PREFIX", "database_mcp"),
            enable_query_logging=os.getenv("DATABASE_MCP_ENABLE_QUERY_LOGGING", "true").lower() == "true",
            enable_metrics=os.getenv("DATABASE_MCP_ENABLE_METRICS", "true").lower() == "true",
        )


class QueryResult(BaseModel):
    """Результат выполнения запроса"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: int = 0
    execution_time: float = 0.0
    error_message: Optional[str] = None


class TableInfo(BaseModel):
    """Информация о таблице"""
    name: str
    schema: Optional[str] = None
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]] = []
    constraints: List[Dict[str, Any]] = []
