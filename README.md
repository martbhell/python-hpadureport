[![Build Status](https://travis-ci.org/martbhell/python-hpadureport.svg?branch=master)](https://travis-ci.org/martbhell/python-hpadureport)

python-hpadureport-parser
=========================

Dependency python-hostlist is used to reudce output and convert long names of things to shorter names.

Install with:
<pre>
pip install python-hostlist
</pre>

<pre>
#!/usr/bin/python
# Script to parse HP SSA diagnostic reports
# Written by Johan Guldmyr 2016
#
# Example output:
$ python python-hpadureport-parser.py -1 relative_path/1ADUReport.xml -2 relative_path/2ADUReport.xml -e "Bus Faults"
CRITICAL: Error counter different on disks: Physical Drive (4 TB SAS HDD) 1I:1:[32-64] (Wednesday November 23, 2016 8:09:55AM vs Friday December 02, 2016 9:56:30AM)
##
$ python python-hpadureport-parser.py -1 relative_path/1ADUReport.xml -2 relative_path/2ADUReport.xml -e "Bus Faults" -v 
disk, value2, value1, diff
Physical Drive (4 TB SAS HDD) 1I:1:32, 27, 23, 4
Physical Drive (4 TB SAS HDD) 1I:1:33, 30, 28, 2
Physical Drive (4 TB SAS HDD) 1I:1:37, 19, 16, 3
[snip]
CRITICAL: Error counter different on disks: Physical Drive (4 TB SAS HDD) 1I:1:[32-64] (Wednesday November 23, 2016 8:09:55AM vs Friday December 02, 2016 9:56:30AM)

</pre>
