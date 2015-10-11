import os, sys
import json
import datetime

from medobs.reservations.models import Office, Phone, Examination_kind, Patient, Template, Reservation_exception, Reservation


with open(sys.argv[1]) as f:
	data = json.load(f)
	# sobj - serialized object
	# Import models without foreign key relation
	offices = {}
	patients = {}
	for sobj in data:

		if sobj['model'] == 'reservations.medical_office':
                        print sobj
			fields = sobj['fields']
			fields['authenticated_only'] = not bool(fields.pop('public'))
			office = Office(pk=sobj['pk'], **fields)
			office.save()
			offices[office.pk] = office

		elif sobj['model'] == 'reservations.patient':
                        print sobj
			fields = sobj['fields']
			patient = Patient(pk=sobj['pk'], **fields)
			patient.save()
			patients[patient.pk] = patient

	# Import other models (except reservations)
	exam_kinds = {}
	for sobj in data:
		model = sobj['model']

		if model == 'reservations.office_phone':
                        print sobj
			fields = sobj['fields']
			fields['office'] = offices[fields['office']]
			phone = Phone(pk=sobj['pk'], **fields)
			phone.save()

		elif model == 'reservations.examination_kind':
                        print sobj
			fields = sobj['fields']
			exam_kind_map = {}
			for office_pk in fields['office']:
				fields['office'] = offices[office_pk]
				exam_kind = Examination_kind(**fields)
				exam_kind.save()
				exam_kind_map[office_pk] = exam_kind
			exam_kinds[sobj['pk']] = exam_kind_map

		elif model == 'reservations.visit_template':
                        print sobj
			fields = sobj['fields']
			fields['office'] = offices[fields['office']]
			template = Template(pk=sobj['pk'], **fields)
			template.save()

		elif model == 'reservations.visit_disable_rule':
                        print sobj
			fields = sobj['fields']
			fields['office'] = offices[fields['office']]
			reservation_exception = Reservation_exception(pk=sobj['pk'], **fields)
			reservation_exception.save()

	# Import reservations
	status_transform = {1: 1, 2: 2, 3: 2, 4: 4}
	for sobj in data:

                if sobj['model'] == 'reservations.visit_reservation':
                        print sobj
			fields = sobj['fields']
			starting_time = datetime.datetime.strptime(fields['starting_time'], "%Y-%m-%d %H:%M:%S")
			reservation = Reservation(
				pk=sobj['pk'],
				office=offices.get(fields['office']),
				patient=patients.get(fields['patient']),
				exam_kind=exam_kinds.get(fields['exam_kind'], {}).get(fields['office']),
				date=starting_time.date(),
				time=starting_time.time(),
				status=status_transform[fields['status']],
				authenticated_only=fields['authenticated_only'],
				reservation_time=fields['booked_at'],
				reserved_by=fields['booked_by']
			)
			reservation.save()
