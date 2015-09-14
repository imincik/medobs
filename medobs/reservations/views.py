import json
from datetime import datetime, date, time, timedelta
from view_utils import get_offices, is_reservation_on_date, send_notification

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from medobs.reservations.forms import PatientForm, PatientDetailForm
from medobs.reservations.models import Medical_office, Patient, Visit_reservation
from medobs.reservations.models import get_hexdigest


def front_page(request):
	try:
		if request.user.is_authenticated():
			office = Medical_office.objects.filter(published=True)[0]
		else:
			office = Medical_office.objects.filter(published=True, public=True)[0]
	except IndexError:
		return render_to_response( "missing_config.html", {},
			context_instance=RequestContext(request))

	return HttpResponseRedirect("/office/%d/" % office.id)

class DateInPast(Exception):
	pass

class BadStatus(Exception):
	pass

def office_page(request, office_id, for_date=None):
	office = get_object_or_404(Medical_office, published=True, pk=office_id)

	if not request.user.is_authenticated() and not office.public: # forbidden office
		return HttpResponseRedirect("/")

	message = None
	start_date = date.today()
	end_date = start_date + timedelta(office.days_to_generate)

	if not request.user.is_authenticated():
		start_date += timedelta(1)
		while not is_reservation_on_date(start_date, office):
			start_date += timedelta(1)
			if start_date == end_date:
				break
	if for_date:
		actual_date = datetime.strptime(for_date, "%Y-%m-%d").date()
		if actual_date < start_date:
			actual_date = start_date
	else:
		actual_date = start_date

	reservation_id = 0

	if request.method == 'POST':
		form = PatientForm(request.POST)
		form.fields["exam_kind"].queryset = office.exam_kinds.all()
		if form.is_valid():
			try:
				reservation = form.cleaned_data["reservation"]
				actual_date = reservation.starting_time.date()
				reservation_id = reservation.id

				if request.user.is_authenticated():
					if reservation.status not in (Visit_reservation.STATUS_ENABLED, Visit_reservation.STATUS_IN_HELD):
						raise BadStatus()
				else:
					if reservation.status != Visit_reservation.STATUS_ENABLED:
						raise BadStatus()

				datetime_limit = datetime.combine(date.today() + timedelta(1), time(0, 0))
				if reservation.starting_time < datetime_limit:
					raise DateInPast()

				hexdigest = get_hexdigest(form.cleaned_data["ident_hash"])
				patient, patient_created = Patient.objects.get_or_create(ident_hash=hexdigest,
						defaults={
							"first_name": form.cleaned_data["first_name"],
							"last_name": form.cleaned_data["last_name"],
							"ident_hash": form.cleaned_data["ident_hash"],
							"phone_number": form.cleaned_data["phone_number"],
							"email": form.cleaned_data["email"],
						})

				if not patient_created and patient.has_reservation():
					messages.error(request, render_to_string("messages/cancel.html", {
							"reservation": patient.visit_reservations.get(starting_time__gte=datetime.now()),
							"user": request.user,
						}))
					return HttpResponseRedirect("/cancel/%d/" % reservation.office_id)

				if not patient_created:
					patient.first_name = form.cleaned_data["first_name"]
					patient.last_name = form.cleaned_data["last_name"]
					patient.phone_number = form.cleaned_data["phone_number"]
					patient.email = form.cleaned_data["email"]
					patient.save()

				reservation.patient = patient
				reservation.exam_kind = form.cleaned_data["exam_kind"]
				reservation.status = Visit_reservation.STATE_ENABLED # clean 'in held' state
				reservation.reservation_time = datetime.now()
				reservation.reservated_by = request.user.username
				reservation.save()

				if patient.email:
					send_notification(reservation)

				messages.success(request, render_to_string("messages/booked.html", {
						"reservation": reservation,
					}))
				return HttpResponseRedirect("/booked/%d/%s/" % (
							reservation.office_id,
							actual_date.strftime("%Y-%m-%d")))
			except DateInPast:
				message = _("You cannot make reservation for today or date in the past.")
			except BadStatus:
				message = _("The reservation has been already booked. Please try again.")
				reservation_id = 0
		else:
			r_val = form["reservation"].value()
			if r_val:
				reservation_id = int(r_val)
				actual_date = Visit_reservation.objects.get(pk=reservation_id).starting_time.date()
	else:
		form = PatientForm()
		form.fields["exam_kind"].queryset = office.exam_kinds.all()

	office_data = {
		"id": office.id,
		"name": office.name,
		"reservations": office.reservations(actual_date),
		"days_status": json.dumps(office.days_status(start_date, end_date))
	}

	return render_to_response(
		"index.html",
		{
			"offices": get_offices(request.user),
			"office": office_data,
			"form": form,
			"message": message,
			"start_date": start_date,
			"actual_date": actual_date,
			"end_date": end_date,
			"reservation_id": reservation_id,
		},
		context_instance=RequestContext(request)
	)

def date_reservations(request, for_date, office_id):
	office = get_object_or_404(Medical_office, pk=office_id)
	for_date = datetime.strptime(for_date, "%Y-%m-%d").date()

	if request.user.is_authenticated():
		response_data = [{
			"id": r.id,
			"time": r.starting_time.time().strftime("%H:%M"),
			"status": r.status,
			"patient": r.patient.full_name if r.patient else "",
			"phone_number": r.patient.phone_number.replace(" ", "") if r.patient else "",
			"email": r.patient.email if r.patient else "",
			"exam_kind": r.exam_kind.title if r.exam_kind else "",
			"reservated_by": r.reservated_by,
			"reservation_time": r.reservation_time.strftime("%d.%m.%Y %H:%M") if r.reservation_time else "",
			"auth_only": r.authenticated_only,
		} for r in office.reservations(for_date)]
	else:
		response_data = [{
			"id": r.id,
			"time": r.starting_time.time().strftime("%H:%M"),
			"disabled": True if r.status != 2 or r.authenticated_only else False,
		} for r in office.reservations(for_date)]

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

