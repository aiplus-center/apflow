"""
Tests for Multi-Phase CrewAI Task Generation

Tests the 4-phase generation flow with mocked CrewAI calls.
"""

import pytest
import json
from unittest.mock import Mock, patch

# Skip entire module if crewai is not installed
pytest.importorskip("crewai")

from apflow.extensions.generate.multi_phase_crew import MultiPhaseGenerationCrew  # noqa: E402


class TestMultiPhaseGenerationCrew:
    """Test suite for MultiPhaseGenerationCrew"""

    @pytest.fixture
    def crew(self):
        """Create a MultiPhaseGenerationCrew instance"""
        return MultiPhaseGenerationCrew(llm_provider="openai", model="gpt-4", api_key="test-key")

    @pytest.fixture
    def mock_crew_result(self):
        """Mock CrewAI Crew.kickoff() result"""

        def create_result(data):
            result = Mock()
            json_str = json.dumps(data)
            result.__str__ = Mock(return_value=json_str)
            result.raw = json_str
            return result

        return create_result

    @pytest.mark.asyncio
    async def test_phase1_analyze_requirement(self, crew, mock_crew_result):
        """Test Phase 1: Requirement analysis"""
        analysis_data = {
            "goal": "Analyze website and generate report",
            "steps": ["Scrape website content", "Analyze with LLM"],
            "executors_needed": ["scrape_executor", "llm_executor"],
            "needs_aggregator": True,
            "execution_pattern": "sequential",
        }

        with patch("crewai.Agent"), patch("crewai.Task"), patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff = Mock(return_value=mock_crew_result(analysis_data))
            mock_crew_class.return_value = mock_crew_instance

            result = await crew._phase1_analyze_requirement(
                requirement="Please analyze the aiperceivable.com website and provide a report.",
                executors_info="Available executors...",
                principles="Framework principles...",
            )

            assert result["success"] is True
            assert "analysis" in result
            analysis = result["analysis"]
            assert analysis["needs_aggregator"] is True
            assert "scrape_executor" in analysis["executors_needed"]
            assert "llm_executor" in analysis["executors_needed"]

    @pytest.mark.asyncio
    async def test_phase2_design_structure(self, crew, mock_crew_result):
        """Test Phase 2: Structure design"""
        structure_data = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Aggregate Results",
                "schemas": {"method": "aggregate_results_executor"},
                "parent_id": None,
                "dependencies": [],
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Scrape Website",
                "schemas": {"method": "scrape_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [],
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "name": "Analyze Content",
                "schemas": {"method": "llm_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [{"id": "550e8400-e29b-41d4-a716-446655440002", "required": True}],
            },
        ]

        analysis = {
            "needs_aggregator": True,
            "executors_needed": ["scrape_executor", "llm_executor"],
        }

        with patch("crewai.Agent"), patch("crewai.Task"), patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff = Mock(return_value=mock_crew_result(structure_data))
            mock_crew_class.return_value = mock_crew_instance

            result = await crew._phase2_design_structure(
                requirement="Please analyze the aiperceivable.com website and provide a report.",
                analysis=analysis,
                executors_info="Available executors...",
                principles="Framework principles...",
            )

            assert result["success"] is True
            assert "structure" in result
            structure = result["structure"]
            assert len(structure) == 3
            # Root should be aggregator
            assert structure[0]["schemas"]["method"] == "aggregate_results_executor"
            assert structure[0]["parent_id"] is None
            # Children should have parent_id
            assert structure[1]["parent_id"] == structure[0]["id"]
            assert structure[2]["parent_id"] == structure[0]["id"]

    @pytest.mark.asyncio
    async def test_phase3_generate_inputs(self, crew, mock_crew_result):
        """Test Phase 3: Input generation"""
        structure = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Aggregate Results",
                "schemas": {"method": "aggregate_results_executor"},
                "parent_id": None,
                "dependencies": [],
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Scrape Website",
                "schemas": {"method": "scrape_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [],
            },
        ]

        tasks_with_inputs = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Aggregate Results",
                "schemas": {"method": "aggregate_results_executor"},
                "parent_id": None,
                "dependencies": [],
                "inputs": {},
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Scrape Website",
                "schemas": {"method": "scrape_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [],
                "inputs": {"url": "https://aiperceivable.com"},
            },
        ]

        with patch("crewai.Agent"), patch("crewai.Task"), patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff = Mock(return_value=mock_crew_result(tasks_with_inputs))
            mock_crew_class.return_value = mock_crew_instance

            result = await crew._phase3_generate_inputs(
                requirement="Please analyze the aiperceivable.com website and provide a report.",
                structure=structure,
                executors_info="Available executors...",
            )

            assert result["success"] is True
            assert "tasks" in result
            tasks = result["tasks"]
            assert len(tasks) == 2
            # Check inputs are present
            assert "inputs" in tasks[0]
            assert "inputs" in tasks[1]
            assert tasks[1]["inputs"]["url"] == "https://aiperceivable.com"

    @pytest.mark.asyncio
    async def test_phase4_review_and_validate(self, crew, mock_crew_result):
        """Test Phase 4: Review and validation"""
        tasks_input = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Aggregate Results",
                "schemas": {"method": "aggregate_results_executor"},
                "inputs": {},
            }
        ]

        validated_tasks = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Aggregate Results",
                "schemas": {"method": "aggregate_results_executor"},
                "parent_id": None,
                "inputs": {},
            }
        ]

        with patch("crewai.Agent"), patch("crewai.Task"), patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff = Mock(return_value=mock_crew_result(validated_tasks))
            mock_crew_class.return_value = mock_crew_instance

            result = await crew._phase4_review_and_validate(
                tasks=tasks_input,
                requirement="Please analyze the aiperceivable.com website and provide a report.",
                principles="Framework principles...",
            )

            assert result["success"] is True
            assert "tasks" in result
            assert len(result["tasks"]) == 1

    @pytest.mark.asyncio
    async def test_full_generation_flow(self, crew, mock_crew_result):
        """Test complete 4-phase generation flow with user's original example"""
        # Phase 1 result
        analysis_data = {
            "goal": "Analyze aiperceivable.com website and generate report",
            "steps": ["Scrape website", "Analyze content"],
            "executors_needed": ["scrape_executor", "llm_executor"],
            "needs_aggregator": True,
            "execution_pattern": "sequential",
        }

        # Phase 2 result
        structure_data = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Aggregate Website Analysis Results",
                "schemas": {"method": "aggregate_results_executor"},
                "parent_id": None,
                "dependencies": [],
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Scrape Website Content",
                "schemas": {"method": "scrape_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [],
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "name": "Analyze Website Content",
                "schemas": {"method": "llm_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [{"id": "550e8400-e29b-41d4-a716-446655440002", "required": True}],
            },
        ]

        # Phase 3 result
        tasks_with_inputs = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Aggregate Website Analysis Results",
                "schemas": {"method": "aggregate_results_executor"},
                "parent_id": None,
                "dependencies": [
                    {"id": "550e8400-e29b-41d4-a716-446655440002", "required": True},
                    {"id": "550e8400-e29b-41d4-a716-446655440003", "required": True},
                ],
                "inputs": {},
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Scrape Website Content",
                "schemas": {"method": "scrape_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [],
                "inputs": {"url": "https://aiperceivable.com"},
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "name": "Analyze Website Content",
                "schemas": {"method": "llm_executor"},
                "parent_id": "550e8400-e29b-41d4-a716-446655440001",
                "dependencies": [{"id": "550e8400-e29b-41d4-a716-446655440002", "required": True}],
                "inputs": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Analyze the website content and generate a detailed report.",
                        }
                    ]
                },
            },
        ]

        # Phase 4 result (same as phase 3 - validation passed)
        validated_tasks = tasks_with_inputs

        with patch("crewai.Agent"), patch("crewai.Task"), patch("crewai.Crew") as mock_crew_class:
            # Mock all 4 phases
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff = Mock(
                side_effect=[
                    mock_crew_result(analysis_data),
                    mock_crew_result(structure_data),
                    mock_crew_result(tasks_with_inputs),
                    mock_crew_result(validated_tasks),
                ]
            )
            mock_crew_class.return_value = mock_crew_instance

            result = await crew.generate(
                requirement="Please analyze the aiperceivable.com website and provide a report.",
                user_id="test_user",
            )

            # Verify success
            assert result["success"] is True
            assert "tasks" in result
            tasks = result["tasks"]

            # Verify structure
            assert len(tasks) == 3

            # Verify root is aggregator
            root_task = tasks[0]
            assert root_task["schemas"]["method"] == "aggregate_results_executor"
            assert root_task["parent_id"] is None

            # Verify child tasks
            scrape_task = tasks[1]
            assert scrape_task["schemas"]["method"] == "scrape_executor"
            assert scrape_task["parent_id"] == root_task["id"]
            assert scrape_task["inputs"]["url"] == "https://aiperceivable.com"

            llm_task = tasks[2]
            assert llm_task["schemas"]["method"] == "llm_executor"
            assert llm_task["parent_id"] == root_task["id"]
            assert "messages" in llm_task["inputs"]

            # Verify user_id was set
            for task in tasks:
                assert task["user_id"] == "test_user"

    @pytest.mark.asyncio
    async def test_generation_handles_phase_failure(self, crew):
        """Test that generation handles phase failures gracefully"""
        with patch("crewai.Agent"), patch("crewai.Task"), patch("crewai.Crew") as mock_crew_class:
            mock_crew_instance = Mock()
            # Phase 1 fails
            mock_crew_instance.kickoff = Mock(side_effect=Exception("Phase 1 failed"))
            mock_crew_class.return_value = mock_crew_instance

            result = await crew.generate(requirement="Test requirement", user_id="test_user")

            assert result["success"] is False
            assert "error" in result
            assert "Phase 1" in result["error"] or "Generation failed" in result["error"]

    def test_extract_json_from_markdown(self, crew):
        """Test JSON extraction from markdown-wrapped text"""
        # Test with markdown code block
        text = '```json\n[{"id": "1"}]\n```'
        result = crew._extract_json(text)
        assert result == '[{"id": "1"}]'

        # Test with just brackets
        text = '[{"id": "1"}]'
        result = crew._extract_json(text)
        assert result == '[{"id": "1"}]'

        # Test with no JSON
        text = "no json here"
        result = crew._extract_json(text)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
