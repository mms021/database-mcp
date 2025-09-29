"""
Инструменты для работы с Docker контейнерами БД
"""

import asyncio
import time
from typing import Dict, Any, Optional, List

from ..utils.logging import DatabaseLogger


class DockerTool:
    """Инструменты для работы с Docker контейнерами БД"""
    
    def __init__(self):
        self.logger = DatabaseLogger()
        self.docker_client = None
        self._init_docker_client()
    
    def _init_docker_client(self):
        """Инициализация Docker клиента"""
        try:
            import docker
            self.docker_client = docker.from_env()
            self.logger.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    async def start_container(
        self,
        database_type: str,
        container_name: str,
        port: Optional[int] = None,
        volume_name: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        image: Optional[str] = None,
        init_script: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Запуск Docker контейнера с базой данных
        
        Args:
            database_type: Тип БД (postgresql, mysql, clickhouse, mongodb, redis)
            container_name: Имя контейнера
            port: Порт для маппинга
            volume_name: Имя volume для данных
            environment: Переменные окружения
            image: Docker образ (опционально)
            init_script: Скрипт инициализации (опционально)
        
        Returns:
            Результат запуска контейнера
        """
        
        if not self.docker_client:
            return {
                "success": False,
                "error": "Docker client not available. Make sure Docker is running and accessible."
            }
        
        try:
            # Определение Docker образа и конфигурации по умолчанию
            config = self._get_default_config(database_type, image)
            
            # Настройка портов
            ports = {}
            if port:
                ports[config["default_port"]] = port
            
            # Настройка volumes
            volumes = []
            if volume_name:
                volumes.append(f"{volume_name}:/var/lib/{database_type}")
            
            # Настройка переменных окружения
            env_vars = config.get("environment", {})
            if environment:
                env_vars.update(environment)
            
            # Проверка существования контейнера
            try:
                existing_container = self.docker_client.containers.get(container_name)
                if existing_container.status == "running":
                    return {
                        "success": True,
                        "message": f"Container {container_name} is already running",
                        "container_name": container_name,
                        "status": "running",
                        "port": port
                    }
                elif existing_container.status == "exited":
                    # Перезапуск существующего контейнера
                    existing_container.start()
                    
                    self.logger.log_docker_operation(
                        operation="start_existing",
                        container_name=container_name,
                        success=True
                    )
                    
                    return {
                        "success": True,
                        "message": f"Restarted existing container {container_name}",
                        "container_name": container_name,
                        "status": "running",
                        "port": port
                    }
            except:
                pass  # Контейнер не существует, создаем новый
            
            # Создание нового контейнера
            container = self.docker_client.containers.run(
                config["image"],
                name=container_name,
                ports=ports,
                volumes=volumes,
                environment=env_vars,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            # Ожидание запуска контейнера
            await asyncio.sleep(5)
            
            # Проверка статуса
            container.reload()
            
            if container.status == "running":
                self.logger.log_docker_operation(
                    operation="start_new",
                    container_name=container_name,
                    success=True
                )
                
                return {
                    "success": True,
                    "message": f"Successfully started container {container_name}",
                    "container_name": container_name,
                    "status": "running",
                    "port": port,
                    "image": config["image"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Container {container_name} failed to start",
                    "container_name": container_name,
                    "status": container.status
                }
                
        except Exception as e:
            self.logger.log_docker_operation(
                operation="start",
                container_name=container_name,
                success=False,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "container_name": container_name
            }
    
    async def stop_container(self, container_name: str) -> Dict[str, Any]:
        """
        Остановка Docker контейнера
        
        Args:
            container_name: Имя контейнера для остановки
        
        Returns:
            Результат остановки контейнера
        """
        
        if not self.docker_client:
            return {
                "success": False,
                "error": "Docker client not available"
            }
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            if container.status == "running":
                container.stop()
                
                self.logger.log_docker_operation(
                    operation="stop",
                    container_name=container_name,
                    success=True
                )
                
                return {
                    "success": True,
                    "message": f"Successfully stopped container {container_name}",
                    "container_name": container_name,
                    "status": "stopped"
                }
            else:
                return {
                    "success": True,
                    "message": f"Container {container_name} is already stopped",
                    "container_name": container_name,
                    "status": container.status
                }
                
        except Exception as e:
            self.logger.log_docker_operation(
                operation="stop",
                container_name=container_name,
                success=False,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "container_name": container_name
            }
    
    async def get_container_status(self, container_name: str) -> Dict[str, Any]:
        """
        Получение статуса Docker контейнера
        
        Args:
            container_name: Имя контейнера
        
        Returns:
            Статус контейнера
        """
        
        if not self.docker_client:
            return {
                "success": False,
                "error": "Docker client not available"
            }
        
        try:
            container = self.docker_client.containers.get(container_name)
            container.reload()
            
            # Получение дополнительной информации
            ports = container.ports
            image = container.image.tags[0] if container.image.tags else container.image.id
            
            return {
                "success": True,
                "container_name": container_name,
                "status": container.status,
                "image": image,
                "ports": ports,
                "created": container.attrs["Created"],
                "state": {
                    "running": container.status == "running",
                    "paused": container.status == "paused",
                    "restarting": container.status == "restarting",
                    "dead": container.status == "dead"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "container_name": container_name
            }
    
    async def list_containers(self, database_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение списка Docker контейнеров
        
        Args:
            database_type: Фильтр по типу БД (опционально)
        
        Returns:
            Список контейнеров
        """
        
        if not self.docker_client:
            return {
                "success": False,
                "error": "Docker client not available",
                "containers": []
            }
        
        try:
            containers = self.docker_client.containers.list(all=True)
            
            db_containers = []
            for container in containers:
                # Фильтрация по типу БД если указан
                if database_type:
                    image_tags = container.image.tags
                    if not any(database_type in tag.lower() for tag in image_tags):
                        continue
                
                container_info = {
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else container.image.id,
                    "ports": container.ports,
                    "created": container.attrs["Created"]
                }
                
                db_containers.append(container_info)
            
            return {
                "success": True,
                "containers": db_containers,
                "count": len(db_containers)
            }
            
        except Exception as e:
            self.logger.logger.error(
                "Error listing Docker containers",
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "containers": []
            }
    
    def _get_default_config(self, database_type: str, custom_image: Optional[str] = None) -> Dict[str, Any]:
        """Получение конфигурации по умолчанию для типа БД"""
        
        configs = {
            "postgresql": {
                "image": custom_image or "postgres:15",
                "default_port": 5432,
                "environment": {
                    "POSTGRES_DB": "testdb",
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "password"
                }
            },
            "mysql": {
                "image": custom_image or "mysql:8.0",
                "default_port": 3306,
                "environment": {
                    "MYSQL_ROOT_PASSWORD": "password",
                    "MYSQL_DATABASE": "testdb"
                }
            },
            "clickhouse": {
                "image": custom_image or "clickhouse/clickhouse-server:latest",
                "default_port": 9000,
                "environment": {}
            },
            "mongodb": {
                "image": custom_image or "mongo:7",
                "default_port": 27017,
                "environment": {
                    "MONGO_INITDB_ROOT_USERNAME": "admin",
                    "MONGO_INITDB_ROOT_PASSWORD": "password"
                }
            },
            "redis": {
                "image": custom_image or "redis:7-alpine",
                "default_port": 6379,
                "environment": {}
            }
        }
        
        return configs.get(database_type, {
            "image": custom_image or "postgres:15",
            "default_port": 5432,
            "environment": {}
        })
