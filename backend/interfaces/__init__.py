"""
Interfaces package for Intel Virtual Assistant Backend.
Contains all interface definitions following SOLID principles.
"""

from .repositories import (
    IMessageRepository,
    IConversationRepository,
    IModelRepository,
    IConfigRepository
)

from .services import (
    IChatService,
    IModelService,
    IVoiceService,
    IToolService,
    IHardwareService,
    IConversationService,
    IHealthService
)

from .providers import (
    IModelProvider,
    IVoiceProvider,
    IToolProvider,
    IHardwareProvider,
    IStorageProvider,
    ICacheProvider,
    IEventProvider
)

__all__ = [
    # Repository interfaces
    "IMessageRepository",
    "IConversationRepository",
    "IModelRepository",
    "IConfigRepository",
    
    # Service interfaces
    "IChatService",
    "IModelService",
    "IVoiceService",
    "IToolService",
    "IHardwareService",
    "IConversationService",
    "IHealthService",
    
    # Provider interfaces
    "IModelProvider",
    "IVoiceProvider",
    "IToolProvider",
    "IHardwareProvider",
    "IStorageProvider",
    "ICacheProvider",
    "IEventProvider"
]