# Environment Variables Reference

This document describes all environment variables used by apflow.

## Naming Convention

apflow follows a consistent naming pattern for environment variables:

- **Preferred**: Variables with `APFLOW_` prefix (e.g., `APFLOW_LOG_LEVEL`)
- **Fallback**: Generic names without prefix (e.g., `LOG_LEVEL`)

When both are set, `APFLOW_*` variables take precedence. This design allows apflow to:
- Run in multi-service environments without conflicts
- Integrate with existing systems that use generic variable names
- Maintain clear ownership of configuration

## Core Configuration

### Database

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_DATABASE_URL` | string | auto-detected | Database connection string. Takes precedence over `DATABASE_URL` |
| `DATABASE_URL` | string | auto-detected | Fallback database connection string |

**Priority for DuckDB file location:**
1. `APFLOW_DATABASE_URL` or `DATABASE_URL` (if set)
2. `.data/apflow.duckdb` (if exists in project)
3. `~/.aiperceivable/data/apflow.duckdb` (if exists, legacy)
4. `.data/apflow.duckdb` (default for new projects)
5. `~/.aiperceivable/data/apflow.duckdb` (default outside projects)

**Examples:**
```bash
# PostgreSQL
APFLOW_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/apflow

# Custom DuckDB path
APFLOW_DATABASE_URL=duckdb:///path/to/custom.duckdb

# Using generic fallback
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/apflow
```

### Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_LOG_LEVEL` | string | INFO | Log level for apflow. Takes precedence over `LOG_LEVEL` |
| `LOG_LEVEL` | string | INFO | Fallback log level |

**Valid values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Examples:**
```bash
# Use apflow-specific log level
APFLOW_LOG_LEVEL=DEBUG

# Or generic fallback
LOG_LEVEL=INFO
```

### API Server

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_API_HOST` | string | 0.0.0.0 | API server host address. Takes precedence over `API_HOST` |
| `API_HOST` | string | 0.0.0.0 | Fallback API host |
| `APFLOW_API_PORT` | integer | 8000 | API server port. Takes precedence over `API_PORT` |
| `API_PORT` | integer | 8000 | Fallback API port |
| `APFLOW_BASE_URL` | string | auto | Base URL for API service |
| `APFLOW_API_PROTOCOL` | string | a2a | API protocol type: `a2a`, `mcp`, or `graphql` |

**Examples:**
```bash
# Use apflow-specific configuration
APFLOW_API_HOST=127.0.0.1
APFLOW_API_PORT=9000
APFLOW_API_PROTOCOL=mcp
# Or GraphQL
APFLOW_API_PROTOCOL=graphql

# Or generic fallback
API_HOST=0.0.0.0
API_PORT=8000
```

### Security

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_JWT_SECRET` | string | - | Secret key for JWT token signing |
| `APFLOW_JWT_ALGORITHM` | string | HS256 | JWT signing algorithm |

**Example:**
```bash
APFLOW_JWT_SECRET=your-secret-key-here
APFLOW_JWT_ALGORITHM=HS256
```

### CORS

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_CORS_ORIGINS` | string | * | Comma-separated allowed CORS origins |
| `APFLOW_CORS_ALLOW_ALL` | boolean | false | Allow all CORS origins |

**Examples:**
```bash
# Specific origins
APFLOW_CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Allow all (development only)
APFLOW_CORS_ALLOW_ALL=true
```

### API Features

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_ENABLE_SYSTEM_ROUTES` | boolean | true | Enable system information routes |
| `APFLOW_ENABLE_DOCS` | boolean | true | Enable API documentation routes |

### CLI Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_CONFIG_DIR` | string | auto-detected | Override CLI config directory location |

**Default locations (priority order):**
1. `APFLOW_CONFIG_DIR` (if set)
2. `.data/` (if in project)
3. `~/.aiperceivable/apflow/`

## Storage Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_MAX_SESSIONS` | integer | 10 | Maximum concurrent storage sessions |
| `APFLOW_SESSION_TIMEOUT` | integer | 300 | Session timeout in seconds |
| `APFLOW_TASK_TABLE_NAME` | string | tasks | Custom task table name |
| `APFLOW_TASK_MODEL_CLASS` | string | - | Custom task model class path |

## Extensions

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_EXTENSIONS` | string | - | Comma-separated extensions by directory name to load (also restricts available executors for security) |
| `APFLOW_EXTENSIONS_IDS` | string | - | Comma-separated extension IDs to load (also restricts available executors for security) |
| `APFLOW_LLM_PROVIDER` | string | - | LLM provider for AI extensions |

**Example:**
```bash
# Load only stdio and http extensions (security: only these executors are accessible)
APFLOW_EXTENSIONS=stdio,http
APFLOW_EXTENSIONS_IDS=system_info_executor,rest_executor
APFLOW_LLM_PROVIDER=openai
```

**Security Note:**
When `APFLOW_EXTENSIONS` is set, only executors from the specified extensions can be accessed via API endpoints (`tasks.execute`, `tasks.generate`). This provides access control to restrict which executors users can invoke. If not set, all installed executors are available.

## Extension-Specific Variables

### STDIO Extension

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_STDIO_ALLOW_COMMAND` | boolean | false | Allow arbitrary command execution |
| `APFLOW_STDIO_COMMAND_WHITELIST` | string | - | Comma-separated allowed commands |

**Example:**
```bash
APFLOW_STDIO_ALLOW_COMMAND=true
APFLOW_STDIO_COMMAND_WHITELIST=echo,ls,cat
```

### Email Extension

The email extension supports sending emails via Resend API or SMTP. Environment variables provide default configuration that can be overridden by task inputs.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RESEND_API_KEY` | string | - | Resend API key for cloud email sending |
| `SMTP_HOST` | string | - | SMTP server hostname |
| `SMTP_PORT` | integer | 587 | SMTP server port |
| `SMTP_USERNAME` | string | - | SMTP authentication username |
| `SMTP_PASSWORD` | string | - | SMTP authentication password |
| `SMTP_USE_TLS` | string | true | Whether to use STARTTLS ("true"/"false") |
| `FROM_EMAIL` | string | - | Default sender email address (shared by both providers) |

**Provider Auto-Detection:**
- If `RESEND_API_KEY` is set, provider defaults to `resend`
- If `SMTP_HOST` is set (and no Resend key), provider defaults to `smtp`

**Example (Resend):**
```bash
RESEND_API_KEY=re_xxxxxxxxxxxxx
FROM_EMAIL=noreply@example.com
```

**Example (SMTP with Gmail):**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
FROM_EMAIL=your-email@gmail.com
```

**See also:** [Email Executor Guide](../examples/email-executor.md) for detailed usage examples.

### Scheduler & Webhooks

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_WEBHOOK_SECRET` | string | - | HMAC secret key for webhook signature validation |
| `APFLOW_WEBHOOK_ALLOWED_IPS` | string | - | Comma-separated IP addresses allowed to trigger webhooks |
| `APFLOW_WEBHOOK_RATE_LIMIT` | integer | 0 | Max webhook requests per minute (0=unlimited) |

**Example:**
```bash
APFLOW_WEBHOOK_SECRET=your-webhook-secret
APFLOW_WEBHOOK_ALLOWED_IPS=10.0.0.1,10.0.0.2
APFLOW_WEBHOOK_RATE_LIMIT=60
```

### Daemon

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_DAEMON_PID_FILE` | string | auto | Custom daemon PID file location |
| `APFLOW_DAEMON_LOG_FILE` | string | auto | Custom daemon log file location |

## Distributed Cluster

These variables configure distributed cluster mode. Set `APFLOW_CLUSTER_ENABLED=true` to activate. Requires PostgreSQL. See the [Distributed Cluster Guide](./distributed-cluster.md) for details.

### Cluster Identity

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_CLUSTER_ENABLED` | boolean | false | Enable distributed cluster mode |
| `APFLOW_NODE_ID` | string | auto-generated | Unique identifier for this node |
| `APFLOW_NODE_ROLE` | string | auto | Node role: `auto`, `leader`, `worker`, or `observer` |

### Leader Election

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_LEADER_LEASE` | integer | 30 | Leader lease duration in seconds |
| `APFLOW_LEADER_RENEW` | integer | 10 | Leader lease renewal interval in seconds |

### Task Lease Management

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_LEASE_DURATION` | integer | 30 | Task lease duration in seconds |
| `APFLOW_LEASE_CLEANUP_INTERVAL` | integer | 10 | Expired lease cleanup interval in seconds |

### Worker Polling

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_POLL_INTERVAL` | integer | 5 | Worker task poll interval in seconds |
| `APFLOW_MAX_PARALLEL_TASKS` | integer | 4 | Maximum concurrent tasks per worker node |

### Node Health Monitoring

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_HEARTBEAT_INTERVAL` | integer | 10 | Heartbeat signal interval in seconds |
| `APFLOW_NODE_STALE_THRESHOLD` | integer | 30 | Seconds without heartbeat before node is `stale` |
| `APFLOW_NODE_DEAD_THRESHOLD` | integer | 120 | Seconds without heartbeat before node is `dead` |

**Example:**
```bash
APFLOW_CLUSTER_ENABLED=true
APFLOW_NODE_ID=node-1
APFLOW_NODE_ROLE=auto
APFLOW_LEADER_LEASE=30
APFLOW_MAX_PARALLEL_TASKS=8
```

## Development & Testing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APFLOW_DEMO_SLEEP_SCALE` | float | 1.0 | Scale factor for demo sleep times |

**Example:**
```bash
# Speed up demos by 10x
APFLOW_DEMO_SLEEP_SCALE=0.1
```

## Third-Party Service Keys

These variables follow the standard naming conventions of third-party services and should **not** have `APFLOW_` prefix:

| Variable | Service | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | OpenAI | API key for OpenAI services |
| `OPENAI_MODEL` | OpenAI | Default OpenAI model name |
| `ANTHROPIC_API_KEY` | Anthropic | API key for Anthropic services |
| `ANTHROPIC_MODEL` | Anthropic | Default Anthropic model name |

**Example:**
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
```

## Complete Example

Here's a complete `.env` file example:

```env
# Database (choose one)
APFLOW_DATABASE_URL=duckdb:///.data/apflow.duckdb
# APFLOW_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/apflow

# Logging
APFLOW_LOG_LEVEL=INFO

# API Server
APFLOW_API_HOST=0.0.0.0
APFLOW_API_PORT=8000
APFLOW_API_PROTOCOL=a2a

# Security
APFLOW_JWT_SECRET=your-secret-key-change-in-production
APFLOW_JWT_ALGORITHM=HS256

# CORS (adjust for production)
APFLOW_CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Features
APFLOW_ENABLE_SYSTEM_ROUTES=true
APFLOW_ENABLE_DOCS=true

# Distributed Cluster (optional)
# APFLOW_CLUSTER_ENABLED=true
# APFLOW_NODE_ROLE=auto
# APFLOW_MAX_PARALLEL_TASKS=4

# LLM Services (if using AI extensions)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

## Best Practices

1. **Use `.env` file**: Store environment variables in a `.env` file in your project root
2. **Never commit secrets**: Add `.env` to `.gitignore`
3. **Use APFLOW_ prefix**: Prefer `APFLOW_*` variables for better isolation
4. **Document overrides**: When using generic fallbacks, document why
5. **Validate in production**: Always validate required variables are set in production

## Priority Summary

When multiple configuration sources exist, apflow follows this priority:

1. **Environment variables with APFLOW_ prefix** (highest)
2. **Generic environment variables** (fallback)
3. **CLI config files** (`.data/` or `~/.aiperceivable/apflow/`)
4. **Default values** (lowest)

This allows maximum flexibility while maintaining sensible defaults.

