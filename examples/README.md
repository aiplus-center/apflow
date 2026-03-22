# apflow Examples

This directory contains practical, runnable examples demonstrating apflow's capabilities.

## Getting Started Examples

### Hello World (`hello_world/`)

Start here if you're new to apflow:

1. **[simple.py](hello_world/simple.py)** - Most basic example
   - Creating a custom executor
   - Building and executing a task
   - Perfect first example

2. **[with_dependencies.py](hello_world/with_dependencies.py)** - Task dependencies
   - Creating multiple tasks
   - Setting up dependencies
   - Execution order management

3. **[built_in_executors.py](hello_world/built_in_executors.py)** - Built-in executors
   - Using REST executor
   - No custom code needed
   - Real API examples

## Executor Examples (`executor_examples/`)

Practical examples for each built-in executor:

### REST Executor
**File**: [rest_executor_example.py](executor_examples/rest_executor_example.py)

Examples:
- Simple GET requests
- POST with JSON data
- Authentication headers
- Query parameters
- Webhook notifications

**Use cases**: API integration, webhook calls, third-party services

### SSH Executor
**File**: [ssh_executor_example.py](executor_examples/ssh_executor_example.py)

**Prerequisites**: `pip install apflow[ssh]`

Examples:
- Basic command execution
- Deployment scripts
- System administration
- Log rotation
- Database backups

**Use cases**: Remote deployments, server maintenance, system administration

### Docker Executor
**File**: [docker_executor_example.py](executor_examples/docker_executor_example.py)

**Prerequisites**:
- `pip install apflow[docker]`
- Docker installed and running

Examples:
- Simple container execution
- Volume mounting
- Data processing
- Batch processing
- ML inference

**Use cases**: Isolated execution, reproducible workflows, batch processing

## Running Examples

### Install apflow

```bash
# Basic installation
pip install apflow

# With specific executors
pip install apflow[ssh]      # SSH executor
pip install apflow[docker]   # Docker executor
pip install apflow[all]      # All executors
```

### Run an example

```bash
# Navigate to examples directory
cd examples

# Run a hello world example
python hello_world/simple.py

# Run an executor example
python executor_examples/rest_executor_example.py
```

## Example Categories

### By Difficulty

**Beginner** (Start here):
- `hello_world/simple.py`
- `hello_world/built_in_executors.py`

**Intermediate**:
- `hello_world/with_dependencies.py`
- `executor_examples/rest_executor_example.py`

**Advanced**:
- `executor_examples/ssh_executor_example.py`
- `executor_examples/docker_executor_example.py`

### By Use Case

**API Integration**:
- `executor_examples/rest_executor_example.py`

**Remote Operations**:
- `executor_examples/ssh_executor_example.py`

**Data Processing**:
- `executor_examples/docker_executor_example.py`

**Workflow Orchestration**:
- `hello_world/with_dependencies.py`

## Additional Resources

- **[Hello World Guide](../docs/getting-started/hello-world.md)** - 5-minute quick start
- **[Executor Selection Guide](../docs/guides/executor-selection.md)** - Choose the right executor
- **[Quick Start](../docs/getting-started/quick-start.md)** - Comprehensive tutorial
- **[API Reference](../docs/api/python.md)** - Complete API documentation

## Need Help?

- **Documentation**: [docs/](../docs/)
- **GitHub Issues**: [Report bugs](https://github.com/aiperceivable/apflow/issues)
- **FAQ**: [docs/guides/faq.md](../docs/guides/faq.md)

## Contributing Examples

Have a useful example? We welcome contributions!

See [Contributing Guide](../docs/development/contributing.md) for details.

---

**Ready to start?** → Begin with [simple.py](hello_world/simple.py)
