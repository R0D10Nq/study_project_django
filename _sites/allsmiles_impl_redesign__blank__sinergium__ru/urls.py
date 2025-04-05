from django.urls import path
from django.conf.urls.static import static
from core.helpers import settings
from core.urls import urlpatterns as core_urlpatterns
from core import views as core_views
from . import views

app_name = '_sites.allsmiles_impl_redesign__blank__sinergium__ru'

urlpatterns = [
]

urlpatterns += static(settings().MEDIA_URL, document_root=settings().MEDIA_ROOT, )
urlpatterns += core_urlpatterns

handler404 = core_views.page_not_found
handler500 = core_views.server_error
