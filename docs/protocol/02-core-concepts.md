# Core Concepts

This section defines the fundamental concepts of the AI Perceivable Flow Protocol. Understanding these concepts is essential for implementing the protocol in any language.

## Protocol Independence

**MUST**: This specification is language-agnostic. Implementations in any programming language MUST adhere to the data structures and behaviors defined here.

**SHOULD**: Implementations SHOULD use standard formats (JSON, JSON Schema) for interoperability.

## Flow

A **Flow** represents a complete workflow or process. It is structured as a hierarchical tree of **Tasks**.

### Flow Characteristics

- **Structure**: A Flow is a Directed Acyclic Graph (DAG) where tasks are nodes and dependencies define the edges.
- **Root Task**: Every flow has a single root task. Complex flows are built by adding children to this root task.
- **Execution**: A flow is executed by executing its root task, which triggers execution of dependent tasks according to dependencies and priorities.

### Flow Lifecycle

1. **Creation**: Flow is created with a root task
2. **Definition**: Tasks are added to the flow (as children or dependencies)
3. **Validation**: Flow structure is validated (no circular dependencies, valid references)
4. **Execution**: Flow is executed (root task starts, dependencies are resolved)
5. **Completion**: Flow completes when all tasks reach terminal states

**MUST**: Implementations MUST support flow creation, validation, and execution.

## Task

A **Task** is the atomic unit of execution within a Flow.

### Task Definition

- **Identity**: Each task has a unique `id` (UUID) that persists across the network.
- **Definition**: A task is defined by its `name` (what to do) and `inputs` (data to work on).
- **State**: A task has a well-defined state (e.g., `pending`, `in_progress`, `completed`).
- **Execution**: A task is executed by an Executor, which processes the task's `inputs` and produces a `result`.

### Task Components

1. **Metadata**: `id`, `name`, `status`, `priority`, `user_id`
2. **Structure**: `parent_id`, `dependencies`
3. **Configuration**: `schemas`, `params`
4. **Data**: `inputs`, `result`, `error`
5. **Tracking**: `progress`, timestamps (`created_at`, `started_at`, `completed_at`)


#### Task Provenance and References

To support provenance and advanced referencing, the following fields are included in the Task model:

- `origin_type`: Indicates how the task was created. Possible values:
    - `create`: Task created freshly
    - `link`: Task linked from another. The source task MUST be in `completed` status (in principle).
    - `copy`: Task copied from another (can be modified)
    - `archive`: Task archive from another (cannot be modified). The source task MUST be in `completed` status (in principle).
- `original_task_id`: The ID of the source task if this task was copied, linked, or snapshotted.
- `has_references`: Boolean indicating whether this task is referenced/copied by others.

These fields enable tracking task lineage, enforcing immutability for snapshots, and ensuring that links/snapshots only reference completed tasks.

See [Data Model](03-data-model.md) for complete task schema.

## Executor

An **Executor** is the component responsible for performing the actual work defined by a Task.

### Executor Role

- **Input**: Takes a Task's `inputs` and `schemas`
- **Processing**: Performs the operation (executor-specific)
- **Output**: Produces a `result` (or raises an error)

### Executor Types

Executors can be categorized by their functionality and implementation:

#### By Functionality

1. **System Executors**: Interact with the local system
   - System information queries (CPU, memory, disk)
   - Command execution (shell commands)
   - File operations

2. **Data Processing Executors**: Process and transform data
   - Data aggregation (combining results from multiple tasks)
   - Data transformation
   - Data validation

3. **External Service Executors**: Interact with external services
   - HTTP/HTTPS requests (REST APIs, webhooks)
   - Database operations
   - Third-party API integrations

4. **AI/LLM Executors**: Execute AI-powered tasks
   - LLM-based agents (e.g., CrewAI)
   - AI model inference
   - Natural language processing

5. **Custom Executors**: User-defined executors for specific use cases
   - Business logic executors
   - Domain-specific operations
   - Integration with proprietary systems

#### By Implementation Category

1. **Built-in Executors**: Provided by the framework implementation
   - System information executors
   - Command executors
   - Result aggregation executors
   - Tool executors (GitHub, web scraping, etc.)

2. **Optional Executors**: Provided by optional extensions
   - LLM executors (requires AI/LLM dependencies)
   - HTTP executors (may require additional dependencies)
   - Specialized executors

3. **Custom Executors**: Created by users
   - User-defined executors implementing the Executor interface
   - Registered with ExecutorRegistry

**MUST**: The protocol defines *how* to invoke an executor, but not *what* the executor does internally.

**Note**: Specific executor implementations (e.g., `system_info_executor`, `command_executor`, `crew_manager`) are implementation-specific. The protocol only specifies the interface and registration mechanism, not the specific executor types that must be provided.

### Common Executor Patterns

While the protocol does not mandate specific executor types, common patterns include:

1. **System Information Executors**: Query system resources (CPU, memory, disk)
2. **Command Executors**: Execute shell commands or system operations
3. **Data Aggregation Executors**: Combine results from multiple dependent tasks
4. **HTTP/API Executors**: Make HTTP requests to external services
5. **LLM Executors**: Execute AI/LLM-powered tasks (requires AI dependencies)
6. **Tool Executors**: Integrate with external tools (GitHub, web scraping, etc.)

**MUST**: Implementations MUST support custom executors for user-defined functionality.

**SHOULD**: Implementations SHOULD provide common built-in executors for standard operations.

**MAY**: Implementations MAY provide specialized executors for specific domains.

### Executor Interface Specification

All executors MUST implement the following interface (language-agnostic specification):

#### Required Methods

**`execute(inputs: Object) -> Object`**

Executes the task with the given inputs.

**Input**:
- `inputs` (object): Task inputs (from `task.inputs`)

**Output**:
- Returns: Execution result (any JSON-serializable object)
- Throws: Error if execution fails

**MUST**: Executors MUST return a result object (not a primitive value).  
**MUST**: Executors MUST raise/throw errors for execution failures.  
**SHOULD**: Executors SHOULD validate inputs before execution.

**Example** (conceptual):
```python
# Python example (for reference only)
async def execute(self, inputs):
    # Validate inputs
    if not inputs.get("url"):
        raise ValueError("url is required")
    
    # Perform work
    result = await fetch_url(inputs["url"])
    
    # Return result
    return {"content": result, "status": "success"}
```

#### Optional Methods

**`cancel() -> void`**

Cancels the execution if supported.

**MUST**: If executor does not support cancellation, this method MAY not exist or MAY be a no-op.  
**SHOULD**: If executor supports cancellation, it SHOULD stop execution gracefully.

**`get_input_schema() -> Object`**

Returns JSON Schema defining valid inputs.

**SHOULD**: Executors SHOULD provide input schema for validation.  
**MAY**: If not provided, inputs are not validated against a schema.

**Example** (conceptual):
```python
# Python example (for reference only)
def get_input_schema(self):
    return {
        "type": "object",
        "required": ["url"],
        "properties": {
            "url": {
                "type": "string",
                "format": "uri"
            }
        }
    }
```

### Executor Registration

Executors MUST be registered with an `ExecutorRegistry` before they can be used.

**Registration Requirements**:
1. **Identifier**: Each executor has a unique identifier (the `method` name in `schemas.method`)
2. **Registry**: Executors are registered in an `ExecutorRegistry`
3. **Lookup**: When a task is executed, the executor is looked up by `schemas.method`

**MUST**: Implementations MUST provide an `ExecutorRegistry` mechanism.  
**MUST**: Executor identifiers MUST be unique within a registry.  
**SHOULD**: Registration SHOULD happen before task execution.

**Implementation Note**: The specific registration mechanism (decorators, function calls, configuration files) is implementation-specific. The protocol only specifies that executors must be registered and accessible via the `method` identifier.

### Executor Execution Contract

**Input Contract**:
- Executor receives `task.inputs` as input
- Inputs MAY be validated against `task.schemas.input_schema` (if present)
- Executor MAY access `task.schemas` and `task.params` for configuration

**Output Contract**:
- Executor MUST return a result object (JSON-serializable)
- Result is stored in `task.result` when task completes
- If executor raises/throws an error, task status is set to `failed` and error is stored in `task.error`

**Error Contract**:
- Executor errors MUST be captured and stored in `task.error`
- Error messages SHOULD be descriptive and include context

## Node

A **Node** is a participant in the network that implements the protocol.

### Node Capabilities

A node can:
- **Submit Flows**: Create and submit task flows for execution
- **Execute Tasks**: Execute tasks using registered executors
- **Store Results**: Persist task state and results
- **Provide API**: Expose protocol-compliant API for external clients

### Node Interoperability

**MUST**: Nodes running different language implementations (Python, Go, Rust) MUST be able to communicate as long as they adhere to the Data Protocol.

**MUST**: Nodes MUST use standard data formats (JSON) for communication.

**SHOULD**: Nodes SHOULD validate incoming data against protocol schemas.

## TaskManager

**TaskManager** is the orchestrator that coordinates task execution, dependency resolution, and priority scheduling.

### TaskManager Responsibilities

1. **Task Execution**: Manages task execution lifecycle
2. **Dependency Resolution**: Ensures tasks wait for dependencies
3. **Priority Scheduling**: Executes tasks in priority order
4. **State Management**: Tracks task state transitions
5. **Error Handling**: Handles execution failures and errors

### TaskManager Behavior Specification

#### Orchestration Algorithm

The TaskManager MUST follow this algorithm for task execution:

```
function executeTaskTree(rootTask):
    // 1. Validate task tree
    validateTaskTree(rootTask)
    
    // 2. Initialize all tasks to pending
    initializeTasks(rootTask)
    
    // 3. Execute loop
    while hasPendingTasks(rootTask):
        // 3.1. Find ready tasks (dependencies satisfied)
        readyTasks = findReadyTasks(rootTask)
        
        // 3.2. Sort by priority
        sortedTasks = sortByPriority(readyTasks)
        
        // 3.3. Execute ready tasks (concurrently if possible)
        for task in sortedTasks:
            executeTask(task)
        
        // 3.4. Wait for tasks to complete or fail
        waitForTasks(sortedTasks)
    
    // 4. Return final state
    return rootTask
```

**MUST**: Implementations MUST follow this general algorithm.  
**MAY**: Implementations MAY optimize or parallelize execution.

#### Dependency Resolution

TaskManager MUST resolve dependencies before allowing task execution:

```
function canExecute(task):
    // Check all dependencies
    for dependency in task.dependencies:
        dep_task = getTask(dependency.id)
        
        // Check if dependency is ready
        if dep_task.status == "pending" or dep_task.status == "in_progress":
            return false  // Not ready
        
        // Check required dependencies
        if dependency.required == true:
            if dep_task.status != "completed":
                return false  // Required dependency failed
    
    return true  // All dependencies satisfied
```

See [Execution Lifecycle](04-execution-lifecycle.md) for detailed dependency resolution rules.

#### Priority Scheduling

TaskManager MUST schedule tasks by priority:

```
function sortByPriority(tasks):
    // Group by priority
    groups = {}
    for task in tasks:
        priority = task.priority ?? 2  // Default: 2
        if priority not in groups:
            groups[priority] = []
        groups[priority].append(task)
    
    // Sort groups (ascending: 0, 1, 2, 3)
    sorted_groups = sorted(groups.keys())
    
    // Flatten
    result = []
    for priority in sorted_groups:
        result.extend(groups[priority])
    
    return result
```

**MUST**: Lower priority values (0) MUST execute before higher values (3).  
**SHOULD**: Tasks with the same priority SHOULD be executed fairly (FIFO, round-robin, etc.).

#### Concurrency Control

TaskManager MAY execute multiple tasks concurrently:

**MUST**: Implementations MUST ensure only one execution of a task at a time.  
**SHOULD**: Implementations SHOULD support concurrent execution of independent tasks.  
**MAY**: Implementations MAY limit concurrency based on available resources.

### TaskManager Interface

TaskManager MUST provide the following operations (language-agnostic):

