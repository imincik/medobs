from django.conf import settings

from medobs import VERSION


_MEDOBS_VERSION = ".".join(map(str, VERSION))

def version(request):
	return {"VERSION": _MEDOBS_VERSION}


def datepicker_i18n_file(request):
	return {"DATEPICKER_I18N_FILE": settings.DATEPICKER_I18N_FILE}


# vim: set ts=4 sts=4 sw=4 noet:
