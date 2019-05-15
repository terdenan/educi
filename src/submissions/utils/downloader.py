import os
import tarfile
import shutil
import re
from abc import ABC, abstractmethod

import requests
from django.conf import settings


class Strategy(ABC):

    @abstractmethod
    def process_sources(self):
        pass

    def __init__(self, submission):
        self._submission = submission

    def _media_path(self, filename):
        """
        Returns path within MEDIA_ROOT where the file with filename
        should be stored regarding its submission.
        """
        return os.path.join(self._submission.store_dir, filename)

    @staticmethod
    def _extract(path, extract_to=None):
        """Extracts archive by given path"""

        if not os.path.isabs(path):
            raise Exception("Specified path argument must be absolute")

        if extract_to is None:
            extract_to = os.path.dirname(path)
        elif not os.path.isabs(extract_to):
            raise Exception("Specified extract_to argument must be absolute")

        with tarfile.open(path) as tf:
            # TODO: consider TarFile.extractall warning
            #  https://docs.python.org/3/library/tarfile.html#tarfile.TarFile.extractall
            tf.extractall(extract_to)

        os.remove(path)


class UploadedSourcesStrategy(Strategy):

    def process_sources(self):
        self.move_from_tmp()

        # TODO: extract if needed

    def move_from_tmp(self):
        initial_path = self._submission.source.path

        filename = os.path.basename(self._submission.source.name)
        media_path = self._media_path(filename)
        new_path = os.path.join(settings.MEDIA_ROOT, media_path)

        self._submission.source.name = media_path
        os.renames(initial_path, new_path)

        self._submission.save()


class DownloadRepositoryStrategy(Strategy):

    def process_sources(self):
        download_url = f"https://{self._submission.repo_url}/tarball/{self._submission.branch}"
        destination = os.path.join(settings.MEDIA_ROOT, self._media_path("sources.tar.gz"))
        destination_dirname = os.path.dirname(destination)

        os.makedirs(destination_dirname)
        filename = self.download_sources(download_url, destination)
        sources_folder_name = self._splitext(filename)
        sources_folder_path = os.path.join(destination_dirname, sources_folder_name)

        self._extract(destination)

        files = os.listdir(sources_folder_path)
        for file in files:
            file_path = os.path.join(sources_folder_path, file)
            shutil.move(file_path, destination_dirname)

        os.rmdir(sources_folder_path)

    def download_sources(self, url, destination):
        """
        Downloads sources from a given url and writes it to destination
        Returns name of a downloaded file out of Content-Disposition cookie
        """
        req = requests.get(url, stream=True)
        filename = self.get_filename_from_cd(req.headers.get('content-disposition'))

        with open(destination, 'ab') as f:
            for chunk in req.iter_content(chunk_size=1024):
                f.write(chunk)

        return filename

    def _splitext(self, path):
        """
        Cuts off all presented extensions from the end of the path
        """
        root, ext = os.path.splitext(path)

        if root == path:
            return root

        return self._splitext(root)

    @staticmethod
    def get_filename_from_cd(cd):
        """
        Get filename from content-disposition
        """
        if not cd:
            return None

        fname = re.findall('filename=(.+)', cd)
        if len(fname) == 0:
            return None
        return fname[0]


class DownloadManager:

    def __init__(self):
        self._strategy = None

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy):
        self._strategy = strategy

    def download(self):
        if self.strategy is None:
            raise Exception("Download strategy wasn't provided")

        self._strategy.process_sources()
