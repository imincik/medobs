#!/usr/bin/python
"""
Automaticaly generate Medobs 'visit template' by selecting office, start/end times and interval.
Running without any arguments prints list of available offices.
"""

import sys
import datetime

from django.core.management.base import BaseCommand, CommandError

from medobs.reservations.models import Medical_office, Visit_template


TEMPLATE_VALID_SINCE = '2000-01-01'

def print_offices_list():
	print 'I: List of available medical offices:'
	for office in Medical_office.objects.all():
		print '\t* %s' % office.name

def create_visit_template(office, starttime, endtime, interval):
	intervaltime = datetime.timedelta(minutes=interval)

	templatetime = starttime
	while templatetime.time() <= endtime.time():
		for day in Visit_template.DAYS:
			if day[0] <= 5: # do not create templates for Saturday and Sunday
				if not Visit_template.objects.filter(office=office, day=day[0], starting_time=templatetime.time()):
					print 'I: Creating template:  %s %s %s' % (office.name, day[1], templatetime.time())
					Visit_template.objects.create(office=office, day=day[0], starting_time=templatetime.time(), valid_since=TEMPLATE_VALID_SINCE)
				else:
					print 'W: Template already exists:  %s %s %s ... (skipping)' % (office.name, day[1], templatetime.time())

		templatetime = templatetime + intervaltime

class Command(BaseCommand):
	help = __doc__

	def add_arguments(self, parser):
		parser.add_argument('officename', type=str, nargs='?', help='Name of the medical office')
		parser.add_argument('starttime', type=str, nargs='?', help='Format: HH:MM')
		parser.add_argument('endtime', type=str, nargs='?', help='Format: HH:MM')
		parser.add_argument('interval', type=int, nargs='?', help='Format: MM')

	def handle(self, *args, **options):
		if options.get('officename') is None:
			print_offices_list()
			sys.exit(0)
		try:
			officename = options['officename']
			starttime = datetime.datetime.strptime(options['starttime'], '%H:%M')
			endtime = datetime.datetime.strptime(options['endtime'], '%H:%M')
			interval = options['interval']
		except:
			raise CommandError("Invalid command parameters.")
		
		if Medical_office.objects.filter(name=officename):
			office = Medical_office.objects.get(name=officename)
			create_visit_template(office, starttime, endtime, interval)
		else:
			print 'E: Office does not exists.'
			sys.exit(1)

# vim: set ts=8 sts=8 sw=8 noet:
