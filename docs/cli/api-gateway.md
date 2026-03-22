# CLI with API Gateway

## Overview

The CLI can be configured to route commands through an API server, enabling:

- **Concurrent access**: Multiple clients (CLI, API, external tools) safely accessing the same database
- **Distributed deployment**: CLI on one machine, API server on another
- **Unified data**: All clients see the same data through shared database
- **Security**: API authentication, request validation, audit logging

## Problem Statement

### DuckDB Concurrency Issue

DuckDB (default database) is optimized for single-process access:

```
┌──────────┬──────────┬──────────┐
│   CLI    │   API    │ External │
│          │ Server   │ Tools    │
└─────┬────┴────┬─────┴────┬─────┘
      │         │          │
      └─────────┴──────────┘
            ↓
        DuckDB (Single-process optimized)
```

**Problem**: Multiple processes accessing DuckDB simultaneously can cause:
- Lock contention
- Transaction conflicts
- Potential data corruption

### Solution: API Gateway Pattern

Route all database access through a single API server:

```
┌──────────┬──────────┬──────────┐
│   CLI    │ External │ Browser  │
│          │ Tools    │ Client   │
└─────┬────┴────┬─────┴────┬─────┘
      │         │          │
      └─────────┼──────────┘
                ↓
          API Server (Single-process)
                ↓
            DuckDB (Safe)
```

**Benefits**:
- Single process accesses database (safe)
- Multiple clients use safe HTTP API
- All writes serialized through API
- Supports concurrent reads
- Enables distributed deployment

## Architecture

### Two Operating Modes

#### Mode 1: Direct Database Access (Default)

```
┌─────────────────────────────┐
│   CLI Process               │
│  (cli_config.py)            │
│    ↓                         │
│  TaskRepository             │
│    ↓                         │
│  DuckDB Instance            │
│  (~/.aiperceivable/data/)    │
└─────────────────────────────┘
```

**When to use**: Single user, single machine, development

**Commands**:
```bash
# No config needed
apflow run batch --tasks '[...]'
apflow tasks list
apflow tasks status task-001
```

**Pros**:
- No server required
- Fast (direct DB access)
- Simple setup
- Good for development

**Cons**:
- Only works locally
- Single-process only
- Cannot share database with API

#### Mode 2: API Gateway (Configured)

```
┌─────────────────┐
│   CLI Process   │
│  (api_client)   │
└────────┬────────┘
         │ HTTP/A2A
         ↓
┌─────────────────────────────┐
│   API Server                │
│  (api/app.py)               │
│    ↓                         │
│  TaskRepository             │
│    ↓                         │
│  DuckDB Instance            │
│  (Shared)                   │
└─────────────────────────────┘
```

**When to use**: Multi-client, production, distributed systems

**Commands**:
```bash
# Configure API server
apflow config init-server

# CLI automatically uses API
apflow run batch --tasks '[...]'
apflow tasks list
apflow tasks status task-001
```

**Pros**:
- Multiple clients safe
- Supports distributed deployment
- Can run API and CLI on different machines
- Production-ready concurrency

**Cons**:
- Requires API server running
- Slightly higher latency (HTTP overhead)
- More complex setup

## Configuration

### Quick Setup

```bash
# Initialize API server configuration (recommended)
apflow config init-server

# This creates:
# - .data/config.cli.yaml with api_server_url and generated JWT secret
```

### Manual Configuration

```bash
# Set API server URL
apflow config set api_server_url http://localhost:8000

# Generate authentication token
apflow config gen-token --role admin --save
```

### Environment Override

```bash
# Override for specific command
export APFLOW_CONFIG_DIR=/custom/config
apflow run batch --tasks '[...]'

# Or use environment variable directly
export APFLOW_API_SERVER=http://api.example.com
export APFLOW_API_AUTH_TOKEN=your-token
```

### Configuration File

**config.cli.yaml**:
```yaml
api_server_url: http://localhost:8000
api_timeout: 30
api_retry_count: 3
auto_use_api_if_configured: true
admin_auth_token: your-jwt-token
jwt_secret: server-jwt-secret
```

## CLI Usage with API Gateway

### Enable API Gateway

Once API server is configured, CLI automatically uses it:

```bash
# No changes needed - CLI detects config and uses API
apflow run batch --tasks '[...]'
```

### Run Without API (Force Direct Access)

If you want to skip API and use direct database access:

```bash
# Temporarily disable API
export APFLOW_API_SERVER=
apflow run batch --tasks '[...]'
```

Or remove configuration:
```bash
rm -rf .data/config.cli.yaml
```

## Error Handling

### Common Errors

**Error: "Cannot connect to API server"**

```bash
# Check if server is running
curl http://localhost:8000/health

# If not, start it
apflow serve
# Or for daemon mode
apflow daemon start --port 8000
```

**Error: "Unauthorized (401)"**

```bash
# Check token
apflow config set api_auth_token <new-token> --sensitive

# Or regenerate
apflow config gen-token --role admin --save
```

**Error: "Connection timeout"**

```bash
# Increase timeout
apflow config set api_timeout 60

# Or check network
ping localhost:8000
```

**Error: "Database locked"**

```bash
# Check if multiple processes accessing DuckDB
ps aux | grep apflow

# Use API server instead to avoid conflicts
apflow config init-server
apflow serve
```

### Error Recovery

Automatic retry with exponential backoff:

```
Request → Fail (retried up to 3 times)
  ↓ Wait 1s, retry
  ↓ Fail, Wait 2s, retry
  ↓ Fail, Wait 4s, retry
  ↓ Final error
```

Configure retry behavior:

```bash
apflow config set api_retry_count 5
apflow config set api_timeout 60
```

## Retry Strategy

### Default Behavior

- **Retries**: 3 attempts
- **Initial delay**: 1 second
- **Backoff**: Exponential (1s → 2s → 4s)
- **Max timeout**: 30 seconds per request

### Configuration

```bash
# Increase retries for unreliable networks
apflow config set api_retry_count 5

# Increase timeout for slow servers
apflow config set api_timeout 60
```

### Idempotent Operations

All CLI operations are idempotent:
- Running same task twice creates duplicate (OK, different ID)
- Querying same task returns same result (safe to retry)
- Cancelling same task twice is safe (already cancelled)

## Deployment Patterns

### Pattern 1: Single Machine (Development)

```
┌─────────────────────────────────┐
│        Same Machine             │
│  ┌─────────────┐                │
│  │   CLI       │ (Manual)       │
│  └──────┬──────┘                │
│         │ HTTP                  │
│  ┌──────▼──────────────────┐    │
│  │   API Server (daemon)  │    │
│  │   (HTTP port 8000)     │    │
│  │        ↓                │    │
│  │   DuckDB (shared)      │    │
│  └────────────────────────┘    │
└─────────────────────────────────┘
```

**Setup**:
```bash
# Initialize configuration
apflow config init-server

# Start API server in background
apflow daemon start --port 8000

# Use CLI (automatically uses API)
apflow run batch --tasks '[...]'
apflow tasks list
```

### Pattern 2: Distributed (Production)

```
┌──────────────────────┐
│   Client Machine A   │
│  ┌────────────────┐  │
│  │  CLI Instance  │  │
│  └────────┬───────┘  │
└───────────│──────────┘
            │ HTTP
┌───────────▼──────────┐
│   API Server        │
│   (machine B)       │
│   (HTTP port 8000)  │
│        ↓            │
│   DuckDB (NFS)      │
└────────────────────┘
            ▲
┌───────────│──────────┐
│   Client Machine C   │
│  ┌────────────────┐  │
│  │  CLI Instance  │  │
│  │ or Web Browser │  │
│  └────────────────┘  │
└──────────────────────┘
```

**Setup**:
```bash
# On API Server Machine
export DATABASE_URL="postgresql+asyncpg://user:pass@db-server/apflow"
apflow daemon start --port 8000

# On Client Machine
apflow config set api_server http://api-server:8000
apflow config set api_auth_token <token> --sensitive
apflow run batch --tasks '[...]'
```

### Pattern 3: Hybrid (API + CLI Mixed)

```
┌─────────────────────┐
│   API Server        │
│   (HTTP clients)    │
│        ↓            │
│   DuckDB            │
└──────────┬──────────┘
           ▲
           │ Direct Access
┌──────────┴──────────┐
│   CLI Instance      │
│   (Local tasks)     │
└─────────────────────┘
```

**Use case**: CLI tasks locally, API for remote access

**Setup**:
```bash
# API and CLI on same machine
# - CLI uses direct DB access (no config)
# - API uses same DuckDB
# - They share data automatically

# Start API server
apflow serve --reload

# In another terminal, use CLI
apflow run batch --tasks '[...]'

# Both see same data
apflow tasks list  # Shows tasks from CLI and API
```

## Migration Guide

### From Direct Access to API Gateway

**Step 1: Start API server**
```bash
apflow daemon start --port 8000
```

**Step 2: Configure CLI**
```bash
apflow config init-server
```

**Step 3: Switch to API**
CLI automatically detects and uses API. No code changes needed.

**Step 4: Verify**
```bash
# This now goes through API instead of direct DB
apflow tasks list
apflow run batch --tasks '[...]'
```

**Step 5: Stop direct access**
Once API is stable, can stop direct CLI database access:

```bash
# Leave config file for automatic API routing
# All CLI commands now use API
```

## Testing & Validation

### Health Check

```bash
# Check if API server is responding
curl http://localhost:8000/health

# Check authentication
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/tasks
```

### Load Testing

```bash
# Test concurrent CLI access through API
for i in {1..10}; do
  (apflow run batch$i --tasks '[...]' &)
done
wait

# All requests handled safely
apflow tasks list
```

### Data Consistency

```bash
# Via API
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/tasks

# Via CLI
apflow tasks list

# Data should be identical
```

## FAQ

### Q: Do I need API server for CLI?

**A**: No. CLI works independently. API server is optional for multi-client scenarios.

### Q: Can CLI and API run at the same time?

**A**: Yes. When API is configured, CLI automatically routes through it. Both read/write to same database.

### Q: What if API server goes down?

**A**: CLI falls back to direct database access (if configured), or fails with connection error.

### Q: Is API gateway required for production?

**A**: Recommended for production because it:
- Handles concurrent access safely
- Supports distributed deployment
- Provides audit logging
- Enables request validation

### Q: Can I use PostgreSQL instead of DuckDB?

**A**: Yes. Set `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/apflow"
apflow daemon start  # Uses PostgreSQL
```

Both CLI and API will use PostgreSQL automatically.

### Q: How do I know if CLI is using API or direct DB?

**A**: Check configuration:
```bash
apflow config path
# Shows active config location

# If api_server is set, CLI uses API
# Otherwise, CLI uses direct DB
```

## Summary

- ✅ **CLI can work with or without API server**
- ✅ **API gateway solves DuckDB concurrency**
- ✅ **All data shared between CLI and API**
- ✅ **Easy to enable: `apflow config init-server`**
- ✅ **Automatic routing: no code changes needed**
- ✅ **Supports distributed deployment**

Use direct access for development, API gateway for production.
