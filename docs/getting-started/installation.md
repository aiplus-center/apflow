# Installation

> **Looking for a step-by-step beginner tutorial?** See the [Quick Start Guide](quick-start.md) for a hands-on introduction. This page covers all installation options.

## Choose Your Deployment Mode

apflow supports two deployment modes. Choose the one that fits your use case:

| Feature | Standalone | Distributed Cluster |
|---------|-----------|---------------------|
| Storage | DuckDB (built-in) | PostgreSQL |
| Nodes | Single process | Multi-node (leader + workers) |
| Setup | Zero configuration | Requires PostgreSQL + env vars |
| Install | `pip install apflow` | `pip install apflow[standard]` |
| Best for | Development, testing, small workloads | Production, scaling, high availability |

## Standalone Installation

Install the core library with no additional setup required:

```bash
pip install apflow
```

**What's included:**

- Task orchestration framework (TaskManager, ExecutableTask, BaseTask)
- DuckDB storage (embedded, zero-configuration)
- Core interfaces and storage layer (TaskStorage, SQLAlchemy)

This is everything you need to define, run, and track tasks on a single machine. No external databases or services required -- start using apflow immediately after install.

## Distributed Cluster Installation

For production deployments with multiple nodes, install the standard bundle:

```bash
pip install apflow[standard]
```

**What's included (on top of core):**

- A2A Protocol Server (agent-to-agent communication)
- CLI tools
- CrewAI executor and batch execution
- LLM execution via LiteLLM
- Web tools (requests, BeautifulSoup, trafilatura)
- Task scheduling (cron-like)

**Prerequisites:**

- A running PostgreSQL database (install the `postgres` extra separately: `pip install apflow[standard,postgres]`)

**Quick setup:**

```bash
# Set required environment variables
export APFLOW_DATABASE_URL="postgresql://user:pass@host:5432/apflow"
export APFLOW_NODE_ROLE="leader"   # or "worker"

# Start the server
apflow serve
```

For complete deployment instructions including leader/worker configuration, networking, and production hardening, see the [Distributed Cluster Guide](../guides/distributed-cluster.md).

## Optional Extras

Individual extras can be installed separately or combined. For example: `pip install apflow[cli,postgres]`.

| Extra | Install | Description |
|-------|---------|-------------|
| `standard` | `pip install apflow[standard]` | Recommended bundle: a2a, cli, crewai, llm, tools, scheduling |
| `a2a` | `pip install apflow[a2a]` | A2A Protocol Server for agent-to-agent communication (HTTP, SSE, WebSocket) |
| `cli` | `pip install apflow[cli]` | Command-line interface (`apflow` command) |
| `crewai` | `pip install apflow[crewai]` | CrewAI executor for LLM-based agent crews, plus batch execution |
| `postgres` | `pip install apflow[postgres]` | PostgreSQL storage for distributed/production deployments |
| `llm` | `pip install apflow[llm]` | LLM execution via LiteLLM |
| `email` | `pip install apflow[email]` | Email executor (Resend API and SMTP) |
| `ssh` | `pip install apflow[ssh]` | SSH executor for remote command execution |
| `docker` | `pip install apflow[docker]` | Docker executor for containerized execution |
| `grpc` | `pip install apflow[grpc]` | gRPC executor for service calls |
| `mcp` | `pip install apflow[mcp]` | MCP (Model Context Protocol) executor |
| `graphql` | `pip install apflow[graphql]` | GraphQL API server with Strawberry GraphQL |
| `scheduling` | `pip install apflow[scheduling]` | Cron-like task scheduling |
| `tools` | `pip install apflow[tools]` | Web tools (requests, BeautifulSoup, trafilatura) |
| `all` | `pip install apflow[all]` | Everything: all optional features combined |

**CLI commands** (available when the corresponding extra is installed):

| Command | Extra required | Description |
|---------|---------------|-------------|
| `apflow` | `cli` | Main command-line interface |
| `apflow-server` | `a2a` | A2A Protocol Server |

## Requirements

- **Python**: 3.10 or higher (3.12+ recommended)
- **DuckDB**: Included by default (no setup required)
- **PostgreSQL**: Only required for distributed cluster deployments (install with `postgres` extra)

## Development Installation

For contributing to apflow or running tests locally:

```bash
# Clone the repository
git clone https://github.com/aiperceivable/apflow.git
cd apflow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all features
pip install -e ".[all,dev]"
```

## Verification

After installation, verify it works:

```python
import apflow
print(apflow.__version__)
```

Or using the CLI (requires `cli` extra):

```bash
apflow --version
```
