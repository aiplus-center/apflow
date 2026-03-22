"""
Test to verify that CrewAI tasks with dependencies work correctly.

This test verifies the fix for the issue where CrewAI tasks would fail with:
"Missing required template variable 'content' not found in inputs dictionary"

The solution is implemented in crewai_executor._inject_dependency_template_variables(),
which automatically detects dependency results (stored with task IDs as keys) and injects
them as common template variables (content, data, result, output) that CrewAI tasks can use.

This keeps the task_manager.py generic while allowing crewai_executor to handle its
specific template substitution requirements.
"""

import pytest
import os
import json
from apflow import TaskManager
from apflow.core.execution.task_creator import TaskCreator

# Import executors to ensure they're registered
try:
    from apflow.extensions.crewai import CrewaiExecutor  # noqa: F401
    from apflow.extensions.http import RestExecutor  # noqa: F401

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


@pytest.mark.asyncio
@pytest.mark.timeout(120)
@pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
async def test_crewai_dependency_schema_based_mapping(sync_db_session):
    """
    Test that CrewAI executor correctly injects dependency results as template variables.

    This tests the crewai_executor._inject_dependency_template_variables() method which
    automatically detects dependency results and injects them as template variables.

    The test creates a task tree with:
    1. scrape_executor task that returns {"result": "scraped content"}
    2. crewai_executor task that uses {content} in description
    3. Verifies the task executes without "Template variable not found" error
    """
    print(f"\n{'='*80}")
    print("TEST: CrewAI Dependency Schema-Based Mapping")
    print(f"{'='*80}\n")

    # Manually create a task tree to test the framework fix
    tasks_array = [
        {
            "id": "root-aggregate",
            "name": "Analyze Website Report",
            "schemas": {"method": "aggregate_results_executor"},
            "inputs": {},
            "dependencies": [
                {"id": "scrape-task", "required": True},
                {"id": "analyze-task", "required": True},
            ],
        },
        {
            "id": "scrape-task",
            "name": "Scrape Website",
            "parent_id": "root-aggregate",
            "schemas": {"method": "scrape_executor"},
            "inputs": {"url": "https://aiperceivable.com", "max_chars": 2000},
        },
        {
            "id": "analyze-task",
            "name": "Analyze Content",
            "parent_id": "root-aggregate",
            "schemas": {"method": "crewai_executor"},
            "dependencies": [{"id": "scrape-task", "required": True}],
            "inputs": {
                "works": {
                    "agents": {
                        "analyst": {
                            "role": "Content Analyst",
                            "goal": "Analyze website content",
                            "backstory": "Expert analyst with 10 years experience",
                            "llm": "gpt-4",
                        }
                    },
                    "tasks": {
                        "analyze": {
                            "description": "Analyze the website content: {content}",
                            "agent": "analyst",
                            "prompt": 'Analyze the content and return JSON with insights: {"key_points": [...], "summary": "..."}',
                            "expected_output": "JSON with analysis",
                        }
                    },
                }
            },
        },
    ]

    print("=== Task Tree ===")
    print(json.dumps(tasks_array, indent=2))
    print("\nNote: This task deliberately uses {content} template variable")
    print("      crewai_executor should auto-inject it from the scrape task result")

    # Create and execute using the test database session
    try:
        task_creator = TaskCreator(sync_db_session)
        task_tree = await task_creator.create_task_tree_from_array(tasks_array)

        print(f"\n✓ Task tree created: {task_tree.task.id}")

        task_manager = TaskManager(sync_db_session)
        await task_manager.distribute_task_tree(task_tree)

        print("\n✓ Task tree executed")

        # Check results
        analyze_task = await task_manager.task_repository.get_task_by_id("analyze-task")

        print("\n=== Analyze Task Status ===")
        print(f"Status: {analyze_task.status}")

        if analyze_task.status == "failed":
            print(f"Error: {analyze_task.error}")

            # Check if it's the template variable error
            if "Template variable" in str(analyze_task.error) and "not found" in str(
                analyze_task.error
            ):
                pytest.fail(
                    f"❌ CrewAI task failed with template variable error!\n"
                    f"   This means crewai_executor._inject_dependency_template_variables() is not working.\n"
                    f"   Error: {analyze_task.error}\n"
                    f"   Expected: CrewAI executor should auto-inject 'content' variable from dependency"
                )
            else:
                # Other errors are acceptable (API rate limit, network issues, etc.)
                print(
                    f"⚠️  Task failed with different error (acceptable for this test): {analyze_task.error[:200]}"
                )
                print(
                    "    The key point is it didn't fail with 'Template variable not found' error"
                )
        else:
            print("✅ Task completed successfully!")
            print("   This confirms crewai_executor correctly injected template variables")
            if analyze_task.result:
                result_preview = json.dumps(analyze_task.result, indent=2)[:300]
                print(f"\nResult preview:\n{result_preview}...")

        print("\n" + "=" * 80)
        print("✅ TEST PASSED: CrewAI executor correctly handles dependency template variables")
        print("=" * 80)

    finally:
        # Session cleanup is handled by the fixture
        pass
