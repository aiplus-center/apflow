# Conformance Requirements

This document defines the conformance requirements for implementations of the AI Perceivable Flow Protocol. Implementations MUST meet the requirements specified in this document to be considered protocol-compliant.

## Conformance Levels

Requirements are categorized using RFC 2119 keywords:

- **MUST**: Mandatory requirement. All implementations MUST comply.
- **SHOULD**: Recommended requirement. Implementations SHOULD comply unless there is a specific reason not to.
- **MAY**: Optional requirement. Implementations MAY choose to support.

## Core Requirements (MUST)

### Data Model Compliance

**MUST**: Implementations MUST support the complete Task schema as defined in [Data Model](03-data-model.md).

**MUST**: Implementations MUST validate all task data against the JSON Schema definitions.

**MUST**: Implementations MUST support all required fields:
- `id` (UUID v4)
- `name` (string)
- `status` (enum: `pending`, `in_progress`, `completed`, `failed`, `cancelled`)

**MUST**: Implementations MUST support all optional fields with correct types and constraints.

### State Machine Compliance

**MUST**: Implementations MUST implement the complete state machine as defined in [Execution Lifecycle](04-execution-lifecycle.md).

**MUST**: Implementations MUST enforce valid state transitions only.

**MUST**: Implementations MUST NOT allow invalid state transitions.

**MUST**: Implementations MUST update timestamps (`started_at`, `completed_at`) according to state transitions.

### Dependency Resolution

**MUST**: Implementations MUST resolve dependencies before allowing task execution.

**MUST**: Implementations MUST respect the `required` flag for each dependency.

**MUST**: Implementations MUST detect and reject circular dependencies.

**MUST**: Implementations MUST validate that all dependency IDs reference existing tasks.

### Priority Scheduling

**MUST**: Implementations MUST schedule tasks by priority (lower values = higher priority).

**MUST**: Implementations MUST execute tasks with priority 0 before priority 1, priority 1 before priority 2, etc.

**MUST**: Implementations MUST respect dependencies over priorities (tasks with higher priority but unsatisfied dependencies MUST wait).

### Executor Interface

**MUST**: Implementations MUST provide an `ExecutorRegistry` mechanism.

**MUST**: Implementations MUST support executor registration with unique identifiers.

**MUST**: Implementations MUST look up executors by `schemas.method` when executing tasks.

**MUST**: Implementations MUST handle executor errors and update task status to `failed`.

### Storage Interface

**MUST**: Implementations MUST provide persistent storage for task state.

**MUST**: Implementations MUST support the following storage operations:
- `createTask`
- `getTask`
- `updateTask`
- `deleteTask`
- `listTasks`
- `getTaskTree`

**MUST**: Implementations MUST ensure data consistency (no orphaned tasks, valid references).

### API Interface

**MUST**: Implementations MUST support JSON-RPC 2.0 over HTTP.

**MUST**: Implementations MUST support all standard methods defined in [Interface Protocol](06-interfaces.md):
- `tasks.create`
- `tasks.get`
- `tasks.update`
- `tasks.delete`
- `tasks.list`
- `tasks.execute`
- `tasks.cancel`
- `tasks.tree`
- `tasks.children`

**MUST**: Implementations MUST return JSON-RPC 2.0 compliant responses.

**MUST**: Implementations MUST use standard JSON-RPC 2.0 error codes for protocol errors.

## Recommended Requirements (SHOULD)

### A2A Protocol Support

**SHOULD**: Implementations SHOULD support A2A Protocol for enhanced agent-to-agent communication.

**SHOULD**: Implementations SHOULD support agent card discovery (`GET /.well-known/agent-card`).

**SHOULD**: Implementations SHOULD support A2A Protocol streaming (SSE, WebSocket).

### Streaming Support

**SHOULD**: Implementations SHOULD support at least one streaming mode (SSE, WebSocket, or push notifications).

**SHOULD**: Implementations SHOULD provide real-time progress updates during task execution.

### Input Validation

**SHOULD**: Implementations SHOULD validate `inputs` against `schemas.input_schema` before execution.

**SHOULD**: Implementations SHOULD provide clear error messages for validation failures.

### Error Handling

**SHOULD**: Implementations SHOULD provide descriptive error messages.

**SHOULD**: Implementations SHOULD include error context (field names, validation details) in error responses.

### Concurrency

**SHOULD**: Implementations SHOULD support concurrent execution of independent tasks.

**SHOULD**: Implementations SHOULD provide configuration for concurrency limits.

### Re-execution

**SHOULD**: Implementations SHOULD support re-execution of failed tasks.

**SHOULD**: Implementations SHOULD support cascading re-execution (re-execute dependents when a task is re-executed).

### Copy Execution

**SHOULD**: Implementations SHOULD support copying tasks before execution.

**SHOULD**: Implementations SHOULD support copying task trees (task + children).

## Optional Requirements (MAY)

### Authentication

**MAY**: Implementations MAY support authentication (JWT, API keys, etc.).

**MAY**: Implementations MAY enforce access control based on `user_id`.

### Retry Mechanisms

**MAY**: Implementations MAY support automatic retry of failed tasks.

