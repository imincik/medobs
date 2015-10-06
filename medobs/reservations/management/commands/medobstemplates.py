#!/usr/bin/python
"""
Automaticaly generate MEDOBS 'visit template' by selecting office, start/end times and interval.
Running without any arguments prints list of available offices.
"""

import sys
import datetime

from django.core.management.base import BaseCommand, CommandError

from medobs.reservations.decorators import command_task
from medobs.reservations.models import Office, Template


TEMPLATE_VALID_SINCE = '2000-01-01'


class Command(BaseCommand):
	help = __doc__

	def add_arguments(self, parser):
		parser.add_argument('officename', type=str, nargs='?', help='Office name')
		parser.add_argument('starttime', type=str, nargs='?', help='Format: HH:MM')
		parser.add_argument('endtime', type=str, nargs='?', help='Format: HH:MM')
		parser.add_argument('interval', type=int, nargs='?', help='Format: MM')

	def print_offices_list(self):
		print 'I: List of available offices:'
		for office in Office.objects.all():
			print '\t* %s' % office.name

	@command_task("medobstemplates")
	def create_templates(self, office, starttime, endtime, interval):
		intervaltime = datetime.timedelta(minutes=interval)

		templatetime = starttime
		while templatetime.time() <= endtime.time():
			for day in Template.DAYS:
				if day[0] <= 5: # do not create templates for Saturday and Sunday
					if not Template.objects.filter(office=office, day=day[0], starting_time=templatetime.time()).exists():
						print 'I: Creating template:  %s %s %s' % (office.name, day[1], templatetime.time())
						Template.objects.create(office=office, day=day[0], starting_time=templatetime.time(), valid_since=TEMPLATE_VALID_SINCE)
					else:
						print 'W: Template already exists:  %s %s %s ... (skipping)' % (office.name, day[1], templatetime.time())

			templatetime = templatetime + intervaltime

	def handle(self, *args, **options):
		if options.get('officename') is None:
			self.print_offices_list()
			sys.exit(0)
		try:
			officename = options['officename']
			starttime = datetime.datetime.strptime(options['starttime'], '%H:%M')
			endtime = datetime.datetime.strptime(options['endtime'], '%H:%M')
			interval = options['interval']
		except:
			raise CommandError("Invalid command parameters.")
		
		try:
			office = Office.objects.get(name=officename)
			self.create_templates(office, starttime, endtime, interval)
		except Office.DoesNotExist:
			print 'E: Office does not exists.'
			sys.exit(1)

# vim: set ts=4 sts=4 sw=4 noet:
