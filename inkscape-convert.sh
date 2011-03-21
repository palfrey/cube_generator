#!/bin/bash

echo "Press return when the dialog box comes up"
inkscape `pwd`/$1 --export-ps /tmp/test.ps
pstoedit -q -f dxf /tmp/test.ps `basename $1 .dxf`-exported.dxf
