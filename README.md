python-hpadureport-parser
=========================

<pre>
#!/usr/bin/python
# Script to parse HP SSA diagnostic reports
# Written by Johan Guldmyr 2016
#
# Currently it:
# - parses the "Bus Faults" of all the hard drives.
# - outputs when the value is different in the two xml files
#
# Example output:
#$ python hpadureport_compare.py |sort|head
#disk, value2, value1
#Physical Drive (4 TB SAS HDD) 1I:1:32, 0x00000027, 0x00000023
#Physical Drive (4 TB SAS HDD) 1I:1:33, 0x00000030, 0x00000028
#Physical Drive (4 TB SAS HDD) 1I:1:37, 0x00000019, 0x0000000e
#
</pre>
