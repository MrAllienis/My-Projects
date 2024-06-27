from django import forms

class UpdateItemForm(forms.Form):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 50, 'rows': 5}),
        label='Description'
    )
    price = forms.IntegerField(label='Price')
