#----------------------------------------------------------------------------
# 
# randomHR
# Copyright (C) 2009 Borys Jurgiel for Faunalia and University of Florence
#
#----------------------------------------------------------------------------
# 
# licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 
#----------------------------------------------------------------------------

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from ui.randomHRbase_ui import Ui_Dialog
import resources_rc
import random
from math import *
from qgis.utils import plugins


fieldSeparators = [',',';']
decSeparators = ['.',',']

class randomHR:

  def __init__(self, iface):
    self.iface = iface


  def initGui(self):
    # create action 
    self.action = QAction(QIcon(':/plugins/randomHR/icons/randomHRIcon.png'), 'Random HR', self.iface.mainWindow())
    self.action.setWhatsThis('AniMove: Random home range overlap')
    QObject.connect(self.action, SIGNAL('triggered()'), self.run)
    self.iface.addPluginToMenu('&AniMove', self.action)
    try:
      self.toolBar = plugins['HomeRange_plugin'].toolBar
    except:
      try:
        self.toolBar = plugins['triangulation'].toolBar
      except:
        self.toolBar = self.iface.addToolBar("AniMove")
        self.toolBar.setObjectName('AniMoveToolBar')
    self.toolBar.addAction(self.action)

  def unload(self):
    self.iface.removePluginMenu('&AniMove',self.action)
    self.toolBar.removeAction(self.action)
    if not self.toolBar.actions(): 
      del self.toolBar

  def run(self):
    dialog = Dialog(self.iface)
    dialog.exec_()



#----------------------------------------------------------------------------



class Dialog(QDialog, Ui_Dialog):
  def __init__(self, iface):
    QDialog.__init__(self)
    self.iface = iface
    self.setupUi(self)
    settings = QSettings()
    self.fieldSeparator = settings.value('/AniMove/randomHR/fieldSeparator', QVariant(fieldSeparators[0])).toString()
    self.decSeparator = settings.value ('/AniMove/randomHR/decSeparator', QVariant(decSeparators[0])).toString()
    if not fieldSeparators.count(self.fieldSeparator):
      self.fieldSeparator = fieldSeparators[0]
    if not decSeparators.count(self.decSeparator):
      self.decSeparator = decSeparators[0]
    if self.fieldSeparator == self.decSeparator: # you can't set the same character for both separators!
      self.fieldSeparator = fieldSeparators[0]
      self.decSeparator = decSeparators[0]

    for i in fieldSeparators:
      self.comboFieldSep.addItem(i)
    for i in decSeparators:
      self.comboDecSep.addItem(i)
    self.comboFieldSep.setCurrentIndex(fieldSeparators.index(self.fieldSeparator))
    self.comboDecSep.setCurrentIndex(decSeparators.index(self.decSeparator))

    self.inSrc.clear()
    self.inFrame.clear()
    self.layers = []
    for i in range(self.iface.mapCanvas().layerCount()):
      layer = self.iface.mapCanvas().layer(i)
      if ( layer.type() == layer.VectorLayer ) and ( layer.geometryType() == QGis.Polygon ):
        self.layers += [layer]
        self.inSrc.addItem(layer.name())
        self.inFrame.addItem(layer.name())

    (n, boolvar) = settings.value('/AniMove/randomHR/iterationNumber', QVariant(10)).toInt()
    if not n in range(1,1000):
       n = 10
    self.spinN.setValue(n)

    self.progressBar.reset()
    QObject.connect(self.butAbout, SIGNAL('clicked()'), self.about)
    QObject.connect(self.butRun, SIGNAL('clicked()'), self.analyse)
    QObject.connect(self.butSaveSummary, SIGNAL('clicked()'), self.saveSummary)
    QObject.connect(self.butSaveRawData, SIGNAL('clicked()'), self.saveRawData)
    QObject.connect(self.spinN, SIGNAL('valueChanged ( int )'), self.iterationNumberChanged)
    QObject.connect(self.comboFieldSep, SIGNAL('currentIndexChanged ( int )'), self.separatorChanged)
    QObject.connect(self.comboDecSep, SIGNAL('currentIndexChanged ( int )'), self.separatorChanged)
    #QObject.connect(self.butStop, SIGNAL("clicked()"), self.stop)
    #self.stopRequested = False
    #self.butStop.setEnabled(False)


  def about(self):
    from DlgAbout import DlgAbout
    dialog = DlgAbout(self)
    dialog.exec_()

 

  def iterationNumberChanged(self, indx):
    settings = QSettings()
    settings.setValue('/AniMove/randomHR/iterationNumber', QVariant(self.spinN.value()))



  def separatorChanged(self, indx):
    if self.comboFieldSep.currentText() == self.comboDecSep.currentText():
      QMessageBox.warning(self,'AniMove: randomHR', 'You can\'t set the same character for both separators!')
      self.comboFieldSep.setCurrentIndex(fieldSeparators.index(self.fieldSeparator))
      self.comboDecSep.setCurrentIndex(decSeparators.index(self.decSeparator))
    else:
      self.fieldSeparator = self.comboFieldSep.currentText()
      self.decSeparator = self.comboDecSep.currentText()
      settings = QSettings()
      settings.setValue('/AniMove/randomHR/fieldSeparator', QVariant(self.fieldSeparator))
      settings.setValue('/AniMove/randomHR/decSeparator', QVariant(self.decSeparator))
  


