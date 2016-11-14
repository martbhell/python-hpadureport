#!/usr/bin/python
# Script to parse HP SSA diagnostic reports
# Written by Johan Guldmyr 2016
#
# Currently it:
# - parses the "bus faults" of all the hard drives.
# - outputs when the value is different in the two xml files
#
# Example output:
#$ python hpadureport_compare.py |sort|head
#disk, value2, value1
#Physical Drive (4 TB SAS HDD) 1I:1:32, 0x00000027, 0x00000023
#Physical Drive (4 TB SAS HDD) 1I:1:33, 0x00000030, 0x00000028
#Physical Drive (4 TB SAS HDD) 1I:1:37, 0x00000019, 0x0000000e
#

import xml.etree.ElementTree as ET
tree = ET.parse('2/ADUReport.xml')
tree2 = ET.parse('3/ADUReport.xml')
root = tree.getroot()
root2 = tree2.getroot()

debug = False

# Top level schema:
#<ADUReport>
#<MetaProperty id="ADU Version" value="2.40.13.0"/>
#<MetaProperty id="Diagnostic Module Version" value="8.4.13.0"/>
#<MetaProperty id="Time Generated" value="Monday November 14, 2016 10:37:26AM"/>
#<Device deviceType="ArrayController" id="AC:1234567890" marketingName="Smart Array P440 in slot 1">...</Device>
#<Device deviceType="ArrayController" id="AC:1234456789" marketingName="Smart Array P440 in slot 2">...</Device>
#<Device deviceType="ArrayController" id="AC:123456789" marketingName="Dynamic Smart Array B140i in slot 0b">...</Device>
#</ADUReport>

def return_disks_bus_faults_dict(root):

  """
  single argument is an xml "root" of an ADUreport.xml
  return a dictionary with each key being "marketingName" of the physical drives
  
  example output:
  {'Physical Drive (4 TB SAS HDD) 1I:1:40': '0x00000001', 'Physical Drive (4 TB SAS HDD) 1I:1:43': '0x00000009', 'Physical Drive (4 TB SAS HDD) 1I:1:61': '0x0000000c', 'Physical Drive (4 TB SAS HDD) 1I:1:57': '0x00000013', 'Physical Drive (4 TB SAS HDD) 1I:1:60': '0x00000001'}

  """

  disk_dict = {}

  for a in root:
  # controller
    if a.tag == "Device":
      for b in a:
        # array or storage enclosure
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
    	            if debug: print d.attrib
    	            for e in d:
    	              id = e.attrib['id']
    	              if id == "Bus Faults":
                        bus_faults = e.attrib['value']
    	                if debug: print "%s : %s" % (marketingName,bus_faults)
                        disk_dict[marketingName] = bus_faults
  return(disk_dict)

report1 = return_disks_bus_faults_dict(root)
report2 = return_disks_bus_faults_dict(root2)

print "disk, value2, value1"
for disk in report2:
	value2 = report2[disk]
	value1 = report1[disk]
	#print "%s : %s" % (value2,value1)
	if value2 != value1:
		print "%s, %s, %s" % (disk, value2,value1)
