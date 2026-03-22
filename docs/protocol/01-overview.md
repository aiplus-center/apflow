# Protocol Overview

The AI Perceivable Flow Protocol defines the standard for interaction between different components of the system, enabling interoperability across multiple language implementations.

## Protocol Goals

*   **Language Agnostic**: The protocol is designed to be implemented in any programming language (Python, Go, Rust, JavaScript, etc.).
*   **Interoperability**: Ensures seamless communication between nodes running different implementations.
*   **Extensibility**: Allows for future enhancements without breaking existing implementations.
*   **Completeness**: Provides all specifications needed to implement a compatible library without reference to specific implementations.

## Protocol Version

**Current Version**: 1.0

**Version Format**: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes to the protocol
- **MINOR**: New features that are backward compatible
- **PATCH**: Bug fixes and clarifications

**MUST**: Implementations MUST specify the protocol version they support.

**SHOULD**: Implementations SHOULD be backward compatible with previous minor versions when possible.

## Key Concepts

*   **Flow**: A complete workflow or process, structured as a hierarchical tree of Tasks.
*   **Task**: The atomic unit of execution within a Flow.
*   **Executor**: The component responsible for performing the actual work defined by a Task.
*   **Node**: A participant in the network that implements the protocol.
*   **TaskManager**: The orchestrator that coordinates task execution, dependency resolution, and priority scheduling.

See [Core Concepts](02-core-concepts.md) for detailed definitions.

## Protocol Standards

The protocol builds on and complies with established standards:

### JSON-RPC 2.0

