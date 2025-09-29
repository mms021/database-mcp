"""
Database MCP - MCP сервис для работы с базами данных

Предоставляет унифицированный интерфейс для подключения и работы 
с различными базами данных через Model Context Protocol.
"""

__version__ = "0.1.0"
__author__ = "Database MCP Team"

from .server import create_mcp_server

__all__ = ["create_mcp_server"]
