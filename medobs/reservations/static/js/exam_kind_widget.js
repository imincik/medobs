(function($) {

	$(document).ready(function () {
		function filter_examinations_kinds() {
			var office_id = $("#id_office").val();
			$('option', $("#id_exam_kind")).each(function() {
				var option = $(this);
				if (option.val() === "" || option.attr('office') == office_id) {
					option.show();
				} else {
					option.hide();
				}
			});
		};
		$("#id_office").change(function() {
			filter_examinations_kinds();
			$("#id_exam_kind").val("");
		});
		filter_examinations_kinds();
	});
})(django.jQuery);