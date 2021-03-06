# -*- coding: utf-8 -*-

import datetime

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import AdminDateWidget
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from medobs.reservations.models import Reservation, Reservation_exception


class ActiveReservationFilter(SimpleListFilter):
	title = _("active reservation")
	parameter_name = 'active_reservation'

	def lookups(self, request, model_admin):
		return (
			('yes', _('Yes')),
			('no', _('No')),
		)

	def queryset(self, request, queryset):
		current_time = datetime.datetime.now()
		q = Q(visit_reservations__date=current_time.date(), visit_reservations__time__gte=current_time.time()) \
			| Q(visit_reservations__date__gt=current_time.date())

		if self.value() == 'yes':
			return queryset.filter(q).distinct()
		elif self.value() == 'no':
			return queryset.exclude(q)

class ExpirationFilter(SimpleListFilter):
	title = _("expiration")
	parameter_name = 'expiration'

	def lookups(self, request, model_admin):
		return (
			('1', _('Not expirated')),
			('2', _('Expirated')),
		)

	def queryset(self, request, queryset):
		today = datetime.date.today()
		if self.value() == '1':
			return queryset.filter(
				Q(valid_since__lte=today)
				& (
					Q(valid_until__gte=today)
					| Q(valid_until__isnull=True)
				)
			)
		elif self.value() == '2':
			return queryset.filter(valid_until__lt=today)


class ReservationStatusFilter(SimpleListFilter):
	title = _("availability")
	parameter_name = 'availability'

	def lookups(self, request, model_admin):
		return (
			('1', _('Available')),
			('2', _('Reservated')),
			('3', _('Hold')),
			('4', _('Reschedule')),
			('5', _('Disabled')),
		)

	def queryset(self, request, queryset):
		disabled_query = Q(status=Reservation.STATUS_DISABLED)
		for exception in Reservation_exception.objects.all():
			q = exception.disabled_reservations_filter()
			disabled_query = disabled_query | q

		if self.value() == '1':
			return queryset.filter(status=Reservation.STATUS_ENABLED, patient__isnull=True).exclude(disabled_query)
		elif self.value() == '2':
			return queryset.filter(patient__isnull=False).exclude(disabled_query)
		elif self.value() == '3':
			return queryset.exclude(disabled_query).filter(status=Reservation.STATUS_IN_HELD)
		elif self.value() == '4':
			return queryset.filter(patient__isnull=False).filter(disabled_query)
		elif self.value() == '5':
			return queryset.filter(patient__isnull=True).filter(disabled_query)


class DateRangeForm(forms.Form):

	def __init__(self, *args, **kwargs):
		field_name = kwargs.pop('field_name')
		data = kwargs.get('data', {})
		super(DateRangeForm, self).__init__(*args, **kwargs)

		self.fields['%s__gte' % field_name] = forms.DateField(
			label=_('From'),
			localize=True,
			required=False,
			widget=AdminDateWidget(
				attrs={'placeholder': ''}
			)
		)

		self.fields['%s__lte' % field_name] = forms.DateField(
			label=_('To'),
			localize=True,
			required=False,
			widget=AdminDateWidget(
				attrs={'placeholder': ''}
			)
		)

		for param_name, value in data.iteritems():
			if param_name not in self.fields.keys():
				self.fields[param_name] = forms.CharField(
					required=False,
					widget=forms.HiddenInput()
				)

	class Media:
		css = {
			'all': ('%sadmin/css/widgets.css' % settings.STATIC_URL, )
		}
         

class DateRangeFilter(admin.filters.FieldListFilter):
	template = 'admin/date_filter.html'

	def __init__(self, field, request, params, model, model_admin, field_path):
		self.lookup_kwarg_since = '%s__gte' % field_path
		self.lookup_kwarg_upto = '%s__lte' % field_path
		super(DateRangeFilter, self).__init__(
			field, request, params, model, model_admin, field_path)

	def choices(self, cl):
		since_lookup = self.used_parameters.get(self.lookup_kwarg_since)
		upto_lookup = self.used_parameters.get(self.lookup_kwarg_upto)
		form = self.get_form(cl, clear_fields=False)
		form.is_valid()
		since_value = form.cleaned_data.get(self.lookup_kwarg_since)
		upto_value = form.cleaned_data.get(self.lookup_kwarg_upto)

		today = datetime.date.today()
		tomorrow = today + datetime.timedelta(days=1)
		week_end = today + datetime.timedelta(days=7-today.weekday()-1)
		if today.month == 12:
			next_month = today.replace(year=today.year + 1, month=1, day=1)
		else:
			next_month = today.replace(month=today.month + 1, day=1)
		next_month = next_month-datetime.timedelta(days=1)

		yield {
			'selected': since_value is None and upto_value is None,
			'query_string': cl.get_query_string({}, [self.lookup_kwarg_since, self.lookup_kwarg_upto]),
			'display': _('Any date')
		}
		since_today_selected = since_value == today and upto_value is None
		yield {
			'selected': since_today_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: today,
				self.lookup_kwarg_upto: None
			}, []),
			'display': _('Since today')
		}
		today_selected = since_value == today and upto_value == today
		yield {
			'selected': today_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: today,
				self.lookup_kwarg_upto: today
			}, []),
			'display': _('Today')
		}
		tomorrow_selected = since_value == tomorrow and upto_value == tomorrow
		yield {
			'selected': tomorrow_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: tomorrow,
				self.lookup_kwarg_upto: tomorrow
			}, []),
			'display': _('Tomorrow')
		}
		this_week_selected = since_value == today and upto_value == week_end
		yield {
			'selected': this_week_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: today,
				self.lookup_kwarg_upto: week_end
			}, []),
			'display': _('This week')
		}
		this_month_selected = since_value == today and upto_value == next_month
		yield {
			'selected': this_month_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: today,
				self.lookup_kwarg_upto: next_month
			}, []),
			'display': _('This month')
		}
		custom_range_selected = \
			not since_today_selected \
			and not today_selected \
			and not tomorrow_selected \
			and not this_week_selected \
			and not this_month_selected \
			and (since_value or upto_value)
		self.form = self.get_form(cl, clear_fields=(not custom_range_selected))
		yield {
			'selected': custom_range_selected,
			'query_string': '',
			'display':
				_('From {0} to {1}').format(since_lookup, upto_lookup) if custom_range_selected else
				_('In range'),
			'form': self.form
		}

	def expected_parameters(self):
		return [self.lookup_kwarg_since, self.lookup_kwarg_upto]

	def get_form(self, cl, clear_fields=True):
		data = dict(cl.params)
		if clear_fields and self.used_parameters.get(self.lookup_kwarg_since):
			data.pop(self.lookup_kwarg_since)
			data.pop(self.lookup_kwarg_upto, None)
		return DateRangeForm(data=data, field_name=self.field_path)

	def queryset(self, request, queryset):
		# Get form with only filter's parameters
		form = DateRangeForm(data=self.used_parameters, field_name=self.field_path)
		if form.is_valid():
			# get no null params
			filter_params = dict(filter(lambda x: bool(x[1]), form.cleaned_data.items()))
			if self.lookup_kwarg_upto in filter_params and self.lookup_kwarg_since not in filter_params:
				q = Q(**filter_params) \
					| Q(**{'{0}__isnull'.format(self.field_path): True})
				return queryset.filter(q)
			return queryset.filter(**filter_params)
		else:
			return queryset


class TimeRangeForm(forms.Form):

	def __init__(self, *args, **kwargs):
		field_name = kwargs.pop('field_name')
		data = kwargs.get('data', {})
		super(TimeRangeForm, self).__init__(*args, **kwargs)
		
		self.fields['%s__gte' % field_name] = forms.TimeField(
			label=_('From'),
			localize=True,
			required=False,
			widget=forms.TimeInput(
				format='%H:%M',
				attrs={'placeholder': ''}
			)
		)

		self.fields['%s__lte' % field_name] = forms.TimeField(
			label=_('To'),
			localize=True,
			required=False,
			widget=forms.TimeInput(
				format='%H:%M',
				attrs={'placeholder': ''}
			)
		)

		for param_name, value in data.iteritems():
			if param_name not in self.fields.keys():
				self.fields[param_name] = forms.CharField(
					required=False,
					widget=forms.HiddenInput()
				)

class TimeRangeFilter(admin.filters.FieldListFilter):
	template = 'admin/time_filter.html'

	def __init__(self, field, request, params, model, model_admin, field_path):
		self.lookup_kwarg_since = '%s__gte' % field_path
		self.lookup_kwarg_upto = '%s__lte' % field_path
		super(TimeRangeFilter, self).__init__(field, request, params, model, model_admin, field_path)

	def choices(self, cl):
		
		since_lookup = self.used_parameters.get(self.lookup_kwarg_since)
		upto_lookup = self.used_parameters.get(self.lookup_kwarg_upto)

		since_value = datetime.time(*map(int, since_lookup.split(":"))) if since_lookup else None
		upto_value = datetime.time(*map(int, upto_lookup.split(":"))) if upto_lookup else None

		midday = datetime.time(12, 0)
		afternoon = datetime.time(23, 59)

		yield {
			'selected': since_lookup is None and upto_lookup is None,
			'query_string': cl.get_query_string({}, [self.lookup_kwarg_since, self.lookup_kwarg_upto]),
			'display': _('Any time')
		}
		morning_selected = since_value == datetime.time(0, 0) and upto_value == midday
		yield {
			'selected': morning_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: datetime.time(0, 0),
				self.lookup_kwarg_upto: midday
			}, []),
			'display': _('Morning')
		}
		afternoon_selected = since_value == midday and upto_value == afternoon
		yield {
			'selected': afternoon_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: midday,
				self.lookup_kwarg_upto: afternoon
			}, []),
			'display': _('Afternoon')
		}
		custom_range_selected = \
			not morning_selected \
			and not afternoon_selected \
			and (since_lookup or upto_lookup)
		self.form = self.get_form(cl, clear_fields=(not custom_range_selected))
		yield {
			'selected': custom_range_selected,
			'query_string': '',#'javascript:django.jQuery("form#id_{0}").submit();'.format(self.field.name),
			'display':
				_('From {0} to {1}').format(since_lookup, upto_lookup) if custom_range_selected else
				_('In range'),
			'form': self.form
		}

	def expected_parameters(self):
		return [self.lookup_kwarg_since, self.lookup_kwarg_upto]

	def get_form(self, cl, clear_fields=True):
		data = dict(cl.params)
		if clear_fields and self.used_parameters.get(self.lookup_kwarg_since):
			data.pop(self.lookup_kwarg_since)
			data.pop(self.lookup_kwarg_upto, None)
		return TimeRangeForm(data=data, field_name=self.field_path)

	def queryset(self, request, queryset):
		# Get form with only filter's parameters
		form = TimeRangeForm(data=self.used_parameters, field_name=self.field_path)
		if form.is_valid():
			# get no null params
			filter_params = dict(filter(lambda x: bool(x[1]), form.cleaned_data.items()))
			if self.lookup_kwarg_upto in filter_params and self.lookup_kwarg_since not in filter_params:
				q = Q(**filter_params) \
					| Q(**{'{0}__isnull'.format(self.field_path): True})
				return queryset.filter(q)
			return queryset.filter(**filter_params)
		else:
			return queryset



class ReservationExceptionDateFilter(admin.filters.ListFilter):
	template = 'admin/date_filter.html'
	title = _('Range')

	def __init__(self, request, params, model, model_admin):
		super(ReservationExceptionDateFilter, self).__init__(request, params, model, model_admin)
		self.lookup_kwarg_since = 'filter__gte'
		self.lookup_kwarg_upto = 'filter__lte'
		if self.lookup_kwarg_since in params:
			self.used_parameters[self.lookup_kwarg_since] = params.pop(self.lookup_kwarg_since)
		if self.lookup_kwarg_upto in params:
			self.used_parameters[self.lookup_kwarg_upto] = params.pop(self.lookup_kwarg_upto)

	def has_output(self):
		return True

	def choices(self, cl):
		since_lookup = self.used_parameters.get(self.lookup_kwarg_since)
		upto_lookup = self.used_parameters.get(self.lookup_kwarg_upto)
		form = self.get_form(cl, clear_fields=False)
		form.is_valid()
		since_value = form.cleaned_data.get(self.lookup_kwarg_since)
		upto_value = form.cleaned_data.get(self.lookup_kwarg_upto)

		today = datetime.date.today()
		tomorrow = today + datetime.timedelta(days=1)
		week_end = today + datetime.timedelta(days=7-today.weekday()-1)
		if today.month == 12:
			next_month = today.replace(year=today.year + 1, month=1, day=1)
		else:
			next_month = today.replace(month=today.month + 1, day=1)
		next_month = next_month-datetime.timedelta(days=1)

		yield {
			'selected': since_value is None and upto_value is None,
			'query_string': cl.get_query_string({}, [self.lookup_kwarg_since, self.lookup_kwarg_upto]),
			'display': _('Any date')
		}
		today_selected = since_value == today and upto_value == today
		yield {
			'selected': today_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: today,
				self.lookup_kwarg_upto: today
			}, []),
			'display': _('Today')
		}
		tomorrow_selected = since_value == tomorrow and upto_value == tomorrow
		yield {
			'selected': tomorrow_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: tomorrow,
				self.lookup_kwarg_upto: tomorrow
			}, []),
			'display': _('Tomorrow')
		}
		this_week_selected = since_value == today and upto_value == week_end
		yield {
			'selected': this_week_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: today,
				self.lookup_kwarg_upto: week_end
			}, []),
			'display': _('This week')
		}
		this_month_selected = since_value == today and upto_value == next_month
		yield {
			'selected': this_month_selected,
			'query_string': cl.get_query_string({
				self.lookup_kwarg_since: today,
				self.lookup_kwarg_upto: next_month
			}, []),
			'display': _('This month')
		}
		custom_range_selected = \
			not today_selected \
			and not tomorrow_selected \
			and not this_week_selected \
			and not this_month_selected \
			and (since_value or upto_value)
		self.form = self.get_form(cl, clear_fields=(not custom_range_selected))
		yield {
			'selected': custom_range_selected,
			'query_string': '',
			'display':
				_('From {0} to {1}').format(since_lookup, upto_lookup) if custom_range_selected else
				_('In range'),
			'form': self.form
		}

	def expected_parameters(self):
		return [self.lookup_kwarg_since, self.lookup_kwarg_upto]

	def get_form(self, cl, clear_fields=True):
		data = dict(cl.params)
		if clear_fields and data.get(self.lookup_kwarg_since):
			data.pop(self.lookup_kwarg_since)
			data.pop(self.lookup_kwarg_upto, None)
		return DateRangeForm(data=data, field_name='filter')

	def queryset(self, request, queryset):
		# Get form with only filter's parameters
		form = DateRangeForm(data=self.used_parameters, field_name='filter')
		if form.is_valid():
			since = form.cleaned_data[self.lookup_kwarg_since]
			upto = form.cleaned_data.get(self.lookup_kwarg_upto)
			if since and upto:
				return queryset.exclude(begin__gt=upto, end__lt=since)
			elif since:
				return queryset.exclude(end__lt=since)
		else:
			return queryset

# vim: set ts=4 sts=4 sw=4 noet:
