"""
Базовые тесты для Database MCP
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.database_mcp.tools.management import ManagementTool
from src.database_mcp.tools.query import QueryTool
from src.database_mcp.tools.metadata import MetadataTool
from src.database_mcp.connectors.base import BaseConnector
from src.database_mcp.utils.config import DatabaseConnection, DatabaseType, ConnectionType


class TestManagementTool:
    """Тесты для ManagementTool"""
    
    @pytest.fixture
    def management_tool(self):
        return ManagementTool()
    
    @pytest.mark.asyncio
    async def test_create_postgres_connector(self, management_tool):
        """Тест создания PostgreSQL коннектора"""
        
        config = DatabaseConnection(
            database_type=DatabaseType.POSTGRESQL,
            connection_type=ConnectionType.LOCAL,
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass"
        )
        
        connector = management_tool._create_connector(config)
        
        assert connector is not None
        assert connector.config.database_type == DatabaseType.POSTGRESQL
        assert connector.config.host == "localhost"
        assert connector.config.database == "testdb"
    
    @pytest.mark.asyncio
    async def test_create_mysql_connector(self, management_tool):
        """Тест создания MySQL коннектора"""
        
        config = DatabaseConnection(
            database_type=DatabaseType.MYSQL,
            connection_type=ConnectionType.LOCAL,
            host="localhost",
            port=3306,
            database="testdb",
            username="testuser",
            password="testpass"
        )
        
        connector = management_tool._create_connector(config)
        
        assert connector is not None
        assert connector.config.database_type == DatabaseType.MYSQL
    
    def test_unsupported_database_type(self, management_tool):
        """Тест неподдерживаемого типа БД"""
        
        config = DatabaseConnection(
            database_type="unsupported_db",
            host="localhost",
            database="testdb"
        )
        
        with pytest.raises(ValueError, match="Unsupported database type"):
            management_tool._create_connector(config)


class TestQueryTool:
    """Тесты для QueryTool"""
    
    @pytest.fixture
    def query_tool(self):
        return QueryTool()
    
    @pytest.fixture
    def mock_connector(self):
        """Мок коннектора для тестов"""
        connector = Mock(spec=BaseConnector)
        connector.is_connected = True
        connector.config.permissions.allow_write = True
        connector.config.permissions.allow_raw_sql = True
        connector.config.permissions.max_result_rows = 1000
        connector.config.permissions.max_query_time = 30
        
        return connector
    
    @pytest.mark.asyncio
    async def test_execute_select_with_limit(self, query_tool, mock_connector):
        """Тест выполнения SELECT с лимитом"""
        
        # Мокируем результат запроса
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = [{"id": 1, "name": "test"}]
        mock_result.columns = ["id", "name"]
        mock_result.row_count = 1
        mock_result.execution_time = 0.1
        
        mock_connector.execute_query = AsyncMock(return_value=mock_result)
        
        # Мокируем connection manager
        with pytest.Mock.patch('src.database_mcp.tools.query.connection_manager') as mock_manager:
            mock_manager.get_connection_context.return_value.__aenter__.return_value = mock_connector
            
            result = await query_tool.execute_select(
                connection_id="test_conn",
                query="SELECT * FROM users",
                limit=50
            )
            
            assert result["success"] is True
            assert result["row_count"] == 1
            assert "LIMIT 50" in result["query"]
    
    @pytest.mark.asyncio
    async def test_execute_write_permission_check(self, query_tool, mock_connector):
        """Тест проверки разрешений для записи"""
        
        # Устанавливаем запрет на запись
        mock_connector.config.permissions.allow_write = False
        
        with pytest.Mock.patch('src.database_mcp.tools.query.connection_manager') as mock_manager:
            mock_manager.get_connection_context.return_value.__aenter__.return_value = mock_connector
            
            result = await query_tool.execute_write(
                connection_id="test_conn",
                query="INSERT INTO users (name) VALUES ('test')"
            )
            
            assert result["success"] is False
            assert "Write operations are not allowed" in result["error"]


class TestMetadataTool:
    """Тесты для MetadataTool"""
    
    @pytest.fixture
    def metadata_tool(self):
        return MetadataTool()
    
    @pytest.fixture
    def mock_connector(self):
        """Мок коннектора для тестов"""
        connector = Mock(spec=BaseConnector)
        connector.is_connected = True
        connector.config.database_type = DatabaseType.POSTGRESQL
        connector.config.database = "testdb"
        connector.config.host = "localhost"
        connector.config.port = 5432
        
        return connector
    
    @pytest.mark.asyncio
    async def test_get_tables(self, metadata_tool, mock_connector):
        """Тест получения списка таблиц"""
        
        mock_tables = ["users", "orders", "products"]
        mock_connector.get_tables = AsyncMock(return_value=mock_tables)
        
        with pytest.Mock.patch('src.database_mcp.tools.metadata.connection_manager') as mock_manager:
            mock_manager.get_connection_context.return_value.__aenter__.return_value = mock_connector
            
            result = await metadata_tool.get_tables("test_conn")
            
            assert result["success"] is True
            assert result["tables"] == mock_tables
            assert result["count"] == 3
            assert result["database_type"] == "postgresql"
    
    @pytest.mark.asyncio
    async def test_get_database_info(self, metadata_tool, mock_connector):
        """Тест получения информации о БД"""
        
        mock_connector.test_connection = AsyncMock(return_value=True)
        mock_connector.get_tables = AsyncMock(return_value=["table1", "table2"])
        
        with pytest.Mock.patch('src.database_mcp.tools.metadata.connection_manager') as mock_manager:
            mock_manager.get_connection_context.return_value.__aenter__.return_value = mock_connector
            
            result = await metadata_tool.get_database_info("test_conn")
            
            assert result["success"] is True
            assert result["connection_id"] == "test_conn"
            assert result["database_type"] == "postgresql"
            assert result["is_connected"] is True
            assert result["table_count"] == 2


class TestDatabaseConfig:
    """Тесты для конфигурации"""
    
    def test_database_connection_validation(self):
        """Тест валидации подключения к БД"""
        
        config = DatabaseConnection(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            database="testdb",
            username="testuser",
            password="testpass"
        )
        
        assert config.database_type == DatabaseType.POSTGRESQL
        assert config.port == 5432  # Значение по умолчанию
        assert config.connection_type == ConnectionType.LOCAL
        assert config.permissions.allow_write is False  # Значение по умолчанию
    
    def test_docker_config_validation(self):
        """Тест валидации Docker конфигурации"""
        
        config = DatabaseConnection(
            database_type=DatabaseType.POSTGRESQL,
            connection_type=ConnectionType.DOCKER,
            host="localhost",
            database="testdb"
        )
        
        assert config.docker_image == "postgres:15"  # Значение по умолчанию


if __name__ == "__main__":
    pytest.main([__file__])
