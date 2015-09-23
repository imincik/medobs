from django.conf.urls import url
from django.views.generic.list import ListView

from medobs.reservations import views
from medobs.reservations.models import Medical_office


urlpatterns = [
	url(r"^$", views.front_page),
	url(r"^android/login/$", views.login),
	url(r"^android/logout/$", views.logout),
	url(r"^office/(?P<office_id>\d+)/(?P<for_date>\d{4}-\d{2}-\d{2})/$", views.office_page),
	url(r"^office/(?P<office_id>\d+)/$", views.office_page),
	url(r"^reservations/(?P<for_date>\d{4}-\d{2}-\d{2})/(?P<office_id>\d+)/$", views.date_reservations),
	url(r"^reservations/(?P<for_date>\d{4}-\d{2}-\d{2})/list/(?P<office_id>\d+)/$", views.list_reservations),
	url(r"^reservations/(?P<r_id>\d+)/hold/$", views.hold_reservation),
	url(r"^reservations/(?P<r_id>\d+)/unhold/$", views.unhold_reservation),
	url(r"^reservations/(?P<r_id>\d+)/unbook/$", views.unbook_reservation),
	url(r"^reservations/(?P<r_id>\d+)/disable/$", views.disable_reservation),
	url(r"^reservations/(?P<r_id>\d+)/enable/$", views.enable_reservation),
	url(r"^reservations/(?P<r_id>\d+)/details/$", views.reservation_details),
	url(r"^reservations/(?P<r_id>\d+)/auth-on/$", views.enable_auth_only),
	url(r"^reservations/(?P<r_id>\d+)/auth-off/$", views.disable_auth_only),
	url(r"^patient/$", views.patient_details),
	url(r"^patient/reservations/$", views.patient_reservations),
	url(r"^days_status/(?P<year>\d{4})/(?P<month>\d{2})/(?P<office_id>\d+)/$", views.days_status),
	url(r"^booked/(?P<office_id>\d+)/(?P<for_date>\d{4}-\d{2}-\d{2})/$", views.booked),
	url(r"^cancel/(?P<object_id>\d+)/$", ListView.as_view(), {
		"queryset": Medical_office.objects.all(),
		"template_object_name": "office",
		"template_name": "cancel.html",
	}),
	url(r"^offices/$", views.list_offices),
]

# vim: set ts=4 sts=4 sw=4 noet: