"""
Настройка логирования для Database MCP
"""

import logging
import sys
from typing import Optional
import structlog
from .config import DatabaseConfig


def setup_logging(
    name: str,
    config: Optional[DatabaseConfig] = None
) -> logging.Logger:
    """
    Настройка структурированного логирования
    
    Args:
        name: Имя логгера
        config: Конфигурация (если None, создается из переменных окружения)
    
    Returns:
        Настроенный логгер
    """
    
    if config is None:
        config = DatabaseConfig.from_env()
    
    # Настройка structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if config.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Настройка стандартного logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level.upper()),
    )
    
    # Создание логгера
    logger = structlog.get_logger(name)
    
    return logger


class DatabaseLogger:
    """Специализированный логгер для операций с БД"""
    
    def __init__(self, logger_name: str = "database_mcp"):
        self.logger = setup_logging(logger_name)
    
    def log_connection(self, database_type: str, host: str, database: str, success: bool, error: Optional[str] = None):
        """Логирование подключения к БД"""
        self.logger.info(
            "Database connection",
            database_type=database_type,
            host=host,
            database=database,
            success=success,
            error=error
        )
    
    def log_query(
        self,
        query: str,
        database_type: str,
        execution_time: float,
        success: bool,
        row_count: int = 0,
        error: Optional[str] = None
    ):
        """Логирование выполнения запроса"""
        self.logger.info(
            "Database query executed",
            query=query[:200] + "..." if len(query) > 200 else query,  # Ограничиваем длину для безопасности
            database_type=database_type,
            execution_time=execution_time,
            success=success,
            row_count=row_count,
            error=error
        )
    
    def log_docker_operation(
        self,
        operation: str,
        container_name: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Логирование Docker операций"""
        self.logger.info(
            "Docker operation",
            operation=operation,
            container_name=container_name,
            success=success,
            error=error
        )
    
    def log_security_event(
        self,
        event_type: str,
        user_action: str,
        database_type: str,
        success: bool,
        details: Optional[str] = None
    ):
        """Логирование событий безопасности"""
        self.logger.warning(
            "Security event",
            event_type=event_type,
            user_action=user_action,
            database_type=database_type,
            success=success,
            details=details
        )
