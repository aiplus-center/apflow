# Environment Variables

apflow can be configured entirely through environment variables. Each variable maps to a YAML config key with the `APFLOW_` prefix.

## Configuration Priority

```
Defaults → apflow.yaml → Environment Variables (highest priority)
```

## Core Variables

| Variable | Config Key | Default | Description |
|----------|-----------|---------|-------------|
| `APFLOW_CONFIG` | — | — | Explicit path to config YAML file |
| `APFLOW_API_SERVER_URL` | `api.server_url` | None | API server URL (enables API mode for scheduler) |
| `APFLOW_API_TIMEOUT` | `api.timeout` | 30.0 | API request timeout (seconds) |
| `APFLOW_API_RETRY_ATTEMPTS` | `api.retry_attempts` | 3 | API retry attempts |
| `APFLOW_API_RETRY_BACKOFF` | `api.retry_backoff` | 1.0 | Initial retry backoff (seconds) |
| `APFLOW_API_JWT_SECRET` | `api.jwt_secret` | None | JWT secret for auto-generated auth tokens |

## Storage

| Variable | Config Key | Default | Description |
|----------|-----------|---------|-------------|
| `DATABASE_URL` | — | SQLite file | Database connection string |
| `APFLOW_DATABASE_URL` | — | — | Alternative to DATABASE_URL |
| `APFLOW_STORAGE_DIALECT` | `storage.dialect` | sqlite | Storage backend (sqlite/postgresql) |
| `APFLOW_STORAGE_PATH` | `storage.path` | .data/apflow.db | SQLite file path |

## Governance

| Variable | Config Key | Default | Description |
|----------|-----------|---------|-------------|
| `APFLOW_GOVERNANCE_DEFAULT_POLICY` | `governance.default_policy` | None | Default cost policy name |
| `APFLOW_GOVERNANCE_DOWNGRADE_CHAIN` | `governance.downgrade_chain` | [] | Comma-separated model names |

## Durability

| Variable | Config Key | Default | Description |
|----------|-----------|---------|-------------|
| `APFLOW_DURABILITY_MAX_ATTEMPTS` | `durability.max_attempts` | 3 | Default retry attempts |
| `APFLOW_DURABILITY_BACKOFF_STRATEGY` | `durability.backoff_strategy` | exponential | fixed/exponential/linear |
| `APFLOW_DURABILITY_CIRCUIT_BREAKER_THRESHOLD` | `durability.circuit_breaker_threshold` | 5 | Consecutive failures to trip breaker |

## Distributed

| Variable | Default | Description |
|----------|---------|-------------|
| `APFLOW_CLUSTER_ENABLED` | false | Enable distributed mode |
| `APFLOW_NODE_ROLE` | auto | Node role (auto/leader/worker) |
| `APFLOW_NODE_ID` | auto-generated | Unique node identifier |
| `APFLOW_MAX_PARALLEL_TASKS` | 4 | Max concurrent task executions |

## YAML Config File

Place `apflow.yaml` in your project root or `~/.aiperceivable/apflow/`:

```yaml
api:
  server_url: http://localhost:8000
  timeout: 60.0
  jwt_secret: ${APFLOW_API_JWT_SECRET}  # env var reference

storage:
  dialect: sqlite
  path: .data/apflow.db

governance:
  default_policy: auto-downgrade
  downgrade_chain:
    - claude-opus-4
    - claude-sonnet-4
    - claude-haiku-4

durability:
  max_attempts: 5
  backoff_strategy: exponential
  circuit_breaker_threshold: 10
```
