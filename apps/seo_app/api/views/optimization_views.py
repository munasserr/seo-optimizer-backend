import logging
from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.seo_app.models import OptimizationRecord
from apps.seo_app.api.serializers.optimization_rec import (
    OptimizationRecordSerializer,
    OptimizationRecordCreateSerializer,
)
from apps.seo_app.tasks.seo_tasks import optimize_content_task

logger = logging.getLogger(__name__)


class OptimizationRecordListCreateAPIView(generics.ListCreateAPIView):
    """Optimization Record API Endpoints"""

    queryset = OptimizationRecord.objects.all().order_by("-created_at")
    serializer_class = OptimizationRecordSerializer

    @swagger_auto_schema(
        operation_id="optimize_list",
        operation_summary="optimize/ GET",
        operation_description="List all optimization records",
        responses={200: OptimizationRecordSerializer(many=True)},
        tags=["Optimization"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id="optimize_create",
        operation_summary="optimize/ POST",
        operation_description="Create new content optimization record",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "content": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Original content",
                    example="Original content",
                ),
                "target_keyword": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Target keyword",
                    example="python development",
                ),
                "target_length": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Target length", example=1500
                ),
                "tone": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Content tone",
                    example="professional",
                ),
            },
            required=["content", "target_keyword", "target_length", "tone"],
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
        tags=["Optimization"],
    )
    def post(self, request, *args, **kwargs):
        """Custom POST for optimization creation."""
        logger.info("[API/OPTIMIZE] POST request received.")

        # using the "create" serializer for validation
        create_serializer = OptimizationRecordCreateSerializer(data=request.data)
        if not create_serializer.is_valid():
            return Response(
                create_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = create_serializer.validated_data
        content = validated_data.get("content")
        target_keyword = validated_data.get("target_keyword")
        target_length = validated_data.get("target_length")
        tone = validated_data.get("tone")

        try:
            with transaction.atomic():
                record = OptimizationRecord.objects.create(
                    input_content=content,
                    target_keyword=target_keyword,
                    target_length=target_length,
                    tone=tone,
                    created_at=timezone.now(),
                )

            optimize_content_task.delay(record.id)

            logger.info(
                f"[API/OPTIMIZE] Created record {record.id} and queued optimization."
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
            logger.exception(
                f"[API/OPTIMIZE] Failed to create optimization record: {e}"
            )
            return Response(
                {
                    "error": "Failed to create optimization record. Please try again later."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request, *args, **kwargs):
        # override to use post method for swagger
        return self.post(request, *args, **kwargs)


class OptimizationRecordRetrieveAPIView(generics.RetrieveAPIView):
    """Retrieve specific optimization record"""

    queryset = OptimizationRecord.objects.all()
    serializer_class = OptimizationRecordSerializer
    lookup_field = "id"

    @swagger_auto_schema(
        operation_id="optimize_read",
        operation_summary="optimize/{id} GET",
        operation_description="Retrieve specific optimization record by UUID",
        responses={
            200: OptimizationRecordSerializer,
            404: "Optimization record not found",
        },
        tags=["Optimization"],
    )
    def get(self, request, *args, **kwargs):
        """Custom GET for individual optimization record retrieval."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            logger.info(f"[API/OPTIMIZE] Retrieved record {instance.id}")
            return Response(serializer.data)
        except OptimizationRecord.DoesNotExist:
            logger.warning(f"[API/OPTIMIZE] Record not found: {kwargs.get('id')}")
            return Response(
                {"error": "Optimization record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception(f"[API/OPTIMIZE] Failed to retrieve record: {e}")
            return Response(
                {"error": "Failed to retrieve optimization record."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
