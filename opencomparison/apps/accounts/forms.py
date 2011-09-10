from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _

from uni_form.helpers import FormHelper, Submit, Layout, Row

attrs_dict = {'class': 'required'}

class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    """
    username = forms.CharField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=30)),
                                                               label=_("User name"))
    
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_("Email address"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password (again)"))
    
    helper = FormHelper()
    layout = Layout(
        'username',
        'email',
        Row('password1','password2'),
    )
    
    helper.add_layout(layout)

    submit = Submit('register','Register')
    helper.add_input(submit)    

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data
        
    def clean_username(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        if User.objects.filter(username__exact=self.cleaned_data['username']):
            raise forms.ValidationError(_("This username is already in use. Please supply a different username."))
        return self.cleaned_data['username']        
        
    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']