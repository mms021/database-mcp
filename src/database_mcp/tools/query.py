"""
Инструменты для выполнения запросов к базам данных
"""

import time
from typing import Dict, Any, Optional, List

from ..connectors.connection_manager import connection_manager
from ..utils.logging import DatabaseLogger


class QueryTool:
    """Инструменты для выполнения запросов к БД"""
    
    def __init__(self):
        self.logger = DatabaseLogger()
    
    async def execute_select(
        self,
        connection_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Выполнение SELECT запроса
        
        Args:
            connection_id: ID подключения к БД
            query: SQL запрос
            params: Параметры запроса
            limit: Ограничение количества строк
        
        Returns:
            Результат выполнения запроса
        """
        
        try:
            # Получение подключения
            async with connection_manager.get_connection_context(connection_id) as connector:
                
                # Проверка ограничений
                if limit and limit > connector.config.permissions.max_result_rows:
                    return {
                        "success": False,
                        "error": f"Limit {limit} exceeds maximum allowed rows {connector.config.permissions.max_result_rows}"
                    }
                
                # Добавление LIMIT если указан
                if limit and "LIMIT" not in query.upper():
                    query = f"{query} LIMIT {limit}"
                
                # Выполнение запроса
                result = await connector.execute_query(query, params)
                
                if result.success:
                    return {
                        "success": True,
                        "data": result.data,
                        "columns": result.columns,
                        "row_count": result.row_count,
                        "execution_time": result.execution_time,
                        "query": query
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message,
                        "execution_time": result.execution_time,
                        "query": query
                    }
                
        except Exception as e:
            self.logger.logger.error(
                "Error executing SELECT query",
                connection_id=connection_id,
                query=query,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def execute_write(
        self,
        connection_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выполнение INSERT/UPDATE/DELETE запроса
        
        Args:
            connection_id: ID подключения к БД
            query: SQL запрос
            params: Параметры запроса
        
        Returns:
            Результат выполнения запроса
        """
        
        try:
            # Получение подключения
            async with connection_manager.get_connection_context(connection_id) as connector:
                
                # Проверка разрешений на запись
                if not connector.config.permissions.allow_write:
                    self.logger.log_security_event(
                        event_type="write_denied",
                        user_action="execute_write",
                        database_type=connector.config.database_type,
                        success=False,
                        details=f"Write operations not allowed for connection {connection_id}"
                    )
                    
                    return {
                        "success": False,
                        "error": "Write operations are not allowed for this connection"
                    }
                
                # Проверка типа запроса
                query_upper = query.upper().strip()
                if not any(query_upper.startswith(op) for op in ["INSERT", "UPDATE", "DELETE"]):
                    return {
                        "success": False,
                        "error": "Only INSERT, UPDATE, DELETE operations are allowed"
                    }
                
                # Выполнение запроса
                result = await connector.execute_write(query, params)
                
                if result.success:
                    return {
                        "success": True,
                        "affected_rows": result.row_count,
                        "execution_time": result.execution_time,
                        "query": query
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message,
                        "execution_time": result.execution_time,
                        "query": query
                    }
                
        except Exception as e:
            self.logger.logger.error(
                "Error executing write query",
                connection_id=connection_id,
                query=query,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def execute_raw_sql(
        self,
        connection_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выполнение произвольного SQL запроса
        
        Args:
            connection_id: ID подключения к БД
            query: SQL запрос
            params: Параметры запроса
        
        Returns:
            Результат выполнения запроса
        """
        
        try:
            # Получение подключения
            async with connection_manager.get_connection_context(connection_id) as connector:
                
                # Проверка разрешений на произвольные SQL
                if not connector.config.permissions.allow_raw_sql:
                    self.logger.log_security_event(
                        event_type="raw_sql_denied",
                        user_action="execute_raw_sql",
                        database_type=connector.config.database_type,
                        success=False,
                        details=f"Raw SQL operations not allowed for connection {connection_id}"
                    )
                    
                    return {
                        "success": False,
                        "error": "Raw SQL operations are not allowed for this connection"
                    }
                
                # Проверка времени выполнения
                start_time = time.time()
                
                # Определение типа запроса
                query_upper = query.upper().strip()
                is_select = query_upper.startswith("SELECT") or query_upper.startswith("WITH")
                is_write = any(query_upper.startswith(op) for op in ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"])
                
                # Выполнение запроса в зависимости от типа
                if is_select:
                    result = await connector.execute_query(query, params)
                elif is_write:
                    # Проверка дополнительных разрешений для DDL
                    if any(query_upper.startswith(op) for op in ["CREATE", "DROP", "ALTER"]) and not connector.config.permissions.allow_ddl:
                        return {
                            "success": False,
                            "error": "DDL operations are not allowed for this connection"
                        }
                    
                    result = await connector.execute_write(query, params)
                else:
                    return {
                        "success": False,
                        "error": "Unsupported SQL operation"
                    }
                
                # Проверка времени выполнения
                execution_time = time.time() - start_time
                if execution_time > connector.config.permissions.max_query_time:
                    self.logger.log_security_event(
                        event_type="query_timeout",
                        user_action="execute_raw_sql",
                        database_type=connector.config.database_type,
                        success=False,
                        details=f"Query execution time {execution_time}s exceeds limit {connector.config.permissions.max_query_time}s"
                    )
                
                if result.success:
                    response = {
                        "success": True,
                        "execution_time": result.execution_time,
                        "query": query
                    }
                    
                    if is_select:
                        response.update({
                            "data": result.data,
                            "columns": result.columns,
                            "row_count": result.row_count
                        })
                    else:
                        response["affected_rows"] = result.row_count
                    
                    return response
                else:
                    return {
                        "success": False,
                        "error": result.error_message,
                        "execution_time": result.execution_time,
                        "query": query
                    }
                
        except Exception as e:
            self.logger.logger.error(
                "Error executing raw SQL query",
                connection_id=connection_id,
                query=query,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
