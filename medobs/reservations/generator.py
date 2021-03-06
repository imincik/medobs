import logging
from datetime import datetime
from datetime import date as dt_date
from datetime import time as dt_time
from datetime import timedelta as dt_timedelta

from medobs.reservations.models import Reservation_exception, Reservation


logger = logging.getLogger('medobs.generator')

def generate_reservations(templates, logging=False):
	#templates = templates if type(templates) == list else list(templates)
	office_templates = {}
	for template in templates:
		if template.office in office_templates:
			office_templates[template.office].append(template)
		else:
			office_templates[template.office] = [template]

	for office, templates in office_templates.iteritems():
		if logging:
			logger.info('Office: %s' % office)
			logger.info('Days to generate: %d' % office.days_to_generate)

		templates_exceptions = list(Reservation_exception.objects.filter(office=office))

		today = dt_date.today()
		end_day = today + dt_timedelta(office.days_to_generate)

		# create cache of existing reservations with this structure
		# { date_string -> { time_string -> { pk: p, status: s } }
		existing_reservations = Reservation.objects.filter(
			office=office, date__gte=today, date__lte=end_day).values_list('pk', 'date', 'time', 'status')
		existing_reservations_cache = {}
		for pk, date, time, status in existing_reservations:
			date_key = str(date)
			if date_key not in existing_reservations_cache:
				existing_reservations_cache[date_key] = {str(time): {'pk': pk, 'status': status}}
			else:
				existing_reservations_cache[date_key][str(time)] = {'pk': pk, 'status': status}

		day = today

		while day <= end_day:
			week_day = day.isoweekday()

			day_cache = existing_reservations_cache.get(str(day), {})
			for tmp in templates:
				if tmp.day == week_day \
						and tmp.valid_since <= day \
						and (tmp.valid_until == None or tmp.valid_until > day):
					starting_time = datetime.combine(day, tmp.starting_time)

					status = Reservation.STATUS_ENABLED
					for templ_exception in templates_exceptions:
						if templ_exception.covers_reservation_time(starting_time):
							status = Reservation.STATUS_DISABLED
							break

					try:
						existing_reservation_info = day_cache.get(str(tmp.starting_time))
						if existing_reservation_info is None:
							obj = Reservation(
								date=day,
								time=tmp.starting_time,
								office=office,
								status=status,
								authenticated_only=tmp.authenticated_only
							)
							obj.save()
							if logging:
								logger.info('* %s' % (starting_time))
						elif logging:
							logger.info('Reservation already exists, skipping ... %s' % (starting_time))

					except Exception:
						logger.exception("Failed to create reservation: %s" % starting_time)

			day += dt_timedelta(1)

# vim: set ts=4 sts=4 sw=4 noet:
