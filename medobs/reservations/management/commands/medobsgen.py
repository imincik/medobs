from django.core.management.base import BaseCommand

from medobs.reservations import generator
from medobs.reservations.models import Visit_template
from medobs.reservations.decorators import command_task


class Command(BaseCommand):
	help = "Pregenerate Visit_reservation records by Visit_template"

	@command_task("medobsgen")
	def handle(self, *args, **options):
		generator.generate_reservations(Visit_template.objects.all(), console_logging=True)


# vim: set ts=4 sts=4 sw=4 noet:
