"""Show UI for collecting stress test data based on forms.py."""


from django.conf import settings
from django.shortcuts import redirect
from .forms import sftpForm, dummycountForm
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
import sys
import os
from stressTest.settings import sftp_folders
from celery import shared_task
from .dummyFiles import writeDummyFiles
from random import randint

sys.path.insert(1, os.path.join(settings.BASE_DIR.parent.parent, 'tools'))  # nopep8
from sftp import sftp  # nopep8


def index(request):
    """Render the index page."""
    global is_work
    global sftp_url
    global sftp_port
    global sftp_username
    global sftp_password
    sftp_url = None
    sftp_port = None
    sftp_username = None
    sftp_password = None

    is_work = False
    sftpform = sftpForm()
    dummyform = dummycountForm()

    if request.method == "POST":
        sftpform = sftpForm(request.POST)
        # dummyform = dummycountForm(request.POST)
        if sftpform.is_valid():
            sftp_url = sftpform.cleaned_data['sftp_url']
            sftp_port = sftpform.cleaned_data['sftp_port']
            sftp_username = sftpform.cleaned_data['sftp_username']
            sftp_password = sftpform.cleaned_data['sftp_password']
            # dummy_amount = form.cleaned_data['dummy_amount']
            print(
                f'Connection URL: {sftp_url}, Port: {sftp_port}, Username: {sftp_username}, Password: {sftp_password}')

            master = sftp(hostname=sftp_url, port=sftp_port,
                          username=sftp_username, password=sftp_password)
            try:
                master.connect()
                print(f"Connected to {sftp_url} as {sftp_username}.")
                is_work = True
            except Exception as ex:
                print(f'Connect to Master error: {ex}')
                is_work = False
            finally:
                master.disconnect()
            # return redirect(request.META.get('HTTP_REFERER'))

    return render(request, 'index.html', {'sftpform': sftpform, 'dummyform': dummyform})


def check_connection_status(request):
    global is_work
    return JsonResponse({'is_work': is_work})


# @shared_task
def do_work(count, sftp_url, sftp_port, sftp_username, sftp_password, progress_observer):
    for i in range(count):

        if not writeDummyFiles(sftp_folders[randint(0, len(sftp_folders)-1)], sftp_url, sftp_port, sftp_username, sftp_password):
            return False
        progress_observer.set_progress(i, count)
    return True


def do_test(request):
    if request.method == "GET":
        dummyform = dummycountForm(request.GET)
        if dummyform.is_valid():
            dummy_amount = dummyform.cleaned_data['dummy_amount']
            if sftp_url != None and sftp_port != None and sftp_username != None and sftp_password != None:
                print(
                    f'Prepare to upload {dummy_amount} files to {sftp_url}')
                # if do_work.delay(dummy_amount, sftp_url, sftp_port, sftp_username, sftp_password):
                if do_work(dummy_amount, sftp_url, sftp_port, sftp_username, sftp_password):
                    return HttpResponse('Success')
            else:
                return HttpResponse('Failed because of missing connection data')
