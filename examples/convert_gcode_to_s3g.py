import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import optparse

parser = optparse.OptionParser()
parser.add_option("-i", "--inputfile", dest="input_file",
                  help="gcode file to read in", default=False)
parser.add_option("-o", "--outputfile", dest="output_file",
                  help="s3g file to write out", default=False)
(options, args) = parser.parse_args()


s = s3g.s3g()
s.writer = s3g.Writer.FileWriter(open(options.output_file, 'w'))

parser = s3g.Gcode.GcodeParser()
parser.s3g = s


with open(options.input_file) as f:
  for line in f:
    parser.ExecuteLine(line)
