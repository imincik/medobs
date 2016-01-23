from django.conf import settings

from medobs import VERSION


_MEDOBS_VERSION = ".".join(map(str, VERSION))

def version(request):
	return {"VERSION": _MEDOBS_VERSION}


# vim: set ts=4 sts=4 sw=4 noet:
