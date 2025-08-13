"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Custom schema view with only 2 groups
schema_view = get_schema_view(
    openapi.Info(
        title="SEO Optimizer API",
        default_version="v1",
        description="""
# SEO Content Analysis & Optimization API

This API provides two main services for SEO content optimization.

## Available Endpoints

### Analysis Group
- `GET /api/analyze/` - List all analysis records
- `POST /api/analyze/` - Create new SEO analysis  
- `GET /api/analyze/{id}/` - Retrieve specific analysis

### Optimization Group  
- `GET /api/optimize/` - List all optimization records
- `POST /api/optimize/` - Create new content optimization
- `GET /api/optimize/{id}/` - Retrieve specific optimization

All POST operations are processed asynchronously. Use the returned ID to check progress.
        """,
        contact=openapi.Contact(email="contact@seooptimizer.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.seo_app.api.urls")),
    # API Documentation
    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]
