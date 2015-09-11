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

				day = datetime.date.today()
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

						obj, created = Visit_reservation.objects.get_or_create(
							date=day,
							time=tmp.starting_time,
							defaults={
								'office': office,
								'status': status,
								'authenticated_only': tmp.authenticated_only
							}
						)
						if created:
							print 'I: Creating reservation: %s' % (starting_time)
						else:
							if status == Visit_reservation.STATUS_DISABLED and obj.status != status:
								print 'I: Disabling reservation: %s' % (starting_time)
								obj.status = status
								obj.save()
							else:
								print 'I: Reservation already exists, skipping it: %s' % (starting_time)

					day += datetime.timedelta(1)

				transaction.savepoint_commit(sid)
		except ValueError:
			transaction.savepoint_rollback(sid)
