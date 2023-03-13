#! /usr/bin/env python


# Two primary data structures are created:

# (1) A list of tuples. Each tuple contains a pair of items: a file size and a 
# file path. The file size is the size of the file pointed to by the file path. 
# The list is sorted on the file sizes. The set of file paths consists of all 
# the paths to the files in directory_l (recursively including subdirectories 
# of directory_l and excluding hidden files and folders by default).

# For example:
# [(file_size_1, file_path_1), (file_size_2, file_path_2), ..., 
# (file_size_n, file_path_n)]

# file_size_1 = size of the file pointed to by file_path_1, 
# file_size_2 = size of the file pointed to by file_path_2, ..., 
# file_size_n = size of the file pointed to by file_path_n

# file_size_1 <= file_size_2 <= ... <= file_size_n

# file_path_1, file_path_2, ..., file_path_n = all the paths to the files in 
# directory_l (recursively including subdirectories of directory_l and 
# excluding hidden files and folders by default)

# (2) A dictionary mapping each unique file size in directory_r to a list of 
# all the paths to files of that size in directory_r (recursively including 
# subdirectories of directory_r and excluding hidden files and folders by 
# default).


# For each file pointed to in (1), its size is checked for existence in (2). 
# If its size does not exist in (2), the file path to it is stored as 
# unmatched. If its size does exist in (2), a byte by byte comparison is done 
# between it and each file matching its size in (2) until a match is found, if 
# any. If a match is not found, the file path to it is stored as unmatched. The 
# stored list of unmatched file paths, if any, is then printed.


# Uses suggestions by msvalkon and Janne Karila in Stack Exchange Code Review:
# https://codereview.stackexchange.com/q/41853


import argparse
import collections
import filecmp
import os
import sys

from operator import itemgetter


# Progress bar code modified from code provided by 6502 in Stack Overflow:
# https://stackoverflow.com/a/6169274

pbar_char_len = 80 - 5

def begin_progress():
  global progress
  print('[' + ' ' * pbar_char_len + ']' + chr(8) * (pbar_char_len + 1), end='')
  sys.stdout.flush()
  progress = 0

def update_progress(x):
  global progress
  x = int(x * pbar_char_len // 100)
  print('*' * (x - progress), end='')
  sys.stdout.flush()
  progress = x

def end_progress():
  print('*' * (pbar_char_len - progress) + ']\n')
  sys.stdout.flush()


def main():
  help_description = \
  'Prints a list of the paths to the files that exist in the directory pointed \
to by directory_l, but that do not exist in the directory pointed to by \
directory_r. File name differences are ignored. Recursively scans \
subdirectories of directory_l and directory_r. Skips hidden files and folders \
by default. Files of the same size are compared byte by byte. Differences in \
directory structures are ignored. For example, if \
directory_l/subdirectory_1/file_name_1 and \
directory_r/subdirectory_2/subdirectory_3/file_name_2 match byte for byte, \
then directory_l/subdirectory_1/file_name_1 exists in directory_r.'

  parser = argparse.ArgumentParser(description = help_description)

  parser.add_argument('-a', '--all', action='store_true', help='include hidden \
files and folders')
  parser.add_argument('directory_l', help='path to a directory of files to \
search for')
  parser.add_argument('directory_r', help='path to a directory of files to \
search in')

  args = vars(parser.parse_args())

  include_hidden = args['all']

  directory_l = args['directory_l']
  directory_r = args['directory_r']

  if not os.path.isdir(directory_l):
    print("Invalid directory path: " + directory_l)
    sys.exit(2)

  if not os.path.isdir(directory_r):
    print("Invalid directory path: " + directory_r)
    sys.exit(2)

  unmatched = find_unmatched(directory_l, directory_r, include_hidden)

  # Prints the paths to any unmatched files.
  if not unmatched:
    print("No unmatched files.")
  else:
    print("Unmatched files:")
    for file_path in unmatched:
      print(file_path)


def find_unmatched(directory_l, directory_r, include_hidden):
  print("Preprocessing...")

  # Creates (1)

  size_file_path_tuple_list_l = sizes_paths(directory_l, include_hidden)
  # Sorts the list by the first item in each tuple pair (size).
  size_file_path_tuple_list_l_sorted = sorted(size_file_path_tuple_list_l, \
key=itemgetter(1)) # (1)


  # Creates (2)

  size_file_path_tuple_list_r = sizes_paths(directory_r, include_hidden)
  size_to_file_path_list_dict_r = \
dict_of_lists(size_file_path_tuple_list_r) # (2)


  # Compares the files

  print("Comparing files...")

  unmatched = []

  # Creates a progress bar

  begin_progress()

  for i, (size_l, file_path_l) in enumerate(size_file_path_tuple_list_l_sorted):
    # size_to_file_path_list_dict_r[size_l] is a list of the paths to the files
    # in directory_r (recursively including subdirectories of directory_r and 
    # excluding hidden files and folders by default) that are the same size as 
    # the file pointed to by file_path_1.

    # Note that in the statement 'size_to_file_path_list_dict_r[size_l]', if 
    # size_l does not exist as a key in size_to_file_path_list_dict_r, then 
    # size_l is added as a key that maps to an empty list.
    if not file_match(file_path_l, size_to_file_path_list_dict_r[size_l]):
      # Either no files in directory_r (recursively including subdirectories of 
      # directory_r and excluding hidden files and folders by default) exist 
      # that are the same size as the file pointed to by file_path_l, or none 
      # of those that do are a byte by byte match.
      unmatched.append(file_path_l)

    update_progress(100 * i / len(size_file_path_tuple_list_l_sorted))

  end_progress()

  return unmatched


# Returns as tuple pairs the size of and path to each of the files in the 
# directory pointed to by 'top', recursively including subdirectories of 'top'. 
# Hidden files and folders are not returned unless 'include_hidden' is True.
def sizes_paths(top, include_hidden):
  for file_path in get_directory_file_paths(top, include_hidden):
    size = os.path.getsize(file_path)
    yield size, file_path


# Returns each of the paths to the files in the directory pointed to by 'top', 
# recursively including subdirectories of 'top'. Hidden files and folders are 
# not returned unless 'include_hidden' is True.
def get_directory_file_paths(top, include_hidden):
  for directory_path, folder_name_list, file_name_list in os.walk(top):
    # directory_path is the path to the current directory
    # folder_name_list is the list of all the folder names in the 
    # current directory
    # file_name_list is the list of the file names in the current directory
    if not include_hidden:
      # Ignore hidden files and folders
      # http://stackoverflow.com/questions/13454164/os-walk-without-hidden-folders
      # Answer by Martijn Pieters
      # Removes the file names that begin with '.' from the list of file names 
      # in the current directory.
      file_name_list = [f for f in file_name_list if not f[0] == '.']
      # Removes the folder names that begin with '.' from the list of folder 
      # names in the current directory.
      folder_name_list[:] = [f for f in folder_name_list if not f[0] == '.']

    for file_name in file_name_list:
      yield os.path.join(directory_path, file_name)


# Creates and returns a dictionary of lists from a list of tuple pairs. 
# The keys in the dictionary are the set of the unique first items from the 
# tuple pairs. Each of these keys is mapped to a list of all the second items 
# from the tuple pairs whose first item matches that key.
# Example:
# {'a': [1, 1], 'c': [1], 'b': [2, 3]} = 
# dict_of_lists([('a', 1), ('a', 1), ('b', 2), ('b', 3), ('c', 1)])
def dict_of_lists(item_list):
  # http://docs.python.org/2/library/collections.html#collections.defaultdict
  d = collections.defaultdict(list)
  for key, value in item_list:
    # If d[key] does not exist, an empty list is created and value is attached 
    # to it. Otherwise, if d[key] does exist, value is appended to it.
    d[key].append(value)
  return d


# Returns True if and only if any of the files pointed to by the file paths in 
# file_path_list_r are a byte by byte match for the file pointed to by 
# file_path_l.
# Note that file_path_list_r may be an empty list.
def file_match(file_path_l, file_path_list_r):
  return any(filecmp.cmp(file_path_l, file_path_r, False) \
for file_path_r in file_path_list_r)


main()
