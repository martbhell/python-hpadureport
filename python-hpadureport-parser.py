#!/usr/bin/python
# Script to parse HP SSA diagnostic reports
# Written by Johan Guldmyr 2016-2017
#
# Currently it:
# - makes python dictionaries of the XML data..
# - use -f argument to get the numbers of disks under "(Since Factory)" other wise (Since Reset)"
# - parses the "bus faults" of all the disks
#  - outputs when the value is different in the two xml files
#
# Example output:
#$ python python-hpadureport-parser.py -1 relative_path/1ADUReport.xml -2 relative_path/2ADUReport.xml -e "Bus Faults"
#CRITICAL: Error counter different on disks: Physical Drive (4 TB SAS HDD) 1I:1:[32-64] (Wednesday November 23, 2016 8:09:55AM vs Friday December 02, 2016 9:56:30AM)
#$ python python-hpadureport-parser.py -1 relative_path/1ADUReport.xml -2 relative_path/2ADUReport.xml -e "Bus Faults" -v 
#disk, value2, value1, diff
#Physical Drive (4 TB SAS HDD) 1I:1:32, 27, 23, 4
#Physical Drive (4 TB SAS HDD) 1I:1:33, 30, 28, 2
#Physical Drive (4 TB SAS HDD) 1I:1:37, 19, 16, 3
#[snip]
#CRITICAL: Error counter different on disks: Physical Drive (4 TB SAS HDD) 1I:1:[32-64] (Wednesday November 23, 2016 8:09:55AM vs Friday December 02, 2016 9:56:30AM)
#

import sys # for sys.exit
import xml.etree.ElementTree as ET
import argparse
import hostlist # used to turn list [ '1I:1:1' ,'1I:1:2'] into string 1I:1:[1-2] 
import json # for dumping output to JSON
import socket # for finding hostname
hostiname = socket.gethostname()
import os.path # for checking if a file exists

######### Arguments
parser = argparse.ArgumentParser(description='Process HP ADU reports')
parser.add_argument('-1', dest='file1', action='store', required=True,
                    help='path to file1')
parser.add_argument('-2', dest='file2', action='store', required=True,
                    help='path to file2')
parser.add_argument('-d', dest='debug', action='store_true',
                    help='enable debug')
parser.add_argument('-f', dest='area', action='store_true',
                    help='since factory, otherwise since Reset')
parser.add_argument('-v', dest='verbosely', action='store_true',
                    help='output verbosely')
parser.add_argument('-e', dest='track_this_error_counter', action='store', required=True,
                    help='counter to track - like "Bus Faults"')
parser.add_argument('-json-file', dest='json_file', action='store',
                    help='write json to this here file')
parser.add_argument('-json-stdout', dest='json_stdout', action='store_true',
                    help='write json to stdout')
parser.add_argument('-n', dest='negative_is_bad', action='store_true',
                    help='count negative difference (usually a counter reset) as bad')
parser.add_argument('-6', dest='six_is_bad', action='store_true',
                    help='count a positive difference of 6 (usually a reboot) as bad')

args = parser.parse_args()
file1 = args.file1
file2 = args.file2
debug = args.debug
verbosely = args.verbosely
track_this_error_counter = args.track_this_error_counter
track_this_error_counter_diff = args.track_this_error_counter + "_diff"
json_file = args.json_file
json_stdout = args.json_stdout
negative_is_bad = args.negative_is_bad
six_is_bad = args.six_is_bad

#########  Nagios return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

######### Read the XML fiels
tree = ET.parse(file1)
tree2 = ET.parse(file2)
root = tree.getroot()
root2 = tree2.getroot()

######### Default "area"
if args.area:
  stats_area = "Monitor and Performance Statistics (Since Factory)"
else:
  stats_area = "Monitor and Performance Statistics (Since Reset)"

