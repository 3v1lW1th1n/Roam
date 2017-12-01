BUILDING
===============================

Setting up build
------------------------------

You only need to do this once.

You need:

- [Visual Studio C++ 2008](http://download.microsoft.com/download/A/5/4/A54BADB6-9C3F-478D-8657-93B3FC9FE62D/vcsetup.exe) (This is for the Python compiler for py2exe)
- [QGIS 2.16] http://download.osgeo.org/qgis/windows/QGIS-OSGeo4W-2.16.3-1-Setup-x86.exe

**Note: 2.18 is also supported however the current release is built with 2.16**

**INSTALL NOTE:**  If you get a ValueError when running python setup.py install sometimes it can't run the visual studio batch
file.  Simply run `C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\Tools\vsvars32.bat` in the shell
before running ``setupdev.bat``

1. Download and install Visual Studio C++ Express
2. Run cmd.exe as admin
2. ``scripts\setupdev.bat 2.16``

Building ui files
-----------------------

1. cmd.exe
2. ``build.bat 2.16 build``

``build.bat`` is a make file with commands to build and package Roam

Following commands are supported:

    - build
    - exe
    - release
    - installer
    - test
    - test-only

Creating Exe
----------------------

1. cmd.exe
2. ``build.bat 2.16 exe``

Making release package
----------------------

1. cmd.exe
2. ``build.bat 2.16 release``
