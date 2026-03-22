# Complete Task Example

This example shows a fully populated Task object with all standard fields. Use this as a reference for constructing valid tasks.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_id": null,
  "user_id": "user-123",
  "name": "system resources",
  "status": "pending",
  "priority": 2,
  "inputs": {
    "resource": "cpu"
  },
  "schemas": {
    "method": "system_info_executor",
    "input_schema": {
      "type": "object",
      "properties": {
        "resource": {
          "type": "string",
          "enum": ["cpu", "memory", "disk", "all"]
        }
      }
    }
  },
  "params": null,
  "result": null,
  "error": null,
  "dependencies": [],
  "progress": 0.0,
  "created_at": "2025-01-15T10:30:00Z",
  "started_at": null,
  "updated_at": "2025-01-15T10:30:00Z",
  "completed_at": null,
  "origin_type": "create",
  "original_task_id": null,
  "has_references": false
}
```
# Example 10: Linked and Snapshotted Tasks

Demonstrates a task created by linking to a completed source task.

### Source Task (Completed)

```json
{
  "id": "source-task-uuid",
  "name": "Generate Report",
  "status": "completed",
  "result": {"report": "..."},
  "created_at": "2025-01-15T09:00:00Z"
}
```

### Linked Task

```json
{
  "id": "linked-task-uuid",
  "name": "Generate Report",
  "status": "pending",
  "origin_type": "link",
  "original_task_id": "source-task-uuid",
  "created_at": "2025-01-15T12:00:00Z"
}
```

**Note:** For `origin_type: link` or `archive`, the `original_task_id` MUST reference a task in `completed` status (in principle).
# Protocol Examples

This section provides comprehensive examples demonstrating the AI Perceivable Flow Protocol. These examples are language-agnostic and can be implemented in any programming language.

## Example 1: Simple Task Execution

The simplest possible task execution - a single task with no dependencies.

### Task Definition

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_id": null,
  "user_id": "user-123",
  "name": "system resources",
  "status": "pending",
  "priority": 2,
  "inputs": {
    "resource": "cpu"
  },
  "schemas": {
    "method": "system_info_executor",
    "input_schema": {
      "type": "object",
      "properties": {
        "resource": {
          "type": "string",
          "enum": ["cpu", "memory", "disk", "all"]
        }
      }
    }
  },
  "params": null,
  "result": null,
  "error": null,
  "dependencies": [],
  "progress": 0.0,
  "created_at": "2025-01-15T10:30:00Z",
  "started_at": null,
  "updated_at": "2025-01-15T10:30:00Z",
  "completed_at": null,
  "origin_type": "create",
  "original_task_id": null,
  "has_references": false
}
```

### Execution Flow

1. Task is created with `status: "pending"`
2. TaskManager checks dependencies (none) → task is ready
3. TaskManager checks priority (2 = normal) → schedules execution
4. Executor is looked up by `schemas.method: "system_info_executor"`
5. Executor's `execute()` is called with `inputs: {"resource": "cpu"}`
6. Task status transitions: `pending` → `in_progress`
7. Executor returns result
8. Task status transitions: `in_progress` → `completed`
9. Result is stored in `task.result`

### Expected Result

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "cpu": {
      "cores": 8,
      "usage": 45.2
    }
  },
  "progress": 1.0,
  "started_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:30:01Z"
}
```

## Example 2: Sequential Tasks (Dependencies)

Two tasks where the second depends on the first.

### Task Definitions

```json
{
  "tasks": [
    {
      "id": "task-1",
      "name": "fetch_data",
      "status": "pending",
      "priority": 1,
      "inputs": {
        "url": "https://api.example.com/data"
      },
      "schemas": {
        "method": "http_fetcher"
      },
      "dependencies": []
    },
    {
      "id": "task-2",
      "name": "process_data",
      "status": "pending",
      "priority": 2,
      "inputs": {
        "operation": "analyze"
      },
      "schemas": {
        "method": "data_processor"
      },
      "dependencies": [
        {
          "id": "task-1",
          "required": true
        }
      ]
    }
  ]
}
```

### Execution Flow

1. Both tasks are created with `status: "pending"`
2. Task 1 has no dependencies → ready to execute
3. Task 1 executes: `pending` → `in_progress` → `completed`
4. Task 2 checks dependencies:
   - Dependency `task-1` has `status: "completed"` → satisfied
   - Task 2 is ready to execute
5. Task 2 executes: `pending` → `in_progress` → `completed`

### Expected Results

**Task 1**:
```json
{
  "id": "task-1",
  "status": "completed",
  "result": {
    "data": [1, 2, 3, 4, 5]
  }
}
```

**Task 2**:
```json
{
  "id": "task-2",
  "status": "completed",
  "result": {
    "analysis": {
      "count": 5,
      "sum": 15,
      "average": 3.0
    }
  }
}
```

## Example 3: Parallel Tasks

Multiple tasks with no dependencies between them, executing in parallel.

### Task Definitions

```json
{
  "tasks": [
    {
      "id": "root-task",
      "name": "root",
      "status": "pending",
      "parent_id": null
    },
    {
      "id": "task-1",
      "name": "fetch_user_data",
      "status": "pending",
      "parent_id": "root-task",
      "priority": 2,
      "inputs": {"user_id": "user-123"}
    },
    {
      "id": "task-2",
      "name": "fetch_product_data",
      "status": "pending",
      "parent_id": "root-task",
      "priority": 2,
      "inputs": {"product_id": "prod-456"}
    },
    {
      "id": "task-3",
      "name": "fetch_order_data",
      "status": "pending",
      "parent_id": "root-task",
      "priority": 2,
      "inputs": {"order_id": "order-789"}
    }
  ]
}
```

### Execution Flow

1. All tasks are created with `status: "pending"`
2. All tasks have no dependencies → all ready to execute
3. All tasks have same priority (2) → can execute in parallel
4. TaskManager executes all three tasks concurrently
5. All tasks complete independently

### Expected Results

All three tasks complete in parallel, with results stored independently.

## Example 4: Complex Task Tree with Dependencies

A complex workflow with multiple levels of dependencies.

### Task Tree Structure

```
Root Task
│
├── Task A (no dependencies)
│
├── Task B (depends on A)
│   │
│   └── Task D (depends on B)
│
└── Task C (depends on A)
    │
    └── Task E (depends on C and D)