**`distributeTaskTree(taskTree: TaskTreeNode) -> TaskTreeNode`**

Executes a task tree with dependency management and priority scheduling.

**Input**:
- `taskTree` (TaskTreeNode): Root task with children

**Output**:
- Returns: Updated task tree with execution results

**MUST**: TaskManager MUST execute tasks according to dependencies and priorities.  
**MUST**: TaskManager MUST handle errors and update task status accordingly.

**`cancelTask(taskId: String, errorMessage: String?) -> void`**

Cancels a running task.

**Input**:
- `taskId` (string): Task ID to cancel
- `errorMessage` (string, optional): Cancellation message

**MUST**: TaskManager MUST transition task to `cancelled` status.  
**SHOULD**: TaskManager SHOULD attempt to stop executor execution.

## Storage Requirements

The protocol requires persistent storage for task state and results.

### Storage Interface Specification

Storage MUST provide the following operations (language-agnostic):

#### Required Operations

**`createTask(task: Task) -> Task`**

Creates a new task in storage.

**MUST**: Storage MUST generate unique UUID for task `id` if not provided.  
**MUST**: Storage MUST persist all task fields.

**`getTask(taskId: String) -> Task`**

Retrieves a task by ID.

**MUST**: Storage MUST return task if exists, or error if not found.

**`updateTask(taskId: String, updates: Object) -> Task`**

Updates task fields.

**MUST**: Storage MUST validate updates against task schema.  
**MUST**: Storage MUST persist updates atomically.

**`deleteTask(taskId: String) -> void`**

Deletes a task from storage.

**MUST**: Storage MUST only delete tasks with status `pending`.  
**MUST**: Storage MUST reject deletion if task has children or dependents.

**`listTasks(filters: Object) -> Array<Task>`**

Lists tasks with optional filters.

**SHOULD**: Storage SHOULD support filtering by `status`, `user_id`, etc.  
**SHOULD**: Storage SHOULD support pagination (`limit`, `offset`).

**`getTaskTree(rootTaskId: String) -> TaskTreeNode`**

Retrieves complete task tree.

**MUST**: Storage MUST return complete tree structure (all descendants).

#### Query Operations

**`findDependentTasks(taskId: String) -> Array<Task>`**

Finds all tasks that depend on a given task.

**MUST**: Storage MUST return all tasks that reference `taskId` in their `dependencies`.

**`getChildren(parentId: String) -> Array<Task>`**

Gets direct children of a task.

**MUST**: Storage MUST return only direct children (not grandchildren).

### Storage Consistency Requirements

**MUST**: Storage MUST ensure data consistency:
- Task state transitions follow state machine rules
- Field values are consistent with status
- Dependencies reference valid tasks
- Parent-child relationships are valid

**SHOULD**: Storage SHOULD use transactions for atomic updates.

**MAY**: Storage MAY support different backends (SQL, NoSQL, in-memory).

### Storage Schema

Storage MUST persist the following task fields:

- **Identity**: `id`, `parent_id`, `user_id`
- **Definition**: `name`, `status`, `priority`
- **Configuration**: `schemas`, `params`
- **Data**: `inputs`, `result`, `error`
- **Structure**: `dependencies`
- **Tracking**: `progress`, `created_at`, `started_at`, `updated_at`, `completed_at`

**MUST**: Storage MUST persist all required fields.  
**SHOULD**: Storage SHOULD index frequently queried fields (`id`, `parent_id`, `user_id`, `status`).

## Extension Points

The protocol provides extension points for custom functionality:

1. **Custom Executors**: Implement custom executors for specific use cases
2. **Storage Backends**: Implement custom storage backends
3. **Transport Layers**: Implement custom transport layers (beyond HTTP)

**MUST**: Implementations MUST support custom executors.  
**MAY**: Implementations MAY support custom storage backends and transport layers.

## See Also

- [Data Model](03-data-model.md) - Complete task schema and data structures
- [Execution Lifecycle](04-execution-lifecycle.md) - State machine and execution rules
- [Interface Protocol](06-interfaces.md) - API specifications
- [Conformance](07-conformance.md) - Implementation requirements
