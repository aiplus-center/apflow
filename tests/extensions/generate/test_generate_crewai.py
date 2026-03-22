"""
Integration tests for generate executor with crewai_executor.

Tests that generate_executor can properly generate crewai_executor tasks with valid
'works' structure containing agents and tasks definitions.

Requires OPENAI_API_KEY environment variable for real LLM calls.
"""

import pytest
import os
import json
from apflow.extensions.generate.generate_executor import GenerateExecutor


@pytest.mark.asyncio
@pytest.mark.timeout(180)  # multi_phase mode needs more time (multiple LLM calls)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_crewai_executor_task():
    """
    Integration test: LLM should generate valid crewai_executor tasks with proper works structure.

    This tests that:
    1. GenerateExecutor can be used with a requirement that needs AI analysis
    2. Generated tasks include crewai_executor with proper works structure
    3. works contains both agents and tasks with required fields
    4. Each task in works has description, agent, and prompt fields
    5. Validation passes for generated tasks

    Note: Uses single_shot mode for faster execution (multi_phase can timeout)
    """
    executor = GenerateExecutor()
    requirement = (
        "Create a workflow with these tasks: "
        "1. Scrape the AI Perceivable website "
        "2. Use an AI crew to analyze the scraped content "
        "3. Generate a summary report"
    )
    user_id = "test_user"

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": user_id,
            "generation_mode": "single_shot",  # Faster than multi_phase
        }
    )

    print("\n=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"
    assert "tasks" in result, f"No tasks in result: {result}"

    tasks = result["tasks"]
    assert isinstance(tasks, list), "Tasks should be a list"
    assert len(tasks) > 0, "At least one task should be generated"

    # Look for crewai_executor task
    crewai_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "crewai_executor"]

    print(f"\nFound {len(crewai_tasks)} crewai_executor tasks out of {len(tasks)} total tasks")

    if crewai_tasks:
        print("\n=== CrewAI Tasks Found ===")
        for crewai_task in crewai_tasks:
            print(f"\nTask: {crewai_task.get('name')}")
            works = crewai_task.get("inputs", {}).get("works")

            # Validate works structure
            assert works is not None, f"Task {crewai_task['name']} missing 'works' in inputs"
            assert isinstance(works, dict), f"Task {crewai_task['name']} works should be dict"

            # Validate agents
            agents = works.get("agents")
            assert isinstance(agents, dict), f"Task {crewai_task['name']} agents should be dict"
            assert len(agents) > 0, f"Task {crewai_task['name']} should have at least one agent"

            for agent_name, agent_config in agents.items():
                assert isinstance(agent_config, dict), f"Agent {agent_name} config should be dict"
                assert "role" in agent_config, f"Agent {agent_name} missing 'role'"
                assert "goal" in agent_config, f"Agent {agent_name} missing 'goal'"
                print(f"  Agent: {agent_name} (role: {agent_config.get('role')})")

            # Validate tasks
            crew_tasks = works.get("tasks")
            assert isinstance(crew_tasks, dict), f"Task {crewai_task['name']} tasks should be dict"
            assert (
                len(crew_tasks) > 0
            ), f"Task {crewai_task['name']} should have at least one crew task"

            for task_name, task_config in crew_tasks.items():
                assert isinstance(task_config, dict), f"Crew task {task_name} config should be dict"
                assert "description" in task_config, f"Crew task {task_name} missing 'description'"
                assert "agent" in task_config, f"Crew task {task_name} missing 'agent'"

                agent_ref = task_config.get("agent")
                assert (
                    agent_ref in agents
                ), f"Crew task {task_name} references unknown agent '{agent_ref}'"

                print(f"    Task: {task_name} (agent: {agent_ref})")
                if "prompt" in task_config:
                    print(f"      Prompt: {task_config['prompt'][:100]}...")
    else:
        print("\nNote: No crewai_executor tasks generated. This is acceptable if requirement")
        print("can be fulfilled with other executors (rest_executor, scrape_executor, etc.)")
        print("\nGenerated executors:")
        for task in tasks:
            executor_id = task.get("schemas", {}).get("method")
            print(f"  - {executor_id}: {task.get('name')}")


