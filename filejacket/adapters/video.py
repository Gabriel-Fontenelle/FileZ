"""
Handler is a package for creating files in an object-oriented way,
allowing extendability to any file system.

Copyright (C) 2021 Gabriel Fontenelle Senno Silva

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Should there be a need for contact the electronic mail
`filejacket <at> gabrielfontenelle.com` can be used.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING
from ..engines.video import VideoEngine

if TYPE_CHECKING:
    from imageio.core.v3_plugin_api import PluginV3
    from numpy import ndarray

__all__ = [
    "VideoEngine",
    "MoviePyVideo",
]


class MoviePyVideo(VideoEngine):
    """
    Class that standardized methods of MoviePy library.
    This class depends on MoviePy, OpenCV and FFMPG installed in the system.
    """

    def get_duration(self) -> int:
        """
        Method to return the duration in seconds of the video.
        """
        return self.video.duration

    def get_frame_rate(self) -> float:
        """
        Method to return the framerate of the video.
        """
        return self.video.fps

    def get_frame_as_bytes(self, index: int, encode_format: str = "jpeg") -> ndarray:
        """
        Method to return content of the frame at index as bytes.
        TODO: Test that buffer is really bytes.
        TODO: Expand the formats dict to allow more types of media.
        """
        formats: dict[str, str] = {"jpeg": ".jpg", "webp": ".webp"}

        from cv2 import imencode, cvtColor, COLOR_BGR2RGB

        # Fix the color from BGR -> RGB.
        success, buffer = imencode(
            formats[encode_format], cvtColor(self.video.get_frame(index), COLOR_BGR2RGB)
        )

        if not success:
            raise ValueError(
                f"Could not convert image to format {encode_format} in MoviePyVideo.get_frame_as_bytes."
            )

        return buffer

    def get_frame_image(self, index) -> Any:
        """
        Method to return the array representing the frame at index.
        """
        return self.video.get_frame(index)

    def get_size(self) -> tuple[int, int]:
        """
        Method to return the width and height of the video.
        """
        return self.video.size

    def prepare_video(self) -> None:
        """
        Method to prepare the video using the stored buffer as the source.
        """
        from moviepy.editor import VideoClip
        from imageio import imopen

        video_array: PluginV3 = imopen(self.source_buffer, io_mode="r", plugin="pyav")  # type: ignore
        self.metadata: dict[str, Any] = video_array.metadata()

        def make_frame(t):
            """
            Internal function to create the frame from video_array.
            This function allow for consuming of video with lazy operation.
            """
            return video_array.read(index=t)

        try:
            duration = self.metadata["duration"]
        except KeyError:
            duration = int(
                float(
                    video_array._container.duration
                    * video_array._video_stream.time_base
                )
                // 1000
            )
            self.metadata["duration"] = duration

        self.video = VideoClip(make_frame, duration=duration)
        self.video.fps = self.metadata["fps"]

    def show(self) -> None:
        """
        Method to display the video for debugging purposes.
        """
        total_frames: int = self.get_frame_amount()

        frame: int = 0

        from cv2 import imshow, waitKey, destroyAllWindows

        while frame < total_frames:
            imshow("Video", self.get_frame_image(frame))
            frame += 1

            if waitKey(25) & 0xFF == ord("q"):
                break

        destroyAllWindows()
