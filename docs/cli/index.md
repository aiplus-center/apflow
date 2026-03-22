# CLI Documentation

This directory contains comprehensive guides for using the apflow CLI.

## Overview

For a high-level overview and quick start, see **[CLI Usage Guide](../guides/cli.md)** in the guides directory.

## Structure

- **[configuration.md](./configuration.md)** - Configuration management
  - Multi-location system (project-local, user-global, environment override)
  - File structure (config.cli.yaml)
  - Configuration commands (init-server, set, gen-token)
  - File permissions and security
  - Best practices

- **[commands.md](./commands.md)** - Complete command reference
  - Task execution (run, list, status, watch)
  - Task management (create, update, delete, copy)
  - Flow management
  - Executor methods
  - Input/output formats

- **[api-gateway.md](./api-gateway.md)** - CLI with API Server integration
  - Direct access vs API gateway modes
  - Why API gateway (DuckDB concurrency)
  - Configuration
  - Error handling and retry strategy
  - Deployment patterns
  - Testing and validation

- **[examples.md](./examples.md)** - Practical usage examples
  - Quick start examples
  - Real-world scenarios
  - Advanced usage patterns
  - Common workflow examples

## Quick Navigation

### For First-Time Users
Start with the **[CLI Usage Guide](../guides/cli.md)** to understand CLI basics, then [commands.md](./commands.md) for practical examples.

### For Configuration
See [configuration.md](./configuration.md) for multi-location setup, file permissions, and management commands.

### For Production Deployment
See [api-gateway.md](./api-gateway.md) for API server integration and distributed deployment patterns.

### For Advanced Usage
See [examples.md](./examples.md) for complex workflows, parallel execution, and scripting.

## Key Concepts

### CLI Modes

**Direct Access** (Default):
- CLI directly accesses database
- No server required
- Fast but single-process only

**API Gateway** (Production):
- CLI communicates with API server
- Multiple clients safe
- Distributed deployment support

### Configuration Priority

1. Environment variable: `APFLOW_CONFIG_DIR` (highest)
2. Project-local: `.data/` directory
3. User-global: `~/.aiperceivable/apflow/`
4. Default: Current directory (lowest)

### File Structure

- `config.cli.yaml` (600 permissions) - All CLI settings (sensitive and non-sensitive)

## Common Tasks

### Initialize Configuration
```bash
apflow config init-server
```

### Execute Tasks
```bash
apflow run batch-id --tasks '[...]'
```

### Query Task Status
```bash
apflow tasks list
apflow tasks status task-id
apflow tasks watch --all
```

### Manage Configuration
```bash
apflow config path              # Show all locations
apflow config set key value     # Set value
apflow config gen-token --save  # Generate JWT token
```

## External Links

- [Main Documentation](../index.md)
- [Getting Started](../../getting-started/index.md)
- [API Server Guide](../api-server.md)
- [Best Practices](../best-practices.md)
- [Contributing Guide](../../development/contributing.md)

## Support

For issues or questions:
1. Check [FAQ](../faq.md)
2. See [Troubleshooting](./configuration.md#troubleshooting) sections
3. Review [Best Practices](../best-practices.md)
4. Open an issue on GitHub
