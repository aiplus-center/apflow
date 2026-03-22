# Generate Executor Guide

This guide demonstrates the `generate_executor`'s intelligent task tree generation capabilities. The generate executor uses LLM to understand business requirements and automatically creates appropriate task trees.

## Overview

The generate executor provides two generation modes:

- **Single-Shot Mode** (default): Fast generation using a single LLM call. Best for simple requirements.
- **Multi-Phase Mode**: Higher quality generation using 4 specialized phases. Best for complex multi-executor workflows.

**See also**: [Generate Executor Improvements](../development/generate-executor-improvements.md) for detailed technical information about the dual-mode system, validation, and auto-fix mechanisms.

## Quick Start

### CLI Usage

Generate a task tree from natural language:

```bash
apflow generate task-tree "YOUR_REQUIREMENT_HERE"
```

Save the output to a file:

```bash
apflow generate task-tree "YOUR_REQUIREMENT" --output tasks.json
```

Use multi-phase mode for better quality:

```bash
apflow generate task-tree "YOUR_REQUIREMENT" --mode multi_phase
```

With custom LLM parameters:

```bash
apflow generate task-tree "YOUR_REQUIREMENT" --temperature 0.9 --max-tokens 6000
```

### Python API Usage

```python
from apflow.extensions.generate import GenerateExecutor

executor = GenerateExecutor(id="gen", name="Task Generator")

# Single-shot mode (default, faster)
result = await executor.execute({
    "requirement": "Fetch user data from API and save to database",
    "user_id": "user_123"
})

# Multi-phase mode (higher quality)
result = await executor.execute({
    "requirement": "Analyze aiperceivable.com website and generate report",
    "generation_mode": "multi_phase",  # Use multi-phase for complex tasks
    "user_id": "user_123"
})

tasks = result["tasks"]
```

## Generation Modes

### Single-Shot Mode

**When to use:**
- Simple, straightforward requirements
- Single-executor workflows
- Speed is priority
- Prototyping and testing

**Characteristics:**
- One LLM call generates complete task tree
- 2-3x faster than multi-phase
- Lower token usage (~2,000 tokens)
- Good quality for simple cases

### Multi-Phase Mode

**When to use:**
- Complex multi-step requirements
- Multi-executor workflows
- Quality is critical
- Production deployments

**Characteristics:**
- 4 specialized phases (analyze, design, generate, validate)
- Higher quality output
- Better structure for complex workflows
- Higher token usage (~6,000 tokens)
- Requires CrewAI: `pip install apflow[crewai]`

## Test Cases

## Test Case 1: Complex Data Pipeline

**Command:**
```bash
apflow generate task-tree "Fetch data from two different APIs in parallel, then merge the results, validate the merged data, and finally save to database"
```

**Expected Behavior:**
- Should generate parallel tasks for fetching from two APIs
- Should create a merge/aggregate task that depends on both fetch tasks
- Should create validation and save tasks in sequence
- Should demonstrate understanding of parallel execution patterns

## Test Case 2: ETL Workflow

**Command:**
```bash
apflow generate task-tree "Extract data from a REST API, transform it by filtering and aggregating, then load it into a database with proper error handling"
```

**Expected Behavior:**
- Should create sequential pipeline: Extract → Transform → Load
- Should use appropriate executors for each step
- Should include proper dependencies for execution order

## Test Case 3: Multi-Source Data Collection

**Command:**
```bash
apflow generate task-tree "Collect system information about CPU and memory in parallel, then run a command to analyze the collected data, and finally aggregate the results"
```

**Expected Behavior:**
- Should use system_info_executor for parallel data collection
- Should create command_executor for analysis
- Should use aggregate_results_executor for final step
- Should demonstrate parent_id for organization and dependencies for execution order

## Test Case 4: API Integration with Processing

**Command:**
```bash
apflow generate task-tree "Call a REST API to get user data, process the response to extract key information using a Python script, validate the processed data, and save results to a file"
```

**Expected Behavior:**
- Should create rest_executor for API call
- Should create command_executor for processing
- Should create validation and file operations
- Should show proper dependency chain

## Test Case 5: Complex Workflow with Conditional Steps

**Command:**
```bash
apflow generate task-tree "Fetch data from API, then process it in two different ways in parallel (filter and aggregate), merge both results, and finally save to database"
```

**Expected Behavior:**
- Should demonstrate fan-out pattern (one task spawns multiple)
- Should demonstrate fan-in pattern (multiple tasks converge)
- Should show proper use of dependencies for parallel execution

## Test Case 6: Real-World Business Scenario

**Command:**
```bash
apflow generate task-tree "Monitor system resources (CPU, memory, disk) in parallel, analyze the collected metrics, generate a report, and send notification if any metric exceeds threshold"
```

**Expected Behavior:**
- Should use system_info_executor multiple times in parallel
- Should create analysis and reporting tasks
- Should demonstrate complex dependency relationships

## Test Case 7: Data Processing Pipeline

**Command:**
```bash
apflow generate task-tree "Download data from multiple sources simultaneously, transform each dataset independently, then combine all transformed results into a single output file"
```

**Expected Behavior:**
- Should show parallel download tasks
- Should show parallel transformation tasks
- Should create final aggregation task
- Should demonstrate proper dependency management

## Test Case 8: API Chain with Error Handling

**Command:**
```bash
apflow generate task-tree "Call API A to get authentication token, use token to call API B for data, process the data, and if processing fails, call a fallback API"
```

**Expected Behavior:**
- Should create sequential API calls with token passing
- Should demonstrate optional dependencies for fallback
- Should show proper error handling pattern

## Test Case 9: Hierarchical Data Processing

**Command:**
```bash
apflow generate task-tree "Fetch data from API, organize it into categories, process each category independently in parallel, then aggregate all category results"
```

**Expected Behavior:**
- Should demonstrate hierarchical organization (parent_id)
- Should show parallel processing within categories
- Should create final aggregation step
- Should show both organizational and execution dependencies

## Test Case 10: Complete Business Workflow

**Command:**
```bash
apflow generate task-tree "Create a workflow that fetches customer data from API, validates customer information, processes orders in parallel for each customer, aggregates order results, calculates totals, and generates a final report"
```

**Expected Behavior:**
- Should demonstrate complex multi-step workflow
- Should show parallel processing pattern
- Should create proper dependency chain
- Should include all necessary executors

## Usage Tips

1. **Be Specific**: More detailed requirements lead to better task trees
2. **Mention Patterns**: Use words like "parallel", "sequential", "merge", "aggregate" to guide generation
3. **Specify Executors**: Mention specific operations (API, database, file, command) for better executor selection
4. **Describe Flow**: Explain the data flow and execution order in your requirement
5. **Choose Mode Wisely**:
   - Use single-shot (default) for simple tasks
   - Use multi-phase for complex multi-executor workflows
   - Multi-phase provides better structure for production use

## Features

With the enhanced generation system, the executor:
- ✅ Select relevant documentation sections based on requirement keywords
- ✅ Understand business context and map to appropriate executors
- ✅ Generate complete, realistic input parameters
- ✅ Create proper dependency chains for execution order
- ✅ Use parent_id appropriately for organization
- ✅ Follow framework best practices and patterns
- ✅ **Validate schema compliance** - catches type mismatches and missing fields
- ✅ **Enforce root task patterns** - ensures aggregator roots for multi-executor trees
- ✅ **Auto-fix common errors** - automatically corrects multiple roots and invalid parent_ids
- ✅ **Dual-mode generation** - choose between speed (single-shot) and quality (multi-phase)

## Mode Comparison

| Aspect | Single-Shot | Multi-Phase |
|--------|-------------|-------------|
| **Speed** | ~2-3 seconds | ~8-12 seconds |
| **Quality (simple)** | Good | Excellent |
| **Quality (complex)** | Fair | Excellent |
| **Token Usage** | ~2,000 | ~6,000 |
| **LLM Calls** | 1 | 4 |
| **Best For** | Simple tasks | Complex workflows |
| **Requirements** | Core only | Requires `apflow[crewai]` |

## Advanced Topics

### Validation and Auto-Fix

The generate executor includes comprehensive validation:

**Schema Compliance**: Validates that task inputs match executor schema definitions
```python
# This will be caught and reported
{
    "schemas": {"method": "scrape_executor"},
    "inputs": {"website": "https://example.com"}  # Wrong! Should be "url"
}
```

**Root Task Pattern**: Ensures multi-executor trees have aggregator roots
```python
# Bad: scrape_executor with children (will trigger warning)
# Good: aggregate_results_executor as root with scrape and llm children
```

**Auto-Fix**: Automatically corrects common errors:
- Multiple root tasks → wraps in aggregate_results_executor
- Invalid parent_ids → reassigns to actual root

### Multi-Phase Flow

When using `generation_mode="multi_phase"`, the system executes 4 phases:

1. **Phase 1: Requirement Analysis**
   - Input: Natural language requirement
   - Output: Structured analysis with goals and constraints
   - Agent: Requirements Analyst

2. **Phase 2: Structure Design**
   - Input: Analysis + Executor schemas
   - Output: Task tree skeleton (IDs, names, methods, relationships)
   - Agent: Task Structure Designer

3. **Phase 3: Input Generation**
   - Input: Task structure + Executor schemas
   - Output: Complete tasks with validated inputs
   - Agent: Task Input Generator

4. **Phase 4: Review & Validation**
   - Input: Complete tasks
   - Output: Validated and corrected task tree
   - Agent: Task Validator

### Troubleshooting

**Multi-phase mode falls back to single-shot**
- Solution: Install CrewAI: `pip install apflow[crewai]`

**Schema validation fails for custom executor**
- Cause: Executor doesn't implement `get_input_schema()`
- Solution: Add `get_input_schema()` method to your executor

**Generated tree has wrong structure**
- Try: Use multi-phase mode for better quality
- Try: Be more specific in requirement description
- Try: Mention executor names explicitly

## Further Reading

- [Generate Executor Improvements](../development/generate-executor-improvements.md) - Detailed technical documentation
- [Task Orchestration Guide](../guides/task-orchestration.md) - Understanding task trees and dependencies
- [Custom Tasks Guide](../guides/custom-tasks.md) - Creating custom executors

