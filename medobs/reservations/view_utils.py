from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from medobs.reservations.models import Office, Reservation

def is_reservation_on_date(for_date, office):
	""" Checks if reservations exist on selected date. """
	return Reservation.objects.filter(date=for_date, office=office).exists()

def get_offices(user):
	if user.is_authenticated():
		return Office.objects.filter(published=True)
	else:
		return Office.objects.filter(published=True, authenticated_only=True)

def send_notification_created(reservation):
	try:
		send_mail(
			"%s - %s" % (reservation.office.name, _("reservation confirmation")),
			render_to_string(
				"email/created.html",
				{"reservation": reservation}
			),
			settings.DEFAULT_FROM_EMAIL,
			[reservation.patient.email],
			fail_silently=False
		)
	except:
		pass


_status_map = {
	Reservation.STATUS_ENABLED: 'enabled',
	Reservation.STATUS_DISABLED: 'disabled',
	Reservation.STATUS_IN_HELD: 'hold',
	Reservation.STATUS_RESERVED: 'reserved',
	Reservation.STATUS_RESCHEDULE: 'reschedule'
}

def get_reservations_data(reservations, all_attrs=True):
	reservations = list(reservations)
	Reservation.compute_actual_status(reservations)
	if all_attrs:
		data = [{
			"id": r.id,
			"time": r.time.strftime("%H:%M"),
			"status": _status_map[r.actual_status],
			"patient": {
				"ident_hash": r.patient.ident_hash,
				"name": r.patient.full_name,
				"phone_number": r.patient.phone_number.replace(" ", ""),
				"email": r.patient.email
			} if r.patient else None,
			"exam_kind": r.exam_kind.title if r.exam_kind else "",
			"reserved_by": r.reserved_by,
			"reservation_time": r.reservation_time.strftime("%d.%m.%Y %H:%M") if r.reservation_time else "",
			"auth_only": r.authenticated_only,
		} for r in reservations]
	else:
		data = [{
			"id": r.id,
			"time": r.time.strftime("%H:%M"),
			"status": "enabled" if r.actual_status == Reservation.STATUS_ENABLED and not r.authenticated_only else "disabled",
		} for r in reservations]
	return data

# vim: set ts=4 sts=4 sw=4 noet:
