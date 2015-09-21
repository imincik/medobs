from datetime import datetime

from django.db import models
from django.contrib import admin
from django.conf import settings
from django.forms import Textarea
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from localflavor.cz.forms import CZBirthNumberField

from medobs.reservations import filters
from medobs.reservations.forms import VisitReservationForm
from medobs.reservations.models import Examination_kind, Medical_office, Office_phone, Patient
from medobs.reservations.models import Visit_reservation_exception, Visit_reservation, Visit_template


class VisitReservationAdmin(admin.ModelAdmin):
	list_display = ("starting_time", "office", "status_display_name", "authenticated_only", "patient")
	readonly_fields = ("reservation_time", "reservated_by")
	list_filter = ("office", "date", "time", filters.ReservationStatusFilter)
	ordering = ("date", "time", "office")
	search_fields = ("^patient__first_name", "^patient__last_name")
	actions = ("enable_reservations", "disable_reservations")
	form = VisitReservationForm
	fieldsets = (
		(None, {"fields": ("office", "date", "time", "status", "authenticated_only")}),
		(_("Booking data"), {"fields": ("patient", "exam_kind", "reservation_time", "reservated_by")}),
	)

	def save_model(self, request, obj, form, change):
		if obj.is_reservated or obj.status == Visit_reservation.STATUS_IN_HELD:
			obj.reservated_by = request.user.get_full_name() or request.user.username
			obj.reservation_time = datetime.now()
		else:
			obj.reservation_time = None
			obj.reservated_by = ""
		return super(VisitReservationAdmin, self).save_model(request, obj, form, change)

	def enable_reservations(self, request, queryset):
		queryset.update(status=Visit_reservation.STATUS_ENABLED)
	enable_reservations.short_description = "Enable selected reservations"

	def disable_reservations(self, request, queryset):
		queryset.update(status=Visit_reservation.STATUS_DISABLED)
	disable_reservations.short_description = "Disable selected reservations"

admin.site.register(Visit_reservation, VisitReservationAdmin)

class VisitReservationInline(admin.TabularInline):
	model = Visit_reservation
	readonly_fields = ("date", "time", "office", "authenticated_only", "exam_kind", "status", "reservation_time", "reservated_by")
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
			form.base_fields['ident_hash'] = CZBirthNumberField(label=_('Identification number'), widget=form.base_fields['ident_hash'].widget)
		return form

admin.site.register(Patient, PatientAdmin)

class VisitTemplateAdmin(admin.ModelAdmin):
	list_display = ("__unicode__", "office", "starting_time", "valid_since", "valid_until", "authenticated_only")
	list_filter = ("office", "day", "starting_time", filters.ExpirationFilter)
	ordering = ("day", "starting_time", "office")

admin.site.register(Visit_template, VisitTemplateAdmin)

class VisitReservationExceptionAdmin(admin.ModelAdmin):
	list_display = ("begin", "end", "office")
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
admin.site.register(Medical_office, MedicalOfficeAdmin)


admin.site.unregister(Site)

# register filters
admin.FieldListFilter.register(lambda f: f and isinstance(f, models.TimeField), filters.TimeRangeFilter, True)
admin.FieldListFilter.register(lambda f: f and isinstance(f, models.DateField), filters.DateRangeFilter, True)
