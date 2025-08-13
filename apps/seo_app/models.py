from django.db import models
import uuid


class BaseRecord(models.Model):
    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="processing"
    )

    # Base Input
    input_content = models.TextField(blank=True, null=True)
    target_keyword = models.CharField(max_length=255)

    # Base Results
    optimized_imporvements = models.JSONField(blank=True, null=True)
    optimized_content = models.TextField(blank=True, null=True)

    # Base Metadata
    processing_time = models.BigIntegerField(blank=True, null=True)  # ms
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True


class AnalysisRecord(BaseRecord):
    input_url = models.URLField(blank=True, null=True)

    seo_score = models.FloatField(blank=True, null=True)
    word_count = models.IntegerField(blank=True, null=True)
    keyword_density = models.FloatField(blank=True, null=True)
    avg_sentence_length = models.FloatField(blank=True, null=True)
    readability_score = models.FloatField(blank=True, null=True)

    issues = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Analysis Record {self.id} - {self.status}"


class OptimizationRecord(BaseRecord):
    input_content = models.TextField(blank=False, null=False)

    target_length = models.IntegerField()
    tone = models.CharField(max_length=255)

    optimized_keyword_denisty = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Optimization Record {self.id} - {self.status}"
