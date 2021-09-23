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
import inspect
import json
from datetime import datetime, time, date


__all__ = [
    'Serializer'
]


class Serializer:
    """
    Class that allow handling of Serialization from object to JSON string and dictionary and Deserialization of JSON
    string and dictionary to object.
    """

    @classmethod
    def from_dict(cls, encoded_dict):
        """
        Method to deserialize a given dictionary to a instance of current child class.
        This method must be overwritten in child class, as it is the responsibility of child class to implement how the
        conversion from dictionary to object will play out.
        """
        raise NotImplementedError("This method `from_dict` should be overwrite in inherent classes!")

    def to_dict(self):
        """
        Method that serialize the current class object to a dictionary.
        """
        encoded_dict = {}
        for key, value in vars(self).items():
            if hasattr(value, 'to_dict'):
                encoded_dict[key] = value.to_dict()

            elif isinstance(value, (str, int)):
                encoded_dict[key] = value

            elif isinstance(value, (dict, list)):
                encoded_dict[key] = value

            elif isinstance(value, bytes):
                encoded_dict[key] = value.decode('utf-8')

            elif isinstance(value, datetime):
                encoded_dict[key] = value.strftime("%m-%d-%Y %H:%M:%S")

            elif isinstance(value, time):
                encoded_dict[key] = value.strftime("%H:%M:%S")

            elif isinstance(value, date):
                encoded_dict[key] = value.strftime("%m-%d-%Y")

            elif inspect.isclass(value):
                encoded_dict[key] = {'import_path': value.__module__, 'classname': value.__name__, 'object': False}

            elif callable(value):
                encoded_dict[key] = {'import_path': value.__module__, 'classname': value.__name__, 'object': True}

            else:
                raise ValueError(f"Couldn't convert {value} to string for use in `to_dict` method!")

        return encoded_dict

    def to_json(self):
        """
        Method that serialize the current class object to JSON string.
        """
        return json.dumps(
            self.to_dict()
        )

    for_json = to_json
    """
    Alias that allow simplejson to work when option for_json is set as True.
    """

    @classmethod
    def from_json(cls, value):
        """
        Method to deserialize a given JSON string to a instance of current child class.
        """
        return cls.from_dict(json.loads(value))
