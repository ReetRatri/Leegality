"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from leegality.views import (
    EdgeCreateView,
    EdgeDeleteView,
    NodeCreateView,
    NodeDeleteView,
    ShortestRouteHistoryView,
    ShortestRouteView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nodes', NodeCreateView.as_view(), name='node-create'),
    path('nodes/<int:node_id>', NodeDeleteView.as_view(), name='node-delete'),
    path('edges', EdgeCreateView.as_view(), name='edge-create'),
    path('edges/<int:edge_id>', EdgeDeleteView.as_view(), name='edge-delete'),
    path('routes/shortest', ShortestRouteView.as_view(), name='shortest-route'),
    path('routes/history', ShortestRouteHistoryView.as_view(), name='shortest-route-history'),
]
