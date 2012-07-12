"""
A machine profile object that holds all values for a specific profile.
"""

import json
import os
import logging

class Profile(object):

  def __init__(self, name=None, abs_path=None):
    """Constructor for the profile object.  If given only a name, looks
    in the ./profiles/ directory for that file.json.  If a path is specified,
    uses the path instead.

    @param str name: Name of the profile
    @param str path: The path to a profile
    """
    self._log = logging.getLogger(self.__class__.__name__)
    if name:
      path = os.path.join(
          os.path.abspath(os.path.dirname(__file__)),'profiles' + os.path.sep)  #Path of the profiles directory
      extension = '.json'
      path = path+name+extension
    elif abs_path:
      path = abs_path
    self._log.info('{"event":"open_profile", "path":%s}'
        %(path))
    with open(path) as f:
      self.values = json.load(f) 

def list_profiles():
  """
  Looks in the ./profiles directory for all files that
  end in .json and returns that list.
  @return A generator of profiles without their .json extensions
  """
  path = os.path.join(
      os.path.abspath(os.path.dirname(__file__)), 'profiles' + os.path.sep)
  profile_extension = '.json'
  for f in os.listdir(path):
    root, ext = os.path.splitext(f)
    if profile_extension == ext:
      yield root
