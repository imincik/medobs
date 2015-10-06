from django.core.management.base import BaseCommand

from medobs.reservations import generator
from medobs.reservations.models import Template
from medobs.reservations.decorators import command_task


class Command(BaseCommand):
	help = "Generate reservations from templates"

	@command_task("medobsgen")
	def handle(self, *args, **options):
		generator.generate_reservations(Template.objects.all(), console_logging=True)


# vim: set ts=4 sts=4 sw=4 noet:
