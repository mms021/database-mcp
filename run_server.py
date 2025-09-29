#!/usr/bin/env python3
"""
Скрипт для запуска Database MCP сервера
"""

import sys
import os

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database_mcp.server import main

if __name__ == "__main__":
    main()
