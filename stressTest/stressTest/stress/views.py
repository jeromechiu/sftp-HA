
import os
import sys
import time
from random import randint

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from stressTest.settings import sftp_folders

from stressTest import settings

from .dummyFiles import writeDummyFiles
from .forms import dummycountForm, sftpForm

sys.path.insert(1, os.path.join(settings.BASE_DIR.parent.parent, 'tools'))  # nopep8
from sftp import sftp  # nopep8

is_work = False
done_count = 0
total_count = 0
uploadfile_detail = ""


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
                master.disconnect()
            except Exception as ex:
                print(f'Connect to Master error: {ex}')
                # is_work = False
            # return redirect(request.META.get('HTTP_REFERER'))
    return render(request, 'index.html', {'sftpform': sftpform, 'dummyform': dummyform})


def check_connection_status(request):
    """Check the status of the SFTP connection."""
    global is_work
    return JsonResponse({'is_work': is_work})


def check_progress(request):
    """Check the progress of the file upload."""
    global done_count
    global total_count
    return JsonResponse({'done_count': done_count, 'total_count': total_count})


def get_file_detail(request):
    """Get the details of the uploaded files."""
    global uploadfile_detail
    return JsonResponse({'result': uploadfile_detail})


def do_work(count, sftp_url, sftp_port, sftp_username, sftp_password):
    """Perform the file upload operation."""
    global done_count
    global total_count
    global uploadfile_detail
    total_count = count
    done_count = 0
    uploadfile_detail = '\n'
    for i in range(count):
        folder = sftp_folders[randint(0, len(sftp_folders)-1)]
        filename = f'{int(time.time())}.txt'
        if writeDummyFiles(folder, sftp_url, sftp_port, sftp_username, sftp_password, filename):
            uploadfile_detail += f'folder: {folder}, filename: {filename} done\n'
            done_count += 1
    return True


def do_test(request):
    """Perform the file upload test."""
    sftpform = sftpForm()
    dummyform = dummycountForm()
    if request.method == "GET":
        dummyform = dummycountForm(request.GET)
        if dummyform.is_valid():
            dummy_amount = dummyform.cleaned_data['dummy_amount']
            if sftp_url != None and sftp_port != None and sftp_username != None and sftp_password != None:
                print(
                    f'Prepare to upload {dummy_amount} files to {sftp_url}')
                if do_work(dummy_amount, sftp_url, sftp_port, sftp_username, sftp_password):
                    print('Upload files successfully')

            else:
                print('No connection to SFTP server')
    return render(request, 'index.html', {'sftpform': sftpform, 'dummyform': dummyform})
