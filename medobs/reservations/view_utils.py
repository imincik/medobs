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
	send_mail(
		_("Visit reservation confirmation"),
		render_to_string(
			"email/first_notification.html",
			{"reservation": reservation}
		),
		settings.DEFAULT_FROM_EMAIL,
		[reservation.patient.email],
		fail_silently=False
	)

# Possible states of visit reservation:
# * disabled
# * enabled
# * hold
# * reservated
# * disabled-reservated (reschedule required)

_reservation_status_map = {
	1: 'disabled',
	2: 'enabled',
	4: 'hold'
}
def get_reservation_status(reservation):
	if reservation.reschedule_required:
		return 'disabled-reservated'
	elif reservation.is_reservated:
		return 'reservated'
	else:
		return _reservation_status_map[reservation.status]

def get_reservations_data(reservations, all_attrs=True):
	if all_attrs:
		data = [{
			"id": r.id,
			"time": r.time.strftime("%H:%M"),
			"status": get_reservation_status(r),
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
			"status": "enabled" if not r.is_reservated and r.status == Visit_reservation.STATUS_ENABLED and not r.authenticated_only else "disabled",
		} for r in reservations]
	return data