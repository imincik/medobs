import json
from datetime import datetime, date, time, timedelta
from view_utils import get_offices, get_reservations_data, is_reservation_on_date
from view_utils import send_reservation_notification, send_reschedule_notificaion, send_cancel_notificaion

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from medobs.reservations.forms import PatientForm, PatientDetailForm
from medobs.reservations.models import Office, Patient, Reservation


def front_page(request):
	try:
		if request.user.is_authenticated():
			office = Office.objects.filter(published=True)[0]
		else:
			office = Office.objects.filter(published=True, authenticated_only=False)[0]
	except IndexError:
		return render_to_response(
			"missing_config.html",
			{},
			context_instance=RequestContext(request)
		)

	return HttpResponseRedirect("/office/%d/" % office.id)

class DateInPast(Exception):
	pass

class BadStatus(Exception):
	pass

def office_page(request, office_id, for_date=None):
	office = get_object_or_404(Office, published=True, pk=office_id)

	if not request.user.is_authenticated() and office.authenticated_only: # authentication required
		return HttpResponseRedirect("/")

	reschedule_reservation = request.GET.get('reschedule')
	if reschedule_reservation:
		try:
			reschedule_reservation = Reservation.objects.get(pk=reschedule_reservation)
		except Reservation.DoesNotExist:
			raise Http404

	form = None
	message = None
	start_date = date.today()
	end_date = start_date + timedelta(office.days_to_generate)
	dates = list(Reservation.objects.filter(date__gte=date.today()).dates("date", "day"))

	if dates:
		if not request.user.is_authenticated():
			start_date = dates[0]
		end_date = dates[-1]

	if for_date:
		actual_date = datetime.strptime(for_date, "%Y-%m-%d").date()
		if actual_date < start_date:
			actual_date = start_date
	else:
		actual_date = start_date

	reservation_id = 0

	if request.method == 'POST':
		action = request.POST.get("action")
		if action == "reschedule":
			old_reservation = get_object_or_404(Reservation, pk=request.POST.get("old_reservation"))
			new_reservation = get_object_or_404(Reservation, pk=request.POST.get("reservation"))
			if new_reservation.patient or new_reservation.get_actual_status() == Reservation.STATUS_DISABLED:
				messages.error(
					request,
					render_to_string(
						"messages/reschedule_failed.html", {
							"old_reservation": old_reservation,
							"new_reservation": new_reservation,
						}
					)
				)
				return HttpResponseRedirect("/status/%d/" % new_reservation.pk)
			actual_date = new_reservation.date
			new_reservation.patient = old_reservation.patient
			new_reservation.exam_kind = old_reservation.exam_kind
			old_reservation.cancel()
			new_reservation.save()
			old_reservation.save()
			send_reschedule_notificaion(old_reservation, new_reservation)
			messages.success(
				request,
				render_to_string(
					"messages/rescheduled.html", {
						"old_reservation": old_reservation,
						"new_reservation": new_reservation,
					}
				)
			)
			return HttpResponseRedirect("/status/%d/" % new_reservation.pk)
		else:
			form = PatientForm(request.POST)
			form.fields["exam_kind"].queryset = office.exam_kinds.all()
			if form.is_valid():
				try:
					reservation = form.cleaned_data["reservation"]
					actual_date = reservation.date
					reservation_id = reservation.id

					if request.user.is_authenticated():
						if reservation.status not in (Reservation.STATUS_ENABLED, Reservation.STATUS_IN_HELD):
							raise BadStatus()
					else:
						if reservation.status != Reservation.STATUS_ENABLED:
							raise BadStatus()

					datetime_limit = datetime.combine(date.today() + timedelta(1), time(0, 0))
					if reservation.starting_time < datetime_limit:
						raise DateInPast()

					hexdigest = Patient.get_ident_hash(form.cleaned_data["ident_hash"])
					patient, patient_created = Patient.objects.get_or_create(
						ident_hash=hexdigest,
						defaults={
							"first_name": form.cleaned_data["first_name"],
							"last_name": form.cleaned_data["last_name"],
							"ident_hash": form.cleaned_data["ident_hash"],
							"phone_number": form.cleaned_data["phone_number"],
							"email": form.cleaned_data["email"],
						}
					)
					if not patient_created and patient.has_reservation():
						messages.error(
							request,
							render_to_string(
								"messages/creation_failed.html", {
									"reservations": patient.actual_reservations(),
									"user": request.user,
								}
							)
						)
						return HttpResponseRedirect("/status/%d/" % reservation.pk)

					if not patient_created:
						patient.first_name = form.cleaned_data["first_name"]
						patient.last_name = form.cleaned_data["last_name"]
						patient.phone_number = form.cleaned_data["phone_number"]
						patient.email = form.cleaned_data["email"]
						patient.save()

					reservation.patient = patient
					reservation.exam_kind = form.cleaned_data["exam_kind"]
					reservation.status = Reservation.STATUS_ENABLED # clean 'in held' state
					reservation.reservation_time = datetime.now()
					reservation.reserved_by = request.user.username
					reservation.save()

					send_reservation_notification(reservation)

					messages.success(
						request,
						render_to_string(
							"messages/created.html", {
								"reservation": reservation,
							}
						)
					)
					return HttpResponseRedirect("/status/%d/" % reservation.pk)

				except DateInPast:
					message = _("Can't make reservation for current day or day in the past.")
				except BadStatus:
					message = _("Can't make reservation. Please try again.")
					reservation_id = 0
			else:
				r_val = form["reservation"].value()
				if r_val:
					reservation_id = int(r_val)
					actual_date = Reservation.objects.get(pk=reservation_id).date
	if form is None:
		form = PatientForm()
		form.fields["exam_kind"].queryset = office.exam_kinds.all()

	office_data = {
		"id": office.id,
		"name": office.name,
		"reservations": json.dumps(
			get_reservations_data(
				office.reservations(actual_date),
				all_attrs=request.user.is_authenticated()
			)
		),
		"days_status": json.dumps(office.days_status(start_date, end_date))
	}

	data = {
		"offices": get_offices(request.user),
		"office": office_data,
		"form": form,
		"message": message,
		"start_date": start_date,
		"actual_date": actual_date,
		"end_date": end_date,
		"reservation_id": reservation_id,
		"reschedule_mode": reschedule_reservation is not None
	}
	if reschedule_reservation:
		data.update({
			"reschedule_mode": True,
			"reservation": reschedule_reservation
		})
	return render_to_response(
		"index.html",
		data,
		context_instance=RequestContext(request)
	)

