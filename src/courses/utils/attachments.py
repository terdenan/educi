import os

from django.conf import settings


def get_attachments_path(course_id):
    path = os.path.join(settings.MEDIA_ROOT, 'courses', f'course_{course_id}', 'attachments')
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def list_attachments(course_id):
    path = get_attachments_path(course_id)
    entries = os.listdir(path)
    return entries


def upload_attachments(course_id, attachments):
    path = get_attachments_path(course_id)
    for file in attachments:
        file_path = os.path.join(path, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
