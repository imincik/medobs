import datetime

from django.core.management.base import BaseCommand, CommandError

from medobs.reservations.models import Visit_reservation


class Command(BaseCommand):
	help = "Automaticaly unhold holded 'visit reservations' done before given expire time"

	def add_arguments(self, parser):
		parser.add_argument('expiretime', type=float, help='Format: MM')

	def handle(self, *args, **options):
		expire = options['expiretime']
		expiretime = datetime.datetime.now() - datetime.timedelta(minutes=expire)
		
		print 'I: UnHolding reservations done before %s' % (expiretime)
		for reservation in Visit_reservation.objects.filter(reservation_time__lte=(expiretime), status=Visit_reservation.STATUS_IN_HELD):
			print 'I: UnHolding reservation: ', reservation
			reservation.status = Visit_reservation.STATUS_ENABLED
			reservation.reservation_time = None
			reservation.reserved_by = ""
			reservation.save()

# vim: set ts=4 sts=4 sw=4 noet:
