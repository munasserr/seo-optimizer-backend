from django.urls import path
from .views.analysis_views import (
    AnalysisRecordListCreateAPIView,
    AnalysisRecordRetrieveAPIView,
)
from .views.optimization_views import (
    OptimizationRecordListCreateAPIView,
    OptimizationRecordRetrieveAPIView,
)

urlpatterns = [
    # Analysis endpoints
    path(
        "api/analyze",
        AnalysisRecordListCreateAPIView.as_view(),
        name="analysis-list-create",
    ),
    path(
        "api/analyze/<uuid:id>",
        AnalysisRecordRetrieveAPIView.as_view(),
        name="analysis-retrieve",
    ),
    # Optimization endpoints
    path(
        "api/optimize",
        OptimizationRecordListCreateAPIView.as_view(),
        name="optimize-list-create",
    ),
    path(
        "api/optimize/<uuid:id>",
        OptimizationRecordRetrieveAPIView.as_view(),
        name="optimize-retrieve",
    ),
]
