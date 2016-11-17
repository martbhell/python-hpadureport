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
#$ python python-hpadureport-parser.py -1 relative_path/1ADUReport.xml -2 relative_path/2ADUReport.xml 
#disk, value2, value1, diff
#Physical Drive (4 TB SAS HDD) 1I:1:32, 27, 23, 4
#Physical Drive (4 TB SAS HDD) 1I:1:33, 30, 28, 2
#Physical Drive (4 TB SAS HDD) 1I:1:37, 19, 16, 3
#
#
</pre>