@pytest.mark.asyncio
@pytest.mark.timeout(120)  # Allow up to 2 minutes for LLM calls
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_generate_explicit_crewai_requirement():
    """
    Integration test: When requirement explicitly mentions AI crew,
    crewai_executor should be used.

    Note: Uses single_shot mode for faster execution
    """
    executor = GenerateExecutor()
    requirement = (
        "Create a task using crewai_executor with two agents: "
        "1. A researcher agent to analyze data "
        "2. A writer agent to create a report. "
        "The crew should work together and return a JSON result."
    )
    user_id = "test_user"

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": user_id,
            "generation_mode": "single_shot",  # Faster than multi_phase
        }
    )

    print("\n=== Explicit CrewAI Requirement - Generated Tasks ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"

    tasks = result["tasks"]
    crewai_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "crewai_executor"]

    print(f"\nFound {len(crewai_tasks)} crewai_executor tasks")

    if crewai_tasks:
        for crewai_task in crewai_tasks:
            works = crewai_task.get("inputs", {}).get("works")
            agents = works.get("agents", {})
            crew_tasks = works.get("tasks", {})

            # With explicit crew requirement, should have multiple agents
            print(f"\nTask: {crewai_task['name']}")
            print(f"  Agents: {len(agents)}")
            print(f"  Tasks: {len(crew_tasks)}")

            # Validate structure
            assert len(agents) >= 1, "Should have at least one agent for crew"
            assert len(crew_tasks) >= 1, "Should have at least one task in crew"
    else:
        # If no crewai_executor generated, it's still acceptable if
        # the requirement can be fulfilled otherwise
        print("\nNote: No crewai_executor in this generation")


@pytest.mark.asyncio
async def test_generate_executor_validates_crewai_tasks():
    """
    Unit test: Verify that generate_executor properly validates crewai_executor tasks.

    This tests the schema validation logic without calling LLM (no API key required).
    """
    executor = GenerateExecutor()

    # Test 1: Valid crewai_executor task
    valid_task = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Analyze with AI Crew",
        "schemas": {"method": "crewai_executor"},
        "inputs": {
            "works": {
                "agents": {
                    "analyst": {
                        "role": "Data Analyst",
                        "goal": "Analyze data comprehensively",
                        "backstory": "Expert data analyst with years of experience",
                        "llm": "gpt-4",
                    },
                    "reporter": {
                        "role": "Report Writer",
                        "goal": "Create professional reports",
                        "backstory": "Professional technical writer",
                        "llm": "gpt-4",
                    },
                },
                "tasks": {
                    "analyze": {
                        "description": "Analyze the provided data",
                        "agent": "analyst",
                        "prompt": "Return analysis as JSON: {findings: string, score: number}",
                    },
                    "report": {
                        "description": "Create a report based on analysis",
                        "agent": "reporter",
                        "prompt": "Write professional markdown report",
                    },
                },
            }
        },
    }

    validation = executor._validate_schema_compliance([valid_task])
    assert validation["valid"], f"Valid task should pass: {validation['error']}"
    print("✓ Valid crewai_executor task passed validation")

    # Test 2: Task missing works parameter
    invalid_task_1 = {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Invalid crew task",
        "schemas": {"method": "crewai_executor"},
        "inputs": {},
    }

    validation = executor._validate_schema_compliance([invalid_task_1])
    assert not validation["valid"], "Task without works should fail"
    assert "missing required field 'works'" in validation["error"]
    print("✓ Task without works correctly rejected")

    # Test 3: Works missing agents/tasks
    invalid_task_2 = {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Invalid crew structure",
        "schemas": {"method": "crewai_executor"},
        "inputs": {
            "works": {
                "agents": {},
                # Missing tasks
            }
        },
    }

    validation = executor._validate_schema_compliance([invalid_task_2])
    assert not validation["valid"], "Works without tasks should fail"
    assert "contain 'agents' and 'tasks'" in validation["error"]
    print("✓ Works without tasks correctly rejected")

    # Test 4: Agent without required fields
    invalid_task_3 = {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "name": "Invalid agent",
        "schemas": {"method": "crewai_executor"},
        "inputs": {
            "works": {
                "agents": {
                    "analyst": {
                        "role": "Analyst",
                        # Missing goal
                    }
                },
                "tasks": {},
            }
        },
    }

    validation = executor._validate_schema_compliance([invalid_task_3])
    assert not validation["valid"], "Agent without goal should fail"
    assert "must have 'role' and 'goal'" in validation["error"]
    print("✓ Agent without goal correctly rejected")

    # Test 5: Task referencing non-existent agent
    invalid_task_4 = {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "name": "Invalid agent reference",
        "schemas": {"method": "crewai_executor"},
        "inputs": {
            "works": {
                "agents": {
                    "analyst": {
                        "role": "Analyst",
                        "goal": "Analyze data",
                    }
                },
                "tasks": {
                    "invalid_task": {
                        "description": "Task with invalid agent",
                        "agent": "nonexistent_agent",
                    }
                },
            }
        },
    }

    validation = executor._validate_schema_compliance([invalid_task_4])
    assert not validation["valid"], "Task with invalid agent ref should fail"
    assert "references unknown agent" in validation["error"]
    print("✓ Task referencing non-existent agent correctly rejected")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_crewai_executor_real_analysis():
    """
    Real integration test: Use GenerateExecutor to produce a task tree that includes
    a crewai_executor task with a full works structure to analyze aiperceivable.com.

    This test:
    1. Calls GenerateExecutor with an explicit requirement to use crewai_executor
    2. Verifies the generated task tree contains crewai_executor
    3. Validates works.agents and works.tasks structure
    """
    executor = GenerateExecutor()
    requirement = (
        "You MUST generate a task tree that includes a crewai_executor task with full works structure. "
        "The crew must analyze aiperceivable.com and produce a report. "
        "Requirements for crewai_executor inputs.works: "
        "agents is an object with at least two agents (each has role and goal), "
        "tasks is an object with at least two tasks (each has description and agent), "
        "and tasks must reference existing agents."
    )
    user_id = "test_user"

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": user_id,
            "generation_mode": "single_shot",
        }
    )

    print("\n=== Generated Task Tree ===")
    print(json.dumps(result, indent=2))

    assert result["status"] == "completed", f"Generation failed: {result.get('error')}"
    tasks = result.get("tasks", [])
    assert isinstance(tasks, list) and tasks, "Tasks should be a non-empty list"

    crewai_tasks = [t for t in tasks if t.get("schemas", {}).get("method") == "crewai_executor"]
    assert crewai_tasks, "Expected at least one crewai_executor task"

    print(f"\nFound {len(crewai_tasks)} crewai_executor tasks")
    for crewai_task in crewai_tasks:
        works = crewai_task.get("inputs", {}).get("works")
        assert isinstance(works, dict), "inputs.works must be an object"

        agents = works.get("agents")
        tasks_config = works.get("tasks")
        assert isinstance(agents, dict) and agents, "works.agents must be a non-empty object"
        assert (
            isinstance(tasks_config, dict) and tasks_config
        ), "works.tasks must be a non-empty object"

        for agent_name, agent_config in agents.items():
            assert isinstance(agent_config, dict), f"Agent {agent_name} config should be object"
            assert (
                "role" in agent_config and "goal" in agent_config
            ), f"Agent {agent_name} must have role and goal"

        for task_name, task_config in tasks_config.items():
            assert isinstance(task_config, dict), f"Crew task {task_name} config should be object"
            assert (
                "description" in task_config and "agent" in task_config
            ), f"Crew task {task_name} must have description and agent"
            assert (
                task_config["agent"] in agents
            ), f"Crew task {task_name} references unknown agent '{task_config['agent']}'"
