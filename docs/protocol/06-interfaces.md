# Interface Protocol

The Interface Protocol defines how external clients (CLIs, Dashboards, other Agents) interact with an AI Perceivable Flow node. This specification is **mandatory** for all implementations.

## Protocol Standards

The protocol implements two complementary standards:

1. **JSON-RPC 2.0**: Standard RPC protocol for request-response communication
2. **A2A Protocol**: Agent-to-Agent communication protocol for AI agent systems

**MUST**: All implementations MUST support JSON-RPC 2.0 over HTTP.  
**SHOULD**: Implementations SHOULD support A2A Protocol for enhanced agent-to-agent communication.  
**MAY**: Implementations MAY support additional transport layers (SSE, WebSocket) for streaming.

## Transport Layer

### HTTP Transport (JSON-RPC 2.0)

**MUST**: Implementations MUST support HTTP/1.1 or HTTP/2.

**Request**:
- **Method**: `POST`
- **Endpoint**: `/` (root endpoint) or `/tasks` (legacy)
- **Content-Type**: `application/json`
- **Body**: JSON-RPC 2.0 request object

**Response**:
- **Content-Type**: `application/json`
- **Body**: JSON-RPC 2.0 response object

### A2A Protocol Transport

**SHOULD**: Implementations SHOULD support A2A Protocol over:
- HTTP (request-response)
- Server-Sent Events (SSE) for streaming
- WebSocket for bidirectional communication

**Endpoints**:
- `GET /.well-known/agent-card`: Agent capability discovery
- `POST /`: A2A Protocol RPC endpoint

## JSON-RPC 2.0 Compliance

The protocol uses JSON-RPC 2.0 for all RPC operations. Implementations MUST comply with the [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification).

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": {},
  "id": "request-id"
}
```

**Fields**:
- `jsonrpc` (string, required): MUST be `"2.0"`
- `method` (string, required): Method name (see [Standard Methods](#standard-methods))
- `params` (object, required): Method parameters (varies by method)
- `id` (string/number, required): Request identifier for matching responses

### Response Format (Success)

```json
{
  "jsonrpc": "2.0",
  "result": {},
  "id": "request-id"
}
```

**Fields**:
- `jsonrpc` (string, required): MUST be `"2.0"`
- `result` (any, required): Method result (varies by method)
- `id` (string/number, required): Request identifier (matches request)

### Response Format (Error)

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Error details"
  },
  "id": "request-id"
}
```

**Fields**:
- `jsonrpc` (string, required): MUST be `"2.0"`
- `error` (object, required): Error object
  - `code` (integer, required): Error code (see [Error Codes](08-errors.md#error-codes))
  - `message` (string, required): Error message
  - `data` (any, optional): Additional error data
- `id` (string/number, required): Request identifier (matches request, or `null` for parse errors)

### JSON-RPC 2.0 Error Codes

| Code | Name | Description |
| :--- | :--- | :--- |
| -32700 | Parse error | Invalid JSON was received |
| -32600 | Invalid Request | The JSON sent is not a valid Request object |
| -32601 | Method not found | The method does not exist / is not available |
| -32602 | Invalid params | Invalid method parameter(s) |
| -32603 | Internal error | Internal JSON-RPC error |
| -32000 to -32099 | Server error | Reserved for implementation-defined server errors |

**MUST**: Implementations MUST use standard JSON-RPC 2.0 error codes for protocol-level errors.

**SHOULD**: Implementations SHOULD use custom error codes (outside -32000 to -32099) for application-specific errors.

## Standard Methods

A compliant node **MUST** support the following methods. All methods follow JSON-RPC 2.0 format.

### Task Management Methods

#### `tasks.create`

Create a new task or task tree.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.create",
  "params": {
    "name": "Task Name",
    "user_id": "user123",
    "parent_id": null,
    "priority": 2,
    "inputs": {},
    "schemas": {
      "method": "executor_id"
    },
    "dependencies": []
  },
  "id": "req-001"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "id": "task-uuid",
    "status": "pending"
  },
  "id": "req-001"
}
```

**Parameters**:
- `name` (string, required): Task name
- `user_id` (string, optional): User identifier
- `parent_id` (string, optional): Parent task ID (UUID)
- `priority` (integer, optional): Priority (0-3, default: 2)
- `inputs` (object, optional): Runtime inputs
- `schemas` (object, optional): Executor configuration
- `dependencies` (array, optional): Dependency list

**MUST**: Validate task schema before creation.  
**MUST**: Generate unique UUID for task `id`.  
**MUST**: Set initial `status` to `"pending"`.

#### `tasks.get`

Retrieve a task by ID.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.get",
  "params": {
    "task_id": "task-uuid"
  },
  "id": "req-002"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "id": "task-uuid",
    "name": "Task Name",
    "status": "completed",
    // ... complete task object
  },
  "id": "req-002"
}
```

