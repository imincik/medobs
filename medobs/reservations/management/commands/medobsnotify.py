from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from medobs.reservations.models import Medical_office, Visit_reservation


class Command(BaseCommand):
	help = "Sends notification emails about tomorrow reservations"

	def handle(self, *args, **options):
		translation.activate(settings.LANGUAGE_CODE)
		actual_date = date.today() + timedelta(1)
		for office in Medical_office.objects.all():
			reservations = list(office.reservations(actual_date))
			Visit_reservation.compute_actual_status(reservations)
			for r in reservations:
				if r.actual_status == Visit_reservation.STATUS_RESERVED and r.patient.email:
					send_mail(
						_("Upcoming reservation notification"),
						render_to_string(
							"email/second_notification.html",
							{"reservation": r}
						),
						settings.DEFAULT_FROM_EMAIL,
						[r.patient.email],
						fail_silently=False
					)

# vim: set ts=4 sts=4 sw=4 noet:
