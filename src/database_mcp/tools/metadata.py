"""
Инструменты для получения метаданных баз данных
"""

from typing import Dict, Any, List

from ..connectors.connection_manager import connection_manager
from ..utils.logging import DatabaseLogger


class MetadataTool:
    """Инструменты для получения метаданных БД"""
    
    def __init__(self):
        self.logger = DatabaseLogger()
    
    async def get_tables(self, connection_id: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение списка таблиц
        
        Args:
            connection_id: ID подключения к БД
            schema: Имя схемы (для PostgreSQL)
        
        Returns:
            Список таблиц
        """
        
        try:
            # Получение подключения
            async with connection_manager.get_connection_context(connection_id) as connector:
                
                # Получение списка таблиц
                tables = await connector.get_tables()
                
                self.logger.logger.info(
                    "Tables retrieved",
                    connection_id=connection_id,
                    table_count=len(tables),
                    database_type=connector.config.database_type
                )
                
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables),
                    "database_type": connector.config.database_type,
                    "database": connector.config.database
                }
                
        except Exception as e:
            self.logger.logger.error(
                "Error getting tables",
                connection_id=connection_id,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "tables": []
            }
    
    async def get_schema(
        self,
        connection_id: str,
        table_name: str,
        include_indexes: bool = False,
        include_constraints: bool = False
    ) -> Dict[str, Any]:
        """
        Получение схемы таблицы
        
        Args:
            connection_id: ID подключения к БД
            table_name: Имя таблицы
            include_indexes: Включить информацию об индексах
            include_constraints: Включить информацию об ограничениях
        
        Returns:
            Схема таблицы
        """
        
        try:
            # Получение подключения
            async with connection_manager.get_connection_context(connection_id) as connector:
                
                # Получение схемы таблицы
                table_info = await connector.get_table_schema(table_name)
                
                self.logger.logger.info(
                    "Table schema retrieved",
                    connection_id=connection_id,
                    table_name=table_name,
                    column_count=len(table_info.columns),
                    database_type=connector.config.database_type
                )
                
                response = {
                    "success": True,
                    "table_name": table_info.name,
                    "schema": table_info.schema,
                    "columns": table_info.columns,
                    "column_count": len(table_info.columns),
                    "database_type": connector.config.database_type,
                    "database": connector.config.database
                }
                
                # Добавление индексов если запрошено
                if include_indexes and table_info.indexes:
                    response["indexes"] = table_info.indexes
                
                # Добавление ограничений если запрошено
                if include_constraints and table_info.constraints:
                    response["constraints"] = table_info.constraints
                
                return response
                
        except Exception as e:
            self.logger.logger.error(
                "Error getting table schema",
                connection_id=connection_id,
                table_name=table_name,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "table_name": table_name
            }
    
    async def get_database_info(self, connection_id: str) -> Dict[str, Any]:
        """
        Получение общей информации о базе данных
        
        Args:
            connection_id: ID подключения к БД
        
        Returns:
            Информация о базе данных
        """
        
        try:
            # Получение подключения
            async with connection_manager.get_connection_context(connection_id) as connector:
                
                # Тестирование подключения
                is_connected = await connector.test_connection()
                
                # Получение списка таблиц
                tables = await connector.get_tables()
                
                info = {
                    "success": True,
                    "connection_id": connection_id,
                    "database_type": connector.config.database_type,
                    "host": connector.config.host,
                    "port": connector.config.port,
                    "database": connector.config.database,
                    "is_connected": is_connected,
                    "table_count": len(tables),
                    "permissions": {
                        "allow_write": connector.config.permissions.allow_write,
                        "allow_ddl": connector.config.permissions.allow_ddl,
                        "allow_raw_sql": connector.config.permissions.allow_raw_sql,
                        "max_query_time": connector.config.permissions.max_query_time,
                        "max_result_rows": connector.config.permissions.max_result_rows
                    }
                }
                
                # Добавление специфичной для БД информации
                if connector.config.database_type in ["postgresql", "mysql"]:
                    info["schema"] = getattr(connector.config, 'schema', None)
                elif connector.config.database_type == "mysql":
                    info["charset"] = getattr(connector.config, 'charset', None)
                
                self.logger.logger.info(
                    "Database info retrieved",
                    connection_id=connection_id,
                    database_type=connector.config.database_type,
                    table_count=len(tables)
                )
                
                return info
                
        except Exception as e:
            self.logger.logger.error(
                "Error getting database info",
                connection_id=connection_id,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "connection_id": connection_id
            }
