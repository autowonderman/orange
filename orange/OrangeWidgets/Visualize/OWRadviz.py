"""
<name>Radviz</name>
<description>Shows data using radviz visualization method</description>
<icon>icons/Radviz.png</icon>
<priority>3100</priority>
"""
# Radviz.py
#
# Show data using radviz visualization method
# 

from OWWidget import *
from random import betavariate 
from OWRadvizGraph import *
from OWkNNOptimization import *
from OWClusterOptimization import *
import time
import OWToolbars
import OWGUI

###########################################################################################
##### WIDGET : Radviz visualization
###########################################################################################
class OWRadviz(OWWidget):
    settingsList = ["pointWidth", "jitterSize", "graphCanvasColor", "globalValueScaling", "showFilledSymbols", "scaleFactor",
                    "showLegend", "optimizedDrawing", "useDifferentSymbols", "autoSendSelection", "useDifferentColors",
                    "tooltipKind", "tooltipValue", "toolbarSelection", "showClusters", "VizRankClassifierName", "clusterClassifierName"]
    jitterSizeNums = [0.0, 0.01, 0.1,   0.5,  1,  2 , 3,  4 , 5, 7, 10, 15, 20]
    jitterSizeList = [str(x) for x in jitterSizeNums]
    scaleFactorNums = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
    scaleFactorList = [str(x) for x in scaleFactorNums]
        
    def __init__(self,parent=None, signalManager = None):
        OWWidget.__init__(self, parent, signalManager, "Radviz", TRUE)

        self.inputs = [("Classified Examples", ExampleTableWithClass, self.cdata), ("Example Subset", ExampleTable, self.subsetdata, 1, 1), ("Selection", list, self.selection)]
        self.outputs = [("Selected Examples", ExampleTableWithClass), ("Unselected Examples", ExampleTableWithClass), ("Example Distribution", ExampleTableWithClass), ("Attribute Selection List", AttributeList), ("VizRank learner", orange.Learner), ("Cluster learner", orange.Learner)]
        
        #add a graph widget
        self.box = QVBoxLayout(self.mainArea)
        self.graph = OWRadvizGraph(self, self.mainArea)
        self.box.addWidget(self.graph)
        
        # cluster dialog
        self.clusterDlg = ClusterOptimization(self, self.signalManager, self.graph, "Radviz")
        self.graph.clusterOptimization = self.clusterDlg

        # optimization dialog
        self.optimizationDlg = kNNOptimization(self, self.signalManager, self.graph, "Radviz")
        self.graph.kNNOptimization = self.optimizationDlg
        self.optimizationDlg.optimizeGivenProjectionButton.show()


        # variables
        self.pointWidth = 4
        self.globalValueScaling = 0
        self.jitterSize = 1
        self.jitterContinuous = 0
        self.scaleFactor = 1.0
        self.showLegend = 1
        self.showFilledSymbols = 1
        self.optimizedDrawing = 1
        self.useDifferentSymbols = 0
        self.useDifferentColors = 1
        self.autoSendSelection = 1
        self.tooltipKind = 0
        self.tooltipValue = 0
        self.graphCanvasColor = str(Qt.white.name())
        self.data = None
        self.toolbarSelection = 0
        self.showClusters = 0
        self.VizRankClassifierName = "VizRank classifier (Scatterplot)"
        self.clusterClassifierName = "Visual cluster classifier (Scatterplot)"

        #load settings
        self.loadSettings()

        #GUI
        # add a settings dialog and initialize its values
        self.tabs = QTabWidget(self.space, 'tabWidget')
        self.GeneralTab = QVGroupBox(self)
        #self.GeneralTab.setFrameShape(QFrame.NoFrame)
        self.SettingsTab = QVGroupBox(self)
        self.tabs.insertTab(self.GeneralTab, "General")
        self.tabs.insertTab(self.SettingsTab, "Settings")

        
        #add controls to self.controlArea widget
        self.shownAttribsGroup = QVGroupBox(self.GeneralTab)
        self.addRemoveGroup = QHButtonGroup(self.GeneralTab)
        self.hiddenAttribsGroup = QVGroupBox(self.GeneralTab)
        self.shownAttribsGroup.setTitle("Shown attributes")
        self.hiddenAttribsGroup.setTitle("Hidden attributes")
        self.attrOrderingButtons = QVButtonGroup("Attribute ordering", self.GeneralTab)
        
        self.shownAttribsLB = QListBox(self.shownAttribsGroup)
        self.shownAttribsLB.setSelectionMode(QListBox.Extended)

        self.hiddenAttribsLB = QListBox(self.hiddenAttribsGroup)
        self.hiddenAttribsLB.setSelectionMode(QListBox.Extended)

        self.optimizationDlgButton = OWGUI.button(self.attrOrderingButtons, self, "VizRank optimization dialog", callback = self.optimizationDlg.reshow)
        self.clusterDetectionDlgButton = OWGUI.button(self.attrOrderingButtons, self, "Cluster detection dialog", callback = self.clusterDlg.reshow)
        self.connect(self.clusterDlg.startOptimizationButton , SIGNAL("clicked()"), self.optimizeClusters)
        self.connect(self.clusterDlg.resultList, SIGNAL("selectionChanged()"),self.showSelectedCluster)
        
        self.zoomSelectToolbar = OWToolbars.ZoomSelectToolbar(self, self.GeneralTab, self.graph, self.autoSendSelection)
        self.graph.autoSendSelectionCallback = self.setAutoSendSelection
        self.connect(self.zoomSelectToolbar.buttonSendSelections, SIGNAL("clicked()"), self.sendSelections)
                               
        self.hbox2 = QHBox(self.shownAttribsGroup)
        self.buttonUPAttr = QPushButton("Attr UP", self.hbox2)
        self.buttonDOWNAttr = QPushButton("Attr DOWN", self.hbox2)

        self.attrAddButton = QPushButton("Add attr.", self.addRemoveGroup)
        self.attrRemoveButton = QPushButton("Remove attr.", self.addRemoveGroup)

        # ####################################
        # SETTINGS TAB
        # #####
        OWGUI.hSlider(self.SettingsTab, self, 'pointWidth', box='Point Width', minValue=1, maxValue=15, step=1, callback = self.updateValues, ticks=1)

        box = OWGUI.widgetBox(self.SettingsTab, " Jittering options ")
        OWGUI.comboBoxWithCaption(box, self, "jitterSize", 'Jittering size (% of size)  ', callback = self.setJitteringSize, items = self.jitterSizeNums, sendSelectedValue = 1, valueType = float)
        OWGUI.checkBox(box, self, 'jitterContinuous', 'Jitter continuous attributes', callback = self.setJitterCont, tooltip = "Does jittering apply also on continuous attributes?")
        OWGUI.comboBoxWithCaption(self.SettingsTab, self, "scaleFactor", 'Scale point position by: ', box = " Point scaling ", callback = self.updateValues, items = self.scaleFactorNums, sendSelectedValue = 1, valueType = float)

        box3 = OWGUI.widgetBox(self.SettingsTab, " General graph settings ")
        
        OWGUI.checkBox(box3, self, 'showLegend', 'Show legend', callback = self.updateValues)
        OWGUI.checkBox(box3, self, 'globalValueScaling', 'Use global value scaling', callback = self.setGlobalValueScaling)
        OWGUI.checkBox(box3, self, 'optimizedDrawing', 'Optimize drawing (biased)', callback = self.updateValues, tooltip = "Speed up drawing by drawing all point belonging to one class value at once")
        OWGUI.checkBox(box3, self, 'useDifferentSymbols', 'Use different symbols', callback = self.updateValues, tooltip = "Show different class values using different symbols")
        OWGUI.checkBox(box3, self, 'useDifferentColors', 'Use different colors', callback = self.updateValues, tooltip = "Show different class values using different colors")
        OWGUI.checkBox(box3, self, 'showFilledSymbols', 'Show filled symbols', callback = self.updateValues)
        OWGUI.checkBox(box3, self, 'showClusters', 'Show clusters', callback = self.updateValues, tooltip = "Show a line boundary around a significant cluster")

        box2 = OWGUI.widgetBox(self.SettingsTab, " Tooltips settings ")
        OWGUI.comboBox(box2, self, "tooltipKind", items = ["Show line tooltips", "Show visible attributes", "Show all attributes"], callback = self.updateValues)
        OWGUI.comboBox(box2, self, "tooltipValue", items = ["Tooltips show data values", "Tooltips show spring values"], callback = self.updateValues, tooltip = "Do you wish that tooltips would show you original values of visualized attributes or the 'spring' values (values between 0 and 1). \nSpring values are scaled values that are used for determining the position of shown points. Observing these values will therefore enable you to \nunderstand why the points are placed where they are.")

        box4 = OWGUI.widgetBox(self.SettingsTab, " Sending selection ")
        OWGUI.checkBox(box4, self, 'autoSendSelection', 'Auto send selected data', callback = self.setAutoSendSelection, tooltip = "Send signals with selected data whenever the selection changes.")
        self.setAutoSendSelection()

        # ####
        self.gSetCanvasColorB = QPushButton("Canvas Color", self.SettingsTab)
        self.connect(self.gSetCanvasColorB, SIGNAL("clicked()"), self.setGraphCanvasColor)


        # ####################################
        # K-NN OPTIMIZATION functionality
        self.connect(self.optimizationDlg.optimizeGivenProjectionButton, SIGNAL("clicked()"), self.optimizeGivenProjectionClick)
        self.connect(self.optimizationDlg.resultList, SIGNAL("selectionChanged()"),self.showSelectedAttributes)
        self.connect(self.optimizationDlg.startOptimizationButton , SIGNAL("clicked()"), self.optimizeSeparation)
        self.connect(self.optimizationDlg.reevaluateResults, SIGNAL("clicked()"), self.reevaluateProjections)

        self.connect(self.optimizationDlg.evaluateProjectionButton, SIGNAL("clicked()"), self.evaluateCurrentProjection)
        self.connect(self.optimizationDlg.showKNNCorrectButton, SIGNAL("clicked()"), self.showKNNCorect)
        self.connect(self.optimizationDlg.showKNNWrongButton, SIGNAL("clicked()"), self.showKNNWrong)

        self.connect(self.buttonUPAttr, SIGNAL("clicked()"), self.moveAttrUP)
        self.connect(self.buttonDOWNAttr, SIGNAL("clicked()"), self.moveAttrDOWN)

        self.connect(self.attrAddButton, SIGNAL("clicked()"), self.addAttribute)
        self.connect(self.attrRemoveButton, SIGNAL("clicked()"), self.removeAttribute)

        self.connect(self.graphButton, SIGNAL("clicked()"), self.graph.saveToFile)

        self.connect(self.optimizationDlg.classifierNameEdit, SIGNAL("textChanged(const QString &)"), self.VizRankClassifierNameChanged)
        self.connect(self.clusterDlg.classifierNameEdit, SIGNAL("textChanged(const QString &)"), self.clusterClassifierNameChanged)
        
        # add a settings dialog and initialize its values
        self.activateLoadedSettings()
        self.resize(900, 700)


    # #########################
    # OPTIONS
    # #########################
    def activateLoadedSettings(self):
        self.graph.updateSettings(showLegend = self.showLegend, showFilledSymbols = self.showFilledSymbols, optimizedDrawing = self.optimizedDrawing, tooltipValue = self.tooltipValue, tooltipKind = self.tooltipKind)
        self.graph.useDifferentSymbols = self.useDifferentSymbols
        self.graph.useDifferentColors = self.useDifferentColors
        self.graph.pointWidth = self.pointWidth
        self.graph.globalValueScaling = self.globalValueScaling
        self.graph.jitterSize = self.jitterSize
        self.graph.scaleFactor = self.scaleFactor
        self.graph.showClusters = self.showClusters
        self.graph.setCanvasBackground(QColor(self.graphCanvasColor))
        apply([self.zoomSelectToolbar.actionZooming, self.zoomSelectToolbar.actionRectangleSelection, self.zoomSelectToolbar.actionPolygonSelection][self.toolbarSelection], [])

        self.optimizationDlg.classifierName = self.VizRankClassifierName
        self.optimizationDlg.classifierNameChanged(self.VizRankClassifierName)
        self.clusterDlg.classifierName = self.clusterClassifierName
        self.clusterDlg.classifierNameChanged(self.clusterClassifierName)

    def VizRankClassifierNameChanged(self, text):
        self.VizRankClassifierName = self.optimizationDlg.classifierName

    def clusterClassifierNameChanged(self, text):
        self.clusterClassifierName = self.clusterDlg.classifierName

    # #########################
    # KNN OPTIMIZATION BUTTON EVENTS
    # #########################
    def saveCurrentProjection(self):
        qname = QFileDialog.getSaveFileName( os.path.realpath(".") + "/Radviz_projection.tab", "Orange Example Table (*.tab)", self, "", "Save File")
        if qname.isEmpty(): return
        name = str(qname)
        if len(name) < 4 or name[-4] != ".":
            name = name + ".tab"
        self.graph.saveProjectionAsTabData(name, self.getShownAttributeList())

    def showKNNCorect(self):
        self.optimizationDlg.showKNNWrongButton.setOn(0)
        self.showSelectedAttributes()

    # show quality of knn model by coloring accurate predictions with lighter color and bad predictions with dark color
    def showKNNWrong(self):
        self.optimizationDlg.showKNNCorrectButton.setOn(0) 
        self.showSelectedAttributes()


    # evaluate knn accuracy on current projection
    def evaluateCurrentProjection(self):
        acc, other_results = self.graph.getProjectionQuality(self.getShownAttributeList())
        if self.data.domain.classVar.varType == orange.VarTypes.Continuous:
            QMessageBox.information( None, "Radviz", 'Mean square error of kNN model is %.2f'%(acc), QMessageBox.Ok + QMessageBox.Default)
        else:
            if self.optimizationDlg.getQualityMeasure() == CLASS_ACCURACY:
                QMessageBox.information( None, "Radviz", 'Classification accuracy of kNN model is %.2f %%'%(acc), QMessageBox.Ok + QMessageBox.Default)
            elif self.optimizationDlg.getQualityMeasure() == AVERAGE_CORRECT:
                QMessageBox.information( None, "Radviz", 'Average probability of correct classification is %.2f %%'%(acc), QMessageBox.Ok + QMessageBox.Default)
            else:
                QMessageBox.information( None, "Radviz", 'Brier score of kNN model is %.2f' % (acc), QMessageBox.Ok + QMessageBox.Default)
            
    # reevaluate projections in result list with different k values
    def reevaluateProjections(self):
        results = list(self.optimizationDlg.getShownResults())
        self.optimizationDlg.clearResults()

        self.progressBarInit()
        self.optimizationDlg.disableControls()

        testIndex = 0
        for (acc, other, tableLen, attrList, tryIndex, strList) in results:
            if self.optimizationDlg.isOptimizationCanceled(): continue
            testIndex += 1
            self.progressBarSet(100.0*testIndex/float(len(results)))

            accuracy, other_results = self.graph.getProjectionQuality(attrList)            
            self.optimizationDlg.addResult(accuracy, other_results, tableLen, attrList, tryIndex, strList)

        self.progressBarFinished()
        self.optimizationDlg.enableControls()
        self.optimizationDlg.finishedAddingResults()
        
    # ################################################################################################
    # find projections where different class values are well separated
    def optimizeSeparation(self):
        if self.data == None: return
        if not self.data.domain.classVar:
            QMessageBox.critical( None, "VizRank Dialog", 'Projections can be evaluated only in datasets with a class value.', QMessageBox.Ok)
            return
        
        listOfAttributes = self.optimizationDlg.getEvaluatedAttributes(self.data)

        text = str(self.optimizationDlg.attributeCountCombo.currentText())
        if text == "ALL": maxLen = len(listOfAttributes)
        else:             maxLen = int(text)
        
        if self.optimizationDlg.getOptimizationType() == self.optimizationDlg.EXACT_NUMBER_OF_ATTRS: minLen = maxLen
        else: minLen = 3

        self.optimizationDlg.clearResults()

        possibilities = 0
        for i in range(minLen, maxLen+1):
            possibilities += combinations(i, len(listOfAttributes))*fact(i-1)/2
            
        self.graph.totalPossibilities = possibilities
        self.graph.triedPossibilities = 0
    
        if self.graph.totalPossibilities > 20000:
            self.warning("There are %s possible radviz projections with this set of attributes"% (createStringFromNumber(self.graph.totalPossibilities)))
        
        self.optimizationDlg.disableControls()
        
        try:
            self.graph.getOptimalSeparation(listOfAttributes, minLen, maxLen, self.optimizationDlg.addResult)
        except:
            type, val, traceback = sys.exc_info()
            sys.excepthook(type, val, traceback)  # print the exception

        self.optimizationDlg.enableControls()
        self.optimizationDlg.finishedAddingResults()
    

    # ################################################################################################
    # find projections that have tight clusters of points that belong to the same class value
    def optimizeClusters(self):
        if self.data == None: return
        if not self.data.domain.classVar or not self.data.domain.classVar.varType == orange.VarTypes.Discrete:
            QMessageBox.critical( None, "Cluster Detection Dialog", 'Clusters can be detected only in data sets with a discrete class value', QMessageBox.Ok)
            return

        listOfAttributes = self.optimizationDlg.getEvaluatedAttributes(self.data)

        text = str(self.optimizationDlg.attributeCountCombo.currentText())
        if text == "ALL": maxLen = len(listOfAttributes)
        else:             maxLen = int(text)
        
        if self.clusterDlg.getOptimizationType() == self.clusterDlg.EXACT_NUMBER_OF_ATTRS: minLen = maxLen
        else: minLen = 3

        self.clusterDlg.clearResults()
        self.clusterDlg.clusterStabilityButton.setOn(0)
        self.clusterDlg.pointStability = None
        
        possibilities = 0
        for i in range(minLen, maxLen+1): possibilities += combinations(i, len(listOfAttributes))*fact(i-1)/2
            
        self.graph.totalPossibilities = possibilities
        self.graph.triedPossibilities = 0
    
        if self.graph.totalPossibilities > 20000:
            proj = str(self.graph.totalPossibilities)
            l = len(proj)
            for i in range(len(proj)-2, 0, -1):
                if (l-i)%3 == 0: proj = proj[:i] + "," + proj[i:]
            self.warning("There are %s possible radviz projections using currently visualized attributes"% (proj))
        
        self.clusterDlg.disableControls()
        try:
            self.graph.getOptimalClusters(listOfAttributes, minLen, maxLen, self.clusterDlg.addResult)
        except:
            type, val, traceback = sys.exc_info()
            sys.excepthook(type, val, traceback)  # print the exception

        self.clusterDlg.enableControls()
        self.clusterDlg.finishedAddingResults()
   

    # ################################################################################################
    # try to find a better projection than the currently shown projection by adding other attributes to the projection and evaluating projections
    def optimizeGivenProjectionClick(self):
        self.optimizationDlg.disableControls()
        acc = self.graph.getProjectionQuality(self.getShownAttributeList())[0]
        # try to find a better separation than the one that is currently shown
        self.graph.optimizeGivenProjection(self.getShownAttributeList(), acc, self.optimizationDlg.getEvaluatedAttributes(self.data), self.optimizationDlg.addResult)
        self.optimizationDlg.enableControls()
        self.optimizationDlg.finishedAddingResults()


    # send signals with selected and unselected examples as two datasets
    def sendSelections(self):
        if not self.data: return
        (selected, unselected, merged) = self.graph.getSelectionsAsExampleTables(self.getShownAttributeList())
    
        self.send("Selected Examples",selected)
        self.send("Unselected Examples",unselected)
        self.send("Example Distribution", merged)

    def sendShownAttributes(self):
        attributes = []
        for i in range(self.shownAttribsLB.count()):
            attributes.append(str(self.shownAttribsLB.text(i)))
        self.send("Attribute Selection List", attributes)


    # ####################################
    # show selected interesting projection
    def showSelectedAttributes(self):
        self.graph.removeAllSelections()
        val = self.optimizationDlg.getSelectedProjection()
        if not val: return
        (accuracy, other_results, tableLen, attrList, tryIndex, strList) = val
        
        kNNValues = None
        if self.optimizationDlg.showKNNCorrectButton.isOn() or self.optimizationDlg.showKNNWrongButton.isOn():
            shortData = self.graph.createProjectionAsExampleTable([self.graph.attributeNames.index(attr) for attr in attrList])
            kNNValues = self.optimizationDlg.kNNClassifyData(shortData)
            if self.optimizationDlg.showKNNCorrectButton.isOn(): kNNValues = [1.0 - val for val in kNNValues]
            clusterClosure = self.graph.clusterClosure
        else: clusterClosure = None

        self.showAttributes(attrList, kNNValues, clusterClosure)


    def showSelectedCluster(self):
        self.graph.removeAllSelections()
        val = self.clusterDlg.getSelectedCluster()
        if not val: return
        (value, closure, vertices, attrList, classValue, enlargedClosure, other, strList) = val

        if self.clusterDlg.clusterStabilityButton.isOn():
            validData = self.graph.getValidList([self.graph.attributeNames.index(attr) for attr in attrList])
            insideColors = Numeric.compress(validData, self.clusterDlg.pointStability)
        else: insideColors = None
        
        self.showAttributes(attrList, insideColors, clusterClosure = (closure, enlargedClosure, classValue))        

        if type(other) == dict:
            for vals in other.values():
                print "class = %s\nvalue = %.2f   points = %d\ndist = %.4f   averageDist = %.4f\n-------" % (self.data.domain.classVar.values[vals[0]], vals[1], vals[2], vals[3], vals[5])
        else:
            print "class = %s\nvalue = %.2f   points = %d\ndist = %.4f   averageDist = %.4f\n-------" % (self.data.domain.classVar.values[other[0]], other[1], other[2], other[3], other[5])
        print "---------------------------"
        

    def showAttributes(self, attrList, insideColors = None, clusterClosure = None):
        if not self.setShownAttributes(attrList): return
        
        self.graph.updateData(attrList, insideColors = insideColors, clusterClosure = clusterClosure)
        self.graph.repaint()
        self.sendShownAttributes()


        
    # ####################
    # LIST BOX FUNCTIONS
    # ####################
    def getShownAttributeList(self):
        list = []
        for i in range(self.shownAttribsLB.count()):
            list.append(str(self.shownAttribsLB.text(i)))
        return list
    
    def setShownAttributes(self, attributes):
        self.shownAttribsLB.clear()
        self.hiddenAttribsLB.clear()
        for attr in attributes: self.shownAttribsLB.insertItem(attr)
        for attr in self.data.domain:
            if attr.name not in attributes: self.hiddenAttribsLB.insertItem(attr.name)
        return 1

    # move selected attribute in "Attribute Order" list one place up
    def moveAttrUP(self):
        self.graph.removeAllSelections()
        self.graph.insideColors = None; self.graph.clusterClosure = None
        for i in range(self.shownAttribsLB.count()):
            if self.shownAttribsLB.isSelected(i) and i != 0:
                text = self.shownAttribsLB.text(i)
                self.shownAttribsLB.removeItem(i)
                self.shownAttribsLB.insertItem(text, i-1)
                self.shownAttribsLB.setSelected(i-1, TRUE)
        self.sendShownAttributes()
        self.updateGraph()

    # move selected attribute in "Attribute Order" list one place down  
    def moveAttrDOWN(self):
        self.graph.removeAllSelections()
        self.graph.insideColors = None; self.graph.clusterClosure = None
        count = self.shownAttribsLB.count()
        for i in range(count-2,-1,-1):
            if self.shownAttribsLB.isSelected(i):
                text = self.shownAttribsLB.text(i)
                self.shownAttribsLB.removeItem(i)
                self.shownAttribsLB.insertItem(text, i+1)
                self.shownAttribsLB.setSelected(i+1, TRUE)
        self.sendShownAttributes()
        self.updateGraph()

    def addAttribute(self):
        self.graph.removeAllSelections()
        self.graph.insideColors = None; self.graph.clusterClosure = None
        count = self.hiddenAttribsLB.count()
        pos   = self.shownAttribsLB.count()
        for i in range(count-1, -1, -1):
            if self.hiddenAttribsLB.isSelected(i):
                text = self.hiddenAttribsLB.text(i)
                self.hiddenAttribsLB.removeItem(i)
                self.shownAttribsLB.insertItem(text, pos)
        if self.globalValueScaling == 1:
            self.graph.rescaleAttributesGlobaly(self.data, self.getShownAttributeList())
        self.sendShownAttributes()
        self.updateGraph()
        self.graph.replot()

    def removeAttribute(self):
        self.graph.removeAllSelections()
        self.graph.insideColors = None; self.graph.clusterClosure = None
        count = self.shownAttribsLB.count()
        pos   = self.hiddenAttribsLB.count()
        for i in range(count-1, -1, -1):
            if self.shownAttribsLB.isSelected(i):
                text = self.shownAttribsLB.text(i)
                self.shownAttribsLB.removeItem(i)
                self.hiddenAttribsLB.insertItem(text, pos)
        if self.globalValueScaling == 1:
            self.graph.rescaleAttributesGlobaly(self.data, self.getShownAttributeList())
        self.sendShownAttributes()
        self.updateGraph()
        self.graph.replot()

    # #####################

    def updateGraph(self, *args):
        self.graph.updateData(self.getShownAttributeList())
        self.graph.update()
        self.repaint()

    # #########################
    # RADVIZ SIGNALS
    # #########################    
    
    # ###### CDATA signal ################################
    # receive new data and update all fields
    def cdata(self, data, clearResults = 1):
        if data:
            name = ""
            if hasattr(data, "name"): name = data.name
            data = orange.Preprocessor_dropMissingClasses(data)
            data.name = name
        if self.data != None and data != None and self.data.checksum() == data.checksum(): return    # check if the new data set is the same as the old one
        exData = self.data
        self.data = data
        self.graph.setData(self.data)
        self.optimizationDlg.setData(data)  
        self.clusterDlg.setData(data, clearResults)
        self.graph.insideColors = None; self.graph.clusterClosure = None
        
        if not (data and exData and str(exData.domain.attributes) == str(data.domain.attributes)): # preserve attribute choice if the domain is the same                
            self.shownAttribsLB.clear()
            self.hiddenAttribsLB.clear()
            if data:
                for i in range(len(data.domain.attributes)):
                    if i < 50: self.shownAttribsLB.insertItem(data.domain.attributes[i].name)
                    else: self.hiddenAttribsLB.insertItem(data.domain.attributes[i].name)
                if data.domain.classVar: self.hiddenAttribsLB.insertItem(data.domain.classVar.name)
                
        self.updateGraph()
        self.sendSelections()
        self.sendShownAttributes()

    def subsetdata(self, data, update = 1):
        if self.graph.subsetData != None and data != None and self.graph.subsetData.checksum() == data.checksum(): return    # check if the new data set is the same as the old one
        self.graph.subsetData = data
        if update: self.updateGraph()
        self.optimizationDlg.setSubsetData(data)
        self.clusterDlg.setSubsetData(data)
       

    # ###### SELECTION signal ################################
    # receive info about which attributes to show
    def selection(self, list):
        self.shownAttribsLB.clear()
        self.hiddenAttribsLB.clear()

        if self.data == None: return

        for attr in self.data.domain:
            if attr.name in list: self.shownAttribsLB.insertItem(attr.name)
            else:                 self.hiddenAttribsLB.insertItem(attr.name)

        self.updateGraph()
    # ################################################

    # #########################
    # RADVIZ EVENTS
    # #########################
    def updateValues(self):
        self.graph.showClusters = self.showClusters
        self.graph.updateSettings(optimizedDrawing = self.optimizedDrawing, useDifferentSymbols = self.useDifferentSymbols, useDifferentColors = self.useDifferentColors)
        self.graph.updateSettings(showFilledSymbols = self.showFilledSymbols, tooltipKind = self.tooltipKind, tooltipValue = self.tooltipValue)
        self.graph.updateSettings(showLegend = self.showLegend, pointWidth = self.pointWidth, scaleFactor = self.scaleFactor)
        self.updateGraph()

    def setJitteringSize(self):
        self.graph.jitterSize = self.jitterSize
        self.graph.setData(self.data)
        self.updateGraph()

    def setJitterCont(self):
        self.graph.updateSettings(jitterContinuous = self.jitterContinuous)
        self.graph.setData(self.data)
        self.updateGraph()

    def setGlobalValueScaling(self):
        self.graph.insideColors = None; self.graph.clusterClosure = None
        self.graph.globalValueScaling = self.globalValueScaling
        self.graph.setData(self.data)
        self.updateGraph()

    def setAutoSendSelection(self):
        if self.autoSendSelection:
            self.zoomSelectToolbar.buttonSendSelections.setEnabled(0)
            self.sendSelections()
        else:
            self.zoomSelectToolbar.buttonSendSelections.setEnabled(1)
        

    def setGraphCanvasColor(self):
        newColor = QColorDialog.getColor(QColor(self.graphCanvasColor))
        if newColor.isValid():
            self.graphCanvasColor = str(newColor.name())
            self.graph.setCanvasColor(QColor(newColor))


    # ######################################################
    # functions used by OWClusterOptimization class
    # ######################################################
    def setMinimalGraphProperties(self):
        attrs = ["pointWidth", "showLegend", "showClusters", "autoSendSelection"]
        self.oldSettings = dict([(attr, getattr(self, attr)) for attr in attrs])
        self.pointWidth = 4
        self.showLegend = 0
        self.showClusters = 0
        self.autoSendSelection = 0
        self.graph.showAttributeNames = 0
        self.graph.setAxisScale(QwtPlot.xBottom, -1.05, 1.05, 1)
        self.graph.setAxisScale(QwtPlot.yLeft, -1.05, 1.05, 1)


    def restoreGraphProperties(self):
        if hasattr(self, "oldSettings"):
            for key in self.oldSettings:
                self.__setattr__(key, self.oldSettings[key])
        self.graph.showAttributeNames = 1
        self.graph.setAxisScale(QwtPlot.xBottom, -1.22, 1.22, 1)
        self.graph.setAxisScale(QwtPlot.yLeft, -1.13, 1.13, 1)



    
#test widget appearance
if __name__=="__main__":
    a=QApplication(sys.argv)
    ow=OWRadviz()
    a.setMainWidget(ow)
    ow.show()
    a.exec_loop()

    #save settings 
    ow.saveSettings()
