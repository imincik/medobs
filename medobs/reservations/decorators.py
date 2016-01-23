import os
import multiprocessing
from functools import wraps

from django.utils.decorators import available_attrs
from django.core.management.base import CommandError
from django.http import HttpResponse

from medobs.reservations.models import Command


class Process(object):
	def __init__(self, target=None, args=None):
		self.target = target
		self.args = args


def async_task(command):
	def decorator(func):
		@wraps(func, assigned=available_attrs(func))
		def _wrapped_func(*args, **kwargs):
			try:
				func(*args, **kwargs)
			finally:
				Command.unlock(command)
		return _wrapped_func
	return decorator


def view_async_task(command):
	def decorator(view_func):
		@wraps(view_func, assigned=available_attrs(view_func))
		def _wrapped_view(request, *args, **kwargs):
			if Command.lock(command, request.user.get_full_name()):
				process, response = view_func(request, *args, **kwargs)
				multiprocessing.Process(
					target=async_task(command)(process.target),
					args=process.args
				).start()
				return response
			else:
				return HttpResponse(status=503)
			
		return _wrapped_view
	return decorator

def command_task(command):
	def decorator(func):
		@wraps(func, assigned=available_attrs(func))
		def _wrapped_func(*args, **kwargs):
			user = os.environ.get('USER', '')
			try:
				if Command.lock(command, user):
					return func(*args, **kwargs)
				else:
					raise CommandError("Command is already running.")
			finally:
				Command.unlock(command)
			
		return _wrapped_func
	return decorator