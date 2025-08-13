import logging
from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.seo_app.models import AnalysisRecord
from apps.seo_app.api.serializers.analysis_rec import (
    AnalysisRecordSerializer,
    AnalysisRecordCreateSerializer,
)
from apps.seo_app.tasks.seo_tasks import analyze_content_task

logger = logging.getLogger(__name__)


class AnalysisRecordListCreateAPIView(generics.ListCreateAPIView):
    """Analysis Record API Endpoints"""

    queryset = AnalysisRecord.objects.all().order_by("-created_at")
    serializer_class = AnalysisRecordSerializer

    @swagger_auto_schema(
        operation_id="analyze_list",
        operation_summary="analyze/ GET",
        operation_description="List all analysis records",
        responses={200: AnalysisRecordSerializer(many=True)},
        tags=["Analysis"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id="analyze_create",
        operation_summary="analyze/ POST",
        operation_description="Create new SEO analysis record",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="URL to analyze",
                    example="https://example.com/blog-post",
                ),
                "content": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Raw text content to analyze",
                    example="Raw text content to analyze",
                ),
                "target_keyword": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Target keyword",
                    example="python development",
                ),
            },
            required=["target_keyword"],
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id": openapi.Schema(
                        type=openapi.TYPE_STRING, example="analysis_123"
                    ),
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING, example="processing"
                    ),
                    "created_at": openapi.Schema(
                        type=openapi.TYPE_STRING, example="2024-01-01T10:00:00Z"
                    ),
                },
            ),
            400: "Bad Request",
        },
        tags=["Analysis"],
    )
    def post(self, request, *args, **kwargs):
        """Custom POST for analysis creation."""
        logger.info("[API/ANALYZE] POST request received.")

        # using the "create" serializer for validation
        create_serializer = AnalysisRecordCreateSerializer(data=request.data)
        if not create_serializer.is_valid():
            return Response(
                create_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = create_serializer.validated_data
        url = validated_data.get("url")
        content = validated_data.get("content")
        target_keyword = validated_data.get("target_keyword")

        try:
            with transaction.atomic():
                record = AnalysisRecord.objects.create(
                    input_url=url,
                    input_content=content,
                    target_keyword=target_keyword.strip(),
                    created_at=timezone.now(),
                )

            analyze_content_task.delay(record.id)

            logger.info(
                f"[API/ANALYZE] Created record {record.id} and queued analysis."
            )
            return Response(
                {
                    "id": record.id,
                    "status": record.status,
                    "created_at": record.created_at,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception(f"[API/ANALYZE] Failed to create analysis record: {e}")
            return Response(
                {"error": "Failed to create analysis record. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request, *args, **kwargs):
        # for swagger 
        return self.post(request, *args, **kwargs)


class AnalysisRecordRetrieveAPIView(generics.RetrieveAPIView):
    """Retrieve specific analysis record"""

    queryset = AnalysisRecord.objects.all()
    serializer_class = AnalysisRecordSerializer
    lookup_field = "id"

    @swagger_auto_schema(
        operation_id="analyze_read",
        operation_summary="analyze/{id} GET",
        operation_description="Retrieve specific analysis record by UUID",
        responses={200: AnalysisRecordSerializer, 404: "Analysis record not found"},
        tags=["Analysis"],
    )
    def get(self, request, *args, **kwargs):
        """Custom GET for individual analysis record retrieval."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            logger.info(f"[API/ANALYZE] Retrieved record {instance.id}")
            return Response(serializer.data)
        except AnalysisRecord.DoesNotExist:
            logger.warning(f"[API/ANALYZE] Record not found: {kwargs.get('id')}")
            return Response(
                {"error": "Analysis record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception(f"[API/ANALYZE] Failed to retrieve record: {e}")
            return Response(
                {"error": "Failed to retrieve analysis record."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
