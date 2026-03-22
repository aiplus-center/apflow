# Examples

This page contains examples and use cases for apflow.

## Demo Task Initialization

> **Note:** The built-in examples module has been removed from apflow core library.
> For demo task initialization, please use the **apflow-demo** project instead.

The **apflow-demo** project provides:
- Complete demo tasks for all executors
- Per-user demo task initialization
- Demo task validation against executor schemas

For more information, see the [apflow-demo](https://github.com/aiperceivable/apflow-demo) repository.

## Executor Metadata API

apflow provides utilities to query executor metadata for demo task generation:

```python
from apflow.core.extensions import (
    get_executor_metadata,
    validate_task_format,
    get_all_executor_metadata
)

# Get metadata for a specific executor
metadata = get_executor_metadata("system_info_executor")
# Returns: id, name, description, input_schema, examples, tags

# Validate a task against executor schema
task = {
    "name": "CPU Analysis",
    "schemas": {"method": "system_info_executor"},
    "inputs": {"resource": "cpu"}
}
is_valid = validate_task_format(task, "system_info_executor")

# Get metadata for all executors
all_metadata = get_all_executor_metadata()
```

## Basic Examples

Examples are also available in the test cases:

- Integration tests: `tests/integration/`
- Extension tests: `tests/extensions/`

            "properties": {
# Examples

> **Note:** Built-in demo tasks have moved to the [apflow-demo](https://github.com/aiperceivable/apflow-demo) project. For full demo task initialization and validation, please use that repository.

For in-project runnable examples and patterns, see:
- [Basic Task Examples](../examples/basic_task.md)
- [Real-World Examples](../examples/real-world.md)
- [Task Tree Examples](../examples/task-tree.md)
    parent_id=root.id
)

child2 = await task_manager.task_repository.create_task(
    name="child2",
    user_id="user_123",
    parent_id=root.id,
    dependencies=[child1.id]  # child2 depends on child1
)

# Build and execute
tree = TaskTreeNode(root)
tree.add_child(TaskTreeNode(child1))
tree.add_child(TaskTreeNode(child2))

result = await task_manager.distribute_task_tree(tree)
```

## Example: CrewAI Task with LLM Key

```python
# Via API with header
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/tasks",
        headers={
            "Content-Type": "application/json",
            "X-LLM-API-KEY": "openai:sk-your-key"  # Provider-specific format
        },
        json={
            "jsonrpc": "2.0",
            "method": "tasks.create",
            "params": {
                "tasks": [{
                    "id": "crewai-task",
                    "name": "CrewAI Research Task",
                    "user_id": "user123",
                    "schemas": {"method": "crewai_executor"},
                    "params": {
                        "works": {
                            "agents": {
                                "researcher": {
                                    "role": "Research Analyst",
                                    "goal": "Research and analyze the given topic",
                                    "llm": "openai/gpt-4"
                                }
                            },
                            "tasks": {
                                "research": {
                                    "description": "Research the topic: {topic}",
                                    "agent": "researcher"
                                }
                            }
                        }
                    },
                    "inputs": {
                        "topic": "Artificial Intelligence"
                    }
                }]
            }
        }
    )
```

For more examples, see the test cases in the main repository.

