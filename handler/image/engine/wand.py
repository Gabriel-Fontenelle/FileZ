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
`handler <at> gabrielfontenelle.com` can be used.
"""
from . import ImageEngine

from wand.display import display as wand_display
from wand.image import Image as WandImageClass
from wand.color import Color

__all__ = [
    "WandImage"
]


class WandImage(ImageEngine):
    """
    Class that standardized methods of Wand library.
    This class depends on Wand being installed in the system.
    """

    class_image = WandImageClass
    """
    Attribute used to store the class reference responsible to create an image.
    """

    def append_to_sequence(self, images, **kwargs):
        """
        Method to append a list of images to the current image, if the current image is not a sequence
        this method should convert it to a sequence.
        """

        self.image.sequence.append(images)

    def change_color(self, colorspace="gray"):
        """
        Method to change the color space of the current image.
        """
        colorscheme = {
            "gray": "gray",
            "Lab": "",
            "YCrCb": "",
            "HSV": ""
        }
        # Convert to grey scale
        self.image.transform_colorspace(colorscheme[colorspace])

    def clone(self):
        """
        Method to copy the current image object and return it.
        """
        return self.image.clone()

    def crop(self, width, height):
        """
        Method to crop the current image object.
        """
        self.image.crop(width=width, height=height, gravity='center')

    def get_bytes(self, encode_format="jpeg"):
        """
        Method to obtain the bytes' representation for the content of the current image object.
        """
        return self.image.make_blob(encode_format)

    def get_size(self):
        """
        Method to obtain the size of current image.
        """
        return self.image.size[0], self.image.size[1]

    def has_sequence(self):
        """
        Method to verify if image has multiple frames, e.g `.gif`, or distinct sizes, e.g `.ico`.
        The current version of Wand doesn't support apng, treating it as a normal single layer png.
        """
        return len(self.image.sequence) > 1

    def has_transparency(self):
        """
        Method to verify if image has a channel for transparency.
        """
        return self.image.alpha_channel

    def prepare_image(self):
        """
        Method to prepare the image using the stored buffer as the source.
        """
        self.image = self.class_image(file=self.source_buffer)

    def resample(self, percentual=10, encode_format="webp"):
        """
        Method to re sample the image sequence with only the percentual amount of items distributed through the image
        sequences.
        """
        if not self.has_sequence():
            return

        total_frames = len(self.image.sequence)

        steps = total_frames // (total_frames * percentual // 100)

        for index in list(set(range(0, total_frames, 1)) - set(range(0, total_frames, steps)))[::-1]:
            del self.image.sequence[index]

    def scale(self, width, height):
        """
        Method to scale the current image object without implementing additional logic.
        """
        self.image.resize(width, height, filter="lanczos2sharp")

    def show(self):
        """
        Method to display the image for debugging purposes.
        """
        if self.has_sequence():
            for image in self.image.sequence:
                wand_display(self.class_image(image))
        else:
            wand_display(self.image)

    def trim(self, color=None):
        """
        Method to trim the current image object.
        The parameter color is used to indicate the color to trim else it will use transparency.
        This method will trim the whole image based on first frame/size if image has sequence.
        """
        if color:
            color = Color(f"rgb({color[0]}, {color[1]}, {color[2]})")

        elif self.has_transparency():
            # Trim transparency
            color = Color('rgba(0,0,0,0)')

        else:
            raise ValueError("Cannot trim image because no color was informed and no alpha channel exists in the "
                             "current image.")

        self.image.trim(background_color=color, reset_coords=True)
