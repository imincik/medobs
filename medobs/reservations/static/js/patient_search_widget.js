(function($) {

	$(document).ready(function () {
		// handle creating of new patients from popup window
		// (wrap dismissAddRelatedObjectPopup function defined in RelatedObjectLookups.js)
		var dismissAddRelatedObjectPopupOrig = window.dismissAddRelatedObjectPopup;
		window.dismissAddRelatedObjectPopup = function(win, newId, newRepr) {
			newId = html_unescape(newId);
			newRepr = html_unescape(newRepr);
			var name = windowname_to_id(win.name);
			var elem = document.getElementById(name);
			if (name === 'id_patient') {
				django.jQuery('#id_patient').val(newId);
				django.jQuery('#id_patient_label').val(newRepr);
				win.close();
			} else {
				dismissAddRelatedObjectPopupOrig(win, newId, newRepr);
			}
		};

		// code source: http://docs.djangoproject.com/en/1.8/ref/contrib/csrf/
		function getCookie(name) {
			var cookieValue = null;
			if (document.cookie && document.cookie != '') {
				var cookies = document.cookie.split(';');
				for (var i = 0; i < cookies.length; i++) {
					var cookie = $.trim(cookies[i]);
					// Does this cookie string begin with the name we want?
					if (cookie.substring(0, name.length + 1) == (name + '=')) {
						cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
						break;
					}
				}
			}
			return cookieValue;
		}
		function csrfSafeMethod(method) {
			// these HTTP methods do not require CSRF protection
			return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
		}
		$.ajaxSetup({
			beforeSend: function(xhr, settings) {
				var csrftoken = getCookie('csrftoken');
				if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
					xhr.setRequestHeader("X-CSRFToken", csrftoken);
				}
			}
		});

		$("#patient_search").click(function() {
			var ident_number = $("#id_patient_ident").val();
			$("#id_patient_search_error").hide();
			if(ident_number != "") {
				$.post("/patient/", {ident_hash: ident_number}, function(data) {
					if(data.pk) {
						$("#id_patient").val(data.pk);
						$("#id_patient_label").val(data.last_name+" "+data.first_name);
					} else {
						$("#id_patient_search_error").show();
					}
				});
			}
		});
		$("#patient_clear").click(function() {
			$("#id_patient").val('');
			$("#id_patient_label").val('');
		});
	});
})(django.jQuery);