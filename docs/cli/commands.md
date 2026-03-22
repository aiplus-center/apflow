# CLI Commands Reference

Complete reference of all CLI commands for executing and managing tasks.

## Task Execution

### apflow run

Execute a task or batch of tasks:

```bash
apflow run <batch_id> [OPTIONS]
```

**Options**:
- `--tasks <json>` - Task definition in JSON format (required)
- `--inputs <json>` - Task inputs as JSON (optional)
- `--tags <tag1,tag2>` - Task tags (optional)
- `--priority <priority>` - Task priority: low, normal, high (default: normal)
- `--user-id <id>` - User ID (optional)
- `--timeout <seconds>` - Execution timeout (default: 300)
- `--retry-count <count>` - Retry failed tasks (default: 0)
- `--retry-delay <seconds>` - Delay between retries (default: 1)
- `--parallel-count <count>` - Run multiple tasks in parallel (default: 1)
- `--demo-mode` - Run in demo mode (for testing)

**Examples**:

Basic execution:
```bash
apflow run batch-001 --tasks '[
  {
    "id": "task1",
    "name": "Check CPU",
    "schemas": {"method": "system_info_executor"},
    "inputs": {"resource": "cpu"}
  }
]'
```

With inputs and tags:
```bash
apflow run batch-002 --tasks '[{...}]' \
  --inputs '{"config": "value"}' \
  --tags production,monitoring \
  --priority high
```

Parallel execution:
```bash
apflow run batch-003 --tasks '[{...}, {...}, {...}]' \
  --parallel-count 3
```

With retry:
```bash
apflow run batch-004 --tasks '[{...}]' \
  --retry-count 3 \
  --retry-delay 5
```

## Task Querying

### apflow tasks list

List all tasks in database:

```bash
apflow tasks list [OPTIONS]
```

**Options**:
- `--user-id <id>` - Filter by user ID
- `--status <status>` - Filter by status: pending, running, completed, failed, cancelled
- `--batch-id <id>` - Filter by batch ID
- `--limit <count>` - Limit results (default: 100)
- `--offset <count>` - Skip N results (default: 0)
- `--sort <field>` - Sort by field: created_at, updated_at, status
- `--reverse` - Reverse sort order

**Examples**:

List all tasks:
```bash
apflow tasks list
```

List by user:
```bash
apflow tasks list --user-id user123
```

List failed tasks:
```bash
apflow tasks list --status failed
```

List with pagination:
```bash
apflow tasks list --limit 50 --offset 0
```

List and sort by date:
```bash
apflow tasks list --sort created_at --reverse
```

### apflow tasks status

Get status of a specific task:

```bash
apflow tasks status <task_id> [OPTIONS]
```

**Options**:
- `--include-details` - Include full task details
- `--watch` - Watch for changes (exit with Ctrl+C)
- `--watch-interval <seconds>` - Polling interval when watching (default: 1)

**Examples**:

Check status:
```bash
apflow tasks status task-001
```

With full details:
```bash
apflow tasks status task-001 --include-details
```

Watch for completion:
```bash
apflow tasks status task-001 --watch
# Press Ctrl+C to stop watching
```

### apflow tasks watch

Monitor task execution in real-time:

```bash
apflow tasks watch [OPTIONS]
```

**Options**:
- `--task-id <id>` - Watch specific task
- `--all` - Watch all running tasks
- `--batch-id <id>` - Watch tasks in batch
- `--user-id <id>` - Watch user's tasks
- `--interval <seconds>` - Polling interval (default: 1)

**Examples**:

Watch single task:
```bash
apflow tasks watch --task-id task-001
```

Watch all running tasks:
```bash
apflow tasks watch --all
```

Watch batch:
```bash
apflow tasks watch --batch-id batch-001
```

Watch with slower polling:
```bash
apflow tasks watch --all --interval 5
```

## Task Cancellation

### apflow tasks cancel

Cancel one or more running tasks:

```bash
apflow tasks cancel <task_ids>... [OPTIONS]
```

**Options**:
- `--force` / `-f` - Force immediate cancellation
- `--error-message` / `-m` - Custom error message for cancellation (default: "Cancelled by user" or "Force cancelled by user")

**Examples**:

Cancel task:
```bash
apflow tasks cancel task-001
```

Cancel multiple tasks:
```bash
apflow tasks cancel task-001 task-002 task-003
```

Force cancel:
```bash
apflow tasks cancel task-001 --force
```

Cancel with custom message:
```bash
apflow tasks cancel task-001 --error-message "Incorrect parameters"
```

## Task Management

### apflow tasks create

Create a task without executing:

```bash
apflow tasks create [OPTIONS]
```

**Options**:
- `--name <name>` - Task name (required)
- `--method <method>` - Executor method (required)
- `--inputs <json>` - Task inputs as JSON
- `--tags <tags>` - Task tags
- `--description <text>` - Task description
- `--batch-id <id>` - Batch ID

**Examples**:

Create task:
```bash
apflow tasks create --name "CPU Check" --method system_info_executor \
  --inputs '{"resource": "cpu"}'
```

With batch and tags:
```bash
apflow tasks create --name "Memory Check" --method system_info_executor \
  --batch-id batch-001 --tags monitoring,system
```

### apflow tasks update

Update task configuration:

```bash
apflow tasks update <task_id> [OPTIONS]
```

**Options**:
- `--name <name>` - Update task name
- `--inputs <json>` - Update task inputs
- `--tags <tags>` - Update task tags
- `--status <status>` - Update task status
- `--description <text>` - Update description
- `--validate` - Validate changes before applying

**Examples**:

Update task name:
```bash
apflow tasks update task-001 --name "New Name"
```

Update inputs:
```bash
apflow tasks update task-001 --inputs '{"resource": "memory"}'
```

Update with validation:
```bash
apflow tasks update task-001 --inputs '{"resource": "disk"}' --validate
```

### apflow tasks delete

Delete a task:

```bash
apflow tasks delete <task_id> [OPTIONS]
```

**Options**:
- `--force` - Delete without confirmation
- `--reason <text>` - Deletion reason
- `--keep-logs` - Keep execution logs after deletion

**Examples**:

Delete task:
```bash
apflow tasks delete task-001
```

Force delete:
```bash
apflow tasks delete task-001 --force
```

Delete and keep logs:
```bash
apflow tasks delete task-001 --force --keep-logs
```


### apflow tasks clone

Clone (copy/link/archive) a task tree. `tasks copy` is a backward-compatible alias.

```bash
apflow tasks clone <task_id> [OPTIONS]
```

**Options**:
- `--origin-type <type>` - Origin type: `copy` (default), `link`, `archive`, or `mixed`
- `--recursive/--no-recursive` - Clone/link entire subtree (default: True)
- `--link-task-ids <ids>` - Comma-separated task IDs to link (for mixed mode)
- `--reset-fields <fields>` - Field overrides as key=value pairs (e.g., 'user_id=new_user,priority=1')
- `--dry-run` - Preview clone without saving to database

**Examples**:

Clone task (default copy mode):
```bash
apflow tasks clone task-001
```

Clone to new batch (with field override):
```bash
apflow tasks clone task-001 --reset-fields batch_id=batch-002
```

Clone with incremented name:
```bash
apflow tasks clone task-001 --reset-fields name="Task (copy)"
```

Clone and reset status:
```bash
apflow tasks clone task-001 --reset-fields status=pending
```

> **Note:** `apflow tasks copy` is a supported alias for backward compatibility and accepts the same options.

## Flow Management

### apflow flow run

Execute a flow (batch of tasks):

```bash
apflow flow run <flow_id> [OPTIONS]
```

**Options**:
- `--tasks <json>` - Task definitions (required)
- `--inputs <json>` - Flow inputs
- `--parallel-count <count>` - Tasks to run in parallel
- `--skip-failed` - Continue even if task fails
- `--timeout <seconds>` - Flow timeout

**Examples**:

Run flow:
```bash
apflow flow run flow-001 --tasks '[{...}, {...}]'
```

Run with parallelism:
```bash
apflow flow run flow-002 --tasks '[...]' --parallel-count 3
```

Skip failed tasks:
```bash
apflow flow run flow-003 --tasks '[...]' --skip-failed
```

### apflow flow status

Get flow execution status:

```bash
apflow flow status <flow_id>
```

**Examples**:

Check flow status:
```bash
apflow flow status flow-001
```

### apflow flow cancel

Cancel a flow:

```bash
apflow flow cancel <flow_id> [OPTIONS]
```

**Options**:
- `--force` - Force cancellation
- `--cancel-tasks` - Cancel remaining tasks in flow

**Examples**:

Cancel flow:
```bash
apflow flow cancel flow-001
```

Cancel with tasks:
```bash
apflow flow cancel flow-001 --cancel-tasks
```

## Query and Filtering

### Common Filter Patterns

Filter by status:
```bash
apflow tasks list --status running
apflow tasks list --status completed
apflow tasks list --status failed
apflow tasks list --status cancelled
```

Filter by user:
```bash
apflow tasks list --user-id alice
apflow tasks list --user-id bob
```

Filter by batch:
```bash
apflow tasks list --batch-id batch-001
apflow tasks list --batch-id batch-002
```

Combine filters:
```bash
apflow tasks list --batch-id batch-001 --status failed
apflow tasks list --user-id alice --status running
```

## Executor Discovery

### apflow executors list

List all available executors:

```bash
apflow executors list [OPTIONS]
```

**Description:**  
Shows all executors that are currently accessible based on APFLOW_EXTENSIONS environment variable configuration. If APFLOW_EXTENSIONS is set, only executors from those extensions are shown (security restriction).

**Options:**
- `--format <format>` - Output format: table (default), json, ids
- `--verbose` - Show detailed executor information (with descriptions)

**Examples:**

Default table format:
```bash
apflow executors list
```

Output:
```
Executor ID            Name                      Extension
────────────────────── ───────────────────────── ──────────
system_info_executor   System Info Executor      stdio
command_executor       Command Executor          stdio
rest_executor          REST Executor             http
apflow_api_executor    ApFlow API Executor       apflow
```

JSON format (useful for scripts and tools):
```bash
apflow executors list --format json
```

Output:
```json
{
  "executors": [
    {
      "id": "system_info_executor",
      "name": "System Info Executor",
      "extension": "stdio",
      "description": "Retrieve system information like CPU, memory, disk usage"
    },
    {
      "id": "command_executor",
      "name": "Command Executor",
      "extension": "stdio",
      "description": "Execute shell commands on the local system"
    },
    {
      "id": "rest_executor",
      "name": "REST Executor",
      "extension": "http",
      "description": "Make HTTP REST API calls"
    }
  ],
  "count": 3,
  "restricted": false
}
```

IDs only format (simple list of executor IDs):
```bash
apflow executors list --format ids
```

Output:
```
system_info_executor
command_executor
rest_executor
apflow_api_executor
```

Verbose output with descriptions:
```bash
apflow executors list --verbose
```

Output:
```
Executor ID            Name                      Extension  Description
────────────────────── ───────────────────────── ────────── ────────────────────────────────
system_info_executor   System Info Executor      stdio      Retrieve system information...
command_executor       Command Executor          stdio      Execute shell commands on...
rest_executor          REST Executor             http       Make HTTP REST API calls
apflow_api_executor    ApFlow API Executor       apflow     Execute tasks through ApFlow API
```

**Restricted Access Example:**

When APFLOW_EXTENSIONS environment variable is set:
```bash
export APFLOW_EXTENSIONS=stdio,http
apflow executors list
```

Output shows only executors from stdio and http extensions:
```
Executor ID            Name                      Extension
────────────────────── ───────────────────────── ──────────
system_info_executor   System Info Executor      stdio
command_executor       Command Executor          stdio
rest_executor          REST Executor             http
```

**Notes:**
- Executor availability depends on installed optional dependencies
- Use `--format json` for programmatic access in scripts
- The executor IDs are used in task schemas when executing tasks
- Check installed extensions with `apflow config list`

## Executor Methods

Common executor methods available:

### system_info_executor

Get system information:

```bash
apflow run batch --tasks '[{
  "id": "t1",
  "name": "CPU Info",
  "schemas": {"method": "system_info_executor"},
  "inputs": {"resource": "cpu"}
}]'
```

**Inputs**:
- `resource`: cpu, memory, disk, network

### http_executor

Make HTTP requests:

```bash
apflow run batch --tasks '[{
  "id": "t1",
  "name": "API Call",
  "schemas": {"method": "http_executor"},
  "inputs": {
    "url": "https://api.example.com/data",
    "method": "GET"
  }
}]'
```

**Inputs**:
- `url`: Target URL
- `method`: GET, POST, PUT, DELETE
- `headers`: HTTP headers (optional)
- `body`: Request body (optional)

### command_executor

Execute shell commands:

```bash
apflow run batch --tasks '[{
  "id": "t1",
  "name": "Run Script",
  "schemas": {"method": "command_executor"},
  "inputs": {
    "command": "ls -la",
    "timeout": 30
  }
}]'
```

**Inputs**:
- `command`: Shell command to execute
- `timeout`: Timeout in seconds

### custom_executor

Custom business logic:

Implement custom executors by extending the executor framework. See [Custom Tasks Guide](../guides/custom-tasks.md) for details.

## Task Input Format

All task inputs are JSON:

```json
{
  "id": "unique-task-id",
  "name": "Human Readable Name",
  "schemas": {
    "method": "executor_method_name"
  },
  "inputs": {
    "param1": "value1",
    "param2": "value2"
  },
  "tags": ["tag1", "tag2"],
  "priority": "high"
}
```

**Fields**:
- `id`: Unique task identifier
- `name`: Human-readable task name
- `schemas.method`: Executor method to use
- `inputs`: Method-specific parameters (object)
- `tags`: Optional tags for organization
- `priority`: low, normal, high (optional)

## Output Format

Task output depends on the executor method. Examples:

**system_info_executor output**:
```json
{
  "cpu": 45.2,
  "memory": 8192,
  "disk": 102400,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**http_executor output**:
```json
{
  "status_code": 200,
  "headers": {...},
  "body": {...},
  "elapsed_time": 0.234
}
```

**command_executor output**:
```json
{
  "stdout": "...",
  "stderr": "",
  "return_code": 0,
  "elapsed_time": 1.234
}
```

## Error Handling

### Common Errors

**Error: "Task not found"**
```bash
# Check if task ID is correct
apflow tasks list | grep task-id
```

**Error: "Database connection error"**
```bash
# Check database configuration
echo $DATABASE_URL
# Or check DuckDB file
ls ~/.aiperceivable/data/apflow.duckdb
```

**Error: "Invalid task format"**
```bash
# Validate JSON
echo '[{"id":"t1","name":"Task","schemas":{"method":"system_info_executor"},"inputs":{}}]' | python -m json.tool
```

**Error: "Executor method not found"**
```bash
# Check available methods
apflow executor list
```

## Debugging

### Debug mode:

```bash
# Enable verbose logging (preferred with APFLOW_ prefix)
export APFLOW_LOG_LEVEL=DEBUG
apflow run batch --tasks '[...]'

# Or use generic LOG_LEVEL (fallback)
export LOG_LEVEL=DEBUG
apflow run batch --tasks '[...]'
```

### Check task details:

```bash
# Get full task information
apflow tasks status task-001 --include-details
```

### Monitor execution:

```bash
# Watch task execution in real-time
apflow tasks watch --task-id task-001
```

## Summary

- ✅ **Execute tasks**: `apflow run` with JSON task definitions
- ✅ **Query tasks**: `apflow tasks list`, `status`, `watch`
- ✅ **Manage tasks**: `create`, `update`, `delete`, `copy`
- ✅ **Cancel tasks**: `apflow tasks cancel` with force option
- ✅ **Monitor flows**: `apflow flow` commands
- ✅ **Debug issues**: `apflow config set log-level DEBUG` Enable debug mode and check logs

All commands support JSON input/output for integration with other tools.
