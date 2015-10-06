from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from medobs.reservations.decorators import command_task
from medobs.reservations.models import Office, Reservation


class Command(BaseCommand):
	help = "Send email notifications for next day reservations"

	@command_task("medobsnotify")
	def handle(self, *args, **options):
		translation.activate(settings.LANGUAGE_CODE)
		actual_date = date.today() + timedelta(1)
		for office in Office.objects.all():
			reservations = list(office.reservations(actual_date))
			Reservation.compute_actual_status(reservations)
			for r in reservations:
				if r.actual_status == Reservation.STATUS_RESERVED and r.patient.email:
					try:
						send_mail(
							"%s - %s" % (r.office.name, _("reservation notification")),
							render_to_string(
								"email/created.html",
								{"reservation": r}
							),
							settings.DEFAULT_FROM_EMAIL,
							[r.patient.email],
							fail_silently=False
						)
					except:
						pass


# vim: set ts=4 sts=4 sw=4 noet:
