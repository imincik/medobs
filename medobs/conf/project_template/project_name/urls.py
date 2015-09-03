from django.conf import settings
from django.contrib import admin
from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import login, logout
from django.views.i18n import javascript_catalog
from django.conf.urls.static import static


js_info_dict = {
	'packages': ('medobs.reservations',),
}

urlpatterns = [
	url(r'', include('medobs.reservations.urls', namespace='reservations')),
	url(r'^accounts/login/$', login, name='login'),
	url(r'^accounts/logout/$', logout, name='logout'),
	url(r'^jsi18n/$', javascript_catalog, js_info_dict),
	url(r"^admin/", include(admin.site.urls)),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
	urlpatterns.append(
		url(r"^admin/doc/", include("django.contrib.admindocs.urls")),
	)