from django.contrib import admin
from djcode.reservations.models import Examination_kind, Medical_office, Office_phone, Patient
from djcode.reservations.models import Visit_disable_rule, Visit_reservation, Visit_template

class Visit_reservation_Admin(admin.ModelAdmin):
	list_display = ("starting_time", "place", "status")
	list_filter = ("status", "place", "starting_time")
admin.site.register(Visit_reservation, Visit_reservation_Admin)

class Patient_Admin(admin.ModelAdmin):
	list_display = ("full_name", "phone_number", "email", "ident_hash", "has_reservation")
	search_fields = ("last_name",)
admin.site.register(Patient, Patient_Admin)

class Visit_template_Admin(admin.ModelAdmin):
	list_display = ("__unicode__", "place", "valid_since", "valid_until")
	list_filter = ("place", "day")
admin.site.register(Visit_template, Visit_template_Admin)

class Visit_disable_rule_Admin(admin.ModelAdmin):
	list_display = ("begin", "end", "place")
	list_filter = ("place", "begin")
admin.site.register(Visit_disable_rule, Visit_disable_rule_Admin)

class Office_phone_Inline(admin.TabularInline):
    model = Office_phone

class Medical_office_Admin(admin.ModelAdmin):
	list_display = ("name", "street", "zip_code", "city", "email", "public")
	inlines = [Office_phone_Inline,]
	ordering = ["id",]
admin.site.register(Medical_office, Medical_office_Admin)

admin.site.register(Examination_kind)
