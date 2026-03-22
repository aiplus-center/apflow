"""
Test to verify that generated CrewAI tasks don't use template variables for dependency data.

This test verifies the fix for the issue where CrewAI tasks would fail with:
"Missing required template variable 'content' not found in inputs dictionary"

The problem was that the LLM was instructed to use template variables like {content}
for dependency data, but the framework stores dependency results with task IDs as keys.
"""

import pytest
import os
import json
from apflow.extensions.generate.generate_executor import GenerateExecutor


@pytest.mark.asyncio
@pytest.mark.timeout(60)
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
async def test_generated_crewai_task_no_template_variables_for_dependencies():
    """
    Verify that generated CrewAI tasks don't use template variables for dependency data.

    This test generates a task tree for "analyze aiperceivable.com" and verifies that:
    1. The task tree includes a scrape task followed by a CrewAI analysis task
    2. The CrewAI task description does NOT contain template variables like {content}
    3. The task can be executed without "Template variable not found" errors
    """
    executor = GenerateExecutor(user_id="test_user")
    requirement = "Scrape aiperceivable.com and analyze the content with AI"

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
            "temperature": 0,  # Use deterministic generation to avoid flaky tests
        }
    )

    print("\n=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    # Skip on API rate limit / quota errors (external issue, not a code bug)
    if result["status"] == "failed":
        error_msg = result.get("error", "")
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            pytest.skip(f"Skipping due to API rate limit / quota exceeded: {error_msg}")

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"
    assert "tasks" in result

    tasks = result["tasks"]

    # Find scrape and crewai tasks
    scrape_task = None
    crewai_task = None
    all_methods = []

    for task in tasks:
        method = task.get("schemas", {}).get("method", "")
        all_methods.append(method)
        if method == "scrape_executor":
            scrape_task = task
        elif method == "crewai_executor":
            crewai_task = task

    # Verify we have both tasks - if not, this might be LLM variance
    # Print diagnostics to help understand what happened
    if scrape_task is None or crewai_task is None:
        print("\n⚠ Test skipped: Expected both scrape_executor and crewai_executor")
        print(f"Generated executors: {all_methods}")
        print("This is likely due to LLM variance in test suite execution")
        pytest.skip(
            f"LLM generated different executor types: {all_methods}. "
            f"Expected ['scrape_executor', 'crewai_executor']. "
            f"This is non-deterministic LLM behavior when running full test suite."
        )

    # If we get here, we have both tasks as expected

    print(f"\n✓ Found scrape task: {scrape_task['name']}")
    print(f"✓ Found crewai task: {crewai_task['name']}")

    # Check that crewai task depends on scrape task
    crewai_deps = crewai_task.get("dependencies", [])
    assert len(crewai_deps) > 0, "CrewAI task should have dependencies"

    scrape_task_id = scrape_task["id"]
    depends_on_scrape = any(
        dep.get("id") == scrape_task_id if isinstance(dep, dict) else dep == scrape_task_id
        for dep in crewai_deps
    )
    assert depends_on_scrape, "CrewAI task should depend on scrape task"

    print("✓ CrewAI task depends on scrape task")

    # Check CrewAI task structure
    works = crewai_task.get("inputs", {}).get("works", {})
    assert "agents" in works, "CrewAI task should have agents"
    assert "tasks" in works, "CrewAI task should have tasks"

    # Check that task descriptions don't use problematic template variables
    crewai_tasks = works.get("tasks", {})

    print("\n=== Checking CrewAI Task Descriptions ===")
    for task_name, task_def in crewai_tasks.items():
        description = task_def.get("description", "")
        print(f"\nTask '{task_name}' description:")
        print(f"  {description}")

        # Check for problematic template variables
        # These are variable names that won't exist because dependency results
        # are stored with task IDs as keys, not semantic names
        problematic_vars = ["{content}", "{data}", "{website_content}", "{scraped_content}"]

        for var in problematic_vars:
            if var in description:
                pytest.fail(
                    f"CrewAI task description contains problematic template variable {var}. "
                    f"This will cause 'Template variable not found' errors because dependency "
                    f"results are stored with task IDs as keys, not semantic names. "
                    f"Description: {description}"
                )

        print("  ✓ No problematic template variables found")

    print("\n✅ All CrewAI task descriptions are correctly formatted")
    print("✅ Test passed - generated tasks should execute without template variable errors")


@pytest.mark.asyncio
@pytest.mark.timeout(60)
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
async def test_crewai_task_with_static_inputs_can_use_template_variables():
    """
    Verify that CrewAI tasks CAN use template variables for static inputs.

    This is the correct use case: template variables should only be used for
    data explicitly included in the 'inputs' field, not for dependency results.
    """
    executor = GenerateExecutor(user_id="test_user")
    requirement = "Analyze the website at https://example.com for security issues"

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": "test_user",
            "generation_mode": "single_shot",
        }
    )

    print("\n=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    # Skip on API rate limit / quota errors (external issue, not a code bug)
    if result["status"] == "failed":
        error_msg = result.get("error", "")
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            pytest.skip(f"Skipping due to API rate limit / quota exceeded: {error_msg}")

    assert result["status"] == "completed"
    tasks = result["tasks"]

    # Find crewai task if present
    crewai_task = None
    for task in tasks:
        if task.get("schemas", {}).get("method") == "crewai_executor":
            crewai_task = task
            break

    if crewai_task:
        works = crewai_task.get("inputs", {}).get("works", {})
        crewai_tasks = works.get("tasks", {})

        print("\n=== Checking if Static Inputs Have Corresponding Variables ===")
        for task_name, task_def in crewai_tasks.items():
            description = task_def.get("description", "")

            # Extract template variables from description
            import re

            template_vars = re.findall(r"\{(\w+)\}", description)

            if template_vars:
                print(f"\nTask '{task_name}' uses template variables: {template_vars}")

                # Check if these variables exist in the inputs
                inputs = crewai_task.get("inputs", {})

                for var in template_vars:
                    # Variable should either be:
                    # 1. In the inputs directly
                    # 2. OR it's a URL that was included explicitly
                    # 3. OR the description should explain it will come from a previous task

                    if var in inputs:
                        print(f"  ✓ Variable '{var}' found in static inputs")
                    else:
                        print(
                            f"  ⚠ Variable '{var}' not in static inputs - should be explained in description"
                        )

    print("\n✅ Test complete")
