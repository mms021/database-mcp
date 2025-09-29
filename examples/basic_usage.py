"""
Примеры использования Database MCP
"""

import asyncio
import json
from src.database_mcp.tools.management import ManagementTool
from src.database_mcp.tools.query import QueryTool
from src.database_mcp.tools.metadata import MetadataTool
from src.database_mcp.tools.docker_tools import DockerTool


async def example_postgresql_connection():
    """Пример подключения к PostgreSQL"""
    print("=== PostgreSQL Connection Example ===")
    
    management = ManagementTool()
    
    # Подключение к PostgreSQL
    result = await management.connect_database(
        database_type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        username="postgres",
        password="password",
        allow_write=True,
        allow_raw_sql=True
    )
    
    print(f"Connection result: {json.dumps(result, indent=2)}")
    
    if result["success"]:
        connection_id = result["connection_id"]
        
        # Получение списка таблиц
        metadata = MetadataTool()
        tables_result = await metadata.get_tables(connection_id)
        print(f"\nTables: {json.dumps(tables_result, indent=2)}")
        
        # Выполнение запроса
        query = QueryTool()
        if tables_result["success"] and tables_result["tables"]:
            table_name = tables_result["tables"][0]
            query_result = await query.execute_select(
                connection_id,
                f"SELECT * FROM {table_name} LIMIT 5"
            )
            print(f"\nQuery result: {json.dumps(query_result, indent=2)}")
        
        # Отключение
        disconnect_result = await management.disconnect_database(connection_id)
        print(f"\nDisconnect result: {json.dumps(disconnect_result, indent=2)}")


async def example_docker_postgresql():
    """Пример запуска PostgreSQL в Docker"""
    print("\n=== Docker PostgreSQL Example ===")
    
    docker_tool = DockerTool()
    
    # Запуск PostgreSQL контейнера
    start_result = await docker_tool.start_container(
        database_type="postgresql",
        container_name="test_postgres",
        port=5433,
        volume_name="postgres_test_data",
        environment={
            "POSTGRES_DB": "testdb",
            "POSTGRES_USER": "testuser",
            "POSTGRES_PASSWORD": "testpass"
        }
    )
    
    print(f"Start container result: {json.dumps(start_result, indent=2)}")
    
    if start_result["success"]:
        # Проверка статуса
        status_result = await docker_tool.get_container_status("test_postgres")
        print(f"\nContainer status: {json.dumps(status_result, indent=2)}")
        
        # Подключение к контейнеру
        management = ManagementTool()
        connection_result = await management.connect_database(
            database_type="postgresql",
            host="localhost",
            port=5433,
            database="testdb",
            username="testuser",
            password="testpass",
            connection_type="docker"
        )
        
        print(f"\nConnection to Docker container: {json.dumps(connection_result, indent=2)}")
        
        # Остановка контейнера
        stop_result = await docker_tool.stop_container("test_postgres")
        print(f"\nStop container result: {json.dumps(stop_result, indent=2)}")


async def example_sqlite_usage():
    """Пример использования SQLite"""
    print("\n=== SQLite Usage Example ===")
    
    management = ManagementTool()
    
    # Подключение к SQLite
    result = await management.connect_database(
        database_type="sqlite",
        host="local",
        database=":memory:",  # В памяти для примера
        allow_write=True,
        allow_raw_sql=True
    )
    
    print(f"SQLite connection result: {json.dumps(result, indent=2)}")
    
    if result["success"]:
        connection_id = result["connection_id"]
        
        # Создание тестовой таблицы
        query = QueryTool()
        create_result = await query.execute_raw_sql(
            connection_id,
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
        )
        print(f"\nCreate table result: {json.dumps(create_result, indent=2)}")
        
        # Вставка данных
        insert_result = await query.execute_write(
            connection_id,
            "INSERT INTO users (name, email) VALUES (?, ?)",
            {"name": "John Doe", "email": "john@example.com"}
        )
        print(f"\nInsert result: {json.dumps(insert_result, indent=2)}")
        
        # Получение данных
        select_result = await query.execute_select(
            connection_id,
            "SELECT * FROM users"
        )
        print(f"\nSelect result: {json.dumps(select_result, indent=2)}")
        
        # Получение схемы таблицы
        metadata = MetadataTool()
        schema_result = await metadata.get_schema(connection_id, "users")
        print(f"\nTable schema: {json.dumps(schema_result, indent=2)}")


async def main():
    """Основная функция с примерами"""
    try:
        # Запуск примеров
        await example_postgresql_connection()
        await example_docker_postgresql()
        await example_sqlite_usage()
        
        print("\n=== All examples completed successfully! ===")
        
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())
