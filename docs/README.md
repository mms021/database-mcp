# Database MCP - Документация

## Обзор

Database MCP - это MCP (Model Context Protocol) сервис для работы с различными базами данных. Он предоставляет унифицированный интерфейс для подключения и выполнения операций с PostgreSQL, MySQL, ClickHouse, SQLite, MongoDB, Redis и Oracle.

## Основные возможности

- **Поддержка множественных БД**: PostgreSQL, MySQL, ClickHouse, SQLite, MongoDB, Redis, Oracle
- **Гибкие подключения**: локальные, Docker, удаленные, облачные
- **Безопасность**: система разрешений, защита от SQL injection
- **Docker интеграция**: автоматическое управление контейнерами
- **Мониторинг**: детальное логирование и метрики

## Установка

### Требования

- Python 3.10+
- Docker (для Docker интеграции)
- Доступ к базам данных

### Установка зависимостей

```bash
pip install -r requirements.txt
```

## Конфигурация

### MCP конфигурация

Добавьте в ваш `mcp.json`:

```json
{
  "mcpServers": {
    "database-mcp": {
      "command": "python",
      "args": ["-m", "database_mcp.server"],
      "env": {
        "DATABASE_MCP_LOG_LEVEL": "INFO",
        "DATABASE_MCP_LOG_FORMAT": "json",
        "DATABASE_MCP_MAX_CONNECTIONS": "10",
        "DATABASE_MCP_DOCKER_NETWORK": "database_mcp_network"
      }
    }
  }
}
```

### Переменные окружения

- `DATABASE_MCP_LOG_LEVEL` - уровень логирования (DEBUG, INFO, WARNING, ERROR)
- `DATABASE_MCP_LOG_FORMAT` - формат логов (json, text)
- `DATABASE_MCP_MAX_CONNECTIONS` - максимальное количество подключений
- `DATABASE_MCP_DOCKER_NETWORK` - имя Docker сети
- `DATABASE_MCP_ENABLE_QUERY_LOGGING` - включить логирование запросов
- `DATABASE_MCP_ENABLE_METRICS` - включить метрики

## Использование

### Подключение к базе данных

```python
# PostgreSQL
{
  "database_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "pass",
  "permissions": {
    "allow_write": false,
    "allow_raw_sql": false
  }
}
```

### Выполнение запросов

```python
# SELECT запрос
{
  "connection_id": "postgres_connection_1",
  "query": "SELECT * FROM users LIMIT 10"
}
```

### Docker интеграция

```python
# Запуск PostgreSQL контейнера
{
  "database_type": "postgresql",
  "container_name": "test_postgres",
  "port": 5433,
  "environment": {
    "POSTGRES_DB": "testdb",
    "POSTGRES_USER": "testuser",
    "POSTGRES_PASSWORD": "testpass"
  }
}
```

## MCP Инструменты

### Управление подключениями

- `database_connect` - подключение к БД
- `database_disconnect` - отключение от БД
- `database_list_connections` - список подключений

### Выполнение запросов

- `database_query` - выполнение SELECT запросов
- `database_execute` - выполнение INSERT/UPDATE/DELETE
- `database_raw_sql` - выполнение произвольных SQL

### Метаданные

- `database_get_tables` - получение списка таблиц
- `database_get_schema` - получение схемы таблицы
- `database_get_info` - информация о БД

### Docker

- `database_docker_start` - запуск Docker контейнера
- `database_docker_stop` - остановка контейнера
- `database_docker_status` - статус контейнера

## Безопасность

### Система разрешений

```python
{
  "permissions": {
    "allow_write": false,      # Разрешить INSERT/UPDATE/DELETE
    "allow_ddl": false,        # Разрешить DDL операции
    "allow_raw_sql": false,    # Разрешить произвольные SQL
    "max_query_time": 30,      # Максимальное время выполнения
    "max_result_rows": 1000    # Максимальное количество строк
  }
}
```

### Защита от SQL injection

Все запросы используют параметризованные запросы для защиты от SQL injection.

## Примеры

См. папку `examples/` для подробных примеров использования.

## Разработка

### Запуск тестов

```bash
pytest tests/
```

### Форматирование кода

```bash
black src tests
```

### Проверка типов

```bash
mypy src
```

## Поддерживаемые базы данных

### PostgreSQL
- Версии: 12+
- Особенности: поддержка схем, SSL, расширенные типы данных

### MySQL
- Версии: 8.0+
- Особенности: поддержка charset, различные движки

### ClickHouse
- Версии: 22.0+
- Особенности: колоночное хранение, аналитические функции

### SQLite
- Версии: 3.30+
- Особенности: встроенная БД, файловое хранение

### MongoDB
- Версии: 4.4+
- Особенности: NoSQL, документная модель

### Redis
- Версии: 6.0+
- Особенности: in-memory, key-value хранилище

### Oracle
- Версии: 19c+
- Особенности: enterprise функции, PL/SQL

## Troubleshooting

### Проблемы с подключением

1. Проверьте доступность хоста и порта
2. Убедитесь в правильности учетных данных
3. Проверьте настройки файрвола

### Проблемы с Docker

1. Убедитесь, что Docker запущен
2. Проверьте права доступа к Docker socket
3. Убедитесь в доступности портов

### Проблемы с производительностью

1. Настройте лимиты запросов
2. Используйте индексы
3. Оптимизируйте запросы

## Лицензия

MIT License
