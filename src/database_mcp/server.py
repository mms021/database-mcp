"""
Основной MCP сервер для работы с базами данных
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .tools.query import QueryTool
from .tools.metadata import MetadataTool
from .tools.management import ManagementTool
from .tools.docker_tools import DockerTool
from .utils.config import DatabaseConfig
from .utils.logging import setup_logging

logger = setup_logging(__name__)


def create_mcp_server() -> FastMCP:
    """Создает и настраивает MCP сервер для работы с базами данных"""
    
    mcp = FastMCP("Database MCP Server")
    
    # Инициализация инструментов
    query_tool = QueryTool()
    metadata_tool = MetadataTool()
    management_tool = ManagementTool()
    docker_tool = DockerTool()
    
    # Регистрация MCP инструментов
    mcp.tool("database_connect")(management_tool.connect_database)
    mcp.tool("database_disconnect")(management_tool.disconnect_database)
    mcp.tool("database_query")(query_tool.execute_select)
    mcp.tool("database_execute")(query_tool.execute_write)
    mcp.tool("database_raw_sql")(query_tool.execute_raw_sql)
    mcp.tool("database_get_tables")(metadata_tool.get_tables)
    mcp.tool("database_get_schema")(metadata_tool.get_schema)
    mcp.tool("database_docker_start")(docker_tool.start_container)
    mcp.tool("database_docker_stop")(docker_tool.stop_container)
    mcp.tool("database_docker_status")(docker_tool.get_container_status)
    
    logger.info("Database MCP Server initialized successfully")
    return mcp


def main():
    """Точка входа для запуска MCP сервера"""
    mcp = create_mcp_server()
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
