# database-mcp

**MCP-сервер, который даёт AI-ассистенту единый безопасный доступ к 7 СУБД: PostgreSQL, MySQL, ClickHouse, SQLite, MongoDB, Redis и Oracle.**

*MCP server (FastMCP) giving AI assistants one safe interface to PostgreSQL, MySQL, ClickHouse, SQLite, MongoDB, Redis and Oracle, with read-only by default and Docker container management.*

## Зачем

AI-ассистенту (Claude Code, Cursor) часто нужно заглянуть в базу: посмотреть схему, проверить данные, построить запрос. database-mcp даёт для этого одинаковые MCP-инструменты для любой СУБД и по умолчанию разрешает только чтение.

## Возможности

- **10 MCP-инструментов:** подключение и отключение, `SELECT`-запросы, запись, произвольный SQL, список таблиц и схема, запуск, остановка и статус Docker-контейнеров с БД.
- **7 коннекторов** с общим базовым интерфейсом: PostgreSQL, MySQL, ClickHouse, SQLite, MongoDB, Redis, Oracle.
- **Безопасность по умолчанию:** запись (`allow_write`) и произвольный SQL (`allow_raw_sql`) выключены и включаются явно для каждого подключения.
- **Docker-интеграция:** поднять нужную БД в контейнере прямо из ассистента.
- **Структурированные логи** (structlog), конфигурация через Pydantic.

## Стек

Python 3.10+ · FastMCP · SQLAlchemy 2 · Pydantic 2 · structlog · Docker SDK · psycopg2, PyMySQL, clickhouse-driver, pymongo, redis-py, cx_Oracle

## Быстрый старт

### Установка

```bash
pip install -r requirements.txt
```

### Конфигурация MCP

Добавьте в ваш `mcp.json`:

```json
{
  "mcpServers": {
    "database-mcp": {
      "command": "python",
      "args": ["-m", "database_mcp.server"],
      "env": {
        "DATABASE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Пример использования

```python
# Подключение к PostgreSQL
{
  "database_type": "postgresql",
  "connection": {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "pass"
  },
  "permissions": {
    "allow_write": false,
    "allow_raw_sql": false
  }
}
```

## Структура проекта

```
database-mcp/
├── src/database_mcp/          # Основной код
│   ├── connectors/            # Коннекторы для БД
│   ├── tools/                # MCP-инструменты (query, metadata, management, docker)
│   └── utils/                # Утилиты
├── tests/                    # Тесты
├── examples/                 # Примеры использования
└── docs/                     # Документация
```

## Разработка

```bash
# Установка зависимостей для разработки
pip install -e ".[dev]"

# Запуск тестов
pytest

# Форматирование кода
black src tests

# Проверка типов
mypy src
```

## Лицензия

MIT License
