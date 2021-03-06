#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

	from django.core.management import execute_from_command_line

	execute_from_command_line(sys.argv)

# vim: set ts=4 sts=4 sw=4 noet:
