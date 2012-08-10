import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import mock

import tempfile

import s3g
import warnings

class SingleHeadReading(unittest.TestCase):

  def setUp(self):
    self.p = s3g.Gcode.GcodeParser()
    self.s = s3g.Gcode.GcodeStates()
    self.s.values['build_name'] = 'test'
    self.profile = s3g.Profile('ReplicatorSingle')
    self.s.profile = self.profile
    self.p.state = self.s
    self.s3g = s3g.s3g()
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    os.unlink(input_path)
    self.writer = s3g.Writer.FileWriter(open(input_path, 'w'))
    self.s3g.writer = self.writer
    self.p.s3g = self.s3g

  def tearDown(self):
    self.profile = None
    self.s = None
    self.writer = None
    self.s3g = None
    self.p = None


  def test_single_head_skeinforge_single_20mm_box(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_20mm_box.gcode'), self.p) 

  def test_single_head_skeinforge_single_snake(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_snake.gcode'), self.p) 

  def test_single_head_miracle_grue(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'miracle_grue_single_extrusion.gcode'), self.p) 

class DualHeadReading(unittest.TestCase):

  def setUp(self):
    self.p = s3g.Gcode.GcodeParser()
    self.s = s3g.Gcode.GcodeStates()
    self.s.values['build_name'] = 'test'
    self.profile = s3g.Profile('ReplicatorDual')
    self.s.profile = self.profile
    self.p.state = self.s
    self.s3g = s3g.s3g()
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    os.unlink(input_path)
    self.writer = s3g.Writer.FileWriter(open(input_path, 'w'))
    self.s3g.writer = self.writer
    self.p.s3g = self.s3g

  def tearDown(self):
    self.profile = None
    self.s = None
    self.writer = None
    self.s3g = None
    self.p = None

  def test_dual_head_skeinforge_hilbert_cube(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_dual_extrusion_hilbert_cube.gcode'), self.p) 

  def test_single_head_skeinforge_single_20mm_box(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_20mm_box.gcode'), self.p) 

  def test_single_head_skeinforge_single_snake(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_snake.gcode'), self.p) 

  def test_single_head_miracle_grue(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'miracle_grue_single_extrusion.gcode'), self.p) 

def PreprocessAndExecuteFile(theFile, parser):
  #Get the skeinforge 50 preprocessor
  preprocessor = s3g.Preprocessors.Skeinforge50Preprocessor()
  #Make the temp file to process the gcode file into
  with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
    pass
  input_path = input_file.name
  os.unlink(input_path)
  preprocessor.process_file(theFile, input_path)
  for line in parser.state.profile.values['print_start_sequence']:
    parser.execute_line(line)
  with open(input_path) as f:
    for line in f:
      parser.execute_line(line)
  parser.line_number = 1    #For better debugging, since the start.gcode is included in this number
  for line in parser.state.profile.values['print_end_sequence']:
    parser.execute_line(line)

if __name__ == '__main__':
  unittest.main()