### Schema "documentation"
#<ADUReport>
#<MetaProperty id="ADU Version" value="2.40.13.0"/>
#<MetaProperty id="Diagnostic Module Version" value="8.4.13.0"/>
#<MetaProperty id="Time Generated" value="Monday November 14, 2016 10:37:26AM"/>
#<Device deviceType="ArrayController" id="AC:1234567890" marketingName="Smart Array P440 in slot 1">...</Device>
#<Device deviceType="ArrayController" id="AC:1234456789" marketingName="Smart Array P440 in slot 2">...</Device>
#<Device deviceType="ArrayController" id="AC:123456789" marketingName="Dynamic Smart Array B140i in slot 0b">...</Device>
#..
#..
#<Device deviceType="PhysicalDrive" id="AC:1234567890,PD:16" marketingName="Physical Drive (4 TB SAS HDD) 1I:1:1">
#<Errors/>
#  <MetaStructure id="Physical Drive Status" size="2560">...</MetaStructure>
#  <MetaStructure id="Monitor and Performance Statistics (Since Factory)">...</MetaStructure>
#  <MetaStructure id="Monitor and Performance Statistics (Since Reset)">...</MetaStructure>
#  <MetaStructure id="Serial SCSI Physical Drive Error Log" size="1536">...</MetaStructure>
#  <MetaStructure id="Mode Sense 10">...</MetaStructure>
#  <MetaStructure id="VPD Page 80 - Serial Number">...</MetaStructure>
#  <MetaStructure id="VPD Page 83 - Array Information">...</MetaStructure>
#  <MetaStructure id="Workload Information">...</MetaStructure>
#</Device>
#..
#..
#</ADUReport>

def return_disks_bus_faults_dict(root):

  """
  single argument is an xml "root" of an ADUreport.xml
  return a dictionary with each key being "marketingName" of the physical drives
  return a dictionary with each key being "disk_short_name" of the physical drives
  return a list of chassis serial numbers found in the report
  return a string with date when the report was generated
  
  example output:
  {'Physical Drive (4 TB SAS HDD) 1I:1:40': '0x00000001', 'Physical Drive (4 TB SAS HDD) 1I:1:43': '0x00000009', 'Physical Drive (4 TB SAS HDD) 1I:1:61': '0x0000000c', 'Physical Drive (4 TB SAS HDD) 1I:1:57': '0x00000013', 'Physical Drive (4 TB SAS HDD) 1I:1:60': '0x00000001'}

  """

  disk_dict = {}
  disk_dict_short = {}
  chassisserialnumbers = []

  for a in root:
  # controller
    if a.tag == "MetaProperty":
      if a.attrib['id'] == "Time Generated":
        time_generated = a.attrib["value"]
    if a.tag == "Device":
      for b in a:
        # array or storage enclosure
	# TODO: this can be shortened I think..
        if b.tag == "MetaStructure":
          if b.attrib['id'] == 'SubSystem Parameters':
            for subsysparam in b:
              if subsysparam.attrib['id'] == "Chassis Serial Number":
                chassisserialnumbers.append(subsysparam.attrib['value'])
        if b.tag == "Device":
          if debug: print("b: %s" % b.tag)
          for c in b:
          # logical drives under arrays
          # disk drives under storage enclosures
          # {'deviceType': 'PhysicalDrive', 'marketingName': 'Physical Drive (4 
            if c.attrib != {}:
              try: 
                devicetype = c.attrib['deviceType']
              except KeyError:
                if debug: print("no deviceType for: %s" % c.attrib)
                continue
              marketingName = c.attrib['marketingName']
              if devicetype == "PhysicalDrive":
		# turns Physical Drive (4 TB SAS HDD) 1I:1:5
		# into 1I:1:5
                disk_short_name = c.attrib['marketingName'].split(' ')[6]
                for d in c:
                  # physical drive status
                  if d.attrib != {}:
                    if d.attrib['id'] == stats_area:
                      if debug: print(d.attrib)
                      for e in d:
                        id = e.attrib['id']
                        if id == track_this_error_counter:
                          bus_faults = e.attrib['value']
                          if debug: print("%s : %s" % (marketingName,bus_faults))
                          disk_dict[marketingName] = bus_faults
                          disk_dict_short[disk_short_name] = bus_faults
  return(disk_dict, disk_dict_short, chassisserialnumbers, time_generated)

def return_disks_all_dict(root):

  """
  single argument is an xml "root" of an ADUreport.xml
  return a dictionary of dictionaries with disks as keys
  return a list of chassis serial numbers found in the report

  """

  disk_dict = {}

  for a in root:
  # controller
    if a.tag == "MetaProperty":
      if a.attrib['id'] == "Time Generated":
        time_generated = a.attrib["value"]
    if a.tag == "Device":
      for b in a:
        # - disk arrays
	# - storage enclosure
        if b.tag == "MetaStructure":
          if b.attrib['id'] == 'SubSystem Parameters':
            if debug: print(b.attrib['id'])
            for subsysparam in b:
              if subsysparam.attrib['id'] == "Chassis Serial Number":
                chassisserialnumbers.append(subsysparam.attrib['value'])
        if b.tag == "Device":
          if debug: print("b: %s" % b.tag)
          for c in b:
          # - logical drives under arrays
          # - disk drives under storage enclosures
          # {'deviceType': 'PhysicalDrive', 'marketingName': 'Physical Drive (4
            if c.attrib != {}:
              try:
                    devicetype = c.attrib['deviceType']
              except KeyError:
                if debug: print("no deviceType for: %s" % c.attrib)
                continue
              marketingName = c.attrib['marketingName']
              if devicetype == "PhysicalDrive":
                disk_dict[marketingName] = { }
                for d in c:
                  # physical drive status
                  if d.attrib != {}:
                    if debug: print(d.attrib)
                    if d.attrib['id'] == stats_area:
                      for e in d:
                        theid = e.attrib['id']
                        try:
                          value = e.attrib['value']
                        except KeyError:
                          #print "no value for id %s" % theid
                          continue
                        disk_dict[marketingName][theid] = value
  return(disk_dict)

if __name__ == "__main__":
#	output = return_disks_all_dict(root)
#	for i in output:
#		print i
#		print output[i]
#		break

  [ report1, report1_short, chassisserialnumbers1, timegenerated1 ] = return_disks_bus_faults_dict(root)
  [ report2, report2_short, chassisserialnumbers2, timegenerated2 ] = return_disks_bus_faults_dict(root2)
  if chassisserialnumbers1 != chassisserialnumbers2:
    print("WARNING: we are comparing different chassis/servers")

  if verbosely or debug: print("disk, value2, value1, diff")
  no_diff_cnt = 0
  neg_cnt = 0
  diff_cnt = 0
  bad_disks = []
  bad_disks_dict = { }
  bad_disks_dict['meta'] = { "tracking": track_this_error_counter, "time1": timegenerated1, "time2": timegenerated2, "hostname": hostiname }
  for disk in report2:
    value2 = int(report2[disk], 16)
    value1 = int(report1[disk], 16)
    diff = value2 - value1
    # write the pertinent data into a dictionary so we can later present it as JSON
    bad_disks_dict[disk] = { "value1": value1, "value2": value2, "diff": diff }
    if value2 != value1:
      if verbosely or debug: print("%s, %s, %s, %s" % (disk, value2,value1, diff))
      # If the value in the lower in the newer report
      # Use "-n" if you want this to count as a bad_disk
    if value2 < value1:
      neg_cnt = neg_cnt + 1
    if negative_is_bad:
      diff_cnt = diff_cnt + 1
      bad_disks.append(disk)
    # If the value is larger in the newer report
    else:
      if diff == 6:
        if verbosely:
          print("difference for %s is 6, rebooted server recently?" % disk)
          # use "-6" if you want a positive value of 6 to not be bad
        if six_is_bad == True:
          diff_cnt = diff_cnt + 1
          bad_disks.append(disk)
        else:
          diff_cnt = diff_cnt + 1
          bad_disks.append(disk)
      # If the values are the same
      else:
        no_diff_cnt = no_diff_cnt + 1
        if debug: print("%s, %s, %s, %s" % (disk, value2,value1, diff))

  ## JSON
  if json_stdout: print(json.dumps(bad_disks_dict))
  if json_file: 
    if os.path.isfile(json_file): 
      with open(json_file, 'a') as outfile:
        json.dump(bad_disks_dict, outfile)
        outfile.write("\n")
    else:
      with open(json_file, 'w') as outfile:
        json.dump(bad_disks_dict, outfile)
        outfile.write("\n")
  ## No more JSON
  # turn list [ '1I:1:1' ,'1I:1:2' ] into string 1I:1:[1-2]
  # turn list [ 'Physical Drive (4 TB SAS HDD) 1I:1:32' ,'Physical Drive (4 TB SAS HDD) 1I:1:33', ... ]
  #  into string Physical Drive (4 TB SAS HDD) 1I:1:[32-64]
  collected_bad_disks = hostlist.collect_hostlist(bad_disks)
  if no_diff_cnt > 0 and diff_cnt < 1:
    if verbosely or debug: print("no differences in the counters between any disks in the reports")
    else: print("OK: No increases of %s on any disks. (%s vs %s)" % (track_this_error_counter,timegenerated1,timegenerated2))
    sys.exit(OK)
  elif no_diff_cnt == 0 and diff_cnt == 0:
    print("UNKNOWN: Found nothing, does '%s' exist?" % track_this_error_counter)
    sys.exit(UNKNOWN)
  else:
    print("CRITICAL: %s increased on these disks: %s (%s vs %s)" % (track_this_error_counter,collected_bad_disks,timegenerated1,timegenerated2))
    sys.exit(CRITICAL)
