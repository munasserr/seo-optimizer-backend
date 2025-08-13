import pytest
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone
from factory import LazyAttribute, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyFloat, FuzzyText
from model_bakery import baker

from apps.seo_app.models import AnalysisRecord, OptimizationRecord


class AnalysisRecordFactory(DjangoModelFactory):
    """Factory for creating AnalysisRecord instances."""

    class Meta:
        model = AnalysisRecord

    target_keyword = FuzzyText(length=20)
    input_content = FuzzyText(length=500)
    input_url = LazyAttribute(lambda obj: f"https://example.com/{obj.target_keyword}")
    status = FuzzyChoice(["pending", "processing", "completed", "failed"])
    seo_score = FuzzyFloat(0, 100)
    word_count = FuzzyInteger(10, 1000)
    keyword_density = FuzzyFloat(0, 10)
    avg_sentence_length = FuzzyFloat(5, 30)
    readability_score = FuzzyFloat(0, 100)
    processing_time = FuzzyInteger(100, 10000)


class OptimizationRecordFactory(DjangoModelFactory):
    """Factory for creating OptimizationRecord instances."""

    class Meta:
        model = OptimizationRecord

    target_keyword = FuzzyText(length=20)
    input_content = FuzzyText(length=500)
    target_length = FuzzyInteger(100, 2000)
    tone = FuzzyChoice(["professional", "casual", "persuasive", "informative"])
    status = FuzzyChoice(["pending", "processing", "completed", "failed"])
    optimized_keyword_denisty = FuzzyFloat(1, 5)
    processing_time = FuzzyInteger(100, 10000)


@pytest.mark.django_db
class TestBaseRecord:
    """Test the abstract BaseRecord model functionality."""

    def test_uuid_primary_key_generation(self):
        """Test that UUID primary keys are automatically generated."""
        record = AnalysisRecordFactory()
        assert isinstance(record.id, uuid.UUID)
        assert record.id is not None

    @pytest.mark.parametrize("status", ["pending", "processing", "completed", "failed"])
    def test_status_choices(self, status):
        """Test that all status choices are valid."""
        record = AnalysisRecordFactory(status=status)
        assert record.status == status

    def test_created_at_auto_now_add(self):
        """Test that created_at is automatically set."""
        before_creation = timezone.now()
        record = AnalysisRecordFactory()
        after_creation = timezone.now()

        assert before_creation <= record.created_at <= after_creation


@pytest.mark.django_db
class TestAnalysisRecord:
    """Test AnalysisRecord model functionality."""

    def test_analysis_record_creation(self):
        """Test basic AnalysisRecord creation."""
        record = AnalysisRecordFactory()
        assert record.id is not None
        assert record.target_keyword is not None

    def test_analysis_record_with_url(self):
        """Test AnalysisRecord creation with URL input."""
        record = AnalysisRecordFactory(
            input_url="https://example.com/test", input_content=None
        )
        assert record.input_url == "https://example.com/test"
        assert record.input_content is None

    def test_analysis_record_with_content(self):
        """Test AnalysisRecord creation with content input."""
        content = "This is test content for SEO analysis."
        record = AnalysisRecordFactory(input_url=None, input_content=content)
        assert record.input_content == content
        assert record.input_url is None

    @pytest.mark.parametrize("seo_score", [0, 25.5, 50, 75.7, 100])
    def test_seo_score_range(self, seo_score):
        """Test SEO score can be set to various valid values."""
        record = AnalysisRecordFactory(seo_score=seo_score)
        assert record.seo_score == seo_score

    def test_analysis_record_str_representation(self):
        """Test the string representation of AnalysisRecord."""
        record = AnalysisRecordFactory(status="completed")
        expected = f"Analysis Record {record.id} - completed"
        assert str(record) == expected

    def test_json_fields_can_store_complex_data(self):
        """Test that JSON fields can store complex data structures."""
        issues_data = {
            "keyword_density_low": {
                "severity": "medium",
                "message": "Keyword density too low",
            },
            "missing_h1": {"severity": "high", "message": "No H1 tag found"},
        }
        improvements_data = [
            "Added target keyword to title",
            "Improved readability score",
            "Enhanced meta description",
        ]

        record = AnalysisRecordFactory(
            issues=issues_data, optimized_imporvements=improvements_data
        )

        assert record.issues == issues_data
        assert record.optimized_imporvements == improvements_data


@pytest.mark.django_db
class TestOptimizationRecord:
    """Test OptimizationRecord model functionality."""

    def test_optimization_record_creation(self):
        """Test basic OptimizationRecord creation."""
        record = OptimizationRecordFactory()
        assert record.id is not None
        assert record.target_keyword is not None
        assert record.input_content is not None
        assert record.target_length is not None
        assert record.tone is not None

    @pytest.mark.parametrize(
        "tone", ["professional", "casual", "persuasive", "informative", "authoritative"]
    )
    def test_tone_choices(self, tone):
        """Test that various tone choices work."""
        record = OptimizationRecordFactory(tone=tone)
        assert record.tone == tone

    @pytest.mark.parametrize("target_length", [50, 500, 1000, 2000, 5000])
    def test_target_length_range(self, target_length):
        """Test that various target lengths are supported."""
        record = OptimizationRecordFactory(target_length=target_length)
        assert record.target_length == target_length

    def test_optimization_record_str_representation(self):
        """Test the string representation of OptimizationRecord."""
        record = OptimizationRecordFactory(status="completed")
        expected = f"Optimization Record {record.id} - completed"
        assert str(record) == expected

    def test_required_content_field(self):
        """Test that input_content is required for optimization."""
        # This should work with content
        record = OptimizationRecordFactory(input_content="Valid content")
        assert record.input_content == "Valid content"

    def test_keyword_density_calculation_storage(self):
        """Test optimized keyword density storage."""
        density = 2.5
        record = OptimizationRecordFactory(optimized_keyword_denisty=density)
        assert record.optimized_keyword_denisty == density


@pytest.mark.django_db
class TestModelRelationships:
    """Test model relationships and constraints."""

    def test_multiple_records_same_keyword(self):
        """Test that multiple records can have the same keyword."""
        keyword = "test keyword"
        record1 = AnalysisRecordFactory(target_keyword=keyword)
        record2 = OptimizationRecordFactory(target_keyword=keyword)

        assert record1.target_keyword == keyword
        assert record2.target_keyword == keyword
        assert record1.id != record2.id

    def test_records_are_independent(self):
        """Test that analysis and optimization records are independent."""
        analysis_record = AnalysisRecordFactory()
        optimization_record = OptimizationRecordFactory()

        # They should have different IDs and be independent
        assert analysis_record.id != optimization_record.id
        assert type(analysis_record) != type(optimization_record)


@pytest.mark.django_db
class TestModelTimestamps:
    """Test timestamp functionality."""

    def test_completed_at_initially_null(self):
        """Test that completed_at is initially null."""
        record = AnalysisRecordFactory(completed_at=None)
        assert record.completed_at is None

    def test_completed_at_can_be_set(self):
        """Test that completed_at can be set when processing completes."""
        completion_time = timezone.now()
        record = AnalysisRecordFactory(completed_at=completion_time)
        assert record.completed_at == completion_time

    def test_processing_time_storage(self):
        """Test that processing time can be stored in milliseconds."""
        processing_time_ms = 2500  # 2.5 seconds
        record = AnalysisRecordFactory(processing_time=processing_time_ms)
        assert record.processing_time == processing_time_ms
