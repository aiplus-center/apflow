# apflow

<p align="center">
  <img src="apflow-logo.svg" alt="apflow Logo" width="128" height="128" />
</p>

**Distributed Task Orchestration Framework**

apflow is a distributed task orchestration framework that scales from a single process to multi-node clusters. It provides a unified execution interface with 12+ built-in executors, A2A protocol support, and automatic leader election with failover.

Start standalone in 30 seconds. Scale to distributed clusters without code changes.

## Deployment Modes

### Standalone (Development and Small Workloads)

```bash
pip install apflow
```

Single process, DuckDB storage, zero configuration. Ideal for development, testing, and small-scale automation.

```python
from apflow.core.builders import TaskBuilder
from apflow import TaskManager, create_session

db = create_session()
task_manager = TaskManager(db)
result = await (
    TaskBuilder(task_manager, "rest_executor")
    .with_name("fetch_data")
    .with_input("url", "https://api.example.com/data")
    .with_input("method", "GET")
    .execute()
)
```

### Distributed Cluster (Production)

```bash
pip install apflow[standard]
```

PostgreSQL-backed, leader/worker topology with automatic leader election, task leasing, and horizontal scaling. Same application code -- only the runtime environment changes.

```bash
# Leader node
APFLOW_CLUSTER_ENABLED=true \
APFLOW_DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/apflow \
APFLOW_NODE_ROLE=auto \
apflow serve --port 8000

# Worker node (on additional machines)
APFLOW_CLUSTER_ENABLED=true \
APFLOW_DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/apflow \
APFLOW_NODE_ROLE=worker \
apflow serve --port 8001
```

Add worker nodes at any time. The cluster auto-discovers them via the shared database.

## Installation Options

| Extra | Command | Includes |
|-------|---------|----------|
| Core | `pip install apflow` | Task orchestration, DuckDB storage, core executors |
| Standard | `pip install apflow[standard]` | Core + A2A server + CLI + CrewAI + LLM + tools |
| A2A Server | `pip install apflow[a2a]` | A2A Protocol server (HTTP/SSE/WebSocket) |
| CLI | `pip install apflow[cli]` | Command-line interface |
| PostgreSQL | `pip install apflow[postgres]` | PostgreSQL storage (required for distributed) |
| CrewAI | `pip install apflow[crewai]` | LLM-based agent crews |
| LLM | `pip install apflow[llm]` | Direct LLM via LiteLLM (100+ providers) |
| SSH | `pip install apflow[ssh]` | Remote command execution |
| Docker | `pip install apflow[docker]` | Containerized execution |
| gRPC | `pip install apflow[grpc]` | gRPC service calls |
| Email | `pip install apflow[email]` | Email sending (SMTP) |
| All | `pip install apflow[all]` | Everything |

## Built-in Executors

| Executor | Purpose | Extra |
|----------|---------|-------|
| RestExecutor | HTTP/REST API calls with auth and retry | core |
| CommandExecutor | Local shell command execution | core |
| SystemInfoExecutor | System information collection | core |
| ScrapeExecutor | Web page scraping | core |
| WebSocketExecutor | Bidirectional WebSocket communication | core |
| McpExecutor | Model Context Protocol tools and data sources | core |
| ApFlowApiExecutor | Inter-instance API calls for distributed execution | core |
| AggregateResultsExecutor | Aggregate results from multiple tasks | core |
| SshExecutor | Remote command execution via SSH | [ssh] |
| DockerExecutor | Containerized command execution | [docker] |
| GrpcExecutor | gRPC service calls | [grpc] |
| SendEmailExecutor | Send emails via SMTP or Resend API | [email] |
| CrewaiExecutor | LLM agent crews via CrewAI | [crewai] |
| BatchCrewaiExecutor | Atomic batch of multiple crews | [crewai] |
| LLMExecutor | Direct LLM interaction via LiteLLM | [llm] |
| GenerateExecutor | Natural language to task tree via LLM | [llm] |

## Architecture

```
                    +--------------------------+
                    |    Client / CLI / API     |
                    +------------+-------------+
                                 |
              +------------------+------------------+
              |                  |                   |
    +---------v--------+ +------v------+ +----------v--------+
    |   Leader Node     | | Worker Node | |   Worker Node      |
    |  (auto-elected)   | |             | |                    |
    |  - Task placement | |  - Execute  | |  - Execute         |
    |  - Lease mgmt     | |  - Heartbeat| |  - Heartbeat       |
    |  - Execute        | |             | |                    |
    +---------+--------+ +------+------+ +----------+--------+
              |                  |                   |
              +------------------+------------------+
                                 |
                    +------------v-------------+
                    |  PostgreSQL (shared)      |
                    |  - Task state             |
                    |  - Leader lease           |
                    |  - Node registry          |
                    +--------------------------+
```

*Standalone mode uses the same architecture with a single node and DuckDB storage.*

## Documentation

- [Getting Started](docs/getting-started/quick-start.md) -- Up and running in 10 minutes
- [Distributed Cluster Guide](docs/guides/distributed-cluster.md) -- Multi-node deployment
- [Executor Selection Guide](docs/guides/executor-selection.md) -- Choose the right executor
- [API Reference](docs/api/python.md) -- Python API documentation
- [Architecture Overview](docs/architecture/overview.md) -- Design and internals
- [Protocol Specification](docs/protocol/index.md) -- A2A Protocol spec

Full documentation: [flow-docs.aiperceivable.com](https://flow-docs.aiperceivable.com)

## Contributing

Contributions are welcome. See [Contributing Guide](docs/development/contributing.md) for setup and guidelines.

## License

Apache-2.0

## Links

- **Documentation**: [flow-docs.aiperceivable.com](https://flow-docs.aiperceivable.com)
- **Website**: [aiperceivable.com](https://aiperceivable.com)
- **GitHub**: [aiperceivable/apflow](https://github.com/aiperceivable/apflow)
- **PyPI**: [apflow](https://pypi.org/project/apflow/)
