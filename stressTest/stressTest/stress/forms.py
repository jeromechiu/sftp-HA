
from django import forms


class sftpForm(forms.Form):
    """
    A form for configuring SFTP connection details.

    Attributes:
        sftp_url (CharField): The SFTP URL.
        sftp_port (IntegerField): The SFTP port.
        sftp_username (CharField): The SFTP username.
        sftp_password (CharField): The SFTP password.
    """
    sftp_url = forms.CharField(
        label='SFTP URL: ', max_length=100, initial='10.65.11.180')
    sftp_port = forms.IntegerField(label='SFTP Port:', initial=2222)
    sftp_username = forms.CharField(
        label='SFTP Username: ', max_length=100, initial='EPuser')
    sftp_password = forms.CharField(
        label='SFTP Password: ', max_length=100, initial=1234)


class dummycountForm(forms.Form):
    """
    A form for specifying the number of dummy files.

    Attributes:
        dummy_amount (IntegerField): The number of dummy files.
    """
    dummy_amount = forms.IntegerField(
        label='Number of Dummy Files:', initial=2, max_value=1000, min_value=1)