**Parameters**:
- `task_id` (string, required): Task ID (UUID)

**MUST**: Return complete task object if task exists.  
**MUST**: Return error if task not found.

#### `tasks.update`

Update task fields.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.update",
  "params": {
    "task_id": "task-uuid",
    "updates": {
      "name": "Updated Name",
      "priority": 1
    }
  },
  "id": "req-003"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "id": "task-uuid",
    "status": "pending"
  },
  "id": "req-003"
}
```

**Parameters**:
- `task_id` (string, required): Task ID (UUID)
- `updates` (object, required): Fields to update

**MUST**: Validate updates against task schema.  
**MUST NOT**: Allow updates to critical fields (`id`, `parent_id`, `user_id`) when task is executing.  
**SHOULD**: Validate `dependencies` updates (no circular dependencies).

#### `tasks.delete`

Delete a task.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.delete",
  "params": {
    "task_id": "task-uuid"
  },
  "id": "req-004"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true
  },
  "id": "req-004"
}
```

**Parameters**:
- `task_id` (string, required): Task ID (UUID)

**MUST**: Only delete tasks with status `pending`.  
**MUST**: Reject deletion if task has children or dependents.  
**SHOULD**: Cascade delete children if explicitly requested (implementation-specific).

#### `tasks.list`

List tasks with filters.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.list",
  "params": {
    "limit": 100,
    "offset": 0,
    "status": "pending",
    "user_id": "user123"
  },
  "id": "req-005"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tasks": [
      {
        "id": "task-uuid",
        "name": "Task Name",
        "status": "pending"
      }
    ],
    "total": 50,
    "limit": 100,
    "offset": 0
  },
  "id": "req-005"
}
```

**Parameters**:
- `limit` (integer, optional): Maximum results (default: 100, max: 1000)
- `offset` (integer, optional): Pagination offset (default: 0)
- `status` (string, optional): Filter by status
- `user_id` (string, optional): Filter by user ID

**MUST**: Support pagination via `limit` and `offset`.  
**SHOULD**: Return total count for pagination.

#### `tasks.execute`

Execute a task or task tree.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.execute",
  "params": {
    "tasks": [
      {
        "id": "task1",
        "name": "Task 1",
        "user_id": "user123",
        "schemas": {
          "method": "executor_id"
        },
        "inputs": {}
      }
    ]
  },
  "id": "req-006"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "root_task_id": "task-uuid",
    "status": "started"
  },
  "id": "req-006"
}
```

**Parameters**:
- `tasks` (array, required): Array of task objects to execute

**MUST**: Validate task tree structure before execution.  
**MUST**: Execute tasks according to dependencies and priorities.  
**SHOULD**: Support streaming mode (see [Streaming](#streaming)).

#### `tasks.cancel`

Cancel a running task.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.cancel",
  "params": {
    "task_id": "task-uuid"
  },
  "id": "req-007"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "task_id": "task-uuid",
    "status": "cancelled"
  },
  "id": "req-007"
}
```

**Parameters**:
- `task_id` (string, required): Task ID (UUID)

**MUST**: Cancel task if status is `pending` or `in_progress`.  
**MUST**: Transition task to `cancelled` status.

### Task Query Methods

#### `tasks.tree`

Get the full task hierarchy.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.tree",
  "params": {
    "task_id": "root-task-uuid"
  },
  "id": "req-008"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "task": {
      "id": "root-task-uuid",
      "name": "Root Task"
    },
    "children": [
      {
        "task": {
          "id": "child-task-uuid",
          "name": "Child Task"
        },
        "children": []
      }
    ]
  },
  "id": "req-008"
}
```

**Parameters**:
- `task_id` (string, required): Root task ID (UUID)

**MUST**: Return complete task tree structure.  
**MUST**: Include all descendants recursively.

#### `tasks.children`

Get direct children of a task.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.children",
  "params": {
    "parent_id": "parent-task-uuid"
  },
  "id": "req-009"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "children": [
      {
        "id": "child-task-uuid",
        "name": "Child Task"
      }
    ]
  },
  "id": "req-009"
}
```

**Parameters**:
- `parent_id` (string, required): Parent task ID (UUID)

**MUST**: Return only direct children (not grandchildren).

### Additional Methods

#### `tasks.copy`

Copy a task tree for re-execution.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.copy",
  "params": {
    "task_id": "task-uuid",
    "copy_children": true
  },
  "id": "req-010"
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "original_task_id": "task-uuid",
    "copied_task_id": "new-task-uuid",
    "status": "pending"
  },
  "id": "req-010"
}
```

**Parameters**:
- `task_id` (string, required): Task ID to copy (UUID)
- `copy_children` (boolean, optional): Also copy children (default: `false`)

**MUST**: Create new task with new UUID.  
**MUST**: Reset execution state (status, result, error, progress).  
**SHOULD**: Preserve task definition (name, inputs, schemas, dependencies).

## A2A Protocol Integration

The protocol implements the A2A (Agent-to-Agent) Protocol standard for enhanced agent-to-agent communication.

### A2A Protocol Overview

A2A Protocol provides:
- Standardized agent communication
- Streaming execution support
- Push notifications
- Agent capability discovery

**Reference**: [A2A Protocol Documentation](https://www.a2aprotocol.org/en/docs)

### Agent Card Discovery

**Endpoint**: `GET /.well-known/agent-card`

**Response**:
```json
{
  "name": "apflow",
  "description": "Agent workflow orchestration and execution platform",
  "url": "http://localhost:8000",
  "version": "0.2.0",
  "capabilities": {
    "streaming": true,
    "push_notifications": true
  },
  "skills": [
    {
      "id": "tasks.execute",
      "name": "Execute Task Tree",
      "description": "Execute a complete task tree with multiple tasks",
      "tags": ["task", "orchestration", "workflow", "execution"]
    }
  ]
}
```

**MUST**: Implementations SHOULD support agent card discovery for A2A Protocol compatibility.

### A2A Protocol Task Mapping

A2A Protocol uses a `Task` object that differs from apflow's Task. The mapping is as follows:

| apflow Task | A2A Protocol Task | Notes |
| :--- | :--- | :--- |
| `id` | `context_id` | Task definition ID |
| `status` | `status.state` | Status mapping |
| `result` | `artifacts` | Execution results |
| `error` | `status.message` | Error messages |
| `user_id` | `metadata.user_id` | User identifier |
| - | `id` | A2A execution instance ID (auto-generated) |
| - | `history` | LLM conversation history (execution-level) |

**MUST**: Implementations MUST map between apflow Task and A2A Protocol Task when using A2A Protocol.

### A2A Protocol Methods

A2A Protocol supports the same methods as JSON-RPC 2.0, but with A2A-specific request/response formats.

**Request Format** (A2A Protocol):
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.execute",
  "params": {
    "tasks": [...]
  },
  "id": "req-001",
  "metadata": {
    "stream": true
  },
  "configuration": {
    "push_notification_config": {
      "url": "https://callback.url",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

**Response Format** (A2A Protocol):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "id": "execution-instance-id",
    "context_id": "task-definition-id",
    "kind": "task",
    "status": {
      "state": "completed",
      "message": {
        "kind": "message",
        "parts": [
          {
            "kind": "data",
            "data": {
              "protocol": "a2a",
              "status": "completed",
              "progress": 1.0,
              "root_task_id": "task-uuid"
            }
          }
        ]
      }
    },
    "artifacts": [...],
    "metadata": {
      "protocol": "a2a",
      "root_task_id": "task-uuid"
    }
  },
  "id": "req-001"
}
```

**MUST**: A2A Protocol responses MUST include `protocol: "a2a"` in metadata and event data.

## Streaming

The protocol supports real-time streaming of task execution updates.

### Streaming Modes

1. **Server-Sent Events (SSE)**: One-way streaming from server to client
2. **WebSocket**: Bidirectional streaming
3. **Push Notifications**: HTTP callbacks to external URLs

### Streaming Request

Enable streaming via `metadata.stream` or `use_streaming` parameter:

```json
{
  "jsonrpc": "2.0",
  "method": "tasks.execute",
  "params": {
    "tasks": [...],
    "use_streaming": true
  },
  "metadata": {
    "stream": true
  },
  "id": "req-001"
}
```

### Streaming Events

Streaming events are sent via EventQueue (A2A Protocol) or SSE/WebSocket.

**Event Format**:
```json
{
  "event": "task_status_update",
  "data": {
    "protocol": "a2a",
    "task_id": "task-uuid",
    "status": "in_progress",
    "progress": 0.5,
    "root_task_id": "root-task-uuid"
  }
}
```

**Event Types**:
- `task_status_update`: Task status changed
- `task_progress_update`: Task progress updated
- `task_completed`: Task completed
- `task_failed`: Task failed
- `task_cancelled`: Task cancelled

**MUST**: Implementations MUST support at least one streaming mode.  
**SHOULD**: Implementations SHOULD support SSE for simple streaming scenarios.

### Push Notifications

Push notifications send task updates to external callback URLs.

**Configuration**:
```json
{
  "configuration": {
    "push_notification_config": {
      "url": "https://callback.url",
      "headers": {
        "Authorization": "Bearer token"
      },
      "method": "POST"
    }
  }
}
```

**Callback Request**:
```json
{
  "task_id": "task-uuid",
  "status": "completed",
  "progress": 1.0,
  "result": {...}
}
```

**MUST**: Implementations MUST send HTTP POST requests to callback URL.  
**SHOULD**: Implementations SHOULD include authentication headers if provided.  
**MAY**: Implementations MAY retry failed callbacks (implementation-specific).

## Authentication

**MAY**: Implementations MAY support authentication (JWT, API keys, etc.).

**SHOULD**: If authentication is supported, implementations SHOULD:
- Validate authentication tokens
- Enforce access control based on `user_id`
- Return appropriate errors for unauthorized requests

**Authentication Header** (if supported):
```
Authorization: Bearer <token>
```

## Error Handling

### Error Response Format

All errors follow JSON-RPC 2.0 error format:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "field": "task_id",
      "reason": "Invalid UUID format"
    }
  },
  "id": "req-001"
}
```

### Common Error Scenarios

1. **Task Not Found**: Return error code -32001 with message "Task not found"
2. **Invalid Task Schema**: Return error code -32602 with validation details
3. **Circular Dependency**: Return error code -32002 with message "Circular dependency detected"
4. **Executor Not Found**: Return error code -32003 with message "Executor not found"
5. **Unauthorized**: Return error code -32004 with message "Unauthorized" (if auth enabled)

## Implementation Requirements

### Method Support

**MUST**: All implementations MUST support all methods listed in [Standard Methods](#standard-methods).

**SHOULD**: Implementations SHOULD support A2A Protocol for enhanced features.

**MAY**: Implementations MAY support additional custom methods.

### Validation

**MUST**: Implementations MUST validate all requests against the schemas defined in this document.

**MUST**: Implementations MUST return appropriate errors for invalid requests.

### Concurrency

**MUST**: Implementations MUST handle concurrent requests correctly.

**SHOULD**: Implementations SHOULD use appropriate concurrency primitives (locks, transactions, etc.).

## See Also

- [Data Model](03-data-model.md) - Task schema definitions
- [Execution Lifecycle](04-execution-lifecycle.md) - State machine and execution rules
- [A2A Protocol Documentation](https://www.a2aprotocol.org/en/docs) - A2A Protocol specification
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification) - JSON-RPC 2.0 standard
