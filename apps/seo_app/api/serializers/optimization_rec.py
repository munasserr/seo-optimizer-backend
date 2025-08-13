from rest_framework import serializers
from apps.seo_app.models import OptimizationRecord


class OptimizationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizationRecord
        fields = "__all__"


class OptimizationRecordCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for creating optimization records via API.
    """

    content = serializers.CharField(
        required=True, help_text="Raw text content to optimize"
    )
    target_keyword = serializers.CharField(
        max_length=255, required=True, help_text="Primary keyword to optimize for"
    )
    target_length = serializers.IntegerField(
        required=True,
        min_value=50,
        max_value=5000,
        help_text="Target word count (50-5000 words)",
    )
    tone = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Desired tone (e.g., professional, casual, persuasive, informative, authoritative)",
    )

    def validate_tone(self, value):
        """
        Validate that tone is one of the accepted values.
        """
        accepted_tones = [
            "professional",
            "casual",
            "persuasive",
            "informative",
            "authoritative",
            "friendly",
            "formal",
            "conversational",
        ]

        if value.lower() not in accepted_tones:
            raise serializers.ValidationError(
                f"Tone must be one of: {', '.join(accepted_tones)}"
            )

        return value.lower()

    def validate_content(self, value):
        """
        Validate content length and quality.
        """
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Content must be at least 10 characters long."
            )

        word_count = len(value.split())
        if word_count < 5:
            raise serializers.ValidationError("Content must contain at least 5 words.")

        return value.strip()
