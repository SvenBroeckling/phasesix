from django import forms


class Html5DateTimeInput(forms.DateInput):
    input_type = "datetime"

    def format_value(self, value):
        return value


class Html5DateInput(forms.DateInput):
    input_type = "date"

    def format_value(self, value):
        return value


class BootstrapTextarea(forms.Textarea):
    def __init__(self, attrs=None):
        default_attrs = {"class": "form-control", "style": "height: auto;", "rows": "3"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