```

### Task Definitions

```json
{
  "tasks": [
    {
      "id": "root",
      "name": "root",
      "status": "pending",
      "parent_id": null
    },
    {
      "id": "task-a",
      "name": "Task A",
      "status": "pending",
      "parent_id": "root",
      "priority": 1,
      "dependencies": []
    },
    {
      "id": "task-b",
      "name": "Task B",
      "status": "pending",
      "parent_id": "root",
      "priority": 2,
      "dependencies": [
        {"id": "task-a", "required": true}
      ]
    },
    {
      "id": "task-c",
      "name": "Task C",
      "status": "pending",
      "parent_id": "root",
      "priority": 2,
      "dependencies": [
        {"id": "task-a", "required": true}
      ]
    },
    {
      "id": "task-d",
      "name": "Task D",
      "status": "pending",
      "parent_id": "root",
      "priority": 3,
      "dependencies": [
        {"id": "task-b", "required": true}
      ]
    },
    {
      "id": "task-e",
      "name": "Task E",
      "status": "pending",
      "parent_id": "root",
      "priority": 4,
      "dependencies": [
        {"id": "task-c", "required": true},
        {"id": "task-d", "required": true}
      ]
    }
  ]
}
```

### Execution Flow

1. **Phase 1**: Task A executes (no dependencies)
2. **Phase 2**: Tasks B and C execute in parallel (both depend on A)
3. **Phase 3**: Task D executes (depends on B)
4. **Phase 4**: Task E executes (depends on C and D)

### Execution Timeline

```
Time 0:  Task A starts
Time 1:  Task A completes
Time 1:  Tasks B and C start (parallel)
Time 2:  Tasks B and C complete
Time 2:  Task D starts
Time 3:  Task D completes
Time 3:  Task E starts
Time 4:  Task E completes
```

## Example 5: Error Handling

Demonstrates error handling when a task fails.

### Task Definitions

```json
{
  "tasks": [
    {
      "id": "task-1",
      "name": "fetch_data",
      "status": "pending",
      "inputs": {"url": "https://invalid-url.example.com"}
    },
    {
      "id": "task-2",
      "name": "process_data",
      "status": "pending",
      "dependencies": [
        {"id": "task-1", "required": true}
      ]
    }
  ]
}
```

### Execution Flow

1. Task 1 executes and fails (invalid URL)
2. Task 1 status: `pending` → `in_progress` → `failed`
3. Task 2 checks dependencies:
   - Dependency `task-1` has `status: "failed"` and `required: true`
   - Task 2 cannot execute
4. Task 2 remains in `pending` status

### Expected Results

**Task 1** (Failed):
```json
{
  "id": "task-1",
  "status": "failed",
  "error": "Connection failed: Unable to resolve host 'invalid-url.example.com'",
  "completed_at": "2025-01-15T10:30:05Z"
}
```

**Task 2** (Blocked):
```json
{
  "id": "task-2",
  "status": "pending",
  "dependencies": [
    {"id": "task-1", "required": true}
  ]
}
```

## Example 6: Optional Dependencies

Demonstrates optional dependencies where a task can execute even if dependency fails.

### Task Definitions

```json
{
  "tasks": [
    {
      "id": "primary",
      "name": "primary_source",
      "status": "pending"
    },
    {
      "id": "fallback",
      "name": "fallback_source",
      "status": "pending"
    },
    {
      "id": "aggregate",
      "name": "aggregate_data",
      "status": "pending",
      "dependencies": [
        {"id": "primary", "required": false},
        {"id": "fallback", "required": false}
      ]
    }
  ]
}
```

### Execution Flow

1. Primary task fails
2. Fallback task completes successfully
3. Aggregate task checks dependencies:
   - Primary: `failed`, `required: false` → can proceed
   - Fallback: `completed`, `required: false` → can proceed
4. Aggregate task executes (uses fallback data)

## Example 7: Priority Scheduling

Demonstrates priority-based scheduling.

### Task Definitions

```json
{
  "tasks": [
    {
      "id": "urgent-task",
      "name": "Urgent Task",
      "status": "pending",
      "priority": 0
    },
    {
      "id": "normal-task",
      "name": "Normal Task",
      "status": "pending",
      "priority": 2
    },
    {
      "id": "low-task",
      "name": "Low Priority Task",
      "status": "pending",
      "priority": 3
    }
  ]
}
```

### Execution Flow

All tasks are ready (no dependencies). Execution order:
1. Urgent task (priority 0)
2. Normal task (priority 2)
3. Low priority task (priority 3)

## Example 8: Re-execution

Demonstrates re-executing a failed task.

### Initial State

```json
{
  "id": "task-1",
  "status": "failed",
  "error": "Temporary network error",
  "result": null,
  "progress": 0.0
}
```

### Re-execution Request

Reset task to `pending` status:

```json
{
  "id": "task-1",
  "status": "pending",
  "error": null,
  "result": null,
  "progress": 0.0,
  "started_at": null,
  "completed_at": null
}
```

### Execution Flow

1. Task status reset: `failed` → `pending`
2. Task executes again: `pending` → `in_progress` → `completed`
3. Task completes successfully

## Example 9: Copy Execution

Demonstrates copying a task before execution.

### Original Task

```json
{
  "id": "original-task",
  "name": "My Task",
  "status": "completed",
  "result": {"output": "result"},
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Copied Task

```json
{
  "id": "copied-task",
  "name": "My Task",
  "status": "pending",
  "result": null,
  "created_at": "2025-01-15T11:00:00Z"
}
```

### Key Differences

- New `id` (UUID)
- `status` reset to `pending`
- `result` reset to `null`
- New `created_at` timestamp
- Original task unchanged

## Executor Type Examples

The protocol supports various executor types. Here are examples of common executor patterns:

### System Information Executor

```json
{
  "id": "task-1",
  "name": "system_info_executor",
  "schemas": {
    "method": "system_info_executor"
  },
  "inputs": {
    "resource": "cpu"
  }
}
```

**Purpose**: Query system resources (CPU, memory, disk).

### Command Executor

```json
{
  "id": "task-2",
  "name": "command_executor",
  "schemas": {
    "method": "command_executor"
  },
  "inputs": {
    "command": "ls -la",
    "cwd": "/tmp"
  }
}
```

**Purpose**: Execute shell commands or system operations.

### Data Aggregation Executor

```json
{
  "id": "task-3",
  "name": "aggregate_results_executor",
  "schemas": {
    "method": "aggregate_results_executor"
  },
  "inputs": {},
  "dependencies": [
    {"id": "task-1", "required": true},
    {"id": "task-2", "required": true}
  ]
}
```

**Purpose**: Combine results from multiple dependent tasks.

### LLM Executor (CrewAI)

```json
{
  "id": "task-4",
  "name": "crew_manager",
  "schemas": {
    "method": "crew_manager"
  },
  "inputs": {
    "text": "Analyze this data..."
  },
  "params": {
    "agents": [...],
    "tasks": [...]
  }
}
```

**Purpose**: Execute AI/LLM-powered tasks (requires AI dependencies).

**Note**: LLM executors typically require additional configuration in `params` (agents, tasks, etc.).

### HTTP/API Executor

```json
{
  "id": "task-5",
  "name": "http_request_executor",
  "schemas": {
    "method": "http_request_executor"
  },
  "inputs": {
    "url": "https://api.example.com/data",
    "method": "GET",
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

**Purpose**: Make HTTP requests to external services.

### Custom Executor

```json
{
  "id": "task-6",
  "name": "my_custom_executor",
  "schemas": {
    "method": "my_custom_executor"
  },
  "inputs": {
    "custom_param": "value"
  }
}
```

**Purpose**: User-defined executor for specific business logic.

**Note**: Custom executors must be registered with ExecutorRegistry before use.

## Multi-Language Implementation Examples

### Python Reference Implementation

```python
# Python example (reference implementation)
import asyncio
from uuid import uuid4

async def execute_task(task, executor_registry):
    # Look up executor
    executor = executor_registry.get(task.schemas.method)
    if not executor:
        raise ValueError(f"Executor not found: {task.schemas.method}")
    
    # Execute
    result = await executor.execute(task.inputs)
    
    # Update task
    task.status = "completed"
    task.result = result
    task.progress = 1.0
    
    return task
```

### Go Implementation Example

```go
// Go example (conceptual)
package main

type Task struct {
    ID     string                 `json:"id"`
    Name   string                 `json:"name"`
    Status string                 `json:"status"`
    Inputs map[string]interface{} `json:"inputs"`
    Result map[string]interface{} `json:"result"`
}

func ExecuteTask(task Task, registry ExecutorRegistry) (Task, error) {
    executor, err := registry.Get(task.Schemas.Method)
    if err != nil {
        return task, err
    }
    
    result, err := executor.Execute(task.Inputs)
    if err != nil {
        task.Status = "failed"
        task.Error = err.Error()
        return task, err
    }
    
    task.Status = "completed"
    task.Result = result
    task.Progress = 1.0
    
    return task, nil
}
```

### Rust Implementation Example

```rust
// Rust example (conceptual)
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
struct Task {
    id: Uuid,
    name: String,
    status: String,
    inputs: serde_json::Value,
    result: Option<serde_json::Value>,
}

async fn execute_task(
    task: Task,
    registry: &ExecutorRegistry,
) -> Result<Task, Box<dyn std::error::Error>> {
    let executor = registry.get(&task.schemas.method)?;
    let result = executor.execute(task.inputs).await?;
    
    Ok(Task {
        status: "completed".to_string(),
        result: Some(result),
        ..task
    })
}
```

### JavaScript/TypeScript Implementation Example

```typescript
// TypeScript example (conceptual)
interface Task {
  id: string;
  name: string;
  status: string;
  inputs: Record<string, any>;
  result?: Record<string, any>;
}

async function executeTask(
  task: Task,
  registry: ExecutorRegistry
): Promise<Task> {
  const executor = registry.get(task.schemas.method);
  if (!executor) {
    throw new Error(`Executor not found: ${task.schemas.method}`);
  }
  
  const result = await executor.execute(task.inputs);
  
  return {
    ...task,
    status: "completed",
    result,
    progress: 1.0,
  };
}
```

## Protocol Compliance Examples

### Valid Task Definition

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "valid_task",
  "status": "pending",
  "priority": 2,
  "inputs": {"key": "value"},
  "schemas": {
    "method": "executor_id"
  },
  "dependencies": []
}
```

✅ **Valid**: All required fields present, valid types, no circular dependencies.

### Invalid Task Definitions

#### Missing Required Field

```json
{
  "name": "invalid_task"
  // Missing: id, status
}
```

❌ **Invalid**: Missing required fields `id` and `status`.

#### Invalid UUID Format

```json
{
  "id": "not-a-uuid",
  "name": "invalid_task",
  "status": "pending"
}
```

❌ **Invalid**: `id` must be valid UUID v4 format.

#### Invalid Status Value

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "invalid_task",
  "status": "invalid_status"
}
```

❌ **Invalid**: `status` must be one of: `pending`, `in_progress`, `completed`, `failed`, `cancelled`.

#### Priority Out of Range

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "invalid_task",
  "status": "pending",
  "priority": 10
}
```

❌ **Invalid**: `priority` must be in range 0-3.

#### Circular Dependency

```json
{
  "tasks": [
    {
      "id": "task-a",
      "dependencies": [{"id": "task-b", "required": true}]
    },
    {
      "id": "task-b",
      "dependencies": [{"id": "task-a", "required": true}]
    }
  ]
}
```

❌ **Invalid**: Circular dependency detected (A depends on B, B depends on A).

## Edge Cases

### Empty Task Tree

```json
{
  "task": {
    "id": "root",
    "name": "root",
    "status": "pending"
  },
  "children": []
}
```

✅ **Valid**: Single root task with no children.

### Task with Many Dependencies

```json
{
  "id": "task-1",
  "dependencies": [
    {"id": "dep-1", "required": true},
    {"id": "dep-2", "required": true},
    {"id": "dep-3", "required": true},
    {"id": "dep-4", "required": false},
    {"id": "dep-5", "required": false}
  ]
}
```

✅ **Valid**: Task can have multiple dependencies (both required and optional).

### Task with Deep Nesting

```
Root
└── Level 1
    └── Level 2
        └── Level 3
            └── Level 4
```

✅ **Valid**: Tasks can be nested to any depth (implementation may have limits).

## See Also

- [Data Model](03-data-model.md) - Complete task schema
- [Execution Lifecycle](04-execution-lifecycle.md) - State machine and execution rules
- [Core Concepts](02-core-concepts.md) - Fundamental concepts
- [Validation](09-validation.md) - Validation rules
