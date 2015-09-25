from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from medobs.reservations.models import Medical_office, Visit_reservation

def is_reservation_on_date(for_date, office):
	""" Checks if reservations exist on selected date. """
	return Visit_reservation.objects.filter(date=for_date, office=office).exists()

def get_offices(user):
	if user.is_authenticated():
		return Medical_office.objects.filter(published=True)
	else:
		return Medical_office.objects.filter(published=True, public=True)

def send_notification(reservation):
	try:
		send_mail(
			_("Confirmation of reservation"),
			render_to_string(
				"email/first_notification.html",
				{"reservation": reservation}
			),
			settings.DEFAULT_FROM_EMAIL,
			[reservation.patient.email],
			fail_silently=False
		)
	except:
		pass


_status_map = {
	Visit_reservation.STATUS_ENABLED: 'enabled',
	Visit_reservation.STATUS_DISABLED: 'disabled',
	Visit_reservation.STATUS_IN_HELD: 'hold',
	Visit_reservation.STATUS_RESERVED: 'reservated',
	Visit_reservation.STATUS_RESCHEDULE: 'reschedule'
}

def get_reservations_data(reservations, all_attrs=True):
	reservations = list(reservations)
	Visit_reservation.compute_actual_status(reservations)
	if all_attrs:
		data = [{
			"id": r.id,
			"time": r.time.strftime("%H:%M"),
			"status": _status_map[r.actual_status],
			"patient": r.patient.full_name if r.patient else "",
			"phone_number": r.patient.phone_number.replace(" ", "") if r.patient else "",
			"email": r.patient.email if r.patient else "",
			"exam_kind": r.exam_kind.title if r.exam_kind else "",
			"reservated_by": r.reservated_by,
			"reservation_time": r.reservation_time.strftime("%d.%m.%Y %H:%M") if r.reservation_time else "",
			"auth_only": r.authenticated_only,
		} for r in reservations]
	else:
		data = [{
			"id": r.id,
			"time": r.time.strftime("%H:%M"),
			"status": "enabled" if r.actual_status == Visit_reservation.STATUS_ENABLED and not r.authenticated_only else "disabled",
		} for r in reservations]
	return data

# vim: set ts=4 sts=4 sw=4 noet:
