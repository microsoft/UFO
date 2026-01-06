# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Dependency Injection Container for Galaxy Framework

This module provides a lightweight dependency injection container to manage
component dependencies and improve testability.
"""

import inspect
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    get_type_hints,
)

from ..core.types import GalaxyFrameworkError

T = TypeVar("T")


class LifecycleScope(Enum):
    """Dependency lifecycle scopes."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DependencyInjectionError(GalaxyFrameworkError):
    """Exception raised for DI-related errors."""

    pass


class ServiceDescriptor:
    """Describes how a service should be constructed."""

    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
        scope: LifecycleScope = LifecycleScope.TRANSIENT,
    ):
        """
        Initialize service descriptor.

        :param service_type: The service interface type
        :param implementation_type: The concrete implementation type
        :param factory: Factory function to create instances
        :param instance: Pre-created instance (for singleton)
        :param scope: Lifecycle scope
        """
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.instance = instance
        self.scope = scope

        # Validation
        if not any([implementation_type, factory, instance]):
            raise DependencyInjectionError(
                f"Service {service_type.__name__} must have either implementation_type, factory, or instance"
            )


class IDependencyContainer(ABC):
    """Interface for dependency injection container."""

    @abstractmethod
    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
    ) -> None:
        """
        Register a service as singleton.

        :param service_type: Service interface type
        :param implementation_type: Implementation type
        :param factory: Factory function
        :param instance: Pre-created instance
        """
        pass

    @abstractmethod
    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
    ) -> None:
        """
        Register a service as transient.

        :param service_type: Service interface type
        :param implementation_type: Implementation type
        :param factory: Factory function
        """
        pass

    @abstractmethod
    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
    ) -> None:
        """
        Register a service as scoped.

        :param service_type: Service interface type
        :param implementation_type: Implementation type
        :param factory: Factory function
        """
        pass

    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.

        :param service_type: Service type to resolve
        :return: Service instance
        """
        pass

    @abstractmethod
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service instance.

        :param service_type: Service type to resolve
        :return: Service instance or None if not found
        """
        pass


