# Database MCP - Быстрый старт

## 🚀 Быстрая установка и запуск

### 1. Установка зависимостей

```bash
cd /Users/mm/Code/mcp/database-mcp
pip install -r requirements.txt
```

### 2. Настройка MCP в Cursor

Добавьте в ваш `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "database-mcp": {
      "command": "python",
      "args": ["/Users/mm/Code/mcp/database-mcp/run_server.py"],
      "env": {
        "DATABASE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 3. Перезапуск Cursor

Перезапустите Cursor для загрузки нового MCP сервера.

## 📊 Примеры использования

### Подключение к PostgreSQL

```python
# Используйте MCP инструмент: database_connect
{
  "database_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "testdb",
  "username": "postgres",
  "password": "password",
  "allow_write": true,
  "allow_raw_sql": true
}
```

### Запуск PostgreSQL в Docker

```python
# Используйте MCP инструмент: database_docker_start
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

### Выполнение запроса

```python
# Используйте MCP инструмент: database_query
{
  "connection_id": "postgresql_abc12345",
  "query": "SELECT * FROM users LIMIT 5"
}
```

## 🐳 Запуск тестовых БД через Docker

```bash
cd docker
docker-compose -f docker-compose.example.yml up -d postgres
```

Это запустит PostgreSQL с тестовыми данными на порту 5432.

## 🔧 Доступные MCP инструменты

1. **database_connect** - подключение к БД
2. **database_disconnect** - отключение от БД
3. **database_query** - выполнение SELECT запросов
4. **database_execute** - выполнение INSERT/UPDATE/DELETE
5. **database_raw_sql** - выполнение произвольных SQL
6. **database_get_tables** - получение списка таблиц
7. **database_get_schema** - получение схемы таблицы
8. **database_docker_start** - запуск Docker контейнера
9. **database_docker_stop** - остановка Docker контейнера
10. **database_docker_status** - статус Docker контейнера

## 🛡️ Безопасность

- Все запросы защищены от SQL injection
- Система разрешений для записи/DDL операций
- Логирование всех операций
- Ограничения на время выполнения и размер результатов

## 📝 Поддерживаемые БД

- ✅ PostgreSQL
- ✅ MySQL  
- ✅ ClickHouse
- ✅ SQLite
- ✅ MongoDB
- ✅ Redis
- ✅ Oracle

## 🐛 Troubleshooting

### Сервер не запускается
- Проверьте установку зависимостей: `pip install -r requirements.txt`
- Проверьте Python версию: `python --version` (должна быть 3.10+)

### Ошибки подключения к БД
- Проверьте доступность хоста и порта
- Убедитесь в правильности учетных данных
- Для Docker: убедитесь что Docker запущен

### MCP инструменты не видны в Cursor
- Перезапустите Cursor
- Проверьте конфигурацию в `~/.cursor/mcp.json`
- Проверьте логи MCP сервера

## 📚 Дополнительная документация

- [Полная документация](docs/README.md)
- [Технические требования](requirements.md)
- [Примеры использования](examples/basic_usage.py)

## 🎯 Что дальше?

1. Подключитесь к вашей БД
2. Изучите структуру таблиц
3. Выполните первые запросы
4. Настройте Docker контейнеры для тестирования
5. Изучите систему разрешений для безопасности
