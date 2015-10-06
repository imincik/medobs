from django import forms
from django.forms.widgets import Media
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.templatetags.admin_static import static
from localflavor.cz.forms import CZBirthNumberField

from medobs.reservations.models import Examination_kind, Patient, Reservation


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
		error_messages={"invalid": _(u"Enter a valid phone number containing numbers only.")}
	)
	reservation = forms.ModelChoiceField(
		queryset=Reservation.objects.all(),
		widget=forms.HiddenInput(),
		error_messages={"required": _("Select reservation time")}
	)
	exam_kind = forms.ModelChoiceField(
		empty_label="----------",
		required=True,
		queryset=Examination_kind.objects.all(),
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


class PatientSearchWidget(forms.Select):
	def label_for_value(self, value):
		if value != '':
			try:
				return unicode(Patient.objects.get(pk=value))
			except Patient.DoesNotExist:
				pass
		return ''

	def render(self, name, value, attrs=None, choices=()):
		if value is None:
			value = ''
		data = {
			'label_attrs': self.build_attrs(id="id_patient_label", value=self.label_for_value(value)),
			'field_attrs': self.build_attrs(attrs, name=name, value=value),
			'search_attrs': self.build_attrs(id="id_patient_ident", type="text")
		}
		return render_to_string("admin/reservations/reservation/patient_search_field.html", data)

	@property
	def media(self):
		media = Media(js=[static('js/patient_search_widget.js')])
		media.add_css({'all': [static('css/patient_search_widget.css')]})
		return media


class ReservationForm(forms.ModelForm):
	time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'))
	class Meta:
		model = Reservation
		exclude = ()
		widgets = {
			'patient': PatientSearchWidget
		}

# vim: set ts=4 sts=4 sw=4 noet:
