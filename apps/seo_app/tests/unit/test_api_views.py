import pytest
import uuid
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.seo_app.models import AnalysisRecord, OptimizationRecord
from apps.seo_app.tests.unit.test_models import (
    AnalysisRecordFactory,
    OptimizationRecordFactory,
)


@pytest.mark.django_db
class TestAPIEndpoints:
    """Simple API endpoint tests focusing on status codes and basic validation."""

    def setup_method(self):
        """Setup test client."""
        self.client = APIClient()

    @pytest.mark.parametrize(
        "endpoint_name,expected_status",
        [
            ("analysis-list-create", status.HTTP_200_OK),
            ("optimize-list-create", status.HTTP_200_OK),
        ],
    )
    def test_list_endpoints_return_200(self, endpoint_name, expected_status):
        """Test that list endpoints return 200 OK."""
        url = reverse(endpoint_name)
        response = self.client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "endpoint_name,record_factory",
        [
            ("analysis-retrieve", AnalysisRecordFactory),
            ("optimize-retrieve", OptimizationRecordFactory),
        ],
    )
    def test_retrieve_existing_record_returns_200(self, endpoint_name, record_factory):
        """Test that retrieve endpoints return 200 for existing records."""
        record = record_factory()
        url = reverse(endpoint_name, kwargs={"id": record.id})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(record.id)

    @pytest.mark.parametrize(
        "endpoint_name,valid_payload,task_path",
        [
            (
                "analysis-list-create",
                {
                    "content": "Test content for anything to work",
                    "target_keyword": "test",
                },
                "apps.seo_app.api.views.analysis_views.analyze_content_task.delay",
            ),
            (
                "optimize-list-create",
                {
                    "content": "Test content for anything to work",
                    "target_keyword": "test",
                    "target_length": 500,
                    "tone": "professional",
                },
                "apps.seo_app.api.views.optimization_views.optimize_content_task.delay",
            ),
        ],
    )
    def test_create_with_valid_payload_returns_201(
        self, endpoint_name, valid_payload, task_path
    ):
        """Test that create endpoints return 201 with valid payload."""
        with patch(task_path) as mock_task:
            url = reverse(endpoint_name)
            response = self.client.post(url, valid_payload, format="json")

            assert response.status_code == status.HTTP_201_CREATED
            assert "id" in response.data
            assert "status" in response.data
            assert "created_at" in response.data
            mock_task.assert_called_once()

    @pytest.mark.parametrize(
        "endpoint_name,invalid_payloads",
        [
            (
                "analysis-list-create",
                [
                    {},  # Empty payload
                    {"content": "test"},  # Missing target_keyword
                    {"target_keyword": "test"},  # Missing content/url
                    {
                        "content": "test",
                        "url": "https://example.com",
                        "target_keyword": "test",
                    },  # Both content and url
                ],
            ),
            (
                "optimize-list-create",
                [
                    {},  # Empty payload
                    {"content": "test"},  # Missing required fields
                    {
                        "content": "test",
                        "target_keyword": "test",
                    },  # Missing target_length and tone
                    {
                        "content": "",
                        "target_keyword": "test",
                        "target_length": 500,
                        "tone": "professional",
                    },  # Empty content
                    {
                        "content": "test",
                        "target_keyword": "test",
                        "target_length": 25,
                        "tone": "professional",
                    },  # Invalid length
                    {
                        "content": "test",
                        "target_keyword": "test",
                        "target_length": 500,
                        "tone": "invalid",
                    },  # Invalid tone
                ],
            ),
        ],
    )
    def test_create_with_invalid_payload_returns_400(
        self, endpoint_name, invalid_payloads
    ):
        """Test that create endpoints return 400 with invalid payloads."""
        url = reverse(endpoint_name)

        for payload in invalid_payloads:
            response = self.client.post(url, payload, format="json")
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "endpoint_name,valid_payload,task_path",
        [
            (
                "analysis-list-create",
                {"url": "https://example.com", "target_keyword": "test"},
                "apps.seo_app.api.views.analysis_views.analyze_content_task.delay",
            ),
            (
                "analysis-list-create",
                {"content": "Test content", "target_keyword": "test"},
                "apps.seo_app.api.views.analysis_views.analyze_content_task.delay",
            ),
        ],
    )
    def test_analysis_create_url_and_content_variants(
        self, endpoint_name, valid_payload, task_path
    ):
        """Test analysis creation with both URL and content variants."""
        with patch(task_path) as mock_task:
            url = reverse(endpoint_name)
            response = self.client.post(url, valid_payload, format="json")

            assert response.status_code == status.HTTP_201_CREATED
            mock_task.assert_called_once()

    @pytest.mark.parametrize(
        "tone",
        [
            "professional",
            "casual",
            "persuasive",
            "informative",
            "authoritative",
            "friendly",
            "formal",
            "conversational",
        ],
    )
    def test_optimization_create_valid_tones(self, tone):
        """Test optimization creation with all valid tone options."""
        with patch(
            "apps.seo_app.api.views.optimization_views.optimize_content_task.delay"
        ):
            url = reverse("optimize-list-create")
            payload = {
                "content": "Test content for anything to work",
                "target_keyword": "test keyword",
                "target_length": 500,
                "tone": tone,
            }
            response = self.client.post(url, payload, format="json")

            assert response.status_code == status.HTTP_201_CREATED

    def test_pagination_structure(self):
        """Test that list endpoints return proper pagination structure."""
        for i in range(3):
            AnalysisRecordFactory(target_keyword=f"test {i}")

        url = reverse("analysis-list-create")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "results" in response.data
        assert isinstance(response.data["results"], list)