#  def stop(self):
#    self.stopRequested = True



  def analyse(self):
    if self.inSrc.currentIndex() == self.inFrame.currentIndex():
      QMessageBox.warning(self,'AniMove: randomHR', 'Please choose two different layers!')
      return
    layerSrc = self.layers[self.inSrc.currentIndex()]
    layerFrame = self.layers[self.inFrame.currentIndex()]
    provSrc = layerSrc.dataProvider()
    provFrame = layerFrame.dataProvider()
    
    if provFrame.featureCount() != 1:
      QMessageBox.warning(self,'AniMove: randomHR', 'The study area layer should contain exactly one polygon or multipolygon!')
      return

    #lock widgets
    self.progressBar.setMinimum(0)
    self.progressBar.setMaximum(0)
    self.lockWidgets(True)
    n = self.spinN.value()
    self.textEdit.setPlainText('Analyzing data (this may take some time)...\n')
    self.repaint()
    self.repaint()

    #prepare the Frame polygon & rect
    provFrame.select()
    provFrame.rewind()
    frameFeat = QgsFeature()
    provFrame.featureAtId(0,frameFeat)
    frameRect=frameFeat.geometry().boundingBox()
    outside = QgsGeometry().fromRect(frameRect).difference(frameFeat.geometry())

    #copy all home ranges to the memory provider layer and measure areas
    layerHR = QgsVectorLayer('MultiPolygon', 'randomHR', 'memory')   #!!!'MultiPolygon'
    self.provHR = layerHR.dataProvider()
    provSrc.select()
    provSrc.rewind()
    feat = QgsFeature()
    self.ranges = []
    while provSrc.nextFeature(feat):
      self.provHR.addFeatures([feat])
      self.ranges += [QgsDistanceArea().measure(feat.geometry())]

    # analyze source overlaps
    self.overlaps = []  #[x][y][iteration]
    self.overlapsTotal = [] #[iteration]
    self.overlaps += self.calculateOverlaps()
    self.overlapsTotal += [self.sum2d(self.overlaps[0])]
    self.textEdit.append('--------------------------------------------------------')
    self.textEdit.append('Number of homeranges: '+str(len(self.ranges)))
    self.textEdit.append('Total area of the homeranges: '+str(round(sum(self.ranges),3)))
    self.textEdit.append('--------------------------------------------------------')
    self.textEdit.append('                   | total overlap area |         SD    ')
    self.textEdit.append('-------------------+--------------------+---------------')
    self.textEdit.append('observed           |%s |        n/a    ' % QString(str(round(self.overlapsTotal[0],3))).rightJustified(19))
    self.textEdit.append('-------------------+--------------------+---------------')

    #the main loop
    self.progressBar.setMaximum(n)
    self.provHR.select()
    i = 0
    while i < n: # and not self.stopRequested:
      i += 1
      #move HRs randomly
      feat = QgsFeature()
      self.provHR.rewind()
      while self.provHR.nextFeature(feat):
        sticksOut = True
        while sticksOut:
          #rotate the HR. If the HR keeps sticking out after 50 moves, rotate again 
          geom = self.rotate(feat.geometry())
          #repeat moving the HR until doesn't stick out (but max 50 times)
          tries = 0
          while sticksOut and tries < 50:
            geom = self.move(geom, frameRect)
            sticksOut = outside.intersects(geom)
            tries += 1
        self.provHR.changeGeometryValues({feat.id():geom})

      self.overlaps += self.calculateOverlaps()
      overlap = self.sum2d(self.overlaps[len(self.overlaps)-1])
      self.overlapsTotal += [overlap]
      self.textEdit.append('iteration %s|%s |        n/a    ' % (QString(str(i)).leftJustified(9), QString(str(round(overlap,3))).rightJustified(19)))
      self.progressBar.setValue(i)
      self.repaint()

    (mean, sd) = self.calculateStats()
    
    self.textEdit.append('-------------------+--------------------+---------------')
    self.textEdit.append('mean               |%s |%s ' % (QString(str(round(mean,3))).rightJustified(19),QString(str(round(sd,3))).rightJustified(14)))
    self.textEdit.append('--------------------------------------------------------\n')
    self.textEdit.append('RESULT')
    dist = self.overlapsTotal[0] - mean
    if dist > 0:
      s = ' '
      t = 'more'
    else:
      s = ''
      t = 'less'
    self.textEdit.append('Distance between the observed and randomized value is:\n%s%s (the observed one is %s).' % (s,str(round(dist,3)),t))
    self.textEdit.append('The standard deviation is:\n %s' % str(round(sd,3)))
    self.textEdit.append('\nThe last iteration result has been added to the map canvas.')
    layerHR.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayer(layerHR)
    self.progressBar.reset()
    self.lockWidgets(False)



  def lockWidgets(self, state):
    self.inSrc.setEnabled(not state)
    self.inFrame.setEnabled(not state)
    self.spinN.setEnabled(not state)
    self.butRun.setEnabled(not state)
    self.butSaveSummary.setEnabled(not state)
    self.butSaveRawData.setEnabled(not state)



  def saveSummary(self):
    fSep = self.fieldSeparator
    fileDialog = QFileDialog()
    fileDialog.setConfirmOverwrite(False)
    fileName = fileDialog.getSaveFileName(self, 'Output file','.','Comma Separated Values (*.csv)')
    if not fileName:
      return 1
    if fileName.right(3).toUpper() != 'CSV':
      fileName += '.csv'
    try:
      outFile = file(fileName,'w')
      outFile.write('Quantum GIS Random Home Range summary\n')
      outFile.write('Frame layer%s%s\n' % (fSep, self.inFrame.currentText().toLatin1()))
      outFile.write('Home ranges layer%s%s\n' % (fSep, self.inSrc.currentText().toLatin1()))
      outFile.write('Number of the home ranges%s%s\n' % (fSep, self.layers[self.inSrc.currentIndex()].dataProvider().featureCount()))
      outFile.write('Number of iterations%s%s\n\n' % (fSep, str(len(self.overlaps)-1)))
      outFile.write(fSep+'total overlap area'+fSep+'SD\n')
      outFile.write('observed'+fSep+str(self.overlapsTotal[0]).replace('.',self.decSeparator)+fSep+'\n')
      for i in range(1,len(self.overlapsTotal)):
        outFile.write('iteration '+str(i)+fSep+str(self.overlapsTotal[i]).replace('.',self.decSeparator)+fSep+'\n')
      (mean, sd) = self.calculateStats()     
      outFile.write('mean'+fSep+str(mean).replace('.',self.decSeparator)+fSep+str(sd).replace('.',self.decSeparator)+'\n')
      outFile.write('observed-randomized'+fSep+str(self.overlapsTotal[0]-mean).replace('.',self.decSeparator)+fSep+'\n\n')
      outFile.close()
      return 0
    except:
      return 2



  def saveRawData(self):
    fileDialog = QFileDialog()
    fileDialog.setConfirmOverwrite(False)
    fileName = fileDialog.getSaveFileName(self, 'Output file','.','Comma Separated Values (*.csv)')
    if not fileName:
      return 1
    if fileName.right(3).toUpper() != 'CSV':
      fileName += '.csv'
    try:
      outFile = file(fileName,'w')
      outFile.write('Quantum GIS Random Home Range raw output\n')
      outFile.write('Frame layer: %s\n' % self.inFrame.currentText().toLatin1())
      outFile.write('Home ranges layer: %s\n' % self.inSrc.currentText().toLatin1())
      outFile.write('Number of the home ranges: %s\n' % self.layers[self.inSrc.currentIndex()].dataProvider().featureCount())
      outFile.write('Number of iterations: %s\n' % str(len(self.overlaps)-1))
      outFile.write('Note: The first column contains the home range area\n\n')
      self.progressBar.setMaximum(len(self.overlaps)-1)
      self.lockWidgets(True)
      for i in range(len(self.overlaps)):
        if i == 0:
          outFile.write('Observed data:\n')
        else : 
          outFile.write('Iteration %s:\n' % str(i))
        for j in range(len(self.overlaps[i])):
          text = str(self.ranges[j]) + self.fieldSeparator
          for k in range(len(self.overlaps[i]) - len(self.overlaps[i][j])):
            text += self.fieldSeparator
          for k in range(len(self.overlaps[i][j])):
            val = self.overlaps[i][j][k]
            text += str(val).replace('.',self.decSeparator) + self.fieldSeparator
          text = text[:len(text)-1] + '\n'
          outFile.write(text)
        self.progressBar.setValue(i)
        self.repaint()
        outFile.write('\n')
      self.progressBar.setValue(0)
      self.lockWidgets(False)
      outFile.close()
      return 0
    except:
      self.progressBar.setValue(0)
      self.lockWidgets(False)
      return 2



  def rotate(self, geom):
    #randomize the angle
    ang = random.uniform(0,2*pi)
    sina = sin(ang)
    cosa = cos(ang)
    i=0 
    # create unique dict of verticles because of overlapping the first and the last one
    uniqueDict = {}
    vertex=geom.vertexAt(i)
    while (vertex.x() != 0 and vertex.y() != 0):
      uniqueDict[i] = vertex
      vertex=geom.vertexAt(i)
      i+=1
    for key in uniqueDict.keys():
      vertex = uniqueDict[key]
      x = cosa * vertex.x() - sina * vertex.y()
      y = sina * vertex.x() + cosa * vertex.y()
      geom.moveVertex(x,y,key)
    return geom



  def move(self, geom, frameRect):
    featRect = geom.boundingBox()
    #compute allowed movement range
    dxMin = frameRect.xMinimum() - featRect.xMinimum()
    dxMax = frameRect.xMaximum() - featRect.xMaximum()
    dyMin = frameRect.yMinimum() - featRect.yMinimum()
    dyMax = frameRect.yMaximum() - featRect.yMaximum()
    #randomize dx and dy
    dx = random.uniform(dxMin,dxMax)
    dy = random.uniform(dyMin,dyMax)
    #move
    geom.translate(dx,dy)
    return geom



  def sum2d(self, data):
    k = 0
    for i in data:
      for j in i:
        k += j
    return k



  def calculateOverlaps(self):
    #collect the geometries
    polygons = []
    feat = QgsFeature()
    self.provHR.select()
    self.provHR.rewind()
    while self.provHR.nextFeature(feat):
      geom = QgsGeometry(feat.geometry())
      polygons += [geom]
    #calculate
    b = []
    for k in range(len(polygons)):
      a = []
      for l in range(k+1,len(polygons)):
        if polygons[k].intersects(polygons[l]):
          overlap = QgsDistanceArea().measure(polygons[k].intersection(polygons[l]))
        else:
          overlap = 0
        a += [overlap]
      b += [a]
    return [b]



  def calculateStats(self):
    data = self.overlapsTotal[1:]
    mean = sum(data)/len(data)
    sd = 0
    for i in data:
      sd+=(i-mean)*(i-mean)
    if len(data)>1:
      sd = sqrt(sd/(len(data)-1))
    else:
      sd = 0
    return (mean, sd)



  #def sumTotalArea(self, provider):
    #area = 0
    #feat = QgsFeature()
    #provider.select()
    #provider.rewind()
    #while provider.nextFeature(feat):
      #geom = QgsGeometry(feat.geometry())
      #area += QgsDistanceArea().measure(geom)
    #return area

