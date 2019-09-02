from typing import Callable, Dict, Optional, Tuple, Type

from django.forms import Form
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormMixin


class FormListView(ListView, FormMixin):

    def get_context_data(self, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = super().get_context_data()
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)


class MultipleFormView(TemplateView):
    """
    Based on https://www.codementor.io/lakshminp/handling-multiple-forms-on-the-same-page-in-django-fv89t2s3j
    """
    initial = {}
    form_classes = {}
    success_urls = {}
    stored = {}
    prefixes = {}
    forms_valid_func = {}
    forms_kwargs_func = {}

    def add_form(self,
                 form_name: str,
                 form_class: Type[Form],
                 valid_func: Optional[Callable[[Form], HttpResponse]] = None,
                 success_url: Optional[str] = None,
                 initial: Optional[dict] = None,
                 prefix: Optional[str] = None,
                 get_kwargs_func: Optional[Callable[[], Tuple[list, dict]]] = None):
        assert valid_func or success_url
        self.form_classes[form_name] = form_class
        if valid_func:
            self.forms_valid_func[form_name] = valid_func
        if success_url:
            self.success_urls[form_name] = success_url
        if initial:
            self.initial[form_name] = initial
        if prefix:
            self.prefixes[form_name] = prefix
        if get_kwargs_func:
            self.forms_kwargs_func[form_name] = get_kwargs_func

    def get_initial(self, form: str) -> dict:
        initial = self.initial.get(form)
        initial = initial if initial else {}
        return {**initial, 'action': form}

    def get_success_url(self, form: str) -> Optional[str]:
        return self.success_urls.get(form)

    def get_prefix(self, form: str) -> Optional[str]:
        return self.prefixes.get(form)

    def get_form_kwargs(self, form: str) -> Tuple[list, dict]:
        kwargs = {
            'initial': self.get_initial(form),
            'prefix': self.get_prefix(form)
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update(self.stored.get(form, {}))
            if self.request.POST['action'] == form:
                post_data = {'data': self.request.POST,
                             'files': self.request.FILES}
                self.stored.update({form: post_data})
                kwargs.update(post_data)
        return [], kwargs

    def get_forms(self) -> Dict[str, Form]:
        forms = {}
        for key, form_class in self.form_classes.items():
            args, kwargs = self.forms_kwargs_func.get(key, self.get_form_kwargs)(key)
            forms[key] = form_class(*args, **kwargs)
        return forms

    def form_valid(self, form: Form, form_name: str) -> HttpResponse:
        valid_method = self.forms_valid_func.get(form_name)
        if valid_method:
            return valid_method(form)
        else:
            return redirect(self.get_success_url(form_name))

    def form_invalid(self, forms: Dict[str, Form]) -> HttpResponse:
        return self.render_to_response(self.get_context_data(forms=forms))

    def get(self, request, *args, **kwargs) -> HttpResponse:
        self.stored = {}
        forms = self.get_forms()
        return self.render_to_response(self.get_context_data(forms=forms))

    def post(self, request, *args, **kwargs) -> HttpResponse:
        form_name = request.POST.get('action')
        forms = self.get_forms()
        form = forms.get(form_name)
        if not form:
            return HttpResponseForbidden()
        elif form.is_valid():
            return self.form_valid(form, form_name)
        else:
            return self.form_invalid(forms)
