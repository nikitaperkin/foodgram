from django.contrib import admin
from django.urls import include, path

from recipes.views import redirect_to_recipe

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<int:pk>/',
        redirect_to_recipe,
        name='recipe-short-link'
    ),
]
