import io
import subprocess


class DockerException(Exception):
    pass


class DockerContainer:

    def __init__(self, image, name):
        self.image = image
        self.name = name
        self._output = io.BytesIO()
        self._running = False

    @property
    def output(self):
        return self._output.getvalue().decode()

    def run(self, *options, command='', command_args=None):
        if self._running:
            raise DockerException(f"Container {self.name} already running")

        options = ' '.join(options)
        command_args = command_args or []
        command_args = ' '.join(command_args)
        cmd = f"docker run --name={self.name} {options} {self.image} {command} {command_args}"
        p = subprocess.run(cmd, shell=True, capture_output=True)
        if p.returncode == 0:
            self._running = True
        return p.returncode

    def exec(self, *options, command='', command_args=None):
        if not self._running:
            raise DockerException(f"Container {self.name} is not running")

        options = ' '.join(options)
        command_args = command_args or []
        command_args = ' '.join(command_args)
        cmd = f"docker exec {options} {self.name} {command} {command_args}"
        p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self._output.write(p.stdout)
        return p.returncode

    def stop(self):
        cmd = f"docker stop {self.name}"
        p = subprocess.run(cmd, shell=True, capture_output=True)
        if p.returncode == 0:
            self._running = False
        return p.returncode

    def rm(self):
        if self._running:
            raise DockerException(f"You cannot remove a running container {self.name}")

        cmd = f"docker rm {self.name}"
        p = subprocess.run(cmd, shell=True, capture_output=True)
        return p.returncode

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if not self._running:
            return

        self.stop()
        self.rm()
