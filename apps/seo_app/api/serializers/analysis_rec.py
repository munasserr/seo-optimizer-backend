from rest_framework import serializers
from apps.seo_app.models import AnalysisRecord


class AnalysisRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRecord
        fields = "__all__"



class AnalysisRecordCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for creating analysis records via API.
    """
    url = serializers.URLField(
        required=False,
        help_text="URL to analyze for SEO metrics"
    )
    content = serializers.CharField(
        required=False,
        help_text="Raw text content to analyze"
    )
    target_keyword = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Primary keyword to optimize for"
    )
    
    def validate(self, data):
        url = data.get('url')
        content = data.get('content')
        
        if not url and not content:
            raise serializers.ValidationError(
                "Either 'url' or 'content' must be provided."
            )
        
        if url and content:
            raise serializers.ValidationError(
                "Provide either 'url' or 'content', not both."
            )
            
        return data