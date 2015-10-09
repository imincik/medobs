from django.conf.urls import url
from django.views.generic.detail import DetailView

from medobs.reservations import views
from medobs.reservations import admin
from medobs.reservations.models import Reservation


urlpatterns = [
	url(r"^$", views.front_page),
	url(r"^android/login/$", views.login),
	url(r"^android/logout/$", views.logout),
	url(r"^office/(?P<office_id>\d+)/(?P<for_date>\d{4}-\d{2}-\d{2})/$", views.office_page, name="office-on-date"),
	url(r"^office/(?P<office_id>\d+)/$", views.office_page),
	url(r"^reservations/(?P<for_date>\d{4}-\d{2}-\d{2})/(?P<office_id>\d+)/$", views.date_reservations),
	url(r"^reservations/(?P<for_date>\d{4}-\d{2}-\d{2})/list/(?P<office_id>\d+)/$", views.list_reservations),
	url(r"^reservations/(?P<r_id>\d+)/hold/$", views.hold_reservation),
	url(r"^reservations/(?P<r_id>\d+)/unhold/$", views.unhold_reservation),
	url(r"^reservations/unbook/$", views.unbook_reservation),
	url(r"^reservations/(?P<r_id>\d+)/disable/$", views.disable_reservation),
	url(r"^reservations/(?P<r_id>\d+)/enable/$", views.enable_reservation),
	url(r"^reservations/(?P<r_id>\d+)/details/$", views.reservation_details),
	url(r"^reservations/(?P<r_id>\d+)/auth-on/$", views.enable_auth_only),
	url(r"^reservations/(?P<r_id>\d+)/auth-off/$", views.disable_auth_only),
	url(r"^patient/$", views.patient_details),
	url(r"^patient/reservations/$", views.patient_reservations),
	url(r"^days_status/(?P<year>\d{4})/(?P<month>\d{2})/(?P<office_id>\d+)/$", views.days_status),
	url(r"^status/(?P<pk>\d+)/$", DetailView.as_view(
		model=Reservation,
		context_object_name="reservation",
		template_name="message.html",
	)),
	url(r"^offices/$", views.list_offices),
	url(r"^admin/generate_reservations/$", admin.generate_reservations, name="generate-reservations"),
]

# vim: set ts=4 sts=4 sw=4 noet: