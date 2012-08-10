import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import io
import struct
import unittest
import threading
import time

from s3g import Writer, Encoder, errors, constants

class StreamWriterTests(unittest.TestCase):
  def setUp(self):
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()  # Stream that we will receive commands on

    file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.w = Writer.StreamWriter(file)

  def tearDown(self):
    self.w = None

  def test_error_reporting(self):
    """Tests that StreamWriter records errors received correctly
    and stores those values in the TransmissionError Thrown.
    """
    expected_errors = [
        'CRCMismatchError',
        'CRCMismatchError',
        'CRCMismatchError',
        'GenericError',
        'GenericError',
        ]
    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['CRC_MISMATCH'])
    for i in range(3):
      self.outputstream.write(Encoder.encode_payload(response_payload))
    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['GENERIC_PACKET_ERROR'])
    for i in range(2):
      self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)
    payload = 'asdf'
    try:
      self.w.send_command(payload) 
    except errors.TransmissionError as e:
      self.assertEqual(expected_errors, e.value)

  def test_send_command(self):
    """
    Passing case: Preload the buffer with a correctly formatted expected response, and verigy that it works correctly
    """
    payload = 'abcde'

    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['SUCCESS'])
    response_payload.extend('12345')
    self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)

    self.assertEqual(response_payload, self.w.send_command(payload))
    self.assertEqual(Encoder.encode_payload(payload), self.inputstream.getvalue())

  def test_send_packet_timeout(self):
    """
    Time out when no data is received. The input stream should have max_rety_count copies of the
    payload packet in it.
    """
    payload = 'abcde'
    packet = Encoder.encode_payload(payload)
    expected_packet = Encoder.encode_payload(payload)

    self.assertRaises(errors.TransmissionError,self.w.send_packet, packet)

    self.inputstream.seek(0)
    for i in range (0, constants.max_retry_count):
      for byte in expected_packet:
        self.assertEquals(byte, ord(self.inputstream.read(1)))

  def test_send_packet_many_bad_responses(self):
    """
    Passing case: test that the transmission can recover from one less than the alloted
    number of errors.
    """
    payload = 'abcde'
    packet = Encoder.encode_payload(payload)
    expected_packet = Encoder.encode_payload(payload)

    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['SUCCESS'])
    response_payload.extend('12345')

    for i in range (0, constants.max_retry_count - 1):
      self.outputstream.write('a')
    self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)

    self.assertEquals(response_payload, self.w.send_packet(packet))

    self.inputstream.seek(0)
    for i in range (0, constants.max_retry_count - 1):
      for byte in expected_packet:
        self.assertEquals(byte, ord(self.inputstream.read(1)))

  def test_send_packet(self):
    """
    Passing case: Preload the buffer with a correctly formatted expected response, and
    verify that it works correctly.
    """
    payload = 'abcde'
    packet = Encoder.encode_payload(payload)
    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['SUCCESS'])
    response_payload.extend('12345')
    self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)

    self.assertEquals(response_payload, self.w.send_packet(packet))
    self.assertEquals(Encoder.encode_payload(payload), self.inputstream.getvalue())

  # TODO: Test timing based errors- can we send half a response, get it to re-send, then send a regular response?

  def test_build_and_send_action_payload(self):
    command = constants.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0
    expected_payload = struct.pack(
      '<BiiiiiIB',
      command,
      point[0], point[1], point[2], point[3], point[4],
      duration,
      relativeAxes
    )

    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['SUCCESS'])
    self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)

    payload = struct.pack(
      '<BiiiiiIB',
      command,
      point[0], point[1], point[2], point[3], point[4],
      duration,
      relativeAxes,
    )
      

    self.w.send_action_payload(payload)

    self.assertEquals(Encoder.encode_payload(expected_payload), self.inputstream.getvalue())

  def test_build_and_send_query_payload_with_null_terminated_string(self):
    cmd = constants.host_query_command_dict['GET_NEXT_FILENAME']
    flag = 0x01
    payload = struct.pack(
      '<BB',
      cmd,
      flag
    )
    filename = 'asdf\x00'

    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['SUCCESS'])
    response_payload.append(constants.sd_error_dict['SUCCESS'])
    response_payload.extend(filename)
    self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)

    payload = struct.pack(
      '<bb',
      cmd,
      flag,
    )
    self.assertEqual(response_payload, self.w.send_query_payload(payload))

    self.assertEqual(Encoder.encode_payload(payload), self.inputstream.getvalue())
    

  def test_build_and_send_query_payload(self):
    cmd = constants.host_query_command_dict['GET_VERSION']
    s3gVersion = 123
    botVersion = 456
    expected_payload = struct.pack(
      '<bH',
      cmd,
      s3gVersion
    )

    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['SUCCESS'])
    response_payload.extend(Encoder.encode_uint16(botVersion))
    self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)

    payload = struct.pack(
      '<bH',
      cmd,
      s3gVersion,
    )

    self.assertEquals(response_payload, self.w.send_query_payload(payload))
    self.assertEquals(Encoder.encode_payload(expected_payload), self.inputstream.getvalue())

  def test_external_stop(self):
    self.w.external_stop = True
    self.assertTrue(self.w.external_stop)

  def test_external_stop_works_precondition(self):
    response_payload = bytearray()
    response_payload.append(constants.response_code_dict['SUCCESS'])
    self.outputstream.write(Encoder.encode_payload(response_payload))
    self.outputstream.seek(0)
    self.w.external_stop = True
    self.assertRaises(Writer.ExternalStopError, self.w.send_command, 'asdf')

  def delay_and_external_stop_in_thread(self):
    time.sleep(constants.timeout_length)
    self.w.external_stop = True

  def test_delay_and_external_stop_in_thread(self):
    self.assertFalse(self.w.external_stop)
    self.delay_and_external_stop_in_thread()
    self.assertTrue(self.w.external_stop)

  @unittest.skip("This test doesnt work 100% of the time since it relies timing too much, so we skip it for mow")
  def test_eternal_stop_works_multithreaded(self):
    t = threading.Thread(target=self.delay_and_external_stop_in_thread)
    try:
      t.start()
      self.w.send_packet('')
    except Writer.ExternalStopError:
      self.assertTrue(self.w.external_stop)
    t.join()    #Kill that thread!

if __name__ == "__main__":
  unittest.main()
