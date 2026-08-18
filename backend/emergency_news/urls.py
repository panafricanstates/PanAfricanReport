from django.contrib import admin
from django.urls import path, re_path, include
from django.http import HttpResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Add this view function
def hello_world(request):
    return HttpResponse("Hello World")

schema_view = get_schema_view(
    openapi.Info(
        title="UbuntuReport API",
        default_version='v1',
        description="Aggregated African breaking news from multiple sources.",
        contact=openapi.Contact(email="adesinaolagunju1@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", hello_world, name="hello-world"),  # 👈 Add this line for root endpoint
    path("admin/", admin.site.urls),
    path("api/", include("newsfeeds.urls")),

    # Swagger & ReDoc routes
    re_path(r"^swagger(?P<format>\.json|\.yaml)$",
            schema_view.without_ui(cache_timeout=0),
            name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0),
         name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0),
         name="schema-redoc"),
]