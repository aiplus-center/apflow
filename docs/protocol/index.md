# AI Perceivable Flow Protocol

The **AI Perceivable Flow Protocol** defines the standard for interaction between different components of the system, enabling interoperability across multiple language implementations.

## What is the Protocol?

The protocol is a language-agnostic specification that ensures seamless communication between nodes running different implementations. It provides all specifications needed to implement a compatible library without reference to specific implementations.

### Key Features

- **Language Agnostic**: Designed to be implemented in any programming language (Python, Go, Rust, JavaScript, etc.)
- **Interoperability**: Ensures seamless communication between nodes running different implementations
- **Extensibility**: Allows for future enhancements without breaking existing implementations
- **Completeness**: Provides all specifications needed to implement a compatible library

## Protocol Documentation

The protocol specification is organized into the following documents:

### 📋 Getting Started

1. **[Overview](01-overview.md)** - Protocol introduction, versioning, and standards
   - Protocol goals and version information
   - Standards compliance (JSON-RPC 2.0, A2A Protocol, JSON Schema)
   - Implementation guide

### 🔑 Core Concepts

2. **[Core Concepts](02-core-concepts.md)** - Fundamental concepts and interfaces
   - Flow, Task, Executor, Node, TaskManager
   - Key definitions and relationships

3. **[Data Model](03-data-model.md)** - Complete task schema and data structures
   - Task schema definition
   - Field specifications and types
   - JSON Schema definitions

### ⚙️ Execution

4. **[Execution Lifecycle](04-execution-lifecycle.md)** - State machine and execution rules
   - Task state transitions
   - Execution rules and dependencies
   - Priority scheduling

### 📚 Reference

5. **[Examples](05-examples.md)** - Comprehensive examples and use cases
   - Basic task examples
   - Complex workflow examples
   - Real-world scenarios

6. **[Interface Protocol](06-interfaces.md)** - API specifications
   - JSON-RPC 2.0 API
   - A2A Protocol integration
   - Transport layer specifications

### ✅ Compliance

7. **[Conformance](07-conformance.md)** - Implementation requirements and compliance
   - MUST/SHOULD/MAY requirements
   - Compliance checklist
   - Testing guidelines

8. **[Error Handling](08-errors.md)** - Error codes and handling procedures
   - Standard error codes
   - Error response format
   - Error handling best practices

9. **[Validation](09-validation.md)** - Validation rules and algorithms
   - Input validation
   - Schema validation
   - Validation algorithms

## Quick Navigation

### For Implementers

**New to the protocol?** Start here:

1. **[Overview](01-overview.md)** - Understand the protocol goals and structure
2. **[Core Concepts](02-core-concepts.md)** - Learn the fundamental concepts
3. **[Data Model](03-data-model.md)** - Understand the task schema
4. **[Execution Lifecycle](04-execution-lifecycle.md)** - Learn how tasks execute
5. **[Examples](05-examples.md)** - See practical examples

**Implementing a library?** Follow this path:

1. Read [Core Concepts](02-core-concepts.md) and [Data Model](03-data-model.md)
2. Study [Execution Lifecycle](04-execution-lifecycle.md) for state transitions
3. Review [Examples](05-examples.md) for usage patterns
4. Implement core components (Task, Executor, TaskManager, Storage, API)
5. Validate using [Conformance](07-conformance.md) checklist
6. Test with [Examples](05-examples.md) and [Validation](09-validation.md) rules

### For Users

**Using an existing implementation?** Check these:

- **[Interface Protocol](06-interfaces.md)** - API reference for clients
- **[Examples](05-examples.md)** - Usage examples
- **[Error Handling](08-errors.md)** - Understanding error responses

## Protocol Version

**Current Version**: 1.0

**Version Format**: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes to the protocol
- **MINOR**: New features that are backward compatible
- **PATCH**: Bug fixes and clarifications

**MUST**: Implementations MUST specify the protocol version they support.

**SHOULD**: Implementations SHOULD be backward compatible with previous minor versions when possible.

## Protocol Standards

The protocol builds on and complies with established standards:

- **JSON-RPC 2.0**: All RPC operations use JSON-RPC 2.0 format
- **A2A Protocol**: Enhanced agent-to-agent communication
- **JSON Schema Draft 7**: Task schema definitions and validation
- **UUID (RFC 4122)**: Task identifiers
- **ISO 8601**: Timestamp fields

See [Overview](01-overview.md) for detailed compliance requirements.

## Next Steps

- **New to the protocol?** → Start with [Overview](01-overview.md)
- **Implementing a library?** → Read [Core Concepts](02-core-concepts.md)
- **Using an API?** → Check [Interface Protocol](06-interfaces.md)
- **Need examples?** → See [Examples](05-examples.md)

---

**Ready to dive in?** → [Start with Overview →](01-overview.md)

