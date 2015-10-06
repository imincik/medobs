from datetime import datetime
from datetime import date as dt_date
from datetime import time as dt_time
from datetime import timedelta as dt_timedelta

from django.db import transaction

from medobs.reservations.models import Reservation_exception, Visit_reservation


def generate_reservations(templates, console_logging=False):
	#templates = templates if type(templates) == list else list(templates)
	office_templates = {}
	for template in templates:
		if template.office in office_templates:
			office_templates[template.office].append(template)
		else:
			office_templates[template.office] = [template]

	for office, templates in office_templates.iteritems():
		if console_logging:
			print '\nOffice: %s' % office
			print 'Days to generate: %d' % office.days_to_generate

		templates_exceptions = list(Reservation_exception.objects.filter(office=office))

		sid = transaction.savepoint()
		today = dt_date.today()
		end_day = today + dt_timedelta(office.days_to_generate)

		# create cache of existing reservations with this structure
		# { date_string -> { time_string -> { pk: p, status: s } }
		existing_reservations = Visit_reservation.objects.filter(
			office=office, date__gte=today, date__lte=end_day).values_list('pk', 'date', 'time', 'status')
		existing_reservations_cache = {}
		for pk, date, time, status in existing_reservations:
			date_key = str(date)
			if date_key not in existing_reservations_cache:
				existing_reservations_cache[date_key] = {str(time): {'pk': pk, 'status': status}}
			else:
				existing_reservations_cache[date_key][str(time)] = {'pk': pk, 'status': status}

		day = today
		try:
			while day <= end_day:
				week_day = day.isoweekday()

				day_cache = existing_reservations_cache.get(str(day), {})
				for tmp in templates:
					if tmp.day == week_day and tmp.valid_since <= day and (tmp.valid_until == None or tmp.valid_until > day):
						starting_time = datetime.combine(day, tmp.starting_time)

						status = Visit_reservation.STATUS_ENABLED
						for templ_exception in templates_exceptions:
							if templ_exception.covers_reservation_time(starting_time):
								status = Visit_reservation.STATUS_DISABLED
								break

						existing_reservation_info = day_cache.get(str(tmp.starting_time))
						if existing_reservation_info is None:
							if console_logging:
								print '* %s' % (starting_time)
							obj = Visit_reservation(
								date=day,
								time=tmp.starting_time,
								office=office,
								status=status,
								authenticated_only=tmp.authenticated_only
							)
							obj.save()
						elif console_logging:
							print 'Reservation already exists, skipping ... %s' % (starting_time)

				day += dt_timedelta(1)

			transaction.savepoint_commit(sid)
		except ValueError:
			transaction.savepoint_rollback(sid)
