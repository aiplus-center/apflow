# Error Handling Specification

This document defines the error handling requirements and error codes for the AI Perceivable Flow Protocol.

## Error Principles

**MUST**: All errors MUST follow JSON-RPC 2.0 error format.

**MUST**: Error messages MUST be descriptive and include context.

**SHOULD**: Error messages SHOULD be human-readable.

**SHOULD**: Error responses SHOULD include error codes for programmatic handling.

## Error Response Format

All errors follow this format:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "field": "task_id",
      "reason": "Invalid UUID format",
      "details": "Expected UUID v4 format"
    }
  },
  "id": "request-id"
}
```

**Fields**:
- `code` (integer, required): Error code (see [Error Codes](#error-codes) section below)
- `message` (string, required): Human-readable error message
- `data` (any, optional): Additional error context

## Error Codes

This section defines all error codes used by the protocol.

### Standard JSON-RPC 2.0 Error Codes

These codes are defined by the JSON-RPC 2.0 specification:

| Code | Name | Description | When to Use |
| :--- | :--- | :--- | :--- |
| -32700 | Parse error | Invalid JSON was received | Request body is not valid JSON |
| -32600 | Invalid Request | The JSON sent is not a valid Request object | Missing required fields (`jsonrpc`, `method`, `params`, `id`) |
| -32601 | Method not found | The method does not exist / is not available | Method name is not recognized |
| -32602 | Invalid params | Invalid method parameter(s) | Parameters don't match method signature or fail validation |
| -32603 | Internal error | Internal JSON-RPC error | Server-side error (unexpected exception, etc.) |

**MUST**: Implementations MUST use these codes for protocol-level errors.

### Protocol-Specific Error Codes

These codes are specific to the AI Perceivable Flow Protocol:

| Code | Name | Description | When to Use |
| :--- | :--- | :--- | :--- |
| -32001 | Task not found | The specified task does not exist | Task ID references non-existent task |
| -32002 | Circular dependency | Circular dependency detected in task tree | Task dependencies form a cycle |
| -32003 | Executor not found | The specified executor is not registered | `schemas.method` doesn't match any registered executor |
| -32004 | Unauthorized | Request is not authorized | Authentication failed or insufficient permissions |
| -32005 | Invalid task schema | Task schema validation failed | Task data doesn't conform to schema (including invalid or missing `origin_type`, `original_task_id`, `has_references`, or if `origin_type` is `link`/`archive` and the referenced task is not `completed`) |
| -32006 | Invalid state transition | Invalid state transition attempted | Attempted transition violates state machine rules |
| -32007 | Dependency not satisfied | Task dependencies are not satisfied | Task cannot execute because dependencies are not ready |
| -32008 | Task already executing | Task is already being executed | Attempt to execute a task that's already `in_progress` |
| -32009 | Cannot delete task | Task cannot be deleted | Task has children, dependents, or is not in `pending` status |
| -32010 | Invalid parent reference | Parent task reference is invalid | `parent_id` references non-existent or invalid task |
| -32011 | Invalid dependency reference | Dependency task reference is invalid | Dependency ID references non-existent task |
| -32012 | Task tree validation failed | Task tree structure is invalid | Tree has multiple roots, circular parent-child, etc. |

**MUST**: Implementations MUST use these codes for protocol-specific errors.

**SHOULD**: Implementations SHOULD provide detailed error data in the `data` field.

## Error Categories

### Validation Errors

Errors that occur when input data fails validation.

**Common Scenarios**:
- Invalid UUID format
- Missing required fields
- Invalid field types
- Field value out of range
- Schema validation failure

**Error Code**: `-32602` (Invalid params) or `-32005` (Invalid task schema)

**Example**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "field": "priority",
      "reason": "Value out of range",
      "expected": "0-3",
      "actual": 5
    }
  },
  "id": "req-001"
}
```

### Not Found Errors

Errors that occur when a referenced resource doesn't exist.

**Common Scenarios**:
- Task not found
- Executor not found
- Parent task not found
- Dependency task not found

**Error Code**: `-32001` (Task not found) or `-32003` (Executor not found)

**Example**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Task not found",
    "data": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  },
  "id": "req-002"
}
```

### State Machine Errors

Errors that occur when state transitions are invalid.

**Common Scenarios**:
- Invalid state transition
- Task already executing
- Task in terminal state

**Error Code**: `-32006` (Invalid state transition) or `-32008` (Task already executing)

**Example**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32006,
    "message": "Invalid state transition",
    "data": {
      "task_id": "task-uuid",
      "current_status": "completed",
      "attempted_transition": "pending -> in_progress",
      "reason": "Cannot transition from terminal state"
    }
  },
  "id": "req-003"
}
```

