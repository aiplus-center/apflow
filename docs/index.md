<style>
/* Hide the sidebar only on the desktop and keep the menu on the mobile. */
@media (min-width: 960px) {
  .md-sidebar--primary,
  .md-nav--primary {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  .md-main__inner {
    max-width: 100% !important;
  }
  .md-content {
    margin-left: 0 !important;
    max-width: 100% !important;
    padding-left: 1rem !important;
  }
}
</style>

# apflow

**Distributed Task Orchestration Framework**

Start standalone in 30 seconds with DuckDB. Scale to distributed clusters with PostgreSQL -- no code changes required.

---

## Deployment Modes

<div class="grid cards" markdown>

-   __Standalone__

    ---

    Single process, DuckDB storage, zero configuration.
    Ideal for development, testing, and small-scale automation.

    ```bash
    pip install apflow
    ```

    [Quick Start](getting-started/quick-start.md){ .md-button }

-   __Distributed Cluster__{ .lg .middle }

    ---

    PostgreSQL-backed, leader/worker topology with automatic leader election, task leasing, and horizontal scaling. Add worker nodes at any time.

    ```bash
    pip install apflow[standard]
    ```

    [Cluster Guide](guides/distributed-cluster.md){ .md-button .md-button--primary }

</div>

!!! tip "Same application code in both modes"
    Write your tasks once. Switch from standalone to distributed by changing only the runtime configuration -- set `APFLOW_CLUSTER_ENABLED=true` and point to PostgreSQL.

---

## Documentation

<div class="grid cards" markdown>

-   __Getting Started__

    ---

    Installation, core concepts, and step-by-step tutorials to get up and running.

    [Getting Started](getting-started/index.md)

-   __Guides__

    ---

    In-depth guides including [distributed cluster deployment](guides/distributed-cluster.md), task orchestration, custom executors, and best practices.

    [Guides](guides/task-orchestration.md)

-   __API Reference__

    ---

    Complete Python API, HTTP API, GraphQL API, and quick-reference cheat sheet.

    [API Reference](api/python.md)

-   __Architecture__

    ---

    System design, task lifecycle, extension registry, and configuration internals.

    [Architecture](architecture/overview.md)

-   __Protocol Specification__

    ---

    The language-agnostic AI Perceivable Flow Protocol for cross-implementation interoperability.

    [Protocol](protocol/index.md)

-   __Development__

    ---

    Environment setup, contribution guidelines, and project roadmap.

    [Development](development/setup.md)

</div>

---

## Key Capabilities

- **12+ Built-in Executors** -- REST, SSH, Docker, gRPC, WebSocket, MCP, CrewAI, LLM, and more. [Executor Selection Guide](guides/executor-selection.md)
- **A2A Protocol** -- Real-time streaming, Server-Sent Events, and WebSocket support for live task monitoring. [HTTP API](api/http.md)
- **CLI Tools** -- Create, run, and monitor tasks from the command line. [CLI Reference](cli/index.md)
- **Real-time Streaming** -- Subscribe to task progress and intermediate results as they happen. [API Server Guide](guides/api-server.md)
- **Scheduler** -- Cron-based and interval scheduling for recurring tasks. [Scheduler Guide](guides/scheduler.md)
- **Extensible Architecture** -- Add custom executors and extend the framework via the extension registry. [Extensions Guide](guides/extensions.md)