**Standard**: [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

**Usage**: All RPC operations use JSON-RPC 2.0 format.

**Compliance**: 
- **MUST**: Implementations MUST support JSON-RPC 2.0 over HTTP.
- **MUST**: Implementations MUST use standard JSON-RPC 2.0 error codes for protocol errors.

See [Interface Protocol](06-interfaces.md) for complete API specification.

### A2A Protocol

**Standard**: [A2A Protocol](https://www.a2aprotocol.org/en/docs)

**Usage**: Enhanced agent-to-agent communication with streaming and push notifications.

**Compliance**:
- **SHOULD**: Implementations SHOULD support A2A Protocol for enhanced features.
- **SHOULD**: Implementations SHOULD support agent card discovery.

See [Interface Protocol](06-interfaces.md) for A2A Protocol integration details.

### JSON Schema

**Standard**: [JSON Schema Draft 7](https://json-schema.org/specification.html)

**Usage**: Task schema definitions and input validation.

**Compliance**:
- **MUST**: Implementations MUST validate tasks against JSON Schema definitions.
- **SHOULD**: Implementations SHOULD use JSON Schema for input validation.

See [Data Model](03-data-model.md) for complete schema definitions.

### UUID

**Standard**: [RFC 4122 - UUID](https://tools.ietf.org/html/rfc4122)

**Usage**: Task identifiers (`id`, `parent_id`, dependency IDs).

**Compliance**:
- **MUST**: Implementations MUST use UUID v4 format for all task identifiers.
- **MUST**: Implementations MUST validate UUID format.

### ISO 8601

**Standard**: [ISO 8601 - Date and Time](https://www.iso.org/iso-8601-date-and-time-format.html)

**Usage**: Timestamp fields (`created_at`, `started_at`, `updated_at`, `completed_at`).

**Compliance**:
- **MUST**: Implementations MUST use ISO 8601 format for timestamps.
- **SHOULD**: Implementations SHOULD use UTC timezone.

## Protocol Structure

The protocol specification is organized into the following documents:

1. **[Overview](01-overview.md)** (this document): Protocol introduction, versioning, and standards
2. **[Core Concepts](02-core-concepts.md)**: Fundamental concepts and interfaces
3. **[Data Model](03-data-model.md)**: Complete task schema and data structures
4. **[Execution Lifecycle](04-execution-lifecycle.md)**: State machine and execution rules
5. **[Examples](05-examples.md)**: Comprehensive examples and use cases
6. **[Interface Protocol](06-interfaces.md)**: API specifications (JSON-RPC 2.0, A2A Protocol)
7. **[Conformance](07-conformance.md)**: Implementation requirements and compliance
8. **[Error Handling](08-errors.md)**: Error codes and handling procedures
9. **[Validation](09-validation.md)**: Validation rules and algorithms

## Implementation Guide

### Getting Started for Implementers

To implement a compatible library:

1. **Read the Specification**: Start with [Core Concepts](02-core-concepts.md) and [Data Model](03-data-model.md).
2. **Understand the State Machine**: Study [Execution Lifecycle](04-execution-lifecycle.md) for state transitions and execution rules.
3. **Review Examples**: See [Examples](05-examples.md) for practical usage patterns.
4. **Implement Core Components**:
   - Task data structures
   - Executor interface
   - TaskManager (orchestration)
   - Storage interface
   - API interface (JSON-RPC 2.0)
5. **Validate Implementation**: Use [Conformance](07-conformance.md) checklist to verify compliance.
6. **Test**: Create test cases based on [Examples](05-examples.md) and [Validation](09-validation.md) rules.

### Core Implementation Requirements

**MUST** implement:
- Complete Task schema
- State machine (all states and valid transitions)
- Dependency resolution
- Priority scheduling
- Executor interface
- Storage interface
- JSON-RPC 2.0 API

**SHOULD** implement:
- A2A Protocol support
- Streaming (SSE, WebSocket, or push notifications)
- Input validation
- Error handling

**MAY** implement:
- Authentication
- Retry mechanisms
- Advanced features

See [Conformance](07-conformance.md) for complete requirements.

### Testing Your Implementation

1. **Unit Tests**: Test individual components (task validation, state transitions, dependency resolution).
2. **Integration Tests**: Test complete workflows (task execution, dependency chains, error handling).
3. **Compliance Tests**: Verify all MUST requirements are met.
4. **Interoperability Tests**: Test with other implementations (if available).

### Contributing Implementations

**SHOULD**: Implementations SHOULD be open source and publicly available.

**SHOULD**: Implementations SHOULD include:
- Complete documentation
- Test suite
- Example code
- Protocol version compatibility information

**MAY**: Implementations MAY seek protocol compliance certification.

## Version History

### Version 1.0 (Current)

**Initial Release**: Complete protocol specification including:
- Task data model
- State machine
- Dependency resolution
- Priority scheduling
- Executor interface
- Storage interface
- JSON-RPC 2.0 API
- A2A Protocol integration
- Validation rules
- Error handling

**Breaking Changes**: None (initial version).

## Compatibility

### Backward Compatibility

**SHOULD**: New minor versions SHOULD be backward compatible with previous minor versions.

**MUST**: Breaking changes MUST result in a new major version.

### Forward Compatibility

**MAY**: Implementations MAY support features from future protocol versions if they are optional.

**SHOULD**: Implementations SHOULD gracefully handle unknown fields (ignore or preserve).

## Protocol Independence

This protocol specification is **independent** of any specific implementation:

- **Language Agnostic**: No language-specific code or examples (except for reference).
- **Implementation Agnostic**: No assumptions about internal implementation details.
- **Complete**: All information needed for implementation is in the protocol documents.

**MUST**: Implementations MUST not require knowledge of specific implementations (e.g., Python reference implementation) to be compliant.

**SHOULD**: Implementations SHOULD reference this protocol specification as the source of truth.

## Reference Implementation

The Python implementation (`apflow`) serves as a **reference implementation**:

- Demonstrates protocol compliance
- Provides examples and patterns
- Validates protocol completeness

**Note**: The reference implementation is for reference only. Implementations in other languages MUST follow the protocol specification, not the reference implementation's internal details.

## Protocol Extensions

The protocol supports extensions for custom functionality:

1. **Custom Executors**: Implement custom executors for specific use cases
   - System executors (system information, commands)
   - Data processing executors (aggregation, transformation)
   - External service executors (HTTP, APIs, databases)
   - AI/LLM executors (LLM agents, AI models)
   - Domain-specific executors (business logic, integrations)

2. **Storage Backends**: Implement custom storage backends
   - Database backends (SQL, NoSQL)
   - File-based storage
   - In-memory storage

3. **Transport Layers**: Implement custom transport layers
   - WebSocket
   - Message queues
   - Custom protocols

**MUST**: Extensions MUST not break protocol compliance.

**SHOULD**: Extensions SHOULD be documented and made available to the community.

**Note**: While implementations may provide various executor types (e.g., `system_info_executor`, `command_executor`, `crew_manager`), the protocol only specifies the interface and registration mechanism. Specific executor identifiers are implementation-specific.

## Getting Help

- **Protocol Questions**: Review the protocol documentation
- **Implementation Questions**: See [Examples](05-examples.md) and [Core Concepts](02-core-concepts.md)
- **Compliance Questions**: See [Conformance](07-conformance.md)
- **Error Handling**: See [Error Handling](08-errors.md)

## See Also

- [Core Concepts](02-core-concepts.md) - Fundamental protocol concepts
- [Data Model](03-data-model.md) - Complete task schema
- [Execution Lifecycle](04-execution-lifecycle.md) - State machine specification
- [Interface Protocol](06-interfaces.md) - API specifications
- [Conformance](07-conformance.md) - Implementation requirements
