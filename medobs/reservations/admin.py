from datetime import datetime

from django.db import models
from django.contrib import admin
from django.conf import settings
from django.forms import Textarea
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404
from localflavor.cz.forms import CZBirthNumberField

from medobs.reservations import filters
from medobs.reservations.forms import VisitReservationForm
from medobs.reservations.models import Examination_kind, Medical_office, Office_phone, Patient, Command
from medobs.reservations.models import Visit_reservation_exception, Visit_reservation, Visit_template
from medobs.reservations.decorators import view_async_task, Process
from medobs.reservations import generator


class ReservationsChangeList(ChangeList):
	def __init__(self, *args, **kwargs):
		super(ReservationsChangeList, self).__init__(*args, **kwargs)
		self.result_list = list(self.result_list)
		Visit_reservation.compute_actual_status(self.result_list)

class VisitReservationAdmin(admin.ModelAdmin):
	list_display = ("starting_time", "office", "admin_status_label", "authenticated_only", "patient")
	readonly_fields = ("reservation_time", "reserved_by")
	list_filter = ("office", "date", "time", filters.ReservationStatusFilter)
	ordering = ("date", "time", "office")
	search_fields = ("^patient__first_name", "^patient__last_name")
	actions = ("enable_reservations", "disable_reservations")
	form = VisitReservationForm
	fieldsets = (
		(None, {"fields": ("office", "date", "time", "status", "authenticated_only")}),
		(_("Reservation data"), {"fields": ("patient", "exam_kind", "reservation_time", "reserved_by")}),
	)
	save_as = True

	status_labels = {
		Visit_reservation.STATUS_ENABLED: _('Available'),
		Visit_reservation.STATUS_DISABLED: _('Disabled'),
		Visit_reservation.STATUS_IN_HELD: _('Hold'),
		Visit_reservation.STATUS_RESERVED: _('Reserved'),
		Visit_reservation.STATUS_RESCHEDULE: _('Reschedule')
	}

	def save_model(self, request, obj, form, change):
		if obj.patient is not None and obj.status != Visit_reservation.STATUS_DISABLED:
			obj.reserved_by = request.user.get_full_name() or request.user.username
			obj.reservation_time = datetime.now()
		else:
			obj.reservation_time = None
			obj.reserved_by = ""
		return super(VisitReservationAdmin, self).save_model(request, obj, form, change)

	def enable_reservations(self, request, queryset):
		queryset.update(status=Visit_reservation.STATUS_ENABLED)
	enable_reservations.short_description = "Enable selected reservations"

	def disable_reservations(self, request, queryset):
		queryset.update(status=Visit_reservation.STATUS_DISABLED)
	disable_reservations.short_description = "Disable selected reservations"

	# Wrap changelist to effectively compute reservations status (filtering disabled reservations
	# from Visit_reservation_exception records)
	def get_changelist(self, request, **kwargs):
		return ReservationsChangeList

	def admin_status_label(self, obj):
		return self.status_labels[obj.actual_status]
	admin_status_label.short_description = "Availability"

admin.site.register(Visit_reservation, VisitReservationAdmin)

class VisitReservationInline(admin.TabularInline):
	model = Visit_reservation
	readonly_fields = ("date", "time", "office", "authenticated_only", "exam_kind", "status", "reservation_time", "reserved_by")
	can_delete = False
	extra = 0
	def has_add_permission(self, request):
		return False

class PatientAdmin(admin.ModelAdmin):
	list_display = ("full_name", "phone_number", "email", "ident_hash", "has_reservation")
	search_fields = ("last_name", "first_name")
	ordering = ("last_name", "first_name")
	inlines = (VisitReservationInline, )

	def get_form(self, request, obj=None, **kwargs):
		self.readonly_fields = () if obj is None else ("ident_hash",)
		form = super(PatientAdmin, self).get_form(request, obj=obj, **kwargs)
		if obj is None:
			form.base_fields['ident_hash'] = CZBirthNumberField(label=_('Birth number'), widget=form.base_fields['ident_hash'].widget)
		return form

admin.site.register(Patient, PatientAdmin)

class VisitTemplateAdmin(admin.ModelAdmin):
	list_display = ("__unicode__", "office", "starting_time", "valid_since", "valid_until", "authenticated_only")
	list_filter = ("office", "day", "starting_time", filters.ExpirationFilter)
	ordering = ("day", "starting_time", "office")
	save_as = True

	def generateReservationsEnabled(self):
		return not Command.is_locked("medobsgen")

admin.site.register(Visit_template, VisitTemplateAdmin)

class VisitReservationExceptionAdmin(admin.ModelAdmin):
	list_display = ("title", "begin", "end", "office")
	list_filter = ("office", filters.ReservationExceptionDateFilter)
	ordering = ("begin", "office")

admin.site.register(Visit_reservation_exception, VisitReservationExceptionAdmin)

class ExaminationKindInline(admin.TabularInline):
	model = Examination_kind
	extra = 0
	formfield_overrides = {
		models.TextField: {
			'widget': Textarea(attrs={
						'rows': 2,
						'cols': 70,
						'style': 'height: 2.5em;'
					})},
	}

class OfficePhoneInline(admin.TabularInline):
    model = Office_phone
    extra = 1

class MedicalOfficeAdmin(admin.ModelAdmin):
	list_display = ("name", "order", "street", "zip_code", "city", "email", "days_to_generate", "published", "public")
	inlines = (ExaminationKindInline, OfficePhoneInline)
	ordering = ("name",)
	fieldsets = (
		(None, {"fields": ("name", "street", "zip_code", "city", "email", "note")}),
		(_("Settings"), {"fields": ("order", "days_to_generate", "published", "public")}),
	)
	formfield_overrides = {
		models.TextField: {
			'widget': Textarea(attrs={
						'rows': 4,
						'cols': 80,
						'style': 'height: 5em;'
					})},
	}

	def generateReservationsEnabled(self):
		return not Command.is_locked("medobsgen")

admin.site.register(Medical_office, MedicalOfficeAdmin)


admin.site.unregister(Site)

# register filters
admin.FieldListFilter.register(lambda f: f and isinstance(f, models.TimeField), filters.TimeRangeFilter, True)
admin.FieldListFilter.register(lambda f: f and isinstance(f, models.DateField), filters.DateRangeFilter, True)


def generate_office_reservations(office_pk):
	generator.generate_reservations(Visit_template.objects.filter(office=office_pk), console_logging=True)

def generate_template_reservations(template_pk):
	generator.generate_reservations(Visit_template.objects.filter(pk=template_pk), console_logging=True)

@staff_member_required
@view_async_task("medobsgen")
def generate_reservations(request):
	template = request.POST.get('template')
	office = request.POST.get('office')
	if template:
		process = Process(target=generate_template_reservations, args=(template,))
	elif office:
		process = Process(target=generate_office_reservations, args=(office,))
	else:
		raise Http404
	return process, HttpResponse()

# vim: set ts=4 sts=4 sw=4 noet:
