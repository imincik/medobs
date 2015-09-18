from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from medobs.reservations.models import Medical_office


class Command(BaseCommand):
	help = "Sends notification emails about tomorrow reservations"

	def handle(self, *args, **options):
		translation.activate(settings.LANGUAGE_CODE)
		actual_date = date.today() + timedelta(1)
		for office in Medical_office.objects.all():
			for r in office.reservations(actual_date):
				if r.is_reservated and r.patient.email:
					send_mail(
						_("Notification about upcoming visit reservation"),
						render_to_string(
							"email/second_notification.html",
							{"reservation": r}
						),
						settings.DEFAULT_FROM_EMAIL,
						[r.patient.email],
						fail_silently=False
					)
