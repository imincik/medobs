import datetime

from django.core.management.base import BaseCommand, CommandError

from medobs.reservations.decorators import command_task
from medobs.reservations.models import Reservation


class Command(BaseCommand):
	help = "Cancel holding of reservation after given time"

	def add_arguments(self, parser):
		parser.add_argument('expiretime', type=float, help='Format: MM')

	@command_task("medobsunhold")
	def handle(self, *args, **options):
		expire = options['expiretime']
		expiretime = datetime.datetime.now() - datetime.timedelta(minutes=expire)
		
		print 'Cancelling holding of reservations done before %s' % (expiretime)
		for reservation in Reservation.objects.filter(reservation_time__lte=(expiretime), status=Reservation.STATUS_IN_HELD):
			print '* %s' % (reservation)
			reservation.status = Reservation.STATUS_ENABLED
			reservation.reservation_time = None
			reservation.reserved_by = ""
			reservation.save()


# vim: set ts=4 sts=4 sw=4 noet:
