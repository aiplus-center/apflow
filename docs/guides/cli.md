# CLI Usage Guide

## Overview

The CLI can work in two modes:
1. **Standalone Mode**: Direct database access (default, no API server needed)
2. **API Gateway Mode**: Route commands through API server (when configured)

When API server is configured via `apflow config`, CLI commands automatically use the API gateway, ensuring data consistency and enabling distributed deployments.

## Documentation

For detailed documentation, see:

- **[Configuration](../cli/configuration.md)** - Managing CLI and API configuration
- **[Commands](../cli/commands.md)** - Complete reference of all CLI commands  
- **[API Gateway Integration](../cli/api-gateway.md)** - Using CLI with API server
- **[Examples](../cli/examples.md)** - Practical usage examples
- **[CLI Directory Overview](../cli/index.md)** - Complete CLI documentation structure

## Quick Start

### Installation

```bash
# Install with CLI support
pip install -e ".[cli]"

# Or install everything
pip install -e ".[all]"
```

### Basic Usage (No API Server Required)

```bash
# Execute a task
apflow run flow --tasks '[{"id": "task1", "name": "Task 1", "schemas": {"method": "system_info_executor"}, "inputs": {"resource": "cpu"}}]'

# Query task status
apflow tasks status task-123

# List tasks from database
apflow tasks list
```

### Configure API Server

```bash
# Quick setup (recommended)
apflow config init-server

# Or manual setup
apflow config set api-server http://localhost:8000
apflow config gen-token --role admin --save api_auth_token
```

## Architecture: CLI vs API

```
┌─────────────────────────────────────────────────────────────┐
│                    Shared Database                          │
│  (DuckDB default, or PostgreSQL if configured)             │
└─────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │                              │
    ┌────┴────┐                  ┌─────┴─────┐
    │   CLI   │                  │    API    │
    │         │                  │  Server   │
    │ Direct  │◄─── or ─────────►│  (HTTP)   │
    │ Access  │    API Gateway   │           │
    └─────────┘                  └───────────┘
```

**Two Modes**:
- **Standalone**: CLI → Direct DB Access (default)
- **API Gateway**: CLI → API Server → DB (when configured)

**Key Points**:
- CLI can work independently without API server
- When API configured, CLI uses API gateway (solves DuckDB concurrency)
- Shared data: Both CLI and API read/write to the same database
- Configuration stored in multi-location system (project-local or user-global)

## Common Questions

### Q: Do I need to start API server to use CLI?

**A: No.** CLI works independently. It directly accesses the database, so no API server is required.

### Q: Can CLI and API run at the same time?

**A: Yes.** They share the same database, so you can:
- Execute tasks via CLI
- Query tasks via API
- Or vice versa

### Q: How does CLI query task status?

**A: Direct database access.** CLI uses `TaskRepository` to query the database directly, not through API.

### Q: Can I use CLI to query tasks created by API?

**A: Yes.** Since they share the same database, CLI can query any task created by API, and vice versa.

### Q: What's the difference between CLI and API?

| Feature | CLI | API |
|---------|-----|-----|
| **Execution** | Direct via TaskExecutor | Via HTTP/A2A protocol |
| **Query** | Direct database access | Via HTTP endpoints |
| **Setup** | No server needed | Requires server |
| **Remote Access** | No (local only) | Yes (HTTP) |
| **A2A Protocol** | No | Yes |
| **Speed** | Fast (direct DB) | Slightly slower (HTTP overhead) |
| **Use Case** | Local dev, scripts | Production, remote access |

## Best Practices

### 1. Development Workflow

```bash
# Use CLI for quick testing
apflow run flow --tasks '[{"id": "task1", "name": "Task 1", "schemas": {"method": "system_info_executor"}, "inputs": {"resource": "cpu"}}]'

# Use API server for integration testing
apflow serve --reload
# Then test API endpoints
```

### 2. Production Deployment

```bash
# Option A: CLI only (for automation/scripts)
# No server needed, just use CLI commands

# Option B: API server (for remote access)
# Start with A2A protocol (default)
apflow daemon start --port 8000
# Or start with MCP protocol
apflow daemon start --port 8000 --protocol mcp
# Then use HTTP API, A2A protocol, or MCP protocol
```

### 3. Monitoring

```bash
# For single task
apflow tasks watch --task-id task-123

# For all tasks
apflow tasks watch --all

# For specific user
apflow tasks list --user-id my-user
```

### 4. Error Handling

```bash
# Check task status after execution
apflow tasks status <task_id>

# If failed, check error message
# Error is stored in task.error field

# Cancel stuck tasks
apflow tasks cancel <task_id> --force

# Cancel with custom error message
apflow tasks cancel <task_id> --error-message "Timed out"
```

## Database Configuration

### Default: DuckDB (Embedded, Zero Config)

CLI uses DuckDB by default - no configuration needed:

```bash
# Just use CLI - database is created automatically
apflow run flow --tasks '[{"id": "task1", "name": "Task 1", "schemas": {"method": "system_info_executor"}, "inputs": {"resource": "cpu"}}]'
```

Database file location: `~/.aiperceivable/data/apflow.duckdb` (or configured path)

### Optional: PostgreSQL

If you want to use PostgreSQL (for production or shared access):

```bash
# Set environment variable
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/apflow"

# Use CLI as normal - it will connect to PostgreSQL
apflow run flow --tasks '[{"id": "task1", "name": "Task 1", "schemas": {"method": "system_info_executor"}, "inputs": {"resource": "cpu"}}]'
```

**Note**: Both CLI and API will use the same database connection string, so they share data automatically.

## Troubleshooting

### Problem: "Task not found"

**Solution**: Check if task ID is correct:
```bash
apflow tasks list  # See all running tasks
apflow tasks status <task_id>  # Check specific task
```

### Problem: "Database connection error"

**Solution**: Check database configuration:
```bash
# For DuckDB (default), no config needed
# For PostgreSQL, check DATABASE_URL environment variable
echo $DATABASE_URL
```

### Problem: "Task is stuck"

**Solution**: Cancel and restart:
```bash
apflow tasks cancel <task_id> --force
apflow run flow <batch_id> --inputs '...'
```

### Problem: "Cannot query task status"

**Solution**: Ensure database is accessible:
```bash
# Check if database file exists (DuckDB)
ls ~/.aiperceivable/data/apflow.duckdb

# Or check PostgreSQL connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM apflow_tasks;"
```

## Summary

- ✅ **CLI is independent** - No API server required
- ✅ **Direct database access** - Fast and efficient
- ✅ **Shared database** - CLI and API can work together
- ✅ **Full functionality** - Execute, query, monitor, cancel tasks
- ✅ **Production ready** - Can be used in scripts and automation

Use CLI for local development and automation, use API server for production deployment and remote access.

## CLI Extension (Dynamic Plugins)

The `apflow` CLI supports dynamic discovery of subcommands through Python's `entry_points` mechanism. This allows external projects to add their own command groups directly to the main CLI without modifying the core library.

### Unified Entry Point

Users always use the same consistent entry point:
- `apflow <your-plugin-name> <command>`

### Example: Users Extension

If a plugin registers a command group called `users`, a user can simply run:
```bash
apflow users stat
```

For more details on how to develop these extensions, see the [Custom Tasks Guide](../guides/custom-tasks.md).

## Extending and Overriding CLI Commands

apflow allows you to register new CLI command groups or single commands, extend existing groups, or override built-in commands and groups. This is done using the `@cli_register` decorator, with the `group` and `override=True` parameters.

### Register a New Command or Group
```python
from apflow.cli.decorators import cli_register

@cli_register(name="my-group", help="My command group")
class MyGroup:
    def foo(self):
        print("foo")
    def bar(self):
        print("bar")
```

### Add a Subcommand to an Existing Group
```python
@cli_register(group="my-group", name="baz", help="Baz command")
def baz():
    print("baz")
```

### Override an Existing Command or Group

```python
@cli_register(name="my-group", override=True)
class NewMyGroup:
    ...

@cli_register(group="my-group", name="foo", override=True)
def new_foo():
    print("new foo")
```

**Override a built-in command (e.g., 'run'):**
```python
from apflow.cli.decorators import cli_register

@cli_register(name="run", override=True, help="Override built-in run command")
def my_run():
    print("This is my custom run command!")
```
Now, running `apflow run` will execute your custom logic instead of the built-in command.

### Core Extension Override

apflow also supports custom extensions for executors, hooks, storage backends, and more. You can register your own or override built-in extensions by passing `override=True` when registering.

**Best Practices:**
- Use `override=True` only when you want to replace an existing command or extension.
- Keep extension logic simple and well-documented.
- Test your extensions thoroughly.
