import pytest
from fastapi.testclient import TestClient
from app.services.assessment_service import AssessmentService


def get_test_client():
    """Create a test client with proper service initialization"""
    from app.main import app
    # Manually initialize the assessment service for testing
    app.state.assessment_service = AssessmentService()
    # Also set the global variable that main.py checks
    import app.main as main_module
    main_module.assessment_service = AssessmentService()
    return TestClient(app)


client = get_test_client()


@pytest.mark.external_deps
class TestAssessmentE2E:
    """End-to-end tests for the assessment system"""

    @pytest.mark.external_deps
    def test_complete_assessment_workflow(self):
        """Test complete assessment workflow from creation to retrieval"""

        # Step 1: Create an assessment
        assessment_request = {
            "user_id": "e2e_test_user",
            "interaction_context": (
                "User designed a scalable e-commerce system with microservices "
                "architecture, load balancer, API gateway, user service, product "
                "service, order service, payment service, and Redis cache. They "
                "discussed database sharding, CDN for static content, and "
                "monitoring strategies."
            ),
            "whiteboard_feedback": {
                "components": [
                    "load_balancer",
                    "api_gateway",
                    "user_service",
                    "product_service",
                    "order_service",
                    "payment_service",
                    "redis_cache",
                    "database",
                ],
                "feedback": "Excellent component identification and architecture design",
            },
            "conversation_history": "Discussion about scaling challenges and trade-offs between consistency and availability",
            "assessment_type": "system_design",
        }

        response = client.post("/api/assessment/evaluate", json=assessment_request)
        assert response.status_code == 200

        assessment_data = response.json()
        assessment_id = assessment_data["assessment_id"]

        # Verify assessment structure
        assert assessment_data["user_id"] == "e2e_test_user"
        assert assessment_data["assessment_type"] == "system_design"
        assert (
            assessment_data["overall_score"] >= 1.0
            and assessment_data["overall_score"] <= 5.0
        )
        assert (
            assessment_data["confidence_score"] >= 1.0
            and assessment_data["confidence_score"] <= 5.0
        )

        # Verify 6-dimensional scores
        dimension_scores = assessment_data["dimension_scores"]
        expected_dimensions = [
            "requirements_analysis",
            "system_architecture",
            "technical_deep_dive",
            "scale_performance",
            "reliability_fault_tolerance",
            "communication_thought_process",
        ]

        for dimension in expected_dimensions:
            assert dimension in dimension_scores
            score_data = dimension_scores[dimension]
            assert "score" in score_data
            assert "feedback" in score_data
            assert "strengths" in score_data
            assert "areas_for_improvement" in score_data
            assert "confidence" in score_data
            assert 1.0 <= score_data["score"] <= 5.0
            assert 1.0 <= score_data["confidence"] <= 5.0

        # Step 2: Retrieve the assessment by ID
        get_response = client.get(f"/api/assessment/{assessment_id}")
        assert get_response.status_code == 200

        retrieved_assessment = get_response.json()
        assert retrieved_assessment["assessment_id"] == assessment_id
        assert retrieved_assessment["user_id"] == "e2e_test_user"

        # Step 3: Get assessment history
        history_response = client.get("/api/assessment/history/e2e_test_user")
        assert history_response.status_code == 200

        history_data = history_response.json()
        assert history_data["user_id"] == "e2e_test_user"
        assert history_data["total_count"] >= 1
        assert len(history_data["assessments"]) >= 1

        # Find our assessment in history
        found_assessment = None
        for assessment in history_data["assessments"]:
            if assessment["assessment_id"] == assessment_id:
                found_assessment = assessment
                break

        assert found_assessment is not None
        assert found_assessment["overall_score"] == assessment_data["overall_score"]

        # Step 4: Get assessment summary
        summary_response = client.get("/api/assessment/summary/e2e_test_user")
        assert summary_response.status_code == 200

        summary_data = summary_response.json()
        assert summary_data["user_id"] == "e2e_test_user"
        assert summary_data["total_assessments"] >= 1
        assert summary_data["average_overall_score"] > 0
        assert summary_data["strongest_dimension"] in expected_dimensions
        assert summary_data["weakest_dimension"] in expected_dimensions
        assert len(summary_data["top_recommendations"]) > 0

        # Step 5: Test pagination in history
        paginated_response = client.get(
            "/api/assessment/history/e2e_test_user?limit=1&offset=0"
        )
        assert paginated_response.status_code == 200

        paginated_data = paginated_response.json()
        assert paginated_data["total_count"] >= 1
        assert len(paginated_data["assessments"]) <= 1
        assert paginated_data["has_more"] == (paginated_data["total_count"] > 1)

    @pytest.mark.external_deps
    def test_assessment_error_handling(self):
        """Test error handling for invalid assessment requests"""

        # Test missing required fields
        invalid_request = {
            "user_id": "test_user"
            # Missing interaction_context
        }

        response = client.post("/api/assessment/evaluate", json=invalid_request)
        assert response.status_code == 422  # Validation error

        # Test empty interaction context
        empty_context_request = {"user_id": "test_user", "interaction_context": ""}

        response = client.post("/api/assessment/evaluate", json=empty_context_request)
        assert response.status_code == 422  # Validation error

        # Test very long interaction context
        long_context = "x" * 10001  # Exceeds 10000 character limit
        long_context_request = {
            "user_id": "test_user",
            "interaction_context": long_context,
        }

        response = client.post("/api/assessment/evaluate", json=long_context_request)
        assert response.status_code == 422  # Validation error

    @pytest.mark.external_deps
    def test_assessment_not_found(self):
        """Test handling of non-existent assessment"""

        # Test getting non-existent assessment
        response = client.get("/api/assessment/non-existent-id")
        assert response.status_code == 404
        assert "Assessment not found" in response.json()["detail"]

        # Test deleting non-existent assessment
        response = client.delete("/api/assessment/non-existent-id")
        assert response.status_code == 404
        assert "Assessment not found" in response.json()["detail"]

    @pytest.mark.external_deps
    def test_assessment_cleanup(self):
        """Test assessment cleanup functionality"""

        # Test cleanup endpoint
        response = client.post("/api/assessment/cleanup?max_age_days=90")
        assert response.status_code == 200
        assert "Cleanup completed" in response.json()["message"]

    @pytest.mark.external_deps
    def test_multiple_assessments_same_user(self):
        """Test multiple assessments for the same user"""

        user_id = "multi_assessment_user"

        # Create first assessment
        assessment1_request = {
            "user_id": user_id,
            "interaction_context": "User designed a simple web application with basic components",
            "assessment_type": "system_design",
        }

        response1 = client.post("/api/assessment/evaluate", json=assessment1_request)
        assert response1.status_code == 200
        assessment1_id = response1.json()["assessment_id"]

        # Create second assessment
        assessment2_request = {
            "user_id": user_id,
            "interaction_context": "User designed a complex distributed system with advanced patterns",
            "assessment_type": "system_design",
        }

        response2 = client.post("/api/assessment/evaluate", json=assessment2_request)
        assert response2.status_code == 200
        assessment2_id = response2.json()["assessment_id"]

        # Verify both assessments exist
        assert assessment1_id != assessment2_id

        # Get history and verify both assessments
        history_response = client.get(f"/api/assessment/history/{user_id}")
        assert history_response.status_code == 200

        history_data = history_response.json()
        assert history_data["total_count"] >= 2

        # Verify assessment IDs are in history
        assessment_ids = [a["assessment_id"] for a in history_data["assessments"]]
        assert assessment1_id in assessment_ids
        assert assessment2_id in assessment_ids

        # Get summary and verify data
        summary_response = client.get(f"/api/assessment/summary/{user_id}")
        assert summary_response.status_code == 200

        summary_data = summary_response.json()
        assert summary_data["total_assessments"] >= 2
        assert summary_data["average_overall_score"] > 0

        # Clean up test assessments
        client.delete(f"/api/assessment/{assessment1_id}")
        client.delete(f"/api/assessment/{assessment2_id}")

    @pytest.mark.external_deps
    def test_assessment_dimensions_validation(self):
        """Test that all 6 dimensions are properly scored and validated"""

        assessment_request = {
            "user_id": "dimension_test_user",
            "interaction_context": "User explained a comprehensive system design with detailed technical analysis",
            "assessment_type": "system_design",
        }

        response = client.post("/api/assessment/evaluate", json=assessment_request)
        assert response.status_code == 200

        assessment_data = response.json()
        dimension_scores = assessment_data["dimension_scores"]

        # Verify all 6 dimensions are present
        expected_dimensions = [
            "requirements_analysis",
            "system_architecture",
            "technical_deep_dive",
            "scale_performance",
            "reliability_fault_tolerance",
            "communication_thought_process",
        ]

        for dimension in expected_dimensions:
            assert dimension in dimension_scores

            score_data = dimension_scores[dimension]

            # Verify score structure
            assert "score" in score_data
            assert "feedback" in score_data
            assert "strengths" in score_data
            assert "areas_for_improvement" in score_data
            assert "confidence" in score_data

            # Verify score ranges
            assert 1.0 <= score_data["score"] <= 5.0
            assert 1.0 <= score_data["confidence"] <= 5.0

            # Verify feedback content
            assert len(score_data["feedback"]) > 0
            assert len(score_data["strengths"]) > 0
            assert len(score_data["areas_for_improvement"]) > 0

        # Verify overall scores
        assert 1.0 <= assessment_data["overall_score"] <= 5.0
        assert 1.0 <= assessment_data["confidence_score"] <= 5.0

        # Verify recommendations and next steps
        assert len(assessment_data["recommendations"]) > 0
        assert len(assessment_data["next_steps"]) > 0

        # Clean up
        assessment_id = assessment_data["assessment_id"]
        client.delete(f"/api/assessment/{assessment_id}")
