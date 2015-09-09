import datetime

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import transaction
from django.db.models import Q

from medobs.reservations.models import Medical_office, Visit_reservation_exception
from medobs.reservations.models import Visit_reservation, Visit_template

class Command(NoArgsCommand):
	help = "Pregenerate Visit_reservation records by Visit_template"

	def handle_noargs(self, **options):
		try:
			for office in Medical_office.objects.all():
				print '\nI: Office: %s' % office
				
				end_day = datetime.date.today() + datetime.timedelta(office.days_to_generate)
				print 'I: Days to generate: %d' % office.days_to_generate

				sid = transaction.savepoint()

				try:
					day = Visit_reservation.objects.filter(office = office).latest("day").day
				except Visit_reservation.DoesNotExist:
					day = datetime.date.today()
				day += datetime.timedelta(1)

				while day <= end_day:
					templates = Visit_template.objects.filter(day = day.isoweekday())
					templates = templates.filter(office = office, valid_since__lte = day)
					templates = templates.filter(Q(valid_until__exact=None) | Q(valid_until__gt=day))

					for tmp in templates:
						starting_time = datetime.datetime.combine(day, tmp.starting_time)

						if Visit_reservation_exception.objects.filter(begin__lte = starting_time,
								end__gte = starting_time, office = office):
							status = Visit_reservation.STATUS_DISABLED
						else:
							status = Visit_reservation.STATUS_ENABLED

						print 'I: Creating reservation: %s' % (starting_time)
						Visit_reservation.objects.create(
							day=day,
							time=tmp.starting_time,
							office=office,
							status=status,
							authenticated_only=tmp.authenticated_only
						)

					day += datetime.timedelta(1)

				transaction.savepoint_commit(sid)
		except ValueError:
			transaction.savepoint_rollback(sid)
