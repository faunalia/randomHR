########################################################
#                                         __init__.py  #
########################################################
#    AniMove project
#    Random HR plugin
#    Randomization of home ranges within a study area
#    (write here a description)
#    by Borys Jurgiel for Faunalia and University of Florence
#    email: borysiasty@aster.pl
########################################################
#
#    Copyright (C) 2009  Borys Jurgiel
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of the GNU General Public License is available at
#    http://www.gnu.org/licenses/gpl.txt, or can be requested to the Free
#    Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
#    Boston, MA 02110-1301 USA.
#
########################################################

def name():
  return 'Random HR'

def description():
  return 'AniMove: Randomization of home ranges within a study area'

def version():
  return 'Version 0.2.3'

def qgisMinimumVersion():
  return '1.0.0'

def authorName():
  return 'Borys Jurgiel for Faunalia and University of Florence'

def author():
  return authorName()

def email():
  return 'qgis@borysjurgiel.pl'

def icon():
  return "icons/randomHRIcon.png"

def homepage():
  return 'http://www.faunalia.it/animove'

def classFactory(iface):
  from randomHR_plugin import randomHR
  return randomHR(iface)
