"""Create a form for input the connection url, port, username, password of sftp, and how many dummy files to be created."""
from django import forms


class sftpForm(forms.Form):
    sftp_url = forms.CharField(
        label='SFTP URL: ', max_length=100, initial='10.65.11.180')
    sftp_port = forms.IntegerField(label='SFTP Port:', initial=2222)
    sftp_username = forms.CharField(
        label='SFTP Username: ', max_length=100, initial='EPuser')
    sftp_password = forms.CharField(
        label='SFTP Password: ', max_length=100, initial=1234)

class dummycountForm(forms.Form):
    dummy_amount = forms.IntegerField(label='Number of Dummy Files:', initial=2, max_value=1000, min_value=1)
