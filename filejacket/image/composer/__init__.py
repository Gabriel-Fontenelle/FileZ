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

# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from ...file import BaseFile


__all__ = ["ImageComposer"]


# class ImageComposer:
#     pass
#
#     @classmethod
#     def transformation_matrix(self):
#         pass
#
#     @classmethod
#     def compose(cls, objects_to_compose: BaseFile, engine=self.image_engine):
#
#         with image.clone() as rotated:
#             rotated.rotate(135, background=Color('rgb(229,221,112)'))
#             rotated.save(filename='transform-rotated-135.jpg')
#
#         pass
#
#