**MAY**: Implementations MAY provide configuration for retry behavior (max attempts, backoff strategy).

### Advanced Features

**MAY**: Implementations MAY support:
- Task checkpoints and resume
- Task scheduling (cron-like)
- Task versioning
- Task templates

## Implementation Checklist

Use this checklist to verify your implementation's conformance:

### Data Model
- [ ] Complete Task schema support
- [ ] JSON Schema validation
- [ ] All required fields supported
- [ ] All optional fields with correct types
- [ ] Field constraints enforced (priority range, progress range, etc.)

### State Machine
- [ ] All states supported (`pending`, `in_progress`, `completed`, `failed`, `cancelled`)
- [ ] Valid transitions enforced
- [ ] Invalid transitions rejected
- [ ] Timestamps updated correctly

### Dependency Resolution
- [ ] Dependencies checked before execution
- [ ] `required` flag respected
- [ ] Circular dependency detection
- [ ] Dependency reference validation

### Priority Scheduling
- [ ] Priority ordering enforced
- [ ] Dependencies take precedence over priority
- [ ] Same-priority tasks handled fairly

### Executor Interface
- [ ] ExecutorRegistry implemented
- [ ] Executor registration supported
- [ ] Executor lookup by method
- [ ] Executor errors handled

### Storage Interface
- [ ] All required operations implemented
- [ ] Data consistency ensured
- [ ] Query operations supported
- [ ] Transaction support (if applicable)

### API Interface
- [ ] JSON-RPC 2.0 compliance
- [ ] All standard methods implemented
- [ ] Error responses compliant
- [ ] Request validation

### Optional Features
- [ ] A2A Protocol support (if applicable)
- [ ] Streaming support (if applicable)
- [ ] Authentication (if applicable)
- [ ] Retry mechanisms (if applicable)

## Compatibility Matrix

### Version Compatibility

| Protocol Version | Compatible Implementations |
| :--- | :--- |
| 1.0 | All implementations following this specification |

**MUST**: Implementations MUST specify the protocol version they support.

**SHOULD**: Implementations SHOULD be backward compatible with previous protocol versions when possible.

### Feature Compatibility

| Feature | Required | Optional |
| :--- | :--- | :--- |
| Core Task Schema | ✅ MUST | |
| State Machine | ✅ MUST | |
| Dependency Resolution | ✅ MUST | |
| Priority Scheduling | ✅ MUST | |
| Executor Interface | ✅ MUST | |
| Storage Interface | ✅ MUST | |
| JSON-RPC 2.0 API | ✅ MUST | |
| A2A Protocol | | ✅ SHOULD |
| Streaming | | ✅ SHOULD |
| Authentication | | ✅ MAY |
| Retry Mechanisms | | ✅ MAY |

### Breaking Changes Policy

**MUST**: Breaking changes to the protocol MUST result in a new major version.

**MUST**: Breaking changes MUST be documented in protocol version history.

**SHOULD**: Implementations SHOULD support multiple protocol versions when possible.

## Validation Requirements

### Schema Validation

**MUST**: Implementations MUST validate all incoming task data against the JSON Schema definitions.

**MUST**: Implementations MUST reject invalid task data with appropriate error codes.

**SHOULD**: Implementations SHOULD provide detailed validation error messages.

### State Validation

**MUST**: Implementations MUST validate state transitions against the state machine.

**MUST**: Implementations MUST reject invalid state transitions.

**MUST**: Implementations MUST ensure field values are consistent with status (e.g., `result` is null when status is not `completed`).

### Dependency Validation

**MUST**: Implementations MUST validate dependencies when tasks are created or updated.

**MUST**: Implementations MUST detect and reject circular dependencies.

**MUST**: Implementations MUST validate that all dependency IDs reference existing tasks.

### Error Handling Validation

**MUST**: Implementations MUST handle all error cases defined in the protocol.

**MUST**: Implementations MUST return appropriate error codes and messages.

**SHOULD**: Implementations SHOULD provide error context (field names, validation details).

## Testing Requirements

### Unit Testing

**SHOULD**: Implementations SHOULD include unit tests for:
- Task schema validation
- State machine transitions
- Dependency resolution
- Priority scheduling
- Executor interface

### Integration Testing

**SHOULD**: Implementations SHOULD include integration tests for:
- Complete task execution flows
- Dependency chains
- Error handling
- API endpoints

### Compliance Testing

**SHOULD**: Implementations SHOULD include compliance tests that verify:
- All MUST requirements are met
- All SHOULD requirements are met (if applicable)
- Protocol compatibility

## Certification

**MAY**: Implementations MAY seek protocol compliance certification.

**SHOULD**: Certification SHOULD verify:
- All MUST requirements
- Recommended SHOULD requirements
- Protocol compatibility

## See Also

- [Data Model](03-data-model.md) - Task schema definitions
- [Execution Lifecycle](04-execution-lifecycle.md) - State machine specification
- [Interface Protocol](06-interfaces.md) - API specifications
- [Validation](09-validation.md) - Validation algorithms
- [Error Handling](08-errors.md) - Error codes and handling

