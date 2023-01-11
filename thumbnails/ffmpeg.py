import os
import re
import subprocess

from imageio.v3 import immeta
from imageio_ffmpeg import get_ffmpeg_exe

ffmpeg_bin = get_ffmpeg_exe()


class _FFMpeg:
    def __init__(self, filename):
        duration, self.size = self._parse_metadata(filename)
        self.duration = int(duration + 1)

    @staticmethod
    def _cross_platform_popen_params(bufsize=100000):
        popen_params = {
            "bufsize": bufsize,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "stdin": subprocess.DEVNULL,
        }
        if os.name == "nt":
            popen_params["creationflags"] = 0x08000000
        return popen_params

    @staticmethod
    def _parse_duration(stdout):
        duration_regex = r"duration[^\n]+([0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9])"
        time = re.search(duration_regex, stdout, re.M | re.I).group(1)
        time = (float(part.replace(",", ".")) for part in time.split(":"))
        return sum(mult * part for mult, part in zip((3600, 60, 1), time))

    @staticmethod
    def _parse_size(stdout):
        size_regex = r"\s(\d+)x(\d+)[,\s]"
        match_size = re.search(size_regex, stdout, re.M)
        return tuple(map(int, match_size.groups()))

    def _parse_metadata(self, filename):
        meta = immeta(filename)
        duration, size = meta.get("duration"), meta.get("size")

        if not all((duration, size)):
            cmd = (ffmpeg_bin, "-hide_banner", "-i", filename)

            popen_params = self._cross_platform_popen_params()
            process = subprocess.Popen(cmd, **popen_params)
            _, stderr = process.communicate()
            stdout = stderr.decode("utf8", errors="ignore")

            duration = self._parse_duration(stdout)
            size = self._parse_size(stdout)

        return duration, size
