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
import os
import pwd
from os import listdir, getcwd
from os.path import isdir

from filejacket import LinuxFileSystem, WindowsFileSystem
from filejacket.file import File
from filejacket.serializer import FileJsonSerializer

HASH_FILES = ['md5', 'sfv']


def recursive_get_all_files(path: str) -> list[str]:
    files: list[str] = []
    for item in listdir(path):
        filepath = f"{path}/{item}"
        if isdir(filepath):
            files += recursive_get_all_files(filepath)
        else:
            files.append(filepath)

    return files


def interactive_get_all_files(path: str) -> list[str]:
    files: list[str] = []

    paths: list[str] = [path]

    while paths:
        path = paths.pop()
        for item in listdir(path):
            filepath = f"{path}/{item}"
            if not isdir(filepath):
                files.append(filepath)
            else:
                paths.append(filepath)

    return files


def get_filename(file_object):
    if file_object.is_content_wholesome:
        # Save content in Good file
        return 'good.txt'

    elif file_object.is_content_wholesome is False:
        # Save content in Bad file
        return 'bad.txt'

    return 'error.txt'


def is_hash_file(file_path):
    try:
        return file_path.rsplit('.', maxsplit=1)[1] in HASH_FILES
    except IndexError:
        return False


def process_hash_file(directory, file_path):
    # Copy hashes files to verify folder
    destination_directory = LinuxFileSystem.join(
        directory,
        LinuxFileSystem.get_filename_from_path(
            file_path
        )
    )

    # We use the stylus of renaming of WindowsFileSystem for our renaming.
    LinuxFileSystem.file_sequence_style = WindowsFileSystem.file_sequence_style

    # Clone will copy the file, renaming it if one already exists in destination.
    LinuxFileSystem.clone(
        source=file_path,
        destination=destination_directory
    )


def process_file(directory, file_path):
    # Load file and hashes` files.
    file_object = File(path=file_path)
    file_object.serializer = FileJsonSerializer

    # Get filename with base in is_content_wholesome attribute that process loaded hashes files.
    filename_to_save = get_filename(file_object)

    # Generate additional hashes
    try:
        file_object.generate_hashes(force=True)
    except (OSError, UnicodeDecodeError) as e:
        # file_to_save = os.path.join(home_dir, f'{filename}-bad.txt')
        with open(LinuxFileSystem.join(directory, "error_processing_new_hashes.txt"), mode='a') as fp:
            fp.write(file_object.complete_filename)
            fp.write("\n")
            fp.write(str(e))
            fp.write("\n\n")

    # Save file structure to `.txt`.
    file_to_save = LinuxFileSystem.join(directory, filename_to_save)
    print(file_to_save)
    with open(file_to_save, mode='a') as fp:
        content = file_object.serialize()
        fp.write(content)
        fp.write("\n")
        
    
if __name__ == "__main__":
    """
    Recursively gets all files from current directory and loads (or generate) its hashes to save it at a new directory 
    called `Verify` in two txt, one for good files and another for bad ones. 
    """
    filename = getcwd()
    filename = filename[:-1] if filename[-1:] == LinuxFileSystem.sep else filename
    filename = LinuxFileSystem.get_filename_from_path(filename)
    home_dir = pwd.getpwuid(os.getuid()).pw_dir

    destination_directory = LinuxFileSystem.join(home_dir, 'Verify', filename)
    hash_directory = LinuxFileSystem.join(destination_directory, 'hashes')

    LinuxFileSystem.create_directory(destination_directory)
    LinuxFileSystem.create_directory(hash_directory)

    print(getcwd())
    print(filename)
    print(hash_directory)

    for file in interactive_get_all_files(getcwd()):
        print(file)
        try:
            if is_hash_file(file):
                process_hash_file(hash_directory, file)
                print("Hash file processed")
                continue

            process_file(destination_directory, file)
            print("File processed")

        except OSError as error:
            file_to_save = LinuxFileSystem.join(destination_directory, 'error_accessing_file.txt')
            with open(file_to_save, mode='a') as fpointer:
                fpointer.write(file)
                fpointer.write("\n")
                fpointer.write(str(error))
                fpointer.write("\n\n")
