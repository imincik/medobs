from django import template

register = template.Library()

@register.filter
def model_filter(apps, arg):
	app_label, model_name = arg.split(".", 1)
	for app in apps:
		if app.get('app_label') == app_label:
			for model in app['models']:
				if model.get('object_name') == model_name:
					return model
	return ''