def booked(request, office_id, for_date):
	office = get_object_or_404(Medical_office, pk=office_id)
	return render_to_response(
		"booked.html",
		{"office": office, "for_date": for_date},
		context_instance=RequestContext(request)
	)

@login_required
def patient_details(request):
	response_data = {
		"first_name": "",
		"last_name": "",
		"phone_number": "",
		"email": "",
	}

	if request.method == 'POST':
		form = PatientDetailForm(request.POST)
		if form.is_valid():
			hexdigest = get_hexdigest(form.cleaned_data["ident_hash"])
			try:
				patient = Patient.objects.get(ident_hash=hexdigest)
				response_data = {
					"first_name": patient.first_name,
					"last_name": patient.last_name,
					"phone_number": patient.phone_number,
					"email": patient.email,
				}
			except Patient.DoesNotExist:
				pass
	return HttpResponse(json.dumps(response_data), "application/json")

@login_required
def hold_reservation(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	if reservation.status == Visit_reservation.STATUS_ENABLED:
		reservation.status = Visit_reservation.STATUS_IN_HELD
		reservation.reservation_time = datetime.now()
		reservation.reservated_by = request.user.username
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def unhold_reservation(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	if reservation.status == Visit_reservation.STATUS_IN_HELD:
		reservation.status = Visit_reservation.STATUS_DISABLED
		reservation.reservation_time = None
		reservation.reservated_by = ""
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def unbook_reservation(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	if reservation.is_reservated:
		reservation.status = Visit_reservation.STATUS_ENABLED
		reservation.patient = None
		reservation.exam_kind = None
		reservation.reservation_time = None
		reservation.reservated_by = ""
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def disable_reservation(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	if reservation.status in (Visit_reservation.STATUS_ENABLED, Visit_reservation.STATUS_IN_HELD) and request.user.is_staff:
		reservation.status = Visit_reservation.STATUS_DISABLED
		reservation.reservation_time = datetime.now()
		reservation.reservated_by = request.user.username
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def enable_reservation(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	if reservation.status == Visit_reservation.STATUS_DISABLED and request.user.is_staff:
		reservation.status = Visit_reservation.STATUS_ENABLED
		reservation.reservation_time = None
		reservation.reservated_by = ""
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def list_reservations(request, for_date, office_id):
	for_date = datetime.strptime(for_date, "%Y-%m-%d").date()
	office = get_object_or_404(Medical_office, pk=office_id)

	reservations = office.reservations(for_date)

	return render_to_response(
		"list_reservations.html",
		{
			"for_date": for_date,
			"office": office,
			"reservations": reservations,
		},
		context_instance=RequestContext(request)
	)

@login_required
def reservation_details(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	response_data = {
		"first_name": reservation.patient.first_name,
		"last_name": reservation.patient.last_name,
		"phone_number": reservation.patient.phone_number,
		"email": reservation.patient.email,
		"exam_kind": reservation.exam_kind_id,
	}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def patient_reservations(request):
	response_data = {"patient": None}

	if request.method == 'POST':
		form = PatientDetailForm(request.POST)
		if form.is_valid():
			hexdigest = get_hexdigest(form.cleaned_data["ident_hash"])
			try:
				response_data["patient"] = Patient.objects.get(ident_hash=hexdigest)
			except Patient.DoesNotExist:
				pass

	return render_to_response("patient_reservations.html", response_data,
		context_instance=RequestContext(request))

def days_status(request, year, month, office_id):
	office = get_object_or_404(Medical_office, pk=office_id)
	year = int(year)
	month = int(month)

	start_date = date(year, month, 1)
	if month == 12:
		end_date = date(year+1, 1, 31)
	else:
		end_date = date(year, month + 1, 1) - timedelta(1)
	response_data = office.days_status(start_date, end_date)

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@csrf_exempt
def login(request):
	try:
		if request.POST:
			username = request.POST["username"]
			password = request.POST["password"]
			
			if username and password:
				user = authenticate(username=username, password=password)
				if user and user.is_authenticated():
					django_login(request, user)
					return HttpResponse(status=200)
	except:
		pass
	return HttpResponse(status=401)

@login_required
def logout(request):
	django_logout(request)
	return HttpResponse(status=200)

@login_required
def list_offices(request):
	response_data = [{
			"id": office.pk,
			"name": office.name,
			"street": office.street,
			"zip_code": office.zip_code,
			"city": office.city,
			"email": office.email,
			"order": office.order,
			"public": office.public,
			"phones": [phone.number for phone in office.phone_numbers.all()],
		} for office in Medical_office.objects.filter(published=True)]
	return HttpResponse(json.dumps(response_data), "application/json")


@login_required
def enable_auth_only(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	reservation.authenticated_only = True
	reservation.save()

	response_data = {"status_ok": True}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response


@login_required
def disable_auth_only(request, r_id):
	reservation = get_object_or_404(Visit_reservation, pk=r_id)
	reservation.authenticated_only = False
	reservation.save()

	response_data = {"status_ok": True}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response