### Dependency Errors

Errors that occur when dependencies are invalid or not satisfied.

**Common Scenarios**:
- Circular dependency
- Invalid dependency reference
- Dependency not satisfied
- Self-reference

**Error Code**: `-32002` (Circular dependency), `-32011` (Invalid dependency reference), or `-32007` (Dependency not satisfied)

**Example**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32002,
    "message": "Circular dependency detected",
    "data": {
      "cycle": [
        "task-a",
        "task-b",
        "task-c",
        "task-a"
      ]
    }
  },
  "id": "req-004"
}
```

### Authorization Errors

Errors that occur when authentication or authorization fails.

**Common Scenarios**:
- Missing authentication token
- Invalid authentication token
- Insufficient permissions
- User ID mismatch

**Error Code**: `-32004` (Unauthorized)

**Example**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32004,
    "message": "Unauthorized",
    "data": {
      "reason": "Invalid authentication token"
    }
  },
  "id": "req-005"
}
```

### Execution Errors

Errors that occur during task execution.

**Common Scenarios**:
- Executor execution failed
- Executor timeout
- Executor not found
- Invalid executor inputs

**Error Code**: `-32003` (Executor not found) or `-32603` (Internal error)

**Example**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "task_id": "task-uuid",
      "executor": "web_crawler",
      "error": "Connection timeout after 30 seconds"
    }
  },
  "id": "req-006"
}
```

## Task Error Field

When a task fails, the error is stored in the `task.error` field.

**Format**: String containing the error message.

**MUST**: `error` MUST be `null` when status is not `failed` or `cancelled`.

**MUST**: `error` MUST be a non-empty string when status is `failed` or `cancelled`.

**SHOULD**: Error messages SHOULD be descriptive and include context.

**Example**:
```json
{
  "id": "task-uuid",
  "status": "failed",
  "error": "Executor 'web_crawler' raised exception: Connection timeout after 30 seconds"
}
```

## Error Propagation

### Dependency Failure Propagation

When a required dependency fails:

1. **Block Execution**: Dependent task MUST NOT execute.
2. **Status**: Dependent task remains in `pending` status.
3. **Error Information**: Dependent task MAY inherit error information (implementation-specific).

**Example**:
```json
{
  "id": "dependent-task",
  "status": "pending",
  "dependencies": [
    {
      "id": "failed-task",
      "required": true
    }
  ],
  "error": null  // Task hasn't failed, but cannot execute due to dependency
}
```

### Cascading Failures

When a task fails, dependent tasks may also be affected:

1. **Required Dependencies**: Tasks with `required: true` dependencies on failed tasks MUST NOT execute.
2. **Optional Dependencies**: Tasks with `required: false` dependencies on failed tasks CAN execute.

## Error Recovery

### Retry Mechanisms

**MAY**: Implementations MAY support automatic retry of failed tasks.

**SHOULD**: If retry is supported, implementations SHOULD:
- Limit the number of retries
- Use exponential backoff
- Provide configuration for retry behavior

**Example Retry Configuration**:
```json
{
  "retry": {
    "max_attempts": 3,
    "backoff": "exponential",
    "initial_delay": 1.0,
    "max_delay": 60.0
  }
}
```

### Manual Recovery

**SHOULD**: Implementations SHOULD support manual re-execution of failed tasks.

**MUST**: Re-execution MUST reset task state to `pending` and clear error.

## Error Handling Best Practices

### For Implementations

1. **Validate Early**: Validate inputs as early as possible.
2. **Provide Context**: Include field names, expected values, and actual values in error messages.
3. **Use Appropriate Codes**: Use standard JSON-RPC codes for protocol errors, custom codes for application errors.
4. **Log Errors**: Log errors with full context for debugging.
5. **Handle Gracefully**: Don't expose internal implementation details in error messages.

### For Clients

1. **Check Error Codes**: Use error codes for programmatic error handling.
2. **Display Messages**: Show error messages to users.
3. **Retry Appropriately**: Retry only for transient errors (not validation errors).
4. **Handle Gracefully**: Provide fallback behavior for expected errors.

## Implementation Requirements

**MUST**: Implementations MUST handle all error cases defined in this document.

**MUST**: Implementations MUST return appropriate error codes.

**SHOULD**: Implementations SHOULD provide detailed error data in the `data` field.

**SHOULD**: Implementations SHOULD log errors with full context.

## See Also

- [Interface Protocol](06-interfaces.md) - API error handling
- [Execution Lifecycle](04-execution-lifecycle.md) - State machine error handling
- [Conformance](07-conformance.md) - Error handling requirements

