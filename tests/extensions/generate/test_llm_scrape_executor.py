import pytest
import os
from apflow.extensions.generate.generate_executor import GenerateExecutor


@pytest.mark.asyncio
@pytest.mark.manual
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set in environment")
async def test_llm_generate_uses_scrape_executor():
    """
    Integration test: LLM should use scrape_executor for website analysis requirements.
    Requires a valid OPENAI_API_KEY in environment.

    Note: Uses multi_phase mode for better quality task generation.
    This is a MANUAL test that makes real API calls and should not run in CI.
    """
    executor = GenerateExecutor()
    requirement = "Please analyze aiperceivable.com and provide an evaluation."
    user_id = "test_user"

    result = await executor.execute(
        {
            "requirement": requirement,
            "user_id": user_id,
            "generation_mode": "multi_phase",  # Use multi-phase for better quality
        }
    )

    assert "tasks" in result, f"LLM did not return tasks: {result}"
    tasks = result["tasks"]

    # Print for debug
    print("Generated tasks:", tasks)

    # At least one task should use scrape_executor or be a valid website analysis task
    has_scrape = any(t.get("schemas", {}).get("method") == "scrape_executor" for t in tasks)

    has_website_task = any(
        "aiperceivable.com" in str(t.get("inputs", {})).lower() or "url" in t.get("inputs", {})
        for t in tasks
    )

    assert has_scrape or has_website_task, (
        f"No scrape_executor or website-related task found. " f"Tasks: {tasks}"
    )
