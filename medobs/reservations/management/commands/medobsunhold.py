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
		for reservation in Visit_reservation.objects.filter(booked_at__lte=(expiretime), status=4):
			print 'I: UnHolding reservation: ', reservation
			reservation.status = 2
			reservation.booked_at = None
			reservation.booked_by = ""
			reservation.save()

# vim: set ts=8 sts=8 sw=8 noet:
