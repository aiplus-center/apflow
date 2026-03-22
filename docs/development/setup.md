# apflow Development Guide

This document is for developers working on the `apflow` project. For user documentation, see [README.md](../../README.md).

## Project Structure

See [docs/architecture/DIRECTORY_STRUCTURE.md](../architecture/DIRECTORY_STRUCTURE.md) for detailed directory structure including source code, tests, and all modules.

## Prerequisites

- **Python 3.10+** (3.12+ recommended, see note below)
- **DuckDB** (default embedded storage, no setup required)
- **PostgreSQL** (optional, for distributed/production scenarios)

> **Note**: The project uses Python 3.12 for compatibility. Python 3.13 may have compatibility issues.

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd apflow

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

#### Option A: Using uv (Recommended - Fastest)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install standard development environment (recommended)
uv pip install -e ".[standard,dev]"

# OR install with all features
uv pip install -e ".[all,dev]"

# OR install with specific extras
uv pip install -e ".[crewai,cli,dev]"  # CrewAI + CLI + dev tools
```

#### Option B: Using pip (Traditional)

```bash
# Install standard development environment (recommended)
pip install -e ".[standard,dev]"

# OR install with all features
pip install -e ".[all,dev]"

# OR install with specific extras
pip install -e ".[crewai,cli,dev]"  # CrewAI + CLI + dev tools
```

#### Option C: Using Poetry (If configured)

```bash
# Install poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install all dependencies
poetry install --with dev
```

### 3. Environment Configuration

Create a `.env` file in the project root (optional, for API service configuration):

```env
# API Service Configuration
APFLOW_API_HOST=0.0.0.0  # Or use API_HOST (fallback)
APFLOW_API_PORT=8000     # Or use API_PORT (fallback)

# Database Configuration
# Priority: APFLOW_DATABASE_URL > DATABASE_URL (fallback)
# 
# Option 1: PostgreSQL
# APFLOW_DATABASE_URL=postgresql+asyncpg://user:password@localhost/apflow
#
# Option 2: DuckDB with custom path
# APFLOW_DATABASE_URL=duckdb:///.data/my_custom.duckdb
#
# Option 3: Default (auto-detected)
# - In project: .data/apflow.duckdb (created automatically)
# - Outside project: ~/.aiperceivable/data/apflow.duckdb

# Logging
APFLOW_LOG_LEVEL=INFO  # Or use LOG_LEVEL (fallback). Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# CLI Configuration (optional, stored in .data/ or ~/.aiperceivable/apflow/)
# APFLOW_CONFIG_DIR=/custom/config/path  # Override config directory location
```

**Environment Variable Naming Convention:**

apflow uses a consistent naming pattern:
- **Preferred**: `APFLOW_*` prefix (e.g., `APFLOW_LOG_LEVEL`, `APFLOW_DATABASE_URL`)
- **Fallback**: Generic names without prefix (e.g., `LOG_LEVEL`, `DATABASE_URL`)

This allows apflow to work seamlessly in multi-service environments while maintaining isolation.

#### CLI Configuration

Configuration is managed through the `apflow config` command and stored securely:

```bash
# Setup API server configuration
apflow config init-server --url http://localhost:8000 --role admin

# Or manually configure
apflow config set api_server_url http://localhost:8000
apflow config gen-token --role admin --save

# View configuration (tokens masked)
apflow config list
apflow config show-path  # Show file locations and priorities
```

**Configuration Storage**:
- **Project-local** (highest priority): `.data/` directory
- **User-global** (fallback): `~/.aiperceivable/apflow/` directory
- **Files**:
  - `config.cli.yaml` (600) - All CLI settings (sensitive and non-sensitive)

### 4. Verify Installation

```bash
# Check installation
python -c "import apflow; print(apflow.__version__)"

# Run tests to verify everything works
pytest tests/ -v
```

## Development Workflow

### Running the Project

#### Run Tests

```bash
# Run all tests (recommended)
pytest tests/ -v

# Run specific test file
pytest tests/test_task_manager.py -v

# Run with coverage
pytest --cov=apflow --cov-report=html tests/

# Run only unit tests (exclude integration tests)
pytest -m "not integration" tests/

# Run only integration tests
pytest -m integration tests/

# Run CLI tests specifically
pytest tests/cli/ -v
```

**Note**: A2A tests are excluded by default (optional a2a dependency). To run them:
```bash
pip install -e ".[a2a]"
pytest tests/api/a2a/ -v
```

#### Run API Server (Development)

```bash
# Method 1: Using CLI (if installed with [cli] extra)
apflow serve --port 8000 --reload
# Or use shorthand:
apflow serve --port 8000 --reload
# Note: 'serve --port 8000' (without 'start') also works

# Method 2: Using Python module directly (recommended)
python -m apflow.api.main

# Method 3: Using entry point (if installed with [a2a] extra)
apflow-server

# Method 4: Direct execution of serve command (for development)
python src/apflow/cli/commands/serve.py start --port 8000 --reload
```

#### Run CLI Commands

```bash
# Run a flow (standard mode with tasks array)
apflow run flow --tasks '[{"id": "task1", "name": "Task 1", "schemas": {"method": "system_info_executor"}, "inputs": {"resource": "cpu"}}]'

