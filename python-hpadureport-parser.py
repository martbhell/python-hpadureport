#!/usr/bin/python
# Script to parse HP SSA diagnostic reports
# Written by Johan Guldmyr 2016
#
# Currently it:
# - makes python dictionaries of the XML data..
# - use -f argument to get the numbers of disks under "(Since Factory)" other wise (Since Reset)"
# - parses the "bus faults" of all the disks
#  - outputs when the value is different in the two xml files
#
# Example output:
#$ python python-hpadureport-parser.py -1 relative_path/1ADUReport.xml -2 relative_path/2ADUReport.xml 
#disk, value2, value1, diff
#Physical Drive (4 TB SAS HDD) 1I:1:32, 27, 23, 4
#Physical Drive (4 TB SAS HDD) 1I:1:33, 30, 28, 2
#Physical Drive (4 TB SAS HDD) 1I:1:37, 19, 16, 3
#

import xml.etree.ElementTree as ET
import argparse

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

args = parser.parse_args()
file1 = args.file1
file2 = args.file2
debug = args.debug

######### Configuration
tree = ET.parse(file1)
tree2 = ET.parse(file2)
root = tree.getroot()
root2 = tree2.getroot()

if args.area:
  stats_area = "Monitor and Performance Statistics (Since Factory)"
else:
  stats_area = "Monitor and Performance Statistics (Since Reset)"

######### End configuration

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
  return a list of chassis serial numbers found in the report
  
  example output:
  {'Physical Drive (4 TB SAS HDD) 1I:1:40': '0x00000001', 'Physical Drive (4 TB SAS HDD) 1I:1:43': '0x00000009', 'Physical Drive (4 TB SAS HDD) 1I:1:61': '0x0000000c', 'Physical Drive (4 TB SAS HDD) 1I:1:57': '0x00000013', 'Physical Drive (4 TB SAS HDD) 1I:1:60': '0x00000001'}

  """

  disk_dict = {}
  chassisserialnumbers = []

  for a in root:
  # controller
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
          if debug: print "b: %s" % b.tag
          for c in b:
    	  # logical drives under arrays
    	  # disk drives under storage enclosures
    	  # {'deviceType': 'PhysicalDrive', 'marketingName': 'Physical Drive (4 
    	    if c.attrib != {}:
      	      try: 
                    devicetype = c.attrib['deviceType']
    	      except KeyError:
    	        if debug: print "no deviceType for: %s" % c.attrib
    	        continue
              marketingName = c.attrib['marketingName']
              if devicetype == "PhysicalDrive":
    	        for d in c:
    	        # physical drive status
    	          if d.attrib != {}:
                    if d.attrib['id'] == stats_area:
    	              if debug: print d.attrib
    	              for e in d:
    	                id = e.attrib['id']
    	                if id == "Bus Faults":
                          bus_faults = e.attrib['value']
    	                  if debug: print "%s : %s" % (marketingName,bus_faults)
                          disk_dict[marketingName] = bus_faults
  return(disk_dict, chassisserialnumbers)

def return_disks_all_dict(root):

  """
  single argument is an xml "root" of an ADUreport.xml
  return a dictionary of dictionaries with disks as keys
  return a list of chassis serial numbers found in the report

  """

  disk_dict = {}

  for a in root:
  # controller
    if a.tag == "Device":
      for b in a:
        # - disk arrays
	# - storage enclosure
        if b.tag == "MetaStructure":
          if b.attrib['id'] == 'SubSystem Parameters':
            if debug: print b.attrib['id']
            for subsysparam in b:
              if subsysparam.attrib['id'] == "Chassis Serial Number":
                chassisserialnumbers.append(subsysparam.attrib['value'])
        if b.tag == "Device":
          if debug: print "b: %s" % b.tag
          for c in b:
    	  # - logical drives under arrays
    	  # - disk drives under storage enclosures
    	  # {'deviceType': 'PhysicalDrive', 'marketingName': 'Physical Drive (4 
    	    if c.attrib != {}:
      	      try: 
                    devicetype = c.attrib['deviceType']
    	      except KeyError:
    	        if debug: print "no deviceType for: %s" % c.attrib
    	        continue
              marketingName = c.attrib['marketingName']
              if devicetype == "PhysicalDrive":
	        disk_dict[marketingName] = { }
    	        for d in c:
    	        # physical drive status
    	          if d.attrib != {}:
    	            if debug: print d.attrib
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

  [ report1, chassisserialnumbers1 ] = return_disks_bus_faults_dict(root)
  [ report2, chassisserialnumbers2 ] = return_disks_bus_faults_dict(root2)
  if chassisserialnumbers1 != chassisserialnumbers2:
    print "comparing differente chassis"

  print "disk, value2, value1, diff"
  no_diff_cnt = 0
  diff_cnt = 0
  for disk in report2:
  	value2 = int(report2[disk], 16)
  	value1 = int(report1[disk], 16)
	diff = value2 - value1
  	if value2 != value1:
		diff_cnt = diff_cnt + 1
  		print "%s, %s, %s, %s" % (disk, value2,value1, diff)
	else:
		no_diff_cnt = no_diff_cnt + 1
		if debug: print "%s, %s, %s, %s" % (disk, value2,value1, diff)
  if no_diff_cnt > 0 and diff_cnt < 1:
    print "no differences in the counters between any disks in the reports"