class DependencyContainer(IDependencyContainer):
    """
    Lightweight dependency injection container.

    Supports singleton, transient, and scoped lifetimes.
    Provides automatic constructor injection based on type hints.
    """

    def __init__(self):
        """Initialize the container."""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._building: List[Type] = []  # Circular dependency detection
        self.logger = logging.getLogger(__name__)

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
    ) -> None:
        """
        Register a service as singleton.

        :param service_type: Service interface type
        :param implementation_type: Implementation type
        :param factory: Factory function
        :param instance: Pre-created instance
        """
        if instance is not None:
            self._singletons[service_type] = instance

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            scope=LifecycleScope.SINGLETON,
        )
        self._services[service_type] = descriptor
        self.logger.debug(f"Registered singleton service: {service_type.__name__}")

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
    ) -> None:
        """
        Register a service as transient.

        :param service_type: Service interface type
        :param implementation_type: Implementation type
        :param factory: Factory function
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            scope=LifecycleScope.TRANSIENT,
        )
        self._services[service_type] = descriptor
        self.logger.debug(f"Registered transient service: {service_type.__name__}")

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
    ) -> None:
        """
        Register a service as scoped.

        :param service_type: Service interface type
        :param implementation_type: Implementation type
        :param factory: Factory function
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            scope=LifecycleScope.SCOPED,
        )
        self._services[service_type] = descriptor
        self.logger.debug(f"Registered scoped service: {service_type.__name__}")

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.

        :param service_type: Service type to resolve
        :return: Service instance
        :raises DependencyInjectionError: If service cannot be resolved
        """
        instance = self.try_resolve(service_type)
        if instance is None:
            raise DependencyInjectionError(
                f"Service {service_type.__name__} is not registered"
            )
        return instance

    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service instance.

        :param service_type: Service type to resolve
        :return: Service instance or None if not found
        """
        # Check if service is registered
        if service_type not in self._services:
            self.logger.warning(f"Service {service_type.__name__} is not registered")
            return None

        descriptor = self._services[service_type]

        # Handle singleton
        if descriptor.scope == LifecycleScope.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]

            instance = self._create_instance(descriptor)
            if instance is not None:
                self._singletons[service_type] = instance
            return instance

        # Handle scoped
        elif descriptor.scope == LifecycleScope.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]

            instance = self._create_instance(descriptor)
            if instance is not None:
                self._scoped_instances[service_type] = instance
            return instance

        # Handle transient
        else:
            return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Optional[Any]:
        """
        Create an instance based on the service descriptor.

        :param descriptor: Service descriptor
        :return: Created instance or None if failed
        """
        # Check for circular dependencies
        if descriptor.service_type in self._building:
            circular_chain = " -> ".join([t.__name__ for t in self._building])
            raise DependencyInjectionError(
                f"Circular dependency detected: {circular_chain} -> {descriptor.service_type.__name__}"
            )

        try:
            self._building.append(descriptor.service_type)

            # Use pre-created instance
            if descriptor.instance is not None:
                return descriptor.instance

            # Use factory function
            if descriptor.factory is not None:
                return self._call_with_injection(descriptor.factory)

            # Use implementation type
            if descriptor.implementation_type is not None:
                return self._create_with_constructor_injection(
                    descriptor.implementation_type
                )

            return None

        except Exception as e:
            self.logger.error(
                f"Failed to create instance of {descriptor.service_type.__name__}: {e}"
            )
            raise DependencyInjectionError(
                f"Failed to create instance of {descriptor.service_type.__name__}: {e}"
            ) from e
        finally:
            if descriptor.service_type in self._building:
                self._building.remove(descriptor.service_type)

    def _create_with_constructor_injection(self, implementation_type: Type[T]) -> T:
        """
        Create an instance using constructor injection.

        :param implementation_type: Implementation type to create
        :return: Created instance
        """
        # Get constructor
        constructor = implementation_type.__init__

        # Get type hints for constructor parameters
        type_hints = get_type_hints(constructor)

        # Get constructor signature
        sig = inspect.signature(constructor)

        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Get parameter type
            param_type = type_hints.get(param_name)
            if param_type is None:
                # Try to get from annotation
                param_type = param.annotation
                if param_type == inspect.Parameter.empty:
                    if param.default == inspect.Parameter.empty:
                        raise DependencyInjectionError(
                            f"Cannot resolve parameter '{param_name}' for {implementation_type.__name__}: no type annotation"
                        )
                    continue  # Skip parameters with default values

            # Resolve dependency
            dependency = self.try_resolve(param_type)
            if dependency is not None:
                kwargs[param_name] = dependency
            elif param.default == inspect.Parameter.empty:
                raise DependencyInjectionError(
                    f"Cannot resolve required parameter '{param_name}' of type {param_type} for {implementation_type.__name__}"
                )

        # Create instance
        return implementation_type(**kwargs)

    def _call_with_injection(self, factory: Callable[..., T]) -> T:
        """
        Call a factory function with dependency injection.

        :param factory: Factory function
        :return: Created instance
        """
        # Get type hints for factory parameters
        type_hints = get_type_hints(factory)

        # Get factory signature
        sig = inspect.signature(factory)

        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            # Get parameter type
            param_type = type_hints.get(param_name)
            if param_type is None:
                param_type = param.annotation
                if param_type == inspect.Parameter.empty:
                    if param.default == inspect.Parameter.empty:
                        raise DependencyInjectionError(
                            f"Cannot resolve parameter '{param_name}' for factory: no type annotation"
                        )
                    continue

            # Resolve dependency
            dependency = self.try_resolve(param_type)
            if dependency is not None:
                kwargs[param_name] = dependency
            elif param.default == inspect.Parameter.empty:
                raise DependencyInjectionError(
                    f"Cannot resolve required parameter '{param_name}' of type {param_type} for factory"
                )

        # Call factory
        return factory(**kwargs)

    def clear_scoped(self) -> None:
        """Clear all scoped instances."""
        self._scoped_instances.clear()
        self.logger.debug("Cleared scoped instances")

    def get_registered_services(self) -> List[Type]:
        """
        Get list of registered service types.

        :return: List of registered service types
        """
        return list(self._services.keys())

    def is_registered(self, service_type: Type) -> bool:
        """
        Check if a service type is registered.

        :param service_type: Service type to check
        :return: True if registered
        """
        return service_type in self._services


# Global container instance
_global_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """
    Get the global dependency container.

    :return: Global container instance
    """
    global _global_container
    if _global_container is None:
        _global_container = DependencyContainer()
    return _global_container


def set_container(container: DependencyContainer) -> None:
    """
    Set the global dependency container.

    :param container: Container to set as global
    """
    global _global_container
    _global_container = container


def resolve(service_type: Type[T]) -> T:
    """
    Resolve a service from the global container.

    :param service_type: Service type to resolve
    :return: Service instance
    """
    return get_container().resolve(service_type)


def try_resolve(service_type: Type[T]) -> Optional[T]:
    """
    Try to resolve a service from the global container.

    :param service_type: Service type to resolve
    :return: Service instance or None
    """
    return get_container().try_resolve(service_type)


# Decorator for automatic service registration
def injectable(
    service_type: Optional[Type] = None,
    scope: LifecycleScope = LifecycleScope.TRANSIENT,
):
    """
    Decorator to automatically register a class as a service.

    :param service_type: Service interface type (defaults to the decorated class)
    :param scope: Service lifecycle scope
    """

    def decorator(cls):
        actual_service_type = service_type or cls
        container = get_container()

        if scope == LifecycleScope.SINGLETON:
            container.register_singleton(actual_service_type, cls)
        elif scope == LifecycleScope.SCOPED:
            container.register_scoped(actual_service_type, cls)
        else:
            container.register_transient(actual_service_type, cls)

        return cls

    return decorator