def date_reservations(request, for_date, office_id):
	office = get_object_or_404(Office, pk=office_id)
	for_date = datetime.strptime(for_date, "%Y-%m-%d").date()
	data = get_reservations_data(
		office.reservations(for_date),
		all_attrs=request.user.is_authenticated()
	)
	response = HttpResponse(json.dumps(data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

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
			hexdigest = Patient.get_ident_hash(form.cleaned_data["ident_hash"])
			try:
				patient = Patient.objects.get(ident_hash=hexdigest)
				response_data = {
					"pk": patient.pk,
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
	reservation = get_object_or_404(Reservation, pk=r_id)
	if reservation.status == Reservation.STATUS_ENABLED:
		reservation.status = Reservation.STATUS_IN_HELD
		reservation.reservation_time = datetime.now()
		reservation.reserved_by = request.user.username
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def unhold_reservation(request, r_id):
	reservation = get_object_or_404(Reservation, pk=r_id)
	if reservation.status == Reservation.STATUS_IN_HELD:
		reservation.status = Reservation.STATUS_ENABLED
		reservation.reservation_time = None
		reservation.reserved_by = ""
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def cancel_reservation(request):
	reservation = get_object_or_404(Reservation, pk=request.POST.get('reservation_id'))
	tmp_reservation = Reservation(
		office=reservation.office,
		patient=reservation.patient,
		date=reservation.date,
		time=reservation.time,
		exam_kind=reservation.exam_kind
	)
	if reservation.patient is not None:
		reservation.cancel()
		reservation.save()
		send_cancel_notificaion(tmp_reservation)
		messages.success(
			request,
			render_to_string(
				"messages/canceled.html", {
					"reservation": tmp_reservation,
				}
			)
		)
	else:
		messages.error(
			request,
			 render_to_string(
				"messages/cancel_failed.html", {
					"reservation": tmp_reservation
				}
			)
		)
	return HttpResponseRedirect("/status/%d/" % reservation.pk)

@login_required
def disable_reservation(request, r_id):
	reservation = get_object_or_404(Reservation, pk=r_id)
	if reservation.status in (Reservation.STATUS_ENABLED, Reservation.STATUS_IN_HELD) and request.user.is_staff:
		reservation.status = Reservation.STATUS_DISABLED
		reservation.reservation_time = datetime.now()
		reservation.reserved_by = request.user.username
		reservation.save()
		response_data = {"status_ok": True}
	else:
		response_data = {"status_ok": False}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

@login_required
def enable_reservation(request, r_id):
	reservation = get_object_or_404(Reservation, pk=r_id)
	if reservation.status == Reservation.STATUS_DISABLED and request.user.is_staff:
		reservation.status = Reservation.STATUS_ENABLED
		reservation.reservation_time = None
		reservation.reserved_by = ""
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
	office = get_object_or_404(Office, pk=office_id)

	return render_to_response(
		"list/office.html",
		{
			"for_date": for_date,
			"office": office,
			"reservations": get_reservations_data(office.reservations(for_date)),
		},
		context_instance=RequestContext(request)
	)

@login_required
def reservation_details(request, r_id):
	reservation = get_object_or_404(Reservation, pk=r_id)
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
		ident_hash = request.POST.get("ident_hash", "")
		if len(ident_hash) < 12:
			ident_hash = Patient.get_ident_hash(ident_hash)
		try:
			response_data["patient"] = Patient.objects.get(ident_hash=ident_hash)
		except Patient.DoesNotExist:
			raise Http404

		return render_to_response(
			"list/patient.html",
			response_data,
			context_instance=RequestContext(request)
		)
	raise Http404

def days_status(request, year, month, office_id):
	office = get_object_or_404(Office, pk=office_id)
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
			"authenticated_only": office.authenticated_only,
			"phones": [phone.number for phone in office.phone_numbers.all()],
		} for office in Office.objects.filter(published=True)]
	return HttpResponse(json.dumps(response_data), "application/json")


@login_required
def enable_auth_only(request, r_id):
	reservation = get_object_or_404(Reservation, pk=r_id)
	reservation.authenticated_only = True
	reservation.save()

	response_data = {"status_ok": True}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response


@login_required
def disable_auth_only(request, r_id):
	reservation = get_object_or_404(Reservation, pk=r_id)
	reservation.authenticated_only = False
	reservation.save()

	response_data = {"status_ok": True}

	response = HttpResponse(json.dumps(response_data), "application/json")
	response["Cache-Control"] = "no-cache"
	return response

# vim: set ts=4 sts=4 sw=4 noet:
