from hashlib import sha1
from datetime import datetime
from datetime import date as dt_date
from datetime import time as dt_time
from datetime import timedelta as dt_timedelta

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class Patient(models.Model):
	first_name = models.CharField(_("first name"), max_length=100)
	last_name = models.CharField(_("last name"), max_length=100)
	ident_hash = models.CharField(_("identify hash"), max_length=128, unique=True)
	phone_number = models.CharField(_("phone number"), max_length=100)
	email = models.EmailField(_("e-mail"), blank=True)

	class Meta:
		verbose_name = _("patient")
		verbose_name_plural = _("patients")

	@staticmethod
	def get_ident_hash(ident_string):
		return sha1(settings.SECRET_KEY + ident_string).hexdigest()

	def __unicode__(self):
		return self.full_name
		
	def _get_full_name(self):
		"Returns the person's full name. Last name first."
		return "%s %s" % (self.last_name, self.first_name)
	full_name = property(_get_full_name)

	def actual_reservations(self):
		current_time = datetime.now()
		q = Q(date=current_time.date(), time__gte=dt_time(current_time.hour, current_time.minute)) | Q(date__gt=current_time.date())
		return self.visit_reservations.filter(q)

	def has_reservation(self):
		return self.actual_reservations().exists()
	has_reservation.boolean = True

	def save(self, *args, **kwargs):
		if not self.id:
			self.ident_hash = self.get_ident_hash(self.ident_hash)
		super(Patient, self).save(*args, **kwargs)

class Office(models.Model):
	name = models.CharField(_("name"), max_length=100, unique=True)
	street = models.TextField(_("street"))
	zip_code = models.CharField(_("zip code"), max_length=20)
	city = models.CharField(_("city"), max_length=100)
	email = models.EmailField(_("e-mail"), blank=True)
	order = models.PositiveIntegerField(_("order"), help_text=_("Office order on user page."))
	public = models.BooleanField(_("public"),
		help_text=_("Check if you want to make this office to be visible on user page without authentication."))
	published = models.BooleanField(_("published"), default=True,
		help_text=_("Check if you want to make this office to be published."))
	days_to_generate = models.PositiveSmallIntegerField(_("days to generate"), default=7, help_text=_("Number of days to generate reservations."))
	note = models.TextField(_("note"), blank=True)

	class Meta:
		verbose_name = _("office")
		verbose_name_plural = _("offices")
		ordering = ("order",)

	def __unicode__(self):
		return self.name

	def reservations(self, for_date):
		""" Returns all reservations in office for selected day. """
		return self.visit_reservations.filter(date=for_date).order_by("time")

	def days_status(self, start_date, end_date):
		""" Returns dict with day and status for day from start date to end date. """
		days = self.visit_reservations.filter(date__range=(start_date, end_date)).dates("date", "day")
		return dict([(self._date2str(day), True) for day in days])

	def _date2str(self, actual_date):
		""" Returns date as string yyyy-m-d (without leading zeros in month and day. """
		return "%d-%d-%d" % (
				int(actual_date.strftime("%Y")),
				int(actual_date.strftime("%m")),
				int(actual_date.strftime("%d")),
			)

	def _get_first_day(self, dt, d_years=0, d_months=0):
		# d_years, d_months are "deltas" to apply to dt
		y, m = dt.year + d_years, dt.month + d_months
		a, m = divmod(m-1, 12)
		return dt_date(y+a, m+1, 1)

	def _get_last_day(self, dt):
		return self._get_first_day(dt, 0, 1) + dt_timedelta(-1)

class Office_phone(models.Model):
	number = models.CharField(_("number"), max_length=50)
	office = models.ForeignKey(Office, verbose_name=_("office"),
			related_name="phone_numbers")

	class Meta:
		verbose_name = _("office phone")
		verbose_name_plural = _("office phones")

	def __unicode__(self):
		return self.number

class Visit_template(models.Model):
	DAYS = (
		(1, _("Monday")),
		(2, _("Tuesday")),
		(3, _("Wednesday")),
		(4, _("Thursday")),
		(5, _("Friday")),
		(6, _("Saturday")),
		(7, _("Sunday")),
	)
	office = models.ForeignKey(Office, verbose_name=_("office"),
			related_name="templates")
	day = models.PositiveSmallIntegerField(_("week day"), choices=DAYS)
	starting_time = models.TimeField(_("time"))
	valid_since = models.DateField(_("valid since"),
			help_text=_("This date is included into interval."))
	valid_until = models.DateField(_("valid until"), null=True, blank=True,
			help_text=_("This date is not included into interval."))
	authenticated_only = models.BooleanField(_("authenticated only"), default=False,
			help_text=_("If true allow reservation only for authenticated users."))
	note = models.TextField(_("note"), blank=True)

	class Meta:
		verbose_name = _("template")
		verbose_name_plural = _("templates")
		unique_together = (("office", "day", "starting_time"),)

	def __unicode__(self):
		return unicode(_(u"{0} at {1}".format(self.get_day_display(), self.starting_time)))

class Visit_reservation_exception(models.Model):
	title = models.CharField(_("title"), max_length=255, blank=True)
	office = models.ForeignKey(Office, verbose_name=_("office"),
			related_name="disables")
	begin = models.DateTimeField(_("begin"),
			help_text=_("This date is included into interval."))
	end = models.DateTimeField(_("end"),
			help_text=_("This date is included into interval."))
	note = models.TextField(_("note"), blank=True)

	class Meta:
		verbose_name = _("exception")
		verbose_name_plural = _("exceptions")
		unique_together = (("office", "begin", "end"),)

	def __unicode__(self):
		return unicode(_(u"{0} (from {1} to {2})".format(self.title, self.begin, self.end)))

	def covers_reservation_time(self, reservation_time):
		return self.begin <= reservation_time and self.end > reservation_time

	def disabled_reservations_filter(self):
		days = (self.end.date() - self.begin.date()).days
		if days == 0:
			return Q(office=self.office, date=self.begin.date(), time__gte=self.begin.time(), time__lt=self.end.time())
		elif days == 1:
			return Q(
				office=self.office, date=self.begin.date(), time__gte=self.begin.time()) | Q(
				office=self.office, date=self.end.date(), time__lt=self.end.time())
		else:
			return Q(
				office=self.office, date=self.begin.date(), time__gte=self.begin.time()) | Q(
				office=self.office, date__gt=self.begin.date(), date__lt=self.end.date()) | Q(
				office=self.office, date=self.end.date(), time__lt=self.end.time())

class Examination_kind(models.Model):
	title = models.TextField(_("title"))
	office = models.ForeignKey(Office, verbose_name=_("office"),
		related_name="exam_kinds")
	order = models.PositiveIntegerField(_("order"), help_text=_("Order of examination kinds."))
	note = models.TextField(_("note"), blank=True)

	class Meta:
		verbose_name = _("examination kind")
		verbose_name_plural = _("examinations kinds")
		ordering = ("order",)

	def __unicode__(self):
		return self.title

class Visit_reservation(models.Model):
	STATUS_DISABLED = 1
	STATUS_ENABLED = 2
	STATUS_IN_HELD = 4
	STATUS_CHOICES = (
		(1, _("disabled")),
		(2, _("enabled")),
		(4, _("hold")),
	)
	STATUS_RESERVED = 3
	STATUS_RESCHEDULE = 5

	date = models.DateField(_("date"))
	time = models.TimeField(_("time"))
	office = models.ForeignKey(Office, verbose_name=_("office"),
			related_name="visit_reservations")
	authenticated_only = models.BooleanField(_("authenticated only"),
			help_text=_("If true allow reservation only for authenticated users."))
	patient = models.ForeignKey(Patient, verbose_name=_("patient"), null=True, blank=True,
			related_name="visit_reservations")
	exam_kind = models.ForeignKey(Examination_kind, verbose_name=_("examination kind"),
			null=True, blank=True)
	status = models.PositiveSmallIntegerField(_("status"), default=2, choices=STATUS_CHOICES)
	reservation_time = models.DateTimeField(_("reservation time"), null=True, blank=True)
	reserved_by = models.CharField(_("reserved by"), max_length=100, blank=True)

	class Meta:
		verbose_name = _("reservation")
		verbose_name_plural = _("reservations")
		ordering = ("-date", "-time")
		unique_together = ("date", "time", "office")

	def __unicode__(self):
		return u"{0} - {1}".format(self.starting_time.strftime("%H:%M - %d.%m.%Y"), self.office.name)

	@property
	def passed(self):
		return self.starting_time < datetime.now()
	@property
	def starting_time(self):
		return datetime(self.date.year, self.date.month, self.date.day, self.time.hour, self.time.minute)

	@property
	def reschedule_required(self):
		if self.patient is None:
			return False
		elif self.status == Visit_reservation.STATUS_DISABLED:
			return True

		status = self.status
		exceptions = list(Visit_reservation_exception.objects.filter(office=self.office))
		for exception in exceptions:
			if exception.covers_reservation_time(self.starting_time):
				return True

		return False

	def unbook(self):
		if self.status != self.STATUS_DISABLED:
			self.status = self.STATUS_ENABLED
		self.patient = None
		self.exam_kind = None
		self.reservation_time = None
		self.reserved_by = ""

	@staticmethod
	def compute_actual_status(reservations):
		exceptions = list(Visit_reservation_exception.objects.all())
		for obj in reservations:
			status = obj.status
			if status != Visit_reservation.STATUS_DISABLED:
				starting_time = obj.starting_time
				for exception in exceptions:
					if exception.office == obj.office and exception.covers_reservation_time(starting_time):
						status = Visit_reservation.STATUS_DISABLED
						break
			if obj.patient is not None:
				if status == Visit_reservation.STATUS_ENABLED:
					status = Visit_reservation.STATUS_RESERVED
				elif status == Visit_reservation.STATUS_DISABLED:
					status = Visit_reservation.STATUS_RESCHEDULE
			obj.actual_status = status
		return reservations


class Command(models.Model):
	name = models.CharField(_("name"), max_length=100, unique=True)
	user = models.CharField(_("user"), max_length=100)
	start_time = models.DateTimeField(_("start time"))
	is_running = models.BooleanField(_("is running"), default=False)

	@classmethod
	@transaction.atomic
	def lock(cls, command_name, user_name):
		command, created = cls.objects.get_or_create(
			name=command_name,
			defaults={
				"is_running": True,
				"user": user_name,
				"start_time": datetime.now()
			}
		)
		if not created:
			if command.is_running:
				return False
			command.is_running = True
			command.user = user_name
			command.start_time = datetime.now()
			command.save()
		return True

	@classmethod
	@transaction.atomic
	def unlock(cls, command_name):
		try:
			command = cls.objects.get(name=command_name)
			if command.is_running:
				command.is_running = False
				command.save()
		except cls.DoesNotExist:
			pass

	@classmethod
	def is_locked(cls, command_name):
		return cls.objects.filter(name=command_name, is_running=True).exists()

# vim: set ts=4 sts=4 sw=4 noet:
