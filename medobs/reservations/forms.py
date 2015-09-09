from django import forms
from django.utils.translation import ugettext_lazy as _
from localflavor.cz.forms import CZBirthNumberField

from medobs.reservations.models import Examination_kind, Patient, Visit_reservation


class PatientForm(forms.ModelForm):
	label_suffix = ":"
	class Meta:
		model = Patient
		exclude = ()

	ident_hash = CZBirthNumberField(label=_("Birth number"))
	phone_number = forms.RegexField(
		label=_("Phone number"),
		min_length=5,
		max_length=100,
		regex = r"\d+",
		error_messages={"invalid": _(u"Enter a valid 'phone number' consisting of numbers only.")}
	)
	reservation = forms.ModelChoiceField(
		queryset=Visit_reservation.objects.all(),
		widget=forms.HiddenInput(),
		error_messages={"required": _("Please select time of visit reservation")}
	)
	exam_kind = forms.ModelChoiceField(
		empty_label=None,
		queryset=Examination_kind.objects.all(),
		widget=forms.RadioSelect(),
		label=_("Examination kind")
	)

	def clean_ident_hash(self):
		data = self.cleaned_data["ident_hash"]
		if data[6] == "/":
			data = data[:6] + data[7:]
		return data

class PatientDetailForm(forms.Form):
	ident_hash = CZBirthNumberField()

	def clean_ident_hash(self):
		data = self.cleaned_data["ident_hash"]
		if data[6] == "/":
			data = data[:6] + data[7:]
		return data

class VisitReservationForm(forms.ModelForm):
	time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'))
	class Meta:
		model = Visit_reservation
		exclude = ()