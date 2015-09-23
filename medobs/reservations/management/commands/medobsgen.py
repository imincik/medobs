import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from medobs.reservations.models import Medical_office, Visit_reservation_exception
from medobs.reservations.models import Visit_reservation, Visit_template

class Command(BaseCommand):
	help = "Pregenerate Visit_reservation records by Visit_template"

	def handle(self, *args, **options):
		try:
			for office in Medical_office.objects.all():
				print '\nI: Office: %s' % office
				
				end_day = datetime.date.today() + datetime.timedelta(office.days_to_generate)
				print 'I: Days to generate: %d' % office.days_to_generate

				sid = transaction.savepoint()

				day = datetime.date.today()

				# create cache of existing reservations with this structure
				# { date_string -> { time_string -> { pk: p, status: s } }
				existing_reservations = Visit_reservation.objects.filter(
					office=office, date__gte=day, date__lte=end_day).values_list('pk', 'date', 'time', 'status')
				existing_reservations_cache = {}
				for pk, date, time, status in existing_reservations:
					date_key = str(date)
					if date_key not in existing_reservations_cache:
						existing_reservations_cache[date_key] = {str(time): {'pk': pk, 'status': status}}
					else:
						existing_reservations_cache[date_key][str(time)] = {'pk': pk, 'status': status}

				# cache visit templates and visit template exception and filter them by date/time without db queries
				office_templates = list(Visit_template.objects.filter(office=office))
				templates_exceptions = list(Visit_reservation_exception.objects.filter(office=office))
				while day <= end_day:
					templates = []
					week_day = day.isoweekday()
					for templ in office_templates:
						if templ.day == week_day and templ.valid_since <= day and (templ.valid_until == None or templ.valid_until > day):
							templates.append(templ)


					day_cache = existing_reservations_cache.get(str(day), {})

					for tmp in templates:
						starting_time = datetime.datetime.combine(day, tmp.starting_time)

						status = Visit_reservation.STATUS_ENABLED
						for templ_exception in templates_exceptions:
							if templ_exception.begin <= starting_time and templ_exception.end >= starting_time:
								status = Visit_reservation.STATUS_DISABLED
								break

						existing_reservation_info = day_cache.get(str(tmp.starting_time))
						if existing_reservation_info is None:
							print 'I: Creating reservation: %s' % (starting_time)
							obj = Visit_reservation(
								date=day,
								time=tmp.starting_time,
								office=office,
								status=status,
								authenticated_only=tmp.authenticated_only
							)
							obj.save()
						else:
							if status == Visit_reservation.STATUS_DISABLED and existing_reservation_info['status'] != status:
								print 'I: Disabling reservation: %s' % (starting_time)
								obj = Visit_reservation.objects.get(pk=existing_reservation_info['pk'])
								obj.status = status
								obj.save()
							else:
								print 'I: Reservation already exists, skipping it: %s' % (starting_time)

					day += datetime.timedelta(1)

				transaction.savepoint_commit(sid)
		except ValueError:
			transaction.savepoint_rollback(sid)

# vim: set ts=4 sts=4 sw=4 noet:
