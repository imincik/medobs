import datetime

from django.core.management.base import BaseCommand, CommandError

from medobs.reservations.models import Visit_reservation


class Command(BaseCommand):
	help = "Automaticaly unhold holded 'visit reservations' done before given expire time"
	args = "expiretime(MM)"
	
	def handle(self, *args, **options):
		if len(args) != 1:
			raise CommandError("Missing command parameter.")

		expire = float(args[0])
		expiretime = datetime.datetime.now() - datetime.timedelta(minutes=expire)
		
		print 'I: UnHolding reservations done before %s' % (expiretime)
		for reservation in Visit_reservation.objects.filter(reservation_time__lte=(expiretime), status=Visit_reservation.STATUS_IN_HELD):
			print 'I: UnHolding reservation: ', reservation
			reservation.status = Visit_reservation.STATUS_ENABLED
			reservation.reservation_time = None
			reservation.reservated_by = ""
			reservation.save()

# vim: set ts=8 sts=8 sw=8 noet:
