# Database MCP

🚀 MCP сервис для работы с различными базами данных

## Описание

Database MCP предоставляет унифицированный интерфейс для подключения и работы с различными базами данных через Model Context Protocol (MCP). Поддерживает PostgreSQL, MySQL, ClickHouse, SQLite, MongoDB, Redis и Oracle.

## Основные возможности

- **Множественные БД**: PostgreSQL, MySQL, ClickHouse, SQLite, MongoDB, Redis, Oracle
- **Гибкие подключения**: локальные, Docker, удаленные, облачные
- **Безопасность**: система разрешений, защита от SQL injection
- **Docker интеграция**: автоматическое управление контейнерами
- **Мониторинг**: детальное логирование и метрики

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
│   ├── docker/               # Docker интеграция
│   ├── security/             # Система безопасности
│   ├── tools/                # MCP инструменты
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
