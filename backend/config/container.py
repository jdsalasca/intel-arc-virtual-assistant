"""
Dependency Injection Container for Intel Virtual Assistant Backend
Manages service lifecycle and dependency wiring following SOLID principles.
"""

import logging
from typing import Dict, Any, Optional, TypeVar, Type
from dataclasses import dataclass

from ..config.settings import AppConfig, get_config
from ..interfaces.services import (
    IChatService, IModelService, IVoiceService, IToolService,
    IConversationService, IHardwareService, IHealthService
)
from ..interfaces.repositories import (
    IMessageRepository, IConversationRepository, IModelRepository
)
from ..interfaces.providers import (
    IModelProvider, IVoiceProvider, IToolProvider, IHardwareProvider
)

from ..services import (
    ChatService, ModelService, VoiceService, ToolService,
    ConversationService, HardwareService, HealthService
)
from ..repositories import (
    SQLiteMessageRepository, SQLiteConversationRepository, SQLiteModelRepository
)
from ..providers import (
    OpenVINOModelProvider, SpeechT5VoiceProvider, ToolProvider, IntelHardwareProvider
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ServiceRegistration:
    """Service registration information."""
    interface: Type
    implementation: Type
    singleton: bool = True
    factory: Optional[callable] = None


class DIContainer:
    """Dependency injection container."""
    
    def __init__(self, config: AppConfig):
        """Initialize DI container with configuration."""
        self._config = config
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._initialized = False
    
    def register(
        self, 
        interface: Type[T], 
        implementation: Type[T], 
        singleton: bool = True,
        factory: Optional[callable] = None
    ) -> None:
        """Register a service with the container."""
        self._registrations[interface] = ServiceRegistration(
            interface=interface,
            implementation=implementation,
            singleton=singleton,
            factory=factory
        )
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a pre-created instance."""
        self._instances[interface] = instance
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service from the container."""
        # Check if we have a pre-created instance
        if interface in self._instances:
            return self._instances[interface]
        
        # Check if we have a registration
        if interface not in self._registrations:
            raise ValueError(f"Service {interface.__name__} not registered")
        
        registration = self._registrations[interface]
        
        # Create instance
        if registration.factory:
            instance = registration.factory()
        else:
            instance = self._create_instance(registration.implementation)
        
        # Store instance if singleton
        if registration.singleton:
            self._instances[interface] = instance
        
        return instance
    
    def _create_instance(self, implementation_type: Type) -> Any:
        """Create an instance with dependency injection."""
        # Get constructor parameters
        import inspect
        signature = inspect.signature(implementation_type.__init__)
        parameters = {}
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            # Try to resolve the parameter type
            param_type = param.annotation
            if param_type != inspect.Parameter.empty:
                try:
                    parameters[param_name] = self.resolve(param_type)
                except ValueError:
                    # If we can't resolve, check if it has a default value
                    if param.default != inspect.Parameter.empty:
                        parameters[param_name] = param.default
                    else:
                        logger.warning(f"Could not resolve parameter {param_name} for {implementation_type.__name__}")
        
        return implementation_type(**parameters)
    
    def initialize(self) -> None:
        """Initialize the container with all service registrations."""
        if self._initialized:
            return
        
        logger.info("Initializing dependency injection container")
        
        # Register providers
        self._register_providers()
        
        # Register repositories
        self._register_repositories()
        
        # Register services
        self._register_services()
        
        self._initialized = True
        logger.info("Dependency injection container initialized")
    
    def _register_providers(self) -> None:
        """Register provider implementations."""
        # Model provider
        def create_model_provider() -> IModelProvider:
            provider = OpenVINOModelProvider(self._config.model.cache_dir)
            return provider
        
        self.register(
            IModelProvider, 
            OpenVINOModelProvider, 
            singleton=True,
            factory=create_model_provider
        )
        
        # Voice provider
        def create_voice_provider() -> IVoiceProvider:
            provider = SpeechT5VoiceProvider(
                f"{self._config.model.cache_dir}/voice"
            )
            return provider
        
        self.register(
            IVoiceProvider,
            SpeechT5VoiceProvider,
            singleton=True,
            factory=create_voice_provider
        )
        
        # Tool provider
        def create_tool_provider() -> IToolProvider:
            provider = ToolProvider({
                "web_search_api_key": self._config.tools.web_search_api_key,
                "gmail_credentials_path": self._config.tools.gmail_credentials_path
            })
            return provider
        
        self.register(
            IToolProvider,
            ToolProvider,
            singleton=True,
            factory=create_tool_provider
        )
        
        # Hardware provider
        self.register(
            IHardwareProvider,
            IntelHardwareProvider,
            singleton=True
        )
    
    def _register_repositories(self) -> None:
        """Register repository implementations."""
        # Message repository
        def create_message_repository() -> IMessageRepository:
            return SQLiteMessageRepository(self._config.database.url)
        
        self.register(
            IMessageRepository,
            SQLiteMessageRepository,
            singleton=True,
            factory=create_message_repository
        )
        
        # Conversation repository
        def create_conversation_repository() -> IConversationRepository:
            return SQLiteConversationRepository(self._config.database.url)
        
        self.register(
            IConversationRepository,
            SQLiteConversationRepository,
            singleton=True,
            factory=create_conversation_repository
        )
        
        # Model repository
        def create_model_repository() -> IModelRepository:
            return SQLiteModelRepository(self._config.database.url)
        
        self.register(
            IModelRepository,
            SQLiteModelRepository,
            singleton=True,
            factory=create_model_repository
        )
    
    def _register_services(self) -> None:
        """Register service implementations."""
        # Chat service
        self.register(IChatService, ChatService, singleton=True)
        
        # Model service
        self.register(IModelService, ModelService, singleton=True)
        
        # Voice service
        self.register(IVoiceService, VoiceService, singleton=True)
        
        # Tool service
        self.register(IToolService, ToolService, singleton=True)
        
        # Conversation service
        self.register(IConversationService, ConversationService, singleton=True)
        
        # Hardware service
        self.register(IHardwareService, HardwareService, singleton=True)
        
        # Health service
        self.register(IHealthService, HealthService, singleton=True)


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global DI container."""
    global _container
    
    if _container is None:
        config = get_config()
        _container = DIContainer(config)
        _container.initialize()
    
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = None


# Dependency functions for FastAPI
def get_chat_service() -> IChatService:
    """Get chat service instance."""
    return get_container().resolve(IChatService)


def get_model_service() -> IModelService:
    """Get model service instance."""
    return get_container().resolve(IModelService)


def get_voice_service() -> IVoiceService:
    """Get voice service instance."""
    return get_container().resolve(IVoiceService)


def get_tool_service() -> IToolService:
    """Get tool service instance."""
    return get_container().resolve(IToolService)


def get_conversation_service() -> IConversationService:
    """Get conversation service instance."""
    return get_container().resolve(IConversationService)


def get_hardware_service() -> IHardwareService:
    """Get hardware service instance."""
    return get_container().resolve(IHardwareService)


def get_health_service() -> IHealthService:
    """Get health service instance."""
    return get_container().resolve(IHealthService)


# Service initialization for application startup
async def initialize_services() -> None:
    """Initialize all services during application startup."""
    try:
        logger.info("Initializing application services")
        
        container = get_container()
        
        # Initialize providers
        model_provider = container.resolve(IModelProvider)
        if hasattr(model_provider, 'initialize'):
            await model_provider.initialize()
        
        voice_provider = container.resolve(IVoiceProvider)
        if hasattr(voice_provider, 'initialize'):
            await voice_provider.initialize()
        
        tool_provider = container.resolve(IToolProvider)
        if hasattr(tool_provider, 'initialize'):
            await tool_provider.initialize()
        
        # Initialize repositories (create tables if needed)
        message_repo = container.resolve(IMessageRepository)
        if hasattr(message_repo, 'initialize'):
            await message_repo.initialize()
        
        conversation_repo = container.resolve(IConversationRepository)
        if hasattr(conversation_repo, 'initialize'):
            await conversation_repo.initialize()
        
        model_repo = container.resolve(IModelRepository)
        if hasattr(model_repo, 'initialize'):
            await model_repo.initialize()
        
        logger.info("Application services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def shutdown_services() -> None:
    """Shutdown all services during application shutdown."""
    try:
        logger.info("Shutting down application services")
        
        container = get_container()
        
        # Shutdown services in reverse order
        for interface in [IHealthService, IHardwareService, IConversationService,
                         IToolService, IVoiceService, IModelService, IChatService]:
            try:
                service = container.resolve(interface)
                if hasattr(service, 'shutdown'):
                    await service.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down {interface.__name__}: {e}")
        
        # Shutdown providers
        for interface in [IToolProvider, IVoiceProvider, IModelProvider, IHardwareProvider]:
            try:
                provider = container.resolve(interface)
                if hasattr(provider, 'shutdown'):
                    await provider.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down {interface.__name__}: {e}")
        
        logger.info("Application services shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during service shutdown: {e}")


# Configuration for FastAPI dependency overrides (useful for testing)
def override_dependencies(app, **overrides):
    """Override dependencies in FastAPI app for testing."""
    dependency_map = {
        IChatService: get_chat_service,
        IModelService: get_model_service,
        IVoiceService: get_voice_service,
        IToolService: get_tool_service,
        IConversationService: get_conversation_service,
        IHardwareService: get_hardware_service,
        IHealthService: get_health_service,
    }
    
    for interface, override_instance in overrides.items():
        if interface in dependency_map:
            app.dependency_overrides[dependency_map[interface]] = lambda: override_instance