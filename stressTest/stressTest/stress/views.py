"""Show UI for collecting stress test data based on forms.py."""


from django.conf import settings
from django.shortcuts import redirect
from .forms import sftpForm
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
import sys
import os

sys.path.insert(1, os.path.join(settings.BASE_DIR.parent.parent, 'tools'))  # nopep8
from sftp import sftp  # nopep8

is_connected = False


def index(request):
    """Render the index page."""
    if request.method == "POST":
        form = sftpForm(request.POST)
        if form.is_valid():
            sftp_url = form.cleaned_data['sftp_url']
            sftp_port = form.cleaned_data['sftp_port']
            sftp_username = form.cleaned_data['sftp_username']
            sftp_password = form.cleaned_data['sftp_password']
            dummy_amount = form.cleaned_data['dummy_amount']
            print(
                f"Connection URL: {sftp_url}, Port: {sftp_port}, Username: {sftp_username}, Password: {sftp_password}, Number of Dummy Files: {dummy_amount}")

            master = sftp(hostname=sftp_url, port=sftp_port,
                          username=sftp_username, password=sftp_password)
            try:
                master.connect()
                print(f"Connected to {sftp_url} as {sftp_username}.")
                global is_connected
                is_connected = True
            except Exception as ex:
                print(f'Connect to Master error: {ex}')
            # return redirect(request.META.get('HTTP_REFERER'))

    else:
        form = sftpForm()

    return render(request, 'index.html', {'form': form})


def check_connection_status(request):
    print(is_connected)
    return JsonResponse({'is_connected': is_connected})
