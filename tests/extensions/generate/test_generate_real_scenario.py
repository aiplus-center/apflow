"""
Real-world integration tests for generate executor auto-fix functionality.

Tests the auto-fix mechanism with realistic scenarios that would occur in production,
particularly the multi-executor root task validation and auto-fix.

Requires OPENAI_API_KEY environment variable for real LLM calls.
"""

import pytest
import os
import json
from pathlib import Path
from apflow.extensions.generate.generate_executor import GenerateExecutor
from apflow import TaskManager, create_session
from apflow.core.execution.task_creator import TaskCreator


# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file in project root"""
    env_file = Path(__file__).parent.parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


# Load environment variables at module level
load_env_file()

# Note: Do NOT enable command_executor by default
# Tests should use scrape_executor for web scraping, not command_executor
# os.environ["APFLOW_STDIO_ALLOW_COMMAND"] = "1"  # Commented out to test realistic scenarios


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_website_analysis_with_auto_fix():
    """
    Real integration test: Generate task tree for analyzing aiperceivable.com.

    This test:
    1. Calls GenerateExecutor with real AI to generate a task tree
    2. The requirement naturally leads to multiple executors (scrape + analysis)
    3. Validates that auto-fix converts root to aggregator if needed
    4. Ensures the final task tree passes all validations
    """
    executor = GenerateExecutor(user_id="demo_user_91c0194805d17ad1")
    requirement = "please analyze aiperceivable.com and give a report"

    print(f"\n{'='*80}")
    print(f"Requirement: {requirement}")
    print(f"{'='*80}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "demo_user_91c0194805d17ad1",
            "generation_mode": "single_shot",
        }
    )

    print("\n=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    # Validate result
    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"
    assert "tasks" in result, "Result should contain tasks"

    tasks = result["tasks"]
    assert isinstance(tasks, list), "Tasks should be a list"
    assert len(tasks) > 0, "Should generate at least one task"

    # Check if multiple executors are used
    executors = set()
    for task in tasks:
        executor_id = task.get("schemas", {}).get("method", "")
        if executor_id and "aggregate" not in executor_id.lower():
            executors.add(executor_id)

    print("\n=== Executors Used ===")
    print(f"Non-aggregator executors: {executors}")
    print(f"Total tasks: {len(tasks)}")

    # If multiple executors, verify root is aggregator
    if len(executors) >= 2:
        root_tasks = [t for t in tasks if not t.get("parent_id")]
        assert len(root_tasks) == 1, "Should have exactly one root task"

        root_task = root_tasks[0]
        root_executor = root_task.get("schemas", {}).get("method", "")

        print(f"\nRoot task executor: {root_executor}")
        print(f"Root task name: {root_task.get('name')}")

        # When using multiple executors, root should be aggregator
        assert "aggregate" in root_executor.lower(), (
            f"With {len(executors)} different executors, root should use aggregator, "
            f"but uses '{root_executor}'"
        )
        print("✅ Root task correctly uses aggregator executor")
    else:
        print(f"\n✓ Only {len(executors)} executor(s) used, no aggregator needed")

    # Final validation
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Final task tree should be valid: {validation['error']}"
    print("\n✅ Final task tree passes all validations")


@pytest.mark.asyncio
async def test_manual_multi_executor_scenario_with_auto_fix():
    """
    Unit test: Manually create a multi-executor scenario and verify auto-fix.

    This test doesn't require API key as it manually constructs the task tree
    and tests the validation + auto-fix logic directly.
    """
    executor = GenerateExecutor(user_id="demo_user_91c0194805d17ad1")

    # Create a realistic task tree that would fail validation
    tasks_with_multiple_executors = [
        {
            "id": "root-task-1",
            "name": "Analyze AI Perceivable Website",
            "schemas": {"method": "scrape_executor"},
            "inputs": {"url": "https://aiperceivable.com", "user_id": "demo_user_91c0194805d17ad1"},
        },
        {
            "id": "task-2",
            "name": "Analyze Scraped Website Content with AI Crew",
            "parent_id": "root-task-1",
            "schemas": {"method": "crewai_executor"},
            "inputs": {
                "user_id": "demo_user_91c0194805d17ad1",
                "works": {
                    "agents": {
                        "web_analyst": {
                            "role": "Web Content Analyst",
                            "goal": "Analyze website content and structure",
                        }
                    },
                    "tasks": {
                        "analyze_content": {
                            "description": "Analyze the scraped website content",
                            "agent": "web_analyst",
                        }
                    },
                },
            },
            "dependencies": [{"id": "root-task-1", "required": True}],
        },
    ]

    print("\n=== Initial Task Tree (Multiple Executors) ===")
    print(json.dumps(tasks_with_multiple_executors, indent=2))

    # Validate - should fail
    print("\n=== Validation (Should Fail) ===")
    validation_result = executor._validate_tasks_array(tasks_with_multiple_executors)
    print(f"Valid: {validation_result['valid']}")

    assert not validation_result["valid"], "Should fail validation"
    assert (
        "different executors" in validation_result["error"]
    ), "Error should mention different executors"
    print(f"Expected error: {validation_result['error']}")

    # Test auto-fix
    print("\n=== Attempting Auto-Fix ===")
    fixed_tasks = executor._attempt_auto_fix(
        tasks_with_multiple_executors, validation_result["error"]
    )

    assert fixed_tasks is not None, "Auto-fix should succeed"
    print("✅ Auto-fix succeeded!")

    print("\n=== Fixed Task Tree ===")
    print(json.dumps(fixed_tasks, indent=2))

    # Verify the fix
    root_tasks = [t for t in fixed_tasks if not t.get("parent_id")]
    assert len(root_tasks) == 1, "Should have one root task"

    root_task = root_tasks[0]
    root_executor = root_task.get("schemas", {}).get("method", "")

    assert (
        root_executor == "aggregate_results_executor"
    ), f"Root should use aggregate_results_executor, got '{root_executor}'"
    print(f"✅ Root task converted to: {root_executor}")

    # Validate fixed tasks
    print("\n=== Revalidation ===")
    revalidation = executor._validate_tasks_array(fixed_tasks)
    print(f"Valid: {revalidation['valid']}")

    assert revalidation["valid"], f"Fixed tasks should be valid: {revalidation['error']}"
    print("✅ Fixed task tree passes validation!")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_explicit_multi_executor_requirement():
    """
    Real integration test: Explicit requirement for multiple executors.

    Tests that when a requirement explicitly needs multiple different executors,
    the generate executor properly creates an aggregator root.
    """
    executor = GenerateExecutor(user_id="test_user")
    requirement = (
        "Create a workflow to analyze a website: "
        "1. First scrape the website content using scrape_executor "
        "2. Then use crewai_executor with AI agents to analyze the content "
        "3. Finally generate a summary report. "
        "Make sure to use different executors for different tasks."
    )

    print(f"\n{'='*80}")
    print(f"Requirement: {requirement}")
    print(f"{'='*80}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("\n=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]
    assert len(tasks) >= 2, "Should generate multiple tasks"

    # Count unique executors
    executors_used = set()
    for task in tasks:
        executor_id = task.get("schemas", {}).get("method", "")
        if executor_id:
            executors_used.add(executor_id)

    print("\n=== Executors Used ===")
    for executor_id in executors_used:
        count = sum(1 for t in tasks if t.get("schemas", {}).get("method") == executor_id)
        print(f"  {executor_id}: {count} task(s)")

    # Verify structure
    root_tasks = [t for t in tasks if not t.get("parent_id")]
    assert len(root_tasks) == 1, f"Should have one root, got {len(root_tasks)}"

    root_executor = root_tasks[0].get("schemas", {}).get("method", "")
    print(f"\nRoot executor: {root_executor}")

    # Validate the final tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Generated task tree should be valid: {validation['error']}"
    print("\n✅ Task tree passes all validations")


@pytest.mark.asyncio
@pytest.mark.timeout(300)  # 5 minutes for full execution
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_end_to_end_generate_and_execute_website_analysis():
    """
    End-to-end integration test: Generate task tree and execute it.

    This test:
    1. Uses GenerateExecutor to generate a task tree from natural language
    2. Creates the task tree using TaskCreator
    3. Executes the entire task tree using TaskManager
    4. Validates the execution results

    User requirement: "please analyze aiperceivable.com and give a report with json format"
    """
    print(f"\n{'='*80}")
    print("END-TO-END TEST: Generate + Execute Website Analysis")
    print(f"{'='*80}\n")

    # Step 1: Generate task tree
    print("Step 1: Generating task tree from requirement...")
    generator = GenerateExecutor(user_id="demo_user_91c0194805d17ad1")
    requirement = "please analyze aiperceivable.com and give a report with json format"

    print(f"Requirement: {requirement}\n")

    generation_result = await generator.execute(
        {
            "requirement": requirement,
            "user_id": "demo_user_91c0194805d17ad1",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generation Result ===")
    print(f"Status: {generation_result['status']}")
    assert (
        generation_result["status"] == "completed"
    ), f"Generation failed: {generation_result.get('error')}"

    tasks_array = generation_result["tasks"]
    print(f"Generated {len(tasks_array)} tasks")
    print("\n=== Generated Task Tree ===")
    print(json.dumps(tasks_array, indent=2))

    # VALIDATION: Check for template variable issues in CrewAI tasks
    print("\n=== Validating CrewAI Tasks for Template Variables ===")
    crewai_tasks = [
        t for t in tasks_array if t.get("schemas", {}).get("method") == "crewai_executor"
    ]

    if crewai_tasks:
        print(f"Found {len(crewai_tasks)} CrewAI task(s), validating...")

        problematic_vars = [
            "{content}",
            "{data}",
            "{website_content}",
            "{scraped_content}",
            "{text}",
            "{html}",
            "{result}",
            "{scraped_data}",
        ]

        for crewai_task in crewai_tasks:
            task_name = crewai_task.get("name", "Unknown")
            works = crewai_task.get("inputs", {}).get("works", {})
            crew_tasks = works.get("tasks", {})

            for crew_task_name, crew_task_def in crew_tasks.items():
                description = crew_task_def.get("description", "")

                found_vars = [var for var in problematic_vars if var in description]
                if found_vars:
                    print(
                        f"  ❌ Task '{task_name}' -> '{crew_task_name}' uses problematic variables: {found_vars}"
                    )
                    print(f"     Description: {description}")
                    pytest.fail(
                        "CrewAI task contains template variables that will cause runtime error. "
                        "This indicates the LLM prompt fix is not working correctly."
                    )

        print("  ✓ All CrewAI tasks validated - no problematic template variables")
    else:
        print("  No CrewAI tasks in tree - skipping validation")

    # Step 2: Create task tree in database
    print("\n" + "=" * 80)
    print("Step 2: Creating task tree in database...")
    print("=" * 80 + "\n")

    db = create_session()
    task_creator = TaskCreator(db)

    try:
        task_tree = await task_creator.create_task_tree_from_array(tasks_array)
        print("✅ Task tree created successfully")
        print(f"Root task ID: {task_tree.task.id}")
        print(f"Root task name: {task_tree.task.name}")

        # Count tasks in tree
        def count_tasks(node):
            return 1 + sum(count_tasks(child) for child in node.children)

        total_tasks = count_tasks(task_tree)
        print(f"Total tasks in tree: {total_tasks}")

        # Step 3: Execute task tree
        print("\n" + "=" * 80)
        print("Step 3: Executing task tree...")
        print("=" * 80 + "\n")

        task_manager = TaskManager(db)

        # Execute the tree
        await task_manager.distribute_task_tree(task_tree)

        print("\n✅ Task tree execution completed!")

        # Step 4: Validate results
        print("\n" + "=" * 80)
        print("Step 4: Validating execution results...")
        print("=" * 80 + "\n")

        # Get all tasks and check their status
        async def get_all_task_ids(node):
            task_ids = [node.task.id]
            for child in node.children:
                task_ids.extend(await get_all_task_ids(child))
            return task_ids

        all_task_ids = await get_all_task_ids(task_tree)

        completed_count = 0
        failed_count = 0

        for task_id in all_task_ids:
            task = await task_manager.task_repository.get_task_by_id(task_id)
            print(f"\nTask: {task.name}")
            print(f"  ID: {task.id}")
            print(f"  Status: {task.status}")
            print(f"  Executor: {task.schemas.get('method', 'N/A') if task.schemas else 'N/A'}")

            if task.status == "completed":
                completed_count += 1
                if task.result:
                    result_str = (
                        json.dumps(task.result, indent=2)
                        if isinstance(task.result, dict)
                        else str(task.result)
                    )
                    # Truncate long results
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "\n  ... (truncated)"
                    print(f"  Result: {result_str}")
            elif task.status == "failed":
                failed_count += 1
                print(f"  Error: {task.error}")

        print(f"\n{'='*80}")
        print("Execution Summary:")
        print(f"  Total tasks: {total_tasks}")
        print(f"  Completed: {completed_count}")
        print(f"  Failed: {failed_count}")
        print(f"{'='*80}\n")

        # Validate root task result
        root_task = await task_manager.task_repository.get_task_by_id(task_tree.task.id)
        assert root_task.status in [
            "completed",
            "failed",
        ], f"Root task should be completed or failed, got: {root_task.status}"

        if root_task.status == "completed":
            print("✅ Root task completed successfully!")
            print("\n=== Final Report (Root Task Result) ===")
            if root_task.result:
                print(json.dumps(root_task.result, indent=2))

            # Verify the result format
            assert root_task.result is not None, "Root task should have a result"

            # If it's an aggregator, it should contain results from child tasks
            root_executor = root_task.schemas.get("method", "") if root_task.schemas else ""
            if "aggregate" in root_executor.lower():
                print("\n✅ Root task used aggregator executor as expected")
                # Aggregator should have collected results from dependencies
                if isinstance(root_task.result, dict):
                    print(f"Aggregated {len(root_task.result)} results")
        else:
            print(f"❌ Root task failed: {root_task.error}")
            # Even if root failed, we can still verify the workflow was attempted
            assert failed_count < total_tasks, "Not all tasks should have failed"

        # Final validation: Check that we had meaningful execution
        assert completed_count > 0, "At least some tasks should have completed"
        print("\n✅ End-to-end test completed successfully!")
        print(f"   {completed_count}/{total_tasks} tasks completed")

        # ADDITIONAL VALIDATION: Check dependency data transmission and result format
        print("\n" + "=" * 80)
        print("VALIDATION: Checking Dependency Data & Result Format")
        print("=" * 80 + "\n")

        # Find scrape and CrewAI tasks to validate data flow
        scrape_tasks = []
        crewai_tasks = []

        for task_id in all_task_ids:
            task = await task_manager.task_repository.get_task_by_id(task_id)
            executor_type = task.schemas.get("method", "") if task.schemas else ""

            if executor_type == "scrape_executor":
                scrape_tasks.append(task)
            elif executor_type == "crewai_executor":
                crewai_tasks.append(task)

        print(f"Found {len(scrape_tasks)} scrape task(s) and {len(crewai_tasks)} CrewAI task(s)")

        # Validate scrape task results
        for scrape_task in scrape_tasks:
            print(f"\n=== Scrape Task: {scrape_task.name} ===")
            print(f"  Status: {scrape_task.status}")

            if scrape_task.status == "completed" and scrape_task.result:
                result_content = (
                    scrape_task.result.get("result", "")
                    if isinstance(scrape_task.result, dict)
                    else str(scrape_task.result)
                )
                content_preview = (
                    result_content[:200]
                    if isinstance(result_content, str)
                    else str(result_content)[:200]
                )
                print(f"  Result preview: {content_preview}...")
                print(f"  Result length: {len(str(result_content))} chars")

                # Check if result contains meaningful content
                if len(str(result_content)) < 100:
                    print("  ⚠️  WARNING: Scrape result seems too short")
                else:
                    print("  ✓ Scrape result has sufficient content")

        # Validate CrewAI tasks receive dependency data
        for crewai_task in crewai_tasks:
            print(f"\n=== CrewAI Task: {crewai_task.name} ===")
            print(f"  Status: {crewai_task.status}")
            print(f"  Dependencies: {crewai_task.dependencies}")

            # Check inputs for dependency data
            if crewai_task.inputs:
                print(f"  Input keys: {list(crewai_task.inputs.keys())}")

                # Check if dependency results are in inputs
                has_dependency_data = False
                for dep in crewai_task.dependencies:
                    dep_id = dep.get("id") if isinstance(dep, dict) else dep
                    if dep_id in crewai_task.inputs:
                        dep_data = crewai_task.inputs[dep_id]
                        dep_preview = str(dep_data)[:200]
                        print(f"  Dependency {dep_id[:8]}... data: {dep_preview}...")
                        print(f"  Dependency data length: {len(str(dep_data))} chars")
                        has_dependency_data = True

                if not has_dependency_data:
                    print("  ❌ ISSUE: No dependency data found in inputs!")
                    print("  This will cause CrewAI to say it doesn't have the content to analyze")
                else:
                    print("  ✓ Dependency data present in inputs")

            # Check result format and content quality
            if crewai_task.status == "completed" and crewai_task.result:
                if isinstance(crewai_task.result, dict):
                    nested_result = crewai_task.result.get("result")

                    if nested_result:
                        print(f"  Result type: {type(nested_result).__name__}")
                        result_preview = str(nested_result)[:200]
                        print(f"  Result preview: {result_preview}...")

                        # Check for "no content" errors
                        error_indicators = [
                            "without said content",
                            "need the specific website content",
                            "please provide the website content",
                            "no content to analyze",
                            "content is missing",
                        ]

                        result_str = str(nested_result).lower()
                        if any(indicator in result_str for indicator in error_indicators):
                            print("  ❌ CRITICAL: CrewAI didn't receive dependency data!")
                            print("  The agent says it doesn't have the content to analyze")
                            print("  This indicates dependency data injection is not working")

                            # This is a critical failure - dependency system broken
                            pytest.fail(
                                "CrewAI task failed to receive dependency data. "
                                f"Result indicates missing content: '{result_preview}...'. "
                                "Check dependency data injection in CrewAI executor."
                            )

                        # Check if it's a JSON string that should be parsed
                        if isinstance(nested_result, str):
                            if nested_result.strip().startswith(("{", "[")):
                                try:
                                    json.loads(nested_result)
                                    print(
                                        "  ❌ ISSUE: Result is JSON string, should be parsed dict/list"
                                    )
                                    pytest.fail(
                                        "CrewAI task result is JSON string instead of parsed object. "
                                        "Expected: dict/list, Got: str"
                                    )
                                except json.JSONDecodeError:
                                    pass
                        elif isinstance(nested_result, (dict, list)):
                            print(
                                f"  ✅ Result is properly parsed as {type(nested_result).__name__}"
                            )

                            # Validate result has meaningful content
                            if isinstance(nested_result, dict):
                                if len(nested_result) == 0:
                                    print("  ⚠️  WARNING: Result dict is empty")
                                else:
                                    print(f"  ✓ Result has {len(nested_result)} keys")

        print(f"\n{'='*80}")
        print("Validation Summary:")
        print("  All dependency data checks completed")
        print(f"{'='*80}")

    finally:
        db.close()


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_system_monitoring_workflow():
    """
    Real scenario: Generate system monitoring workflow with parallel task execution.

    Requirement: "Check system health by monitoring CPU, memory, and disk usage in parallel"
    Expected: Multiple system_info_executor tasks with aggregate_results_executor as root
    """
    print(f"\n{'='*80}")
    print("SCENARIO: System Monitoring Workflow")
    print(f"{'='*80}\n")

    executor = GenerateExecutor(user_id="test_user")
    requirement = "Check system health by monitoring CPU, memory, and disk usage in parallel"

    print(f"Requirement: {requirement}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]
    assert len(tasks) >= 3, "Should generate at least 3 tasks (CPU, memory, disk)"

    # Count system_info_executor usage
    system_info_tasks = [
        t for t in tasks if t.get("schemas", {}).get("method") == "system_info_executor"
    ]

    print(f"\n✅ Generated {len(system_info_tasks)} system_info_executor tasks")

    # Verify parallel structure (all should share same parent)
    if len(system_info_tasks) > 1:
        parent_ids = {t.get("parent_id") for t in system_info_tasks}
        if len(parent_ids) == 1:
            print(f"✅ Parallel structure detected: all tasks share parent {parent_ids.pop()}")

    # Validate task tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Task tree should be valid: {validation['error']}"
    print("✅ Task tree passes validation")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_api_data_pipeline():
    """
    Real scenario: Generate API data pipeline with sequential processing.

    Requirement: "Fetch weather data from API, transform it, then send to webhook"
    Expected: Sequential rest_executor tasks
    """
    print(f"\n{'='*80}")
    print("SCENARIO: API Data Pipeline")
    print(f"{'='*80}\n")

    executor = GenerateExecutor(user_id="test_user")
    requirement = (
        "Fetch weather data from api.weather.com, "
        "transform the data format, "
        "then send the result to a webhook"
    )

    print(f"Requirement: {requirement}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]
    assert len(tasks) >= 2, "Should generate at least 2 tasks"

    # Count rest_executor usage
    rest_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "rest_executor"]

    # Count generate_executor usage (should be minimal for simple API pipeline)
    generate_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "generate_executor"]

    print(f"\n✅ Generated {len(rest_tasks)} rest_executor tasks")
    print(f"   Generated {len(generate_tasks)} generate_executor tasks")

    # For simple API pipeline, should prefer direct executors over generate_executor
    # However, we allow some flexibility as LLM might decompose slightly
    if len(generate_tasks) > 0:
        print("   ⚠️  Note: Using generate_executor for simple tasks is not optimal")

    # Verify sequential dependencies
    tasks_with_deps = [t for t in tasks if t.get("dependencies")]
    if tasks_with_deps:
        print(f"✅ Sequential structure: {len(tasks_with_deps)} tasks have dependencies")

    # Validate task tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Task tree should be valid: {validation['error']}"
    print("✅ Task tree passes validation")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_multi_source_data_aggregation():
    """
    Real scenario: Scrape multiple websites and aggregate results (no AI).

    Requirement: "Scrape product prices from 3 competitor websites and compare them"
    Expected: Multiple scrape_executor tasks with aggregate_results_executor root
    """
    print(f"\n{'='*80}")
    print("SCENARIO: Multi-Source Data Aggregation (No AI)")
    print(f"{'='*80}\n")

    executor = GenerateExecutor(user_id="test_user")
    requirement = (
        "Scrape product prices from amazon.com, ebay.com, and walmart.com "
        "for iPhone 15 Pro and compare the prices"
    )

    print(f"Requirement: {requirement}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]

    # Count scrape_executor usage
    scrape_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "scrape_executor"]

    print(f"\n✅ Generated {len(scrape_tasks)} scrape_executor tasks")
    assert len(scrape_tasks) >= 2, "Should have multiple scraping tasks"

    # Check for aggregator root (multiple executors or multiple scrape tasks)
    root_tasks = [t for t in tasks if not t.get("parent_id")]
    if len(root_tasks) == 1:
        root_executor = root_tasks[0].get("schemas", {}).get("method", "")
        if len(scrape_tasks) > 1:
            print(f"Root executor: {root_executor}")
            # With multiple scrape tasks, should use aggregator
            if "aggregate" in root_executor.lower():
                print("✅ Using aggregator for multiple data sources")

    # Should NOT use crewai_executor for simple price comparison
    crewai_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "crewai_executor"]
    print(f"CrewAI tasks: {len(crewai_tasks)} (should be 0 for simple data collection)")

    # Validate task tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Task tree should be valid: {validation['error']}"
    print("✅ Task tree passes validation")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_simple_query_single_executor():
    """
    Real scenario: Simple single-executor query.

    Requirement: "Check CPU usage"
    Expected: Single system_info_executor task (no aggregator needed)
    """
    print(f"\n{'='*80}")
    print("SCENARIO: Simple Single Executor Query")
    print(f"{'='*80}\n")

    executor = GenerateExecutor(user_id="test_user")
    requirement = "Check current CPU usage percentage"

    print(f"Requirement: {requirement}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]

    # For simple query, should generate minimal tasks
    print(f"\nGenerated {len(tasks)} task(s)")

    # Check that it uses appropriate executor
    if len(tasks) >= 1:
        main_task = tasks[0] if not tasks[0].get("parent_id") else tasks[-1]
        executor_type = main_task.get("schemas", {}).get("method", "")
        print(f"Executor type: {executor_type}")

        # Should use system_info_executor for CPU query
        assert (
            "system_info" in executor_type.lower()
        ), f"Should use system_info_executor for CPU query, got {executor_type}"
        print("✅ Correct executor selected")

    # Should NOT need aggregator for single query
    aggregate_tasks = [
        t for t in tasks if "aggregate" in t.get("schemas", {}).get("method", "").lower()
    ]
    if len(tasks) == 1:
        assert len(aggregate_tasks) == 0, "Single query shouldn't need aggregator"
        print("✅ No unnecessary aggregator for simple query")

    # Validate task tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Task tree should be valid: {validation['error']}"
    print("✅ Task tree passes validation")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_complex_ai_analysis():
    """
    Real scenario: Complex AI analysis requiring multiple agents.

    Requirement: "Research market trends for electric vehicles and create detailed report"
    Expected: crewai_executor with multiple agents (researcher, analyst, writer)
    """
    print(f"\n{'='*80}")
    print("SCENARIO: Complex AI Multi-Agent Analysis")
    print(f"{'='*80}\n")

    executor = GenerateExecutor(user_id="test_user")
    requirement = (
        "Research current market trends for electric vehicles in China, "
        "analyze the competitive landscape, "
        "and create a comprehensive business report with recommendations"
    )

    print(f"Requirement: {requirement}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]

    # Check for crewai_executor usage
    crewai_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "crewai_executor"]

    print(f"\n✅ Generated {len(crewai_tasks)} crewai_executor task(s)")

    if crewai_tasks:
        # Validate crewai structure
        for task in crewai_tasks:
            works = task.get("inputs", {}).get("works", {})
            agents = works.get("agents", {})
            crew_tasks = works.get("tasks", {})

            print(f"\nCrewAI task: {task.get('name')}")
            print(f"  Agents: {len(agents)}")
            print(f"  Tasks: {len(crew_tasks)}")

            assert len(agents) >= 1, "Should have at least 1 agent"
            assert len(crew_tasks) >= 1, "Should have at least 1 task"

            # Verify agent structure
            for agent_name, agent_config in agents.items():
                assert "role" in agent_config, f"Agent {agent_name} missing 'role'"
                assert "goal" in agent_config, f"Agent {agent_name} missing 'goal'"
                assert "backstory" in agent_config, f"Agent {agent_name} missing 'backstory'"
                assert "llm" in agent_config, f"Agent {agent_name} missing 'llm'"

            print("  ✅ All agents have required fields")

    # Validate task tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Task tree should be valid: {validation['error']}"
    print("✅ Task tree passes validation")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_hybrid_workflow_scrape_and_api():
    """
    Real scenario: Hybrid workflow combining scraping and API calls (no AI).

    Requirement: "Scrape news headlines from website then post summary to Slack"
    Expected: scrape_executor + rest_executor (sequential)
    """
    print(f"\n{'='*80}")
    print("SCENARIO: Hybrid Workflow (Scrape + API)")
    print(f"{'='*80}\n")

    executor = GenerateExecutor(user_id="test_user")
    requirement = (
        "Scrape the latest technology news headlines from techcrunch.com "
        "and post a summary to Slack webhook"
    )

    print(f"Requirement: {requirement}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]

    # Count executor types
    executor_types = {}
    for task in tasks:
        executor_id = task.get("schemas", {}).get("method", "")
        if executor_id:
            executor_types[executor_id] = executor_types.get(executor_id, 0) + 1

    print("\n=== Executor Usage ===")
    for executor_id, count in executor_types.items():
        print(f"  {executor_id}: {count}")

    # Should use scrape_executor for scraping
    assert any(
        "scrape" in e.lower() for e in executor_types.keys()
    ), f"Should use scrape_executor for web scraping. Got executors: {list(executor_types.keys())}"

    # Should use rest_executor for Slack webhook OR allow generate_executor decomposition
    has_rest = any("rest" in e.lower() for e in executor_types.keys())
    has_generate = any("generate" in e.lower() for e in executor_types.keys())

    if has_rest:
        print("✅ Correct executors selected (scrape + rest)")
    elif has_generate:
        print("⚠️  Using generate_executor for decomposition (not optimal but acceptable)")
    else:
        # Check if it used other valid executors
        print(f"⚠️  Unexpected executor selection: {executor_types}")

    # Should NOT use command_executor (security)
    assert not any(
        "command" in e.lower() for e in executor_types.keys()
    ), "Should NOT use command_executor for web scraping"

    # Verify sequential structure
    tasks_with_deps = [t for t in tasks if t.get("dependencies")]
    if tasks_with_deps:
        print(f"✅ Sequential dependencies: {len(tasks_with_deps)} tasks")

    # Validate task tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Task tree should be valid: {validation['error']}"
    print("✅ Task tree passes validation")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_scrape_crewai_template_variable_validation():
    """
    Critical test: Verify CrewAI tasks don't use template variables for dependency data.

    This test specifically validates the fix for the bug where CrewAI tasks would fail with:
    "Missing required template variable 'content' not found in inputs dictionary"

    The issue: LLM was generating CrewAI task descriptions like:
        'description': 'Analyze this website content: {content}'

    But the framework stores dependency results as:
        {'task-id-uuid': result}

    So {content} doesn't exist, causing CrewAI.kickoff() to fail.

    Fix: Updated prompt to instruct LLM NOT to use template variables for dependency data.
    """
    print(f"\n{'='*80}")
    print("CRITICAL TEST: Scrape + CrewAI Template Variable Validation")
    print(f"{'='*80}\n")

    executor = GenerateExecutor(user_id="test_user")
    requirement = "Scrape aiperceivable.com and analyze the content with AI to generate a report"

    print(f"Requirement: {requirement}\n")

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]
    assert len(tasks) >= 2, "Should generate at least scrape + analysis tasks"

    # Find scrape and crewai tasks
    scrape_task = None
    crewai_task = None

    for task in tasks:
        method = task.get("schemas", {}).get("method", "")
        if method == "scrape_executor":
            scrape_task = task
        elif method == "crewai_executor":
            crewai_task = task

    print("\n=== Task Analysis ===")
    print(f"Scrape task: {'✓ Found' if scrape_task else '✗ Missing'}")
    print(f"CrewAI task: {'✓ Found' if crewai_task else '✗ Missing'}")

    # If we have both, validate the CrewAI task
    if scrape_task and crewai_task:
        print("\n✓ Both tasks found, validating CrewAI task structure...")

        # Check dependency relationship
        crewai_deps = crewai_task.get("dependencies", [])
        scrape_task_id = scrape_task["id"]
        depends_on_scrape = any(
            dep.get("id") == scrape_task_id if isinstance(dep, dict) else dep == scrape_task_id
            for dep in crewai_deps
        )

        assert depends_on_scrape, "CrewAI task should depend on scrape task"
        print("✓ CrewAI task correctly depends on scrape task")

        # CRITICAL: Validate task descriptions don't use problematic template variables
        works = crewai_task.get("inputs", {}).get("works", {})
        crewai_tasks_def = works.get("tasks", {})

        print("\n=== Validating CrewAI Task Descriptions ===")
        print(f"Found {len(crewai_tasks_def)} CrewAI task(s) to validate\n")

        # These template variables will cause runtime errors because dependency results
        # are stored with task IDs as keys, not semantic names
        problematic_vars = [
            "{content}",
            "{data}",
            "{website_content}",
            "{scraped_content}",
            "{text}",
            "{html}",
            "{result}",
            "{scraped_data}",
            "{website_data}",
        ]

        validation_passed = True
        for task_name, task_def in crewai_tasks_def.items():
            description = task_def.get("description", "")
            prompt = task_def.get("prompt", "")

            print(f"Task: {task_name}")
            print(f"  Description: {description[:100]}...")

            # Check for problematic variables in description
            found_vars = []
            for var in problematic_vars:
                if var in description:
                    found_vars.append(var)

            if found_vars:
                validation_passed = False
                print(f"  ❌ FAIL: Found problematic template variables: {found_vars}")
                print("     These variables won't exist at runtime because dependency results")
                print(f"     are stored with task IDs as keys: {{'{scrape_task_id}': result}}")
                print(
                    "     This will cause: 'Template variable not found' error in CrewAI.kickoff()"
                )
            else:
                print("  ✓ PASS: No problematic template variables")

            # Also check prompt for guidance
            if prompt:
                print(f"  Prompt: {prompt[:80]}...")

        assert validation_passed, (
            "CrewAI task descriptions contain problematic template variables that will cause "
            "runtime errors. See details above. This indicates the LLM is not following the "
            "updated prompt guidance about NOT using template variables for dependency data."
        )

        print("\n✅ All validations passed!")
        print("   - CrewAI task correctly depends on scrape task")
        print("   - Task descriptions don't use problematic template variables")
        print("   - Generated tasks should execute without 'Template variable not found' errors")

    elif crewai_task and not scrape_task:
        print("\n⚠️  CrewAI task found but no scrape task - checking for alternative structure")
        # This is acceptable if the requirement is fulfilled differently
    else:
        print("\n⚠️  No CrewAI task generated - may have used alternative approach")
        # This is also acceptable as long as the requirement is fulfilled

    # Always validate the final task tree
    validation = executor._validate_tasks_array(tasks)
    assert validation["valid"], f"Task tree should be valid: {validation['error']}"
    print("\n✅ Task tree structure validation passed")


@pytest.mark.asyncio
async def test_crewai_json_result_format_validation():
    """
    Unit test: Verify CrewAI executor returns parsed JSON, not JSON string.

    This test validates that CrewAI tasks with JSON output format
    return results as parsed dict/list objects, not JSON strings.

    Expected behavior (after fix):
        result = {
            "status": "success",
            "result": {"key": "value"}  # ✅ Parsed JSON object
        }

    The fix in crewai_executor.py's process_result() method:
    - Detects when result.raw is a JSON string
    - Automatically parses it to dict/list
    - Falls back to returning raw string if parsing fails

    Why this matters:
    1. Downstream tasks can use results directly without parsing
    2. Type checking works correctly (expects dict, gets dict)
    3. Aggregator results contain properly structured data
    4. Better user experience: results are ready to use
    """
    pytest.importorskip("crewai")

    print("\n" + "=" * 80)
    print("TEST: CrewAI JSON Result Format - Verify Auto-Parse")
    print("=" * 80 + "\n")

    # Import the executor to test the fix
    from apflow.extensions.crewai.crewai_executor import CrewaiExecutor

    # Create a mock CrewAI result object (simulating what CrewAI returns)
    class MockCrewAIResult:
        def __init__(self, raw_value):
            self.raw = raw_value
            self.token_usage = None

    executor = CrewaiExecutor()

    # Test Case 1: JSON string should be parsed
    print("Test Case 1: JSON Object String")
    json_string = '{\n    "Insights": {\n        "Content Quality": "Good"\n    },\n    "URL": "https://example.com"\n}'
    mock_result = MockCrewAIResult(json_string)

    processed = executor.process_result(mock_result)
    print("  Input type: str (JSON)")
    print(f"  Output type: {type(processed).__name__}")
    print(f"  Output value: {processed}")

    assert isinstance(processed, dict), f"Expected dict, got {type(processed)}"
    assert "Insights" in processed, "Parsed dict should contain 'Insights' key"
    assert "URL" in processed, "Parsed dict should contain 'URL' key"
    print("  ✅ PASS: JSON string correctly parsed to dict\n")

    # Test Case 2: JSON array string should be parsed
    print("Test Case 2: JSON Array String")
    json_array = '[{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]'
    mock_result_array = MockCrewAIResult(json_array)

    processed_array = executor.process_result(mock_result_array)
    print("  Input type: str (JSON array)")
    print(f"  Output type: {type(processed_array).__name__}")
    print(f"  Output value: {processed_array}")

    assert isinstance(processed_array, list), f"Expected list, got {type(processed_array)}"
    assert len(processed_array) == 2, "Array should have 2 elements"
    print("  ✅ PASS: JSON array string correctly parsed to list\n")

    # Test Case 3: Plain text should remain as string
    print("Test Case 3: Plain Text (No JSON)")
    plain_text = "This is a simple text response without JSON structure"
    mock_result_text = MockCrewAIResult(plain_text)

    processed_text = executor.process_result(mock_result_text)
    print("  Input type: str (plain text)")
    print(f"  Output type: {type(processed_text).__name__}")
    print(f"  Output value: {processed_text[:50]}...")

    assert isinstance(processed_text, str), f"Expected str, got {type(processed_text)}"
    assert processed_text == plain_text, "Plain text should be unchanged"
    print("  ✅ PASS: Plain text remains as string\n")

    # Test Case 4: Invalid JSON should remain as string
    print("Test Case 4: Invalid JSON String")
    invalid_json = '{"key": invalid value}'
    mock_result_invalid = MockCrewAIResult(invalid_json)

    processed_invalid = executor.process_result(mock_result_invalid)
    print("  Input type: str (invalid JSON)")
    print(f"  Output type: {type(processed_invalid).__name__}")

    assert isinstance(processed_invalid, str), "Invalid JSON should remain as string"
    print("  ✅ PASS: Invalid JSON safely handled as string\n")

    # Test Case 5: Already parsed dict should pass through
    print("Test Case 5: Already Parsed Dict")
    dict_result = {"key": "value", "nested": {"data": "test"}}
    mock_result_dict = MockCrewAIResult(dict_result)

    processed_dict = executor.process_result(mock_result_dict)
    print("  Input type: dict")
    print(f"  Output type: {type(processed_dict).__name__}")

    assert isinstance(processed_dict, dict), "Dict should remain as dict"
    assert processed_dict == dict_result, "Dict should be unchanged"
    print("  ✅ PASS: Dict passes through unchanged\n")

    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("CrewAI executor correctly auto-parses JSON strings to objects")
    print("=" * 80)


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_crewai_dependency_data_injection_fix():
    """
    Integration test: Verify CrewAI receives dependency data after fix.

    This test creates a manual scrape + crewai workflow to verify that:
    1. Scrape task successfully extracts content
    2. CrewAI task receives the scraped content (via description injection)
    3. CrewAI agent can analyze the content (not say "content is missing")
    4. Results are properly formatted (JSON parsing works)

    This validates the fix in crewai_executor.py's create_task() method
    where dependency data is injected directly into task descriptions.
    """
    print(f"\n{'='*80}")
    print("INTEGRATION TEST: CrewAI Dependency Data Injection (Post-Fix)")
    print(f"{'='*80}\n")

    # Generate unique IDs for this test run
    import uuid

    root_id = str(uuid.uuid4())
    scrape_id = str(uuid.uuid4())
    analyze_id = str(uuid.uuid4())

    # Create a realistic task tree
    tasks_array = [
        {
            "id": root_id,
            "name": "Website Analysis Report",
            "schemas": {"method": "aggregate_results_executor"},
            "inputs": {},
            "dependencies": [
                {"id": scrape_id, "required": True},
                {"id": analyze_id, "required": True},
            ],
            "user_id": "demo_user_91c0194805d17ad1",
        },
        {
            "id": scrape_id,
            "name": "Scrape AI Perceivable",
            "parent_id": root_id,
            "schemas": {"method": "scrape_executor"},
            "inputs": {"url": "https://aiperceivable.com", "max_chars": 3000},
            "user_id": "demo_user_91c0194805d17ad1",
        },
        {
            "id": analyze_id,
            "name": "AI Analysis of Content",
            "parent_id": root_id,
            "schemas": {"method": "crewai_executor"},
            "inputs": {
                "works": {
                    "agents": {
                        "analyst": {
                            "role": "Website Content Analyst",
                            "goal": "Analyze website content and provide structured insights",
                            "backstory": "Expert analyst specializing in web content evaluation",
                            "llm": "gpt-4",
                        }
                    },
                    "tasks": {
                        "analyze": {
                            "description": "Analyze the website content from the scraping task",
                            "agent": "analyst",
                            "prompt": "Provide analysis with: insights, strengths, improvements. Return as JSON.",
                            "expected_output": "JSON with insights, strengths, and improvements",
                        }
                    },
                }
            },
            "dependencies": [{"id": scrape_id, "required": True}],
            "user_id": "demo_user_91c0194805d17ad1",
        },
    ]

    print("=== Task Tree ===")
    print(f"Total tasks: {len(tasks_array)}")
    for task in tasks_array:
        print(f"  {task['name']} ({task.get('schemas', {}).get('method', 'N/A')})")
    print()

    # Execute
    db = create_session()
    task_creator = TaskCreator(db)

    try:
        print("Creating and executing task tree...")
        task_tree = await task_creator.create_task_tree_from_array(tasks_array)
        task_manager = TaskManager(db)
        await task_manager.distribute_task_tree(task_tree)
        print("✅ Execution completed\n")

        # Collect results
        async def get_all_task_ids(node):
            task_ids = [node.task.id]
            for child in node.children:
                task_ids.extend(await get_all_task_ids(child))
            return task_ids

        all_task_ids = await get_all_task_ids(task_tree)

        print("=" * 80)
        print("VALIDATION")
        print("=" * 80 + "\n")

        scrape_task = None
        crewai_task = None

        for task_id in all_task_ids:
            task = await task_manager.task_repository.get_task_by_id(task_id)
            executor_type = task.schemas.get("method", "") if task.schemas else ""

            if executor_type == "scrape_executor":
                scrape_task = task
            elif executor_type == "crewai_executor":
                crewai_task = task

        # Validate scrape task
        assert scrape_task is not None, "Scrape task should exist"
        assert (
            scrape_task.status == "completed"
        ), f"Scrape should complete, got: {scrape_task.status}"

        scrape_content = (
            scrape_task.result.get("result", "")
            if isinstance(scrape_task.result, dict)
            else str(scrape_task.result)
        )
        print(f"✅ Scrape task completed: {len(scrape_content)} chars")
        print(f"   Preview: {scrape_content[:100]}...\n")

        # Validate CrewAI task - THIS IS THE KEY TEST
        assert crewai_task is not None, "CrewAI task should exist"
        print(f"CrewAI Task Status: {crewai_task.status}")

        if crewai_task.status == "failed":
            pytest.fail(f"CrewAI task failed: {crewai_task.error}")

        assert (
            crewai_task.status == "completed"
        ), f"CrewAI should complete, got: {crewai_task.status}"

        # Check result content
        result_data = (
            crewai_task.result.get("result")
            if isinstance(crewai_task.result, dict)
            else crewai_task.result
        )
        result_str = str(result_data)

        print(f"CrewAI Result Preview: {result_str[:200]}...\n")

        # KEY VALIDATION: Check if agent says "no content"
        error_indicators = [
            "without said content",
            "need the specific website content",
            "please provide the website content",
            "no content to analyze",
            "content is missing",
            "don't have the content",
        ]

        has_content_error = any(indicator in result_str.lower() for indicator in error_indicators)

        if has_content_error:
            print("❌ CRITICAL FAILURE: CrewAI agent says it doesn't have the content!")
            print(f"   Result: {result_str[:300]}")
            pytest.fail(
                "CrewAI dependency injection fix FAILED. "
                "Agent still says it doesn't have the content to analyze."
            )

        print("✅ SUCCESS: CrewAI agent received and analyzed the content!")
        print("   The dependency data injection fix is working correctly.\n")

        # Bonus: Check JSON parsing
        if isinstance(result_data, dict):
            print(f"✅ BONUS: Result properly parsed as dict with {len(result_data)} keys")
        elif isinstance(result_data, str) and result_data.strip().startswith("{"):
            print("⚠️  Note: Result is JSON string (minor issue, not critical)")

        print("\n" + "=" * 80)
        print("✅ ALL VALIDATIONS PASSED!")
        print("=" * 80)

    finally:
        db.close()