# Or legacy mode (executor ID + inputs)
apflow run flow system_info_executor --inputs '{"resource": "cpu"}'

# Start daemon mode
apflow daemon start
```

### Code Quality

#### Pre-commit Hooks (Recommended)

Set up pre-commit hooks to automatically run `ruff check --fix` before each commit:

```bash
# Install pre-commit (included in [dev] extra)
pip install pre-commit

# Install git hooks
pre-commit install
```

After setup, `ruff check src/ tests/ --fix` will run automatically on every `git commit`.

#### Format Code

```bash
# Format all code
black src/ tests/

# Check formatting without applying
black --check src/ tests/
```

#### Lint Code

```bash
# Run linter
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/
```

#### Type Checking

```bash
# Run type checker
mypy src/apflow/

# Check specific module
mypy src/apflow/core/interfaces/ src/apflow/core/execution/ src/apflow/core/storage/
### Continuous Integration

The project uses GitHub Actions for CI. The workflow is defined in `.github/workflows/ci.yml`.

It runs tests (`pytest`) across Python 3.10, 3.11, and 3.12.
You can run them locally using the commands mentioned above.

### Database Operations

#### Default DuckDB (No Setup Required)

DuckDB is the default embedded storage. It requires no external setup - it creates database files locally.

```bash
# Test storage (creates temporary DuckDB file)
pytest tests/test_storage.py -v
```

#### PostgreSQL (Optional)

If you want to test with PostgreSQL:

```bash
# Install PostgreSQL extra
pip install -e ".[postgres]"

# Set environment variable
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/apflow"

# Run database migrations (if using Alembic)
alembic upgrade head
```

#### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Running Services

#### API Service

```bash
# Development mode (auto-reload)
apflow serve --port 8000 --reload

# Production mode
apflow serve --port 8000 --workers 4
```

#### Daemon Mode

```bash
# Start daemon
apflow daemon start

# Stop daemon
apflow daemon stop

# Check daemon status
apflow daemon status
```

## Dependency Management

### Core Dependencies

Installed with `pip install apflow` (pure orchestration framework):

- `pydantic` - Data validation
- `sqlalchemy` - ORM
- `alembic` - Database migrations
- `duckdb-engine` - Default embedded storage

**Note**: CrewAI is NOT in core dependencies - it's available via [crewai] extra.

### Optional Dependencies

#### A2A Protocol Server (`[a2a]`)

```bash
pip install -e ".[a2a]"
```

Includes:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `a2a-sdk[http-server]` - A2A protocol support
- `httpx`, `aiohttp` - HTTP clients
- `websockets` - WebSocket support

#### CLI Tools (`[cli]`)

```bash
pip install -e ".[cli]"
```

Includes:
- `click`, `rich`, `typer` - CLI framework and utilities

#### PostgreSQL (`[postgres]`)

```bash
pip install -e ".[postgres]"
```

Includes:
- `asyncpg` - Async PostgreSQL driver
- `psycopg2-binary` - Sync PostgreSQL driver

#### CrewAI Support (`[crewai]`)

```bash
pip install -e ".[crewai]"
```

Includes:
- `crewai[tools]` - Core CrewAI orchestration engine
- `crewai-tools` - CrewAI tools
- CrewaiExecutor for LLM-based agent crews
- BatchCrewaiExecutor for atomic batch execution of multiple crews

**Note**: BatchCrewaiExecutor is part of [crewai] because it's specifically designed for batching CrewAI crews together.

**Note**: For examples and learning templates, see the test cases in `tests/integration/` and `tests/extensions/`. Test cases serve as comprehensive examples demonstrating real-world usage patterns.

#### LLM Support (`[llm]`)

```bash
pip install -e ".[llm]"
```

Includes:
- `litellm` - Unified LLM interface supporting 100+ providers

#### Standard (`[standard]`)

```bash
# Recommended for most developers
pip install -e ".[standard,dev]"
```

Includes:
- **A2A Protocol Server** - Agent-to-Agent communication protocol
- **CLI Tools** - Command-line interface
- **CrewAI Support** - LLM-based agent crew orchestration
- **LLM Support** - Direct LLM interaction via LiteLLM
- **Development Tools** - When combined with [dev]

**This is the recommended installation profile** for most use cases as it provides:
- API server capability (A2A Protocol)
- CLI tools for task management and execution
- LLM support for AI-powered tasks
- Batch execution via CrewAI
- Full development environment when combined with [dev]

#### Development (`[dev]`)

```bash
pip install -e ".[dev]"
```

Includes:
- `pytest`, `pytest-asyncio`, `pytest-cov` - Testing
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

### Standard Installation (Recommended)

```bash
# Install standard features + development tools (recommended)
pip install -e ".[standard,dev]"

# This installs:
# - A2A Protocol Server
# - CLI tools
# - CrewAI and LLM support
# - Development tools (pytest, ruff, mypy, etc.)
```

### Full Installation

```bash
# Install everything (all extras + dev tools)
pip install -e ".[all,dev]"
```

## Testing

### Test Structure

See [docs/architecture/DIRECTORY_STRUCTURE.md](../architecture/DIRECTORY_STRUCTURE.md#test-suite-tests-) for complete test directory structure.

Test structure mirrors source code structure:
- `tests/core/` - Core framework tests
- `tests/extensions/` - Extension tests
- `tests/api/a2a/` - A2A Protocol Server tests
- `tests/cli/` - CLI tests
- `tests/integration/` - Integration tests

### Writing Tests

#### Test Fixtures

Use the provided fixtures from `conftest.py`:

```python
import pytest

@pytest.mark.asyncio
async def test_my_feature(sync_db_session, sample_task_data):
    # Use sync_db_session for database operations
    # Use sample_task_data for test data
    pass
```

#### Test Markers

```python
# Mark as integration test (requires external services)
@pytest.mark.integration
async def test_external_service():
    pass

# Mark as slow test
@pytest.mark.slow
def test_performance():
    pass

# Mark as requiring API keys
@pytest.mark.requires_api_keys
async def test_api_integration(api_keys_available):
    pass
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=apflow --cov-report=html tests/

# View HTML report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## Code Organization

### Module Structure

**Core Modules** (always included with `pip install apflow`):
- **`execution/`**: Task orchestration specifications (TaskManager, StreamingCallbacks)
- **`interfaces/`**: Core interfaces (ExecutableTask, BaseTask, TaskStorage)
- **`storage/`**: Storage abstractions and implementations (DuckDB default, PostgreSQL optional)
- **`utils/`**: Utility functions

**Optional Extension Modules**:
- **`extensions/crewai/`**: CrewAI LLM task support [crewai extra]
  - `crewai_executor.py`: CrewaiExecutor for LLM-based agent crews
  - `batch_crewai_executor.py`: BatchCrewaiExecutor for atomic batch execution of multiple crews
  - `types.py`: CrewaiExecutorState, BatchState
  - Note: BatchCrewaiExecutor is included in [crewai] as it's specifically for batching CrewAI crews

**Learning Resources**:
- **Test cases**: Serve as examples (see `tests/integration/` and `tests/extensions/`)
  - Integration tests demonstrate real-world usage patterns
  - Extension tests show how to use specific executors
  - Test cases can be used as learning templates

**Service Modules**:
- **`api/`**: API layer (A2A server, route handlers) [a2a extra]
- **`cli/`**: Command-line interface [cli extra]
**Protocol Standard**: The framework adopts **A2A (Agent-to-Agent) Protocol** as the standard protocol. See `api/` module for A2A Protocol implementation.

### Adding New Features

1. **New Custom Task**: Implement `ExecutableTask` interface (core)
2. **New CrewAI Crew**: Add to `ext/crews/` [ext extra]
3. **New Batch**: Add to `ext/batches/` [ext extra]
4. **New Storage Backend**: Add dialect to `storage/dialects/`
5. **New API Endpoint**: Add handler to `api/routes/` (protocol-agnostic route handlers)
6. **New CLI Command**: Add to `cli/commands/`

### Code Style

- **Line length**: 100 characters
- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings
- **Imports**: Sort imports with `ruff`
- **Comments**: Write comments in English

## Debugging

### Enable Debug Logging

```python
import logging
from apflow.utils.logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
```

### Using Debugger

```bash
# Run with Python debugger
python -m pdb -m pytest tests/test_task_manager.py::TestTaskManager::test_create_task
```

### Common Issues

#### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e "."

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Database Connection Issues

```bash
# For DuckDB: Check file permissions
ls -la *.duckdb

# For PostgreSQL: Verify connection string
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_CONNECTION_STRING'); print(engine.connect())"
```

## Building and Distribution

### Build Package

```bash
# Build source distribution
python -m build

# Build wheel
python -m build --wheel
```

### Local Installation Test

```bash
# Install from local build
pip install dist/apflow-0.2.0-py3-none-any.whl
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Make your changes**
   - Write code
   - Add tests
   - Update documentation
4. **Run quality checks**
   ```bash
   black src/ tests/
   ruff check --fix src/ tests/
   mypy src/apflow/
   pytest tests/
   ```
5. **Commit changes**
   ```bash
   git commit -m "feat: Add my feature"
   ```
6. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass (`pytest tests/`)
- [ ] Code is formatted (`black src/ tests/`)
- [ ] No linting errors (`ruff check src/ tests/`)
- [ ] Type checking passes (`mypy src/apflow/`)
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (if needed)

## Resources

- **User Documentation**: [README.md](../../README.md)
- **Changelog**: [CHANGELOG.md](../../CHANGELOG.md)
- **Website**: [aiperceivable.com](https://aiperceivable.com)
- **Issue Tracker**: [GitHub Issues](https://github.com/aiperceivable/apflow/issues)

## Getting Help

- **Questions**: Open a GitHub issue
- **Bugs**: Report via GitHub issues
- **Feature Requests**: Open a GitHub discussion
- **Documentation**: Check [docs/](docs/) directory

## License

Apache-2.0 - See [LICENSE](LICENSE) file for details.

