import sys
from modelBuild import *
from PyQt4.QtGui import QPixmap, QImage, QPen, QGraphicsPixmapItem, QGraphicsLineItem
from PyQt4.QtCore import pyqtSignal
from PyQt4.Qt import QCursor
from kkitUtil import getColor
from setsolver import *
from PyQt4 import QtSvg
#from moose import utils
from goose.utils import *

class GraphicalView(QtGui.QGraphicsView):

    def __init__(self,parent,border,layoutPt,createdItem,instance,mesh,voxelIndex,mainWindow = None,multiScale = True):
        QtGui.QGraphicsView.__init__(self,parent)
        self.mesh = mesh
        self.voxelIndex = voxelIndex
        self.state = None
        self.move  = False
        self.resetState()
        self.connectionSign          = None
        self.connectionSource        = None
        self.expectedConnection      = None
        self.selections              = []
        self.connector               = None

        self.instance = instance
        self.mainWindow = mainWindow
        self.multiScale = multiScale
        self.moose = instance["moose"]
        self.connectionSignImagePath = "../gui/icons/connection.png"
        self.connectionSignImage     = QImage(self.connectionSignImagePath)

        # self.expectedConnectionPen   = QPen()
        self.setScene(parent)
        #self.modelRoot = modelRoot
        self.modelRoot = instance["model"].path
        self.sceneContainerPt = parent
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.itemSelected = False
        self.customrubberBand = None
        self.rubberbandWidth = 0
        self.rubberbandHeight = 0
        self.moved = False
        self.showpopupmenu = False
        self.popupmenu4rlines = True
        self.border = 6
        self.setRenderHints(QtGui.QPainter.Antialiasing)
        self.layoutPt = layoutPt
        # All the object which are stacked on the scene are listed
        self.stackOrder = self.sceneContainerPt.items(Qt.Qt.DescendingOrder)
        #From stackOrder selecting only compartment
        self.cmptStackorder = [i for i in self.stackOrder if isinstance(i,ComptItem)]
        self.viewBaseType = "editorView"
        self.iconScale = 1
        self.arrowsize = 2
        self.defaultComptsize = 5
        if self.multiScale == True:
            self.connectorlist = {"plot": None ,"move": None}
        else:
            self.connectorlist = {"plot": None ,"clone": None,"move": None,"delete": None}

    def setRefWidget(self,path):
        self.viewBaseType = path

    def resizeEvent(self, event):
        self.fitInView(self.sceneContainerPt.itemsBoundingRect().x()-10,self.sceneContainerPt.itemsBoundingRect().y()-10,self.sceneContainerPt.itemsBoundingRect().width()+20,self.sceneContainerPt.itemsBoundingRect().height()+20,Qt.Qt.IgnoreAspectRatio)
        #print("Called =>", event)
        return
    def resolveCompartmentInteriorAndBoundary(self, item, position):
        bound = item.rect().adjusted(3,3,-3,-3)
        return COMPARTMENT_INTERIOR if bound.contains(item.mapFromScene(position)) else COMPARTMENT_BOUNDARY

    def resetState(self):
        self.state = { "press"      :   { "mode"     :  INVALID
                                        , "item"     :  None
                                        , "sign"     :  None
                                        , "pos"    :  None
                                        }
                    , "move"        :   { "happened": False
                                        }
                    , "release"     :   { "mode"    : INVALID
                                        , "item"    : None
                                        , "sign"    : None
                                        }
                }


    def resolveItem(self, items, position):
        solution = None
        for item in items:
            if hasattr(item, "name"):
                if item.name == ITEM:
                    return (item, ITEM)
                if item.name == COMPARTMENT:
                    solution = (item, self.resolveCompartmentInteriorAndBoundary(item, position))

        for item in items:
            # if isinstance(item, QtGui.QGraphicsPixmapItem):
            #     return (item, CONNECTOR)
            if isinstance(item, QtSvg.QGraphicsSvgItem):
                return (item, CONNECTOR)

            if isinstance(item, QtGui.QGraphicsPolygonItem):
                return (item, CONNECTION)

        if solution is None:
            return (None, EMPTY)
        return solution

    def editorMousePressEvent(self, event):
        # self.deselectSelections()
        # if self.state["press"]["item"] is not None:
        #     self.state["press"]["item"].setSelected(False)
        # self.resetState()
        if event.buttons() == QtCore.Qt.LeftButton:
            self.clickPosition  = self.mapToScene(event.pos())
            (item, itemType) = self.resolveItem(self.items(event.pos()), self.clickPosition)
            self.state["press"]["mode"] = VALID
            self.state["press"]["item"] = item
            self.state["press"]["type"] = itemType
            self.state["press"]["pos"]  = event.pos()
            #If connector exist and if mousePress on Compartment interior,
            # then removing any connect if exist
            if itemType == COMPARTMENT_INTERIOR:
                self.removeConnector()
            elif itemType == ITEM:
                self.showConnector(self.state["press"]["item"])
                # DEBUG(self.state["press"]["item"].mobj)
                self.mainWindow.show_property_slot(self.state["press"]["item"].mobj, self.moose)
            # self.layoutPt.plugin.mainWindow.objectEditSlot(self.state["press"]["item"].mobj, False)
        else:
            self.resetState()
        #print(self.state)


    def editorMouseMoveEvent(self, event):

        if self.state["press"]["mode"] == INVALID:
            self.state["move"]["happened"] = False
            return

        # if self.move:
        #     initial = self.mapToScene(self.state["press"]["pos"])
        #     final = self.mapToScene(event.pos())
        #     displacement = final - initial
        #     #print("Displacement", displacement)
        #     for item in self.selectedItems:
        #         if isinstance(item, KineticsDisplayItem) and not isinstance(item,ComptItem) and not isinstance(item,CplxItem):
        #             item.moveBy(displacement.x(), displacement.y())
        #             self.layoutPt.positionChange(item.mobj.path)
        #     self.state["press"]["pos"] = event.pos()
        #     return

        self.state["move"]["happened"] = True
        itemType = self.state["press"]["type"]
        item     = self.state["press"]["item"]

        if itemType == CONNECTOR:
            ''' connecting 2 object is removed and movement is impled'''
            #actionType = str(item.data(0).toString())
            actionType = str(item.data(0))
            if actionType == "move":
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
                initial = item.parent().pos()
                final = self.mapToScene(event.pos())
                displacement = final-initial
                if not isinstance(item.parent(),FuncItem) and not isinstance(item.parent(),CplxItem):
                    self.removeConnector()
                    item.parent().moveBy(displacement.x(), displacement.y())
                    if isinstance(item.parent(),PoolItem):
                        for funcItem in item.parent().childItems():
                            if isinstance(funcItem,FuncItem):
                                self.layoutPt.updateArrow(funcItem)

                self.state["press"]["pos"] = event.pos()
                self.layoutPt.positionChange(item.parent().mobj)
            if actionType == "clone":
                pixmap = QtGui.QPixmap(24, 24)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter()
                painter.begin(pixmap)
                painter.setRenderHints(painter.Antialiasing)
                pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor("black")), 1)
                pen.setWidthF(1.5)
                painter.setPen(pen)
                painter.drawLine(12,7,12,17)
                painter.drawLine(7,12,17,12)
                painter.end()
                #self.setCursor(QtGui.QCursor(pixmap))
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(pixmap))

        if itemType == ITEM:
            if self.multiScale == True:
                pass
            else:
                self.drawExpectedConnection(event)

        if itemType == COMPARTMENT_BOUNDARY:
            initial = self.mapToScene(self.state["press"]["pos"])
            final = self.mapToScene(event.pos())
            displacement = final - initial
            item.moveBy(displacement.x(), displacement.y())
            self.layoutPt.positionChange(item.mobj.path)
            self.state["press"]["pos"] = event.pos()

        if itemType == COMPARTMENT_INTERIOR:
            if self.customrubberBand == None:
                self.customrubberBand = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle,self)
                self.customrubberBand.show()

            startingPosition = self.state["press"]["pos"]
            endingPosition = event.pos()
            displacement   = endingPosition - startingPosition

            x0 = startingPosition.x()
            x1 = endingPosition.x()
            y0 = startingPosition.y()
            y1 = endingPosition.y()

            if displacement.x() < 0 :
                x0,x1= x1,x0

            if displacement.y() < 0 :
                y0,y1= y1,y0

            self.customrubberBand.setGeometry(QtCore.QRect(QtCore.QPoint(x0, y0), QtCore.QSize(abs(displacement.x()), abs(displacement.y()))))


        # if itemType == COMPARTMENT:
        #     rubberband selection

        # if itemType == COMPARTMENT_BOUNDARY:

        # if itemType == ITEM:
        #     dragging the item

    def editorMouseReleaseEvent(self, event):
        if self.move:
            self.move = False
            self.setCursor(Qt.Qt.ArrowCursor)

        if self.state["press"]["mode"] == INVALID:
            self.state["release"]["mode"] = INVALID
            self.resetState()
            return

        self.clickPosition  = self.mapToScene(event.pos())
        (item, itemType) = self.resolveItem(self.items(event.pos()), self.clickPosition)
        self.state["release"]["mode"] = VALID
        self.state["release"]["item"] = item
        self.state["release"]["type"] = itemType

        clickedItemType = self.state["press"]["type"]

        if clickedItemType == ITEM:
            if not self.state["move"]["happened"]:
                self.showConnector(self.state["press"]["item"])
                ## ObjectEditor connect is removed temparory
                #self.layoutPt.plugin.mainWindow.objectEditSlot(self.state["press"]["item"].mobj, True)
                # compartment's rectangle size is calculated depending on children
                #self.layoutPt.comptChilrenBoundingRect()
                l = self.modelRoot
                if self.modelRoot.find('/',1) > 0:
                    l = self.modelRoot[0:self.modelRoot.find('/',1)]

                linfo = self.moose.Annotator(l+'/info')
                for k, v in self.layoutPt.qGraCompt.items():
                    rectcompt = v.childrenBoundingRect()
                    if linfo.modeltype == "new_kkit":
                        #if newly built model then compartment is size is fixed for some size.
                        comptBoundingRect = v.boundingRect()
                        if not comptBoundingRect.contains(rectcompt):
                            self.layoutPt.updateCompartmentSize(v)
                    else:
                        #if already built model then compartment size depends on max and min objects
                        v.setRect(rectcompt.x()-10,rectcompt.y()-10,(rectcompt.width()+20),(rectcompt.height()+20))

            else:
                if isinstance(self.state["release"]["item"], KineticsDisplayItem):
                    if self.multiScale == False:
                        if not self.moose.element(self.state["press"]["item"].mobj) == self.moose.element(self.state["release"]["item"].mobj):
                            self.populate_srcdes( self.state["press"]["item"].mobj
                                                , self.state["release"]["item"].mobj
                                                )
                        else:
                            pass
                    else:
                        pass
                if self.multiScale == False:
                    self.removeExpectedConnection()
                self.removeConnector()

        if clickedItemType  == CONNECTOR:
            #actionType = str(self.state["press"]["item"].data(0).toString())
            actionType = str(self.state["press"]["item"].data(0))

            if actionType == "move":
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.Qt.ArrowCursor))

            elif actionType == "delete":
                self.removeConnector()
                pixmap = QtGui.QPixmap(24, 24)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter()
                painter.begin(pixmap)
                painter.setRenderHints(painter.Antialiasing)
                pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor("black")), 1)
                pen.setWidthF(1.5)
                painter.setPen(pen)
                painter.drawLine(8,8,16,16)
                painter.drawLine(8,16,16,8)
                painter.end()
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(pixmap))
                reply = QtGui.QMessageBox.question(self, "Deleting Object","Do want to delete object and its connections",
                                                   QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.Yes:
                    #delete solver first as topology is changing
                    deleteSolver(self.modelRoot,self.moose)
                    self.deleteObj([item.parent()])
                    QtGui.QApplication.restoreOverrideCursor()
                else:
                    QtGui.QApplication.restoreOverrideCursor()

            elif actionType == "plot":
                mooseElement = self.moose.element(item.parent().mobj.path)
                DEBUG(mooseElement)
                if isinstance (mooseElement,self.moose.PoolBase):
                    info = self.moose.element(mooseElement.vec[0].path+'/info')
                    color,bgcolor = getColor(info,self.moose)
                    self.mainWindow.plot_slot( QCursor.pos()
                                             , mooseElement
                                             , [CONCENTRATION, N]
                                             , LINE_PLOT
                                             , ( bgcolor.red() / 255.0
                                               , bgcolor.green() / 255.0
                                               , bgcolor.blue() / 255.0
                                               , bgcolor.alpha() / 255.0
                                               )
                                             )
                    # if not self.moose.exists(self.modelRoot+'/data'):
                    #     self.moose.Neutral(self.modelRoot+'/data')
                    # if not self.moose.exists(self.modelRoot+'/data/graph_0'):
                    #     self.moose.Neutral(self.modelRoot+'/data/graph_0')
                    # self.moose.le(self.modelRoot+'/data')
                    # self.graph = self.moose.element(self.modelRoot+'/data/graph_0')
                    # tablePath = utils.create_table_path(self.moose.element(self.modelRoot), self.graph, mooseElement, "Conc")
                    # table     = utils.create_table(tablePath,mooseElement, "Conc","Table2")
            elif actionType == "clone":
                if self.state["move"]["happened"]:
                    QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.Qt.ArrowCursor))
                    self.state["press"]["item"].parent().mobj
                    cloneObj = self.state["press"]["item"]
                    posWrtComp = self.mapToScene(event.pos())
                    itemAtView = self.sceneContainerPt.itemAt(self.mapToScene(event.pos()))
                    self.removeConnector()
                    if isinstance(itemAtView,ComptItem):
                        #Solver should be deleted
                            ## if there is change in 'Topology' of the model
                            ## or if copy has to made then object should be in unZombify mode
                        deleteSolver(self.modelRoot,self.moose)
                        # for key,value in self.layoutPt.qGraCompt.iteritems():
                        #     print key,value
                        lKey = [key for key, value in self.layoutPt.qGraCompt.iteritems() if value == itemAtView][0]
                        iR = 0
                        iP = 0
                        t = self.moose.element(cloneObj.parent().mobj)
                        name = t.name
                        if isinstance(cloneObj.parent().mobj,self.moose.PoolBase):
                            retValue = self.objExist(lKey.path,name,iP)
                            if retValue != None:
                                name += retValue

                            pmooseCp = self.moose.copy(t,lKey.path,name,1)
                            if pmooseCp.path != '/':
                                ct = self.moose.element(pmooseCp)
                                concInit = pmooseCp.concInit[0]
                                #this is b'cos if pool copied across the comptartment,
                                #then it doesn't calculate nInit according but if one set
                                #concInit then it would, just a hack
                                ct.concInit = concInit
                                #itemAtView = self.state["release"]["item"]
                                poolObj = self.moose.element(ct)
                                poolinfo = self.moose.element(poolObj.path+'/info')
                                qGItem =PoolItem(poolObj,itemAtView)
                                self.layoutPt.mooseId_GObj[poolObj] = qGItem
                                bgcolor = getRandColor()
                                color,bgcolor = getColor(poolinfo,self.moose)
                                qGItem.setDisplayProperties(posWrtComp.x(),posWrtComp.y(),color,bgcolor)
                                self.emit(QtCore.SIGNAL("dropped"),poolObj)

                        if isinstance(cloneObj.parent().mobj,self.moose.ReacBase):
                            retValue = self.objExist(lKey.path,name,iR)
                            if retValue != None :
                                name += retValue
                            rmooseCp = self.moose.copy(t,lKey.path,name,1)
                            if rmooseCp.path != '/':
                                ct = self.moose.element(rmooseCp)
                                #itemAtView = self.state["release"]["item"]
                                reacObj = self.moose.element(ct)
                                reacinfo = self.moose.Annotator(reacObj.path+'/info')
                                qGItem = ReacItem(reacObj,itemAtView)
                                self.layoutPt.mooseId_GObj[reacObj] = qGItem
                                posWrtComp = self.mapToScene(event.pos())
                                qGItem.setDisplayProperties(posWrtComp.x(),posWrtComp.y(),"white", "white")
                                self.emit(QtCore.SIGNAL("dropped"),reacObj)

                    else:
                        if itemAtView == None:
                            QtGui.QMessageBox.information(None,'Dropping Not possible ','Dropping not allowed outside the compartment',QtGui.QMessageBox.Ok)
                        else:
                            srcdesString = ((self.state["release"]["item"]).mobj).className
                            QtGui.QMessageBox.information(None,'Dropping Not possible','Dropping on \'{srcdesString}\' not allowed'.format(srcdesString = srcdesString),QtGui.QMessageBox.Ok)
        if clickedItemType == CONNECTION:
            if self.multiScale == True:
                pass
            else:
                popupmenu = QtGui.QMenu('PopupMenu', self)
                popupmenu.addAction("Delete", lambda : self.deleteConnection(item))
                popupmenu.exec_(self.mapToGlobal(event.pos()))

        if clickedItemType == COMPARTMENT_BOUNDARY:
            if not self.state["move"]["happened"]:
                ## Object Editor signal is disconnected
                #self.layoutPt.plugin.mainWindow.objectEditSlot(self.state["press"]["item"].mobj, True)
                pass
            self.resetState()

        if clickedItemType == COMPARTMENT_INTERIOR:
            if self.state["move"]["happened"]:
                startingPosition = self.state["press"]["pos"]
                endingPosition = event.pos()
                displacement   = endingPosition - startingPosition

                x0 = startingPosition.x()
                x1 = endingPosition.x()
                y0 = startingPosition.y()
                y1 = endingPosition.y()

                if displacement.x() < 0 :
                    x0,x1= x1,x0

                if displacement.y() < 0 :
                    y0,y1= y1,y0

                self.selectedItems = selectedItems = self.items(x0,y0,abs(displacement.x()), abs(displacement.y()))
                # print("Rect => ", self.customrubberBand.rect())
                # selectedItems = self.items(self.mapToScene(self.customrubberBand.rect()).boundingRect())
                self.selectSelections(selectedItems)
                for item in selectedItems:
                    if isinstance(item, KineticsDisplayItem) and not isinstance(item,ComptItem):
                        item.setSelected(True)
                #print("Rubberband Selections => ", self.selections)
                self.customrubberBand.hide()
                self.customrubberBand = None
                popupmenu = QtGui.QMenu('PopupMenu', self)
                if self.multiScale == False:
                    popupmenu.addAction("Delete", lambda : self.deleteSelections(x0,y0,x1,y1))
                popupmenu.addAction("Zoom",   lambda : self.zoomSelections(x0,y0,x1,y1))
                popupmenu.addAction("Move",   lambda : self.moveSelections())
                popupmenu.exec_(self.mapToGlobal(event.pos()))
                # self.delete = QtGui.QAction(self.tr('delete'), self)
                # self.connect(self.delete, QtCore.SIGNAL('triggered()'), self.deleteItems)
                # self.zoom = QtGui.QAction(self.tr('zoom'), self)
                # self.connect(self.zoom, QtCore.SIGNAL('triggered()'), self.zoomItem)
                # self.move = QtGui.QAction(self.tr('move'), self)
                # self.connect(self.move, QtCore.SIGNAL('triggered()'), self.moveItem)




            # else:
            #     self.layoutPt.plugin.mainWindow.objectEditSlot(self.state["press"]["item"].mobj, True)

        self.resetState()

    def drawExpectedConnection(self, event):
        self.connectionSource = self.state["press"]["item"]
        sourcePoint      = self.connectionSource.mapToScene(
            self.connectionSource.boundingRect().center()
                                          )
        destinationPoint = self.mapToScene(event.pos())
        if self.expectedConnection is None:
            self.expectedConnection = QGraphicsLineItem( sourcePoint.x()
                                                       , sourcePoint.y()
                                                       , destinationPoint.x()
                                                       , destinationPoint.y()
                                                       )
            self.expectedConnection.setPen(QPen(Qt.Qt.DashLine))

            self.sceneContainerPt.addItem(self.expectedConnection)
        else:
            self.expectedConnection.setLine( sourcePoint.x()
                                           , sourcePoint.y()
                                           , destinationPoint.x()
                                           , destinationPoint.y()
                                           )

        '''
        print " drawExpectedConnection ()() ",self.state["item"]["press"].mobj
        sourcePoint      = self.connectionSource.mapToScene(
            self.connectionSource.boundingRect().center()
                                          )
        destinationPoint = self.mapToScene(event.pos())
        if self.expectedConnection is None:
            self.expectedConnection = QGraphicsLineItem( sourcePoint.x()
                                                       , sourcePoint.y()
                                                       , destinationPoint.x()
                                                       , destinationPoint.y()
                                                       )
            self.expectedConnection.setPen(QPen(Qt.Qt.DashLine))

            self.sceneContainerPt.addItem(self.expectedConnection)
        else:
            self.expectedConnection.setLine( sourcePoint.x()
                                           , sourcePoint.y()
                                           , destinationPoint.x()
                                           , destinationPoint.y()
                                           )
        '''
    def removeExpectedConnection(self):
        #print("removeExpectedConnection")
        self.sceneContainerPt.removeItem(self.expectedConnection)
        self.expectedConnection = None
        self.connectionSource   = None

    def removeConnector(self):
        try:
            for l,k in self.connectorlist.items():
                if k is not None:
                    self.sceneContainerPt.removeItem(k)
                    self.connectorlist[l] = None
            '''
            if self.connectionSign is not None:
                    # self.sceneContainerPt.removeItem(self.connectionSign)
                    # self.connectionSign = None
            '''
        except:
            #print("Exception received!")
            pass
        # if self.connectionSign is not None:
        #     print "self.connectionSign ",self.connectionSign
        #     self.sceneContainerPt.removeItem(self.connectionSign)
        #     self.connectionSign = None

    def showConnector(self, item):
        self.removeConnector()
        self.connectionSource = item
        rectangle = item.boundingRect()

        for l in self.connectorlist.keys():
            self.xDisp = 0
            self.yDisp = 0
            self.connectionSign = None
            if isinstance(item.mobj,self.moose.PoolBase) or isinstance(item.mobj,self.moose.ReacBase):
                if l == "clone":
                    #self.connectionSign = QtSvg.QGraphicsSvgItem('icons/clone.svg')
                    self.connectionSign = QtSvg.QGraphicsSvgItem(CLONE_ICON_PATH)
                    #self.connectionSign.setData(0, QtCore.QVariant("clone"))
                    self.connectionSign.setData(0, "clone")
                    self.connectionSign.setParent(self.connectionSource)
                    self.connectionSign.setScale(
                        (1.0 * rectangle.height()) / self.connectionSign.boundingRect().height()
                                                )
                    position = item.mapToParent(rectangle.bottomLeft())
                    self.xDisp = 15
                    self.yDisp = 2
                    self.connectionSign.setToolTip("Click and drag to clone the object")
                    self.connectorlist["clone"] = self.connectionSign
            if isinstance(item.mobj,self.moose.PoolBase):
                if l == "plot":
                    # self.connectionSign = QtSvg.QGraphicsSvgItem('icons/plot.svg')
                    # self.connectionSign.setData(0, QtCore.QVariant("plot"))
                    self.connectionSign = QtSvg.QGraphicsSvgItem(PLOT_ICON_PATH)
                    self.connectionSign.setData(0, "plot")
                    self.connectionSign.setParent(self.connectionSource)
                    self.connectionSign.setScale(
                        (1.0 * rectangle.height()) / self.connectionSign.boundingRect().height()
                                                )
                    position = item.mapToParent(rectangle.topLeft())
                    self.xDisp = 15
                    self.yDisp = 0
                    self.connectionSign.setToolTip("plot the object")
                    self.connectorlist["plot"] = self.connectionSign

            if l == "move":
                # self.connectionSign = QtSvg.QGraphicsSvgItem('icons/move.svg')
                # self.connectionSign.setData(0, QtCore.QVariant("move"))
                self.connectionSign = QtSvg.QGraphicsSvgItem(MOVE_ICON_PATH)
                self.connectionSign.setData(0, "move")
                self.connectionSign.setParent(self.connectionSource)
                self.connectionSign.setToolTip("Drag to connect.")
                self.connectionSign.setScale(
                    (1.0 * rectangle.height()) / self.connectionSign.boundingRect().height()
                                            )
                position = item.mapToParent(rectangle.topRight())
                self.connectorlist["move"] = self.connectionSign
            elif l == "delete":
                # self.connectionSign = QtSvg.QGraphicsSvgItem('icons/delete.svg')
                self.connectionSign = QtSvg.QGraphicsSvgItem(DELETE_ICON_PATH)
                self.connectionSign.setParent(self.connectionSource)
                self.connectionSign.setData(0, "delete")
                self.connectionSign.setScale(
                    (1.0 * rectangle.height()) / self.connectionSign.boundingRect().height()
                                            )
                position = item.mapToParent(rectangle.bottomRight())
                self.connectionSign.setToolTip("Delete the object")
                self.connectorlist["delete"] = self.connectionSign

            if self.connectionSign != None:
                self.connectionSign.setFlag(QtGui.QGraphicsItem.ItemIsSelectable,True)
                self.connectionSign.setParentItem(item.parentItem())
                self.connectionSign.setPos(0.0,0.0)
                self.connectionSign.moveBy( position.x()-self.xDisp
                                          , position.y() +self.yDisp - rectangle.height() / 2.0
                                          )

    def objExist(self,path,name,index):
        #Need to check what to do if group come's b/w compartment and object
        #Ideally /compartment/group/obj != /compartment/obj WRT path, but object belong to same
        #compartment.

        if index == 0:
            fPath = path+'/'+name
        else:
            fPath = path+'/'+name+'_'+str(index)
        if self.moose.exists(fPath):
            index += 1
            return self.objExist(path,name,index)
        else:
            if index == 0:
                return
            else:
                return ('_'+str(index))

    def selectSelections(self, selections):
        for selection in selections :
            if isinstance(selection, KineticsDisplayItem):
                self.selections.append(selection)

    def deselectSelections(self):
        for selection in self.selections:
            selection.setSelected(False)
        self.selections  = []

    def mousePressEvent(self, event):
        selectedItem = None
        if self.viewBaseType == "editorView":
            return self.editorMousePressEvent(event)

        elif self.viewBaseType == "runView":
            pos = event.pos()
            item = self.itemAt(pos)
            if item:
                itemClass = type(item).__name__
                if ( itemClass!='ComptItem' and itemClass != 'QGraphicsPolygonItem' and
                    itemClass != 'QGraphicsEllipseItem' and itemClass != 'QGraphicsRectItem'):
                    self.setCursor(Qt.Qt.CrossCursor)
                    mimeData = QtCore.QMimeData()
                    mimeData.setText(item.mobj.name)
                    mimeData.setData("text/plain", "")
                    mimeData.data =(self.modelRoot,item.mobj)
                    drag = QtGui.QDrag(self)
                    drag.setMimeData(mimeData)
                    dropAction = drag.start(QtCore.Qt.MoveAction)
                    self.setCursor(Qt.Qt.ArrowCursor)


    def mouseMoveEvent(self,event):
        if self.viewBaseType == "editorView":
            return self.editorMouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        if self.viewBaseType == "editorView":
            for preSelectedItem in self.sceneContainerPt.selectedItems():
                preSelectedItem.setSelected(False)
            return self.editorMouseReleaseEvent(event)

        return

        if self.state["press"]["mode"] == CONNECTION:
            desPos =self.mapToScene(event.pos())
            destination = self.items(event.pos())
            src = self.state["press"]["item"]
            des  = [j for j in destination if isinstance(j,KineticsDisplayItem)]
            if len(des):
                self.populate_srcdes(src.mobj,des[0].mobj)
                #print " pop", self.layoutPt.srcdesConnection()
        self.setCursor(Qt.Qt.ArrowCursor)
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)
        '''if(self.customrubberBand):
            self.customrubberBand.hide()
            self.customrubberBand = 0
            if event.button() == QtCore.Qt.LeftButton and self.itemSelected == False :
                self.endingPos = event.pos()
                self.endScenepos = self.mapToScene(self.endingPos)
                self.rubberbandWidth = (self.endScenepos.x()-self.startScenepos.x())
                self.rubberbandHeight = (self.endScenepos.y()-self.startScenepos.y())
                selecteditems = self.sceneContainerPt.selectedItems()
                #print "selecteditems ",selecteditems
                if self.rubberbandWidth != 0 and self.rubberbandHeight != 0 and len(selecteditems) != 0 :
                    self.showpopupmenu = True
        '''
        #self.itemSelected = False
        '''
        if self.showpopupmenu:
            popupmenu = QtGui.QMenu('PopupMenu', self)
            self.delete = QtGui.QAction(self.tr('delete'), self)
            self.connect(self.delete, QtCore.SIGNAL('triggered()'), self.deleteItems)
            self.zoom = QtGui.QAction(self.tr('zoom'), self)
            self.connect(self.zoom, QtCore.SIGNAL('triggered()'), self.zoomItem)
            self.move = QtGui.QAction(self.tr('move'), self)
            self.connect(self.move, QtCore.SIGNAL('triggered()'), self.moveItem)
            popupmenu.addAction(self.delete)
            popupmenu.addAction(self.zoom)
            popupmenu.addAction(self.move)
            popupmenu.exec_(event.globalPos())
        self.showpopupmenu = False
        '''

    def updateItemTransformationMode(self, on):
        for v in self.sceneContainerPt.items():
            if( not isinstance(v,ComptItem)):
                #if ( isinstance(v, PoolItem) or isinstance(v, ReacItem) or isinstance(v, EnzItem) or isinstance(v, CplxItem) ):
                if isinstance(v,KineticsDisplayItem):
                    v.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations, on)

    def keyPressEvent(self,event):
        key = event.key()
        if (key ==  Qt.Qt.Key_A and (event.modifiers() & Qt.Qt.ShiftModifier)): # 'A' fits the view to iconScale factor
            itemignoreZooming = False
            self.updateItemTransformationMode(itemignoreZooming)
            self.fitInView(self.sceneContainerPt.itemsBoundingRect().x()-10,self.sceneContainerPt.itemsBoundingRect().y()-10,self.sceneContainerPt.itemsBoundingRect().width()+20,self.sceneContainerPt.itemsBoundingRect().height()+20,Qt.Qt.IgnoreAspectRatio)
            self.layoutPt.drawLine_arrow(itemignoreZooming=False)

        elif (key == Qt.Qt.Key_Less or key == Qt.Qt.Key_Minus):# and (event.modifiers() & Qt.Qt.ShiftModifier)): # '<' key. zooms-in to iconScale factor
            self.iconScale *= 0.8
            self.updateScale( self.iconScale )

        elif (key == Qt.Qt.Key_Greater or key == Qt.Qt.Key_Plus):# and (event.modifiers() & Qt.Qt.ShiftModifier)): # '>' key. zooms-out to iconScale factor
            self.iconScale *= 1.25
            self.updateScale( self.iconScale )

        elif (key == Qt.Qt.Key_Period): # '.' key, lower case for '>' zooms in
            self.scale(1.1,1.1)

        elif (key == Qt.Qt.Key_Comma): # ',' key, lower case for '<' zooms in
            self.scale(1/1.1,1/1.1)

        elif (key == Qt.Qt.Key_A):  # 'a' fits the view to initial value where iconscale=1
            self.iconScale = 1
            self.updateScale( self.iconScale )
            self.fitInView(self.sceneContainerPt.itemsBoundingRect().x()-10,self.sceneContainerPt.itemsBoundingRect().y()-10,self.sceneContainerPt.itemsBoundingRect().width()+20,self.sceneContainerPt.itemsBoundingRect().height()+20,Qt.Qt.IgnoreAspectRatio)

    def updateScale( self, scale ):
        for item in self.sceneContainerPt.items():
            if isinstance(item,KineticsDisplayItem):
                item.refresh(scale)
                #iteminfo = item.mobj.path+'/info'
                #xpos,ypos = self.positioninfo(iteminfo)
                xpos = item.scenePos().x()
                ypos = item.scenePos().y()

                if isinstance(item,ReacItem) or isinstance(item,EnzItem) or isinstance(item,MMEnzItem):
                     item.setGeometry(xpos,ypos,
                                     item.gobj.boundingRect().width(),
                                     item.gobj.boundingRect().height())
                elif isinstance(item,CplxItem):
                    item.setGeometry(item.gobj.boundingRect().width()/2,item.gobj.boundingRect().height(),
                                     item.gobj.boundingRect().width(),
                                     item.gobj.boundingRect().height())
                elif isinstance(item,PoolItem) or isinstance(item, PoolItemCircle):
                     item.setGeometry(xpos, ypos,item.gobj.boundingRect().width()
                                     +PoolItem.fontMetrics.width('  '),
                                     item.gobj.boundingRect().height())
                     item.bg.setRect(0, 0, item.gobj.boundingRect().width()+PoolItem.fontMetrics.width('  '), item.gobj.boundingRect().height())

        self.layoutPt.drawLine_arrow(itemignoreZooming=False)
        self.layoutPt.comptChilrenBoundingRect()
        #compartment width is resize according apart from calculating boundingRect
        # for k, v in self.layoutPt.qGraCompt.items():
        #     rectcompt = v.childrenBoundingRect()
        #     comptPen = v.pen()
        #     comptWidth =  self.defaultComptsize*self.iconScale
        #     comptPen.setWidth(comptWidth)
        #     v.setPen(comptPen)
        #     v.setRect(rectcompt.x()-comptWidth,rectcompt.y()-comptWidth,(rectcompt.width()+2*comptWidth),(rectcompt.height()+2*comptWidth))

    def moveSelections(self):
        self.setCursor(Qt.Qt.CrossCursor)
        self.move = True
        return

    def GrVfitinView(self):
        #print " here in GrVfitinView"
        itemignoreZooming = False
        self.layoutPt.updateItemTransformationMode(itemignoreZooming)
        self.fitInView(self.sceneContainerPt.itemsBoundingRect().x()-10,self.sceneContainerPt.itemsBoundingRect().y()-10,self.sceneContainerPt.itemsBoundingRect().width()+20,self.sceneContainerPt.itemsBoundingRect().height()+20,Qt.Qt.IgnoreAspectRatio)
        self.layoutPt.drawLine_arrow(itemignoreZooming=False)


    def deleteSelections(self,x0,y0,x1,y1):
        if( x1-x0 > 0  and y1-y0 >0):
            self.rubberbandlist = self.sceneContainerPt.items(self.mapToScene(QtCore.QRect(x0, y0, x1 - x0, y1 - y0)).boundingRect(), Qt.Qt.IntersectsItemShape)
            for unselectitem in self.rubberbandlist:
                if unselectitem.isSelected() == True:
                    unselectitem.setSelected(0)
            self.deleteObj(self.rubberbandlist)
            # deleteSolver(self.layoutPt.modelRoot)
            # for item in (qgraphicsitem for qgraphicsitem in self.rubberbandlist):
            #     #First Loop to remove all the enz b'cos if parent (which is a Pool) is removed,
            #     #then it will created problem at qgraphicalitem not having parent.
            #     #So first delete enz and then delete pool
            #         if isinstance(item,MMEnzItem) or isinstance(item,EnzItem) or isinstance(item,CplxItem):
            #             self.deleteItem(item)
            # for item in (qgraphicsitem for qgraphicsitem in self.rubberbandlist):
            #     if not (isinstance(item,MMEnzItem) or isinstance(item,EnzItem) or isinstance(item,CplxItem)):
            #         if isinstance(item,PoolItem):
            #             plot = moose.wildcardFind(self.layoutPt.modelRoot+'/data/graph#/#')
            #             for p in plot:
            #                 if len(p.neighbors['requestOut']):
            #                     if item.mobj.path == moose.element(p.neighbors['requestOut'][0]).path:
            #                         p.tick = -1
            #                         moose.delete(p)
            #                         self.layoutPt.plugin.view.getCentralWidget().plotWidgetContainer.plotAllData()
            #         self.deleteItem(item)
        self.selections = []
    def deleteObj(self,item):
        self.rubberbandlist = item
        deleteSolver(self.layoutPt.modelRoot,self.moose)
        for item in (qgraphicsitem for qgraphicsitem in self.rubberbandlist):
            #First Loop to remove all the enz b'cos if parent (which is a Pool) is removed,
            #then it will created problem at qgraphicalitem not having parent.
            #So first delete enz and then delete pool
                if isinstance(item,MMEnzItem) or isinstance(item,EnzItem) or isinstance(item,CplxItem):
                    self.deleteItem(item)
        for item in (qgraphicsitem for qgraphicsitem in self.rubberbandlist):
            if not (isinstance(item,MMEnzItem) or isinstance(item,EnzItem) or isinstance(item,CplxItem)):
                if isinstance(item,PoolItem):
                    plot = self.moose.wildcardFind(self.layoutPt.modelRoot+'/data/graph#/#')
                    for p in plot:
                        if len(p.neighbors['requestOut']):
                            if item.mobj.path == self.moose.element(p.neighbors['requestOut'][0]).path:
                                p.tick = -1
                                self.moose.delete(p)
                                self.layoutPt.plugin.view.getCentralWidget().plotWidgetContainer.plotAllData()
                self.deleteItem(item)

    def deleteObject2line(self,qpolygonline,src,des,endt):
        object2lineInfo = self.layoutPt.object2line[des]
        if len(object2lineInfo) == 1:
            for polygon,objdes,endtype,numL in object2lineInfo:
                if polygon == qpolygonline and objdes == src and endtype == endt:
                    del(self.layoutPt.object2line[des])
                else:
                    print " check this condition when is len is single and else condition",qpolygonline, objdes,endtype
        else:
            n = 0
            for polygon,objdes,endtype,numL in object2lineInfo:
                if polygon == qpolygonline and objdes == src and endtype == endt:
                    tup = object2lineInfo[:n]+object2lineInfo[n+1:]
                    self.layoutPt.object2line[des] = tup
                    #d[keyNo].append((a,b,c))
                else:
                    n = n+1

    def deleteConnection(self,item):
        #Delete moose connection, i.e one can click on connection arrow and delete the connection
        deleteSolver(self.layoutPt.modelRoot,self.moose)
        msgIdforDeleting = " "
        if isinstance(item,QtGui.QGraphicsPolygonItem):
            src = self.layoutPt.lineItem_dict[item]
            lineItem_value = self.layoutPt.lineItem_dict[item]
            i = iter(lineItem_value)
            source  = i.next()
            destination  = i.next()
            endt = i.next()
            numl = i.next()
            self.deleteObject2line(item,source,destination,endt)
            self.deleteObject2line(item,destination,source,endt)
            try:
                del self.layoutPt.lineItem_dict[item]
            except KeyError:
                pass
            srcZero = [k for k, v in self.layoutPt.mooseId_GObj.iteritems() if v == src[0]]
            srcOne = [k for k, v in self.layoutPt.mooseId_GObj.iteritems() if v == src[1]]

            if isinstance (self.moose.element(srcZero[0]),self.moose.MMenz):
                gItem =self.layoutPt.mooseId_GObj[self.moose.element(srcZero[0])]
                # This block is done b'cos for MMenz while loaded from ReadKKit, the msg
                # from parent pool to Enz is different as compared to direct model building.
                # if ReadKKit get the msg from parent Pool, else from MMenz itself.

                # Rules: If some one tries to remove connection parent Pool to Enz
                # then delete entire enz itself, this is True for enz and mmenz
                for msg in srcZero[0].msgIn:
                    if self.moose.element(msg.e1.path) == self.moose.element(srcOne[0].path):
                        if src[2] == "t":
                            if msg.destFieldsOnE2[0] == "enzDest":
                                # delete indivial msg if later adding parent is possible
                                # msgIdforDeleting = msg
                                # moose.delete(msgIdforDeleting)
                                # self.sceneContainerPt.removeItem(item)
                                self.deleteItem(gItem)
                                return
                        else:
                            self.getMsgId(src,srcZero,srcOne,item)
                            self.moose.delete(msgIdforDeleting)
                            self.sceneContainerPt.removeItem(item)
                            setupItem(self.instance,self.layoutPt.srcdesConnection,self.mesh,self.voxelIndex)
                for msg in self.moose.element(srcZero[0].parent).msgIn:
                    if self.moose.element(msg.e2.path) == self.moose.element(srcZero[0].parent.path):
                        if src[2] == 't':
                            if len(msg.destFieldsOnE1) > 0:
                                if msg.destFieldsOnE1[0] == "enzDest":
                                    # delete indivial msg if later adding parent is possible
                                    # msgIdforDeleting = msg
                                    # moose.delete(msgIdforDeleting)
                                    # self.sceneContainerPt.removeItem(item)
                                    self.deleteItem(gItem)
                                return
                        else:
                            self.getMsgId(src,srcZero,srcOne,item)

            elif isinstance (self.moose.element(srcZero[0]),self.moose.Enz):
                self.getMsgId(src,srcZero,srcOne,item)

            elif isinstance(self.moose.element(srcZero[0]),self.moose.Function):
                v = self.moose.Variable(srcZero[0].path+'/x')
                found = False
                for msg in v.msgIn:
                    if self.moose.element(msg.e1.path) == self.moose.element(srcOne[0].path):
                        if src[2] == "sts":
                            if msg.destFieldsOnE2[0] == "input":
                                msgIdforDeleting = msg
                                self.deleteSceneObj(msgIdforDeleting,item)
                                found = True
                if not found:
                    for msg in srcZero[0].msgOut:
                        if self.moose.element(msg.e2.path) == self.moose.element(srcOne[0].path):
                            if src[2] == "stp":
                                if msg.destFieldsOnE2[0] == "setN":
                                    gItem =self.layoutPt.mooseId_GObj[self.moose.element(srcZero[0])]
                                    self.deleteItem(gItem)
                                    return
                                elif msg.destFieldsOnE2[0] == "setNumKf" or msg.destFieldsOnE2[0] == "setConcInit" or msg.destFieldsOnE2[0]=="increment":
                                    msgIdforDeleting = msg
                                    self.deleteSceneObj(msgIdforDeleting,item)
            else:
                self.getMsgId(src,srcZero,srcOne,item)

    def deleteSceneObj(self,msgIdforDeleting,item):
        self.moose.delete(msgIdforDeleting)
        self.sceneContainerPt.removeItem(item)
        setupItem(self.instance,self.layoutPt.srcdesConnection,self.mesh,self.voxelIndex)

    def getMsgId(self,src,srcZero,srcOne,item):
        for msg in srcZero[0].msgOut:
            msgIdforDeleting = " "
            if self.moose.element(msg.e2.path) == self.moose.element(srcOne[0].path):
                if src[2] == 's':
                    # substrate connection for R,E
                    if msg.srcFieldsOnE1[0] == "subOut":
                        msgIdforDeleting = msg
                        self.deleteSceneObj(msgIdforDeleting,item)
                        return
                elif src[2] == 'p':
                    # product connection for R,E
                    if msg.srcFieldsOnE1[0] == "prdOut":
                        msgIdforDeleting = msg
                        self.deleteSceneObj(msgIdforDeleting,item)
                        return
                elif src[2] == 't':
                    if msg.srcFieldsOnE1[0] == "enzOut":
                        gItem =self.layoutPt.mooseId_GObj[self.moose.element(srcZero[0])]
                        self.deleteItem(gItem)
                        return
                elif src[2] == 'tab':
                    #stimulation Table connection
                    if msg.srcFieldsOnE1[0] == "output":
                        msgIdforDeleting = msg
                        self.deleteSceneObj(msgIdforDeleting,item)
        return

    def deleteItem(self,item):
        #delete Items
        ## ObjectEditor signal is disconnected here
        #self.layoutPt.plugin.mainWindow.objectEditSlot('/', False)
        if self.multiScale == True:
            pass
        else:
            if isinstance(item,KineticsDisplayItem):
                if self.moose.exists(item.mobj.path):
                    # if isinstance(item.mobj,Function):
                    #     print " inside the function"
                    #     for items in moose.element(item.mobj.path).children:
                    #         print items
                    if isinstance(item,PoolItem) or isinstance(item,self.moose.BufPool):
                        # pool is item is removed, then check is made if its a parent to any
                        # enz if 'yes', then enz and its connection are removed before
                        # removing Pool
                        for items in self.moose.element(item.mobj.path).children:
                            # if isinstance(moose.element(items), Function):
                            #     gItem = self.layoutPt.mooseId_GObj[moose.element(items)]
                            #     for l in self.layoutPt.object2line[gItem]:
                            #         sceneItems = self.sceneContainerPt.items()
                            #         if l[0] in sceneItems:
                            #             #deleting the connection which is connected to Enz
                            #             self.sceneContainerPt.removeItem(l[0])
                            #     moose.delete(items)
                            #     self.sceneContainerPt.removeItem(gItem)
                            if isinstance(self.moose.element(items), self.moose.EnzBase):
                                gItem = self.layoutPt.mooseId_GObj[self.moose.element(items)]
                                for l in self.layoutPt.object2line[gItem]:
                                    # Need to check if the connection on the scene exist
                                    # or its removed from some other means
                                    # E.g Enz to pool and pool to Enz is connected,
                                    # when enz is removed the connection is removed,
                                    # but when pool tried to remove then qgraphicscene says
                                    # "item scene is different from this scene"
                                    sceneItems = self.sceneContainerPt.items()
                                    if l[0] in sceneItems:
                                        #deleting the connection which is connected to Enz
                                        self.sceneContainerPt.removeItem(l[0])
                                self.moose.delete(items)
                                self.sceneContainerPt.removeItem(gItem)

                    for l in self.layoutPt.object2line[item]:
                        sceneItems = self.sceneContainerPt.items()
                        if l[0] in sceneItems:
                            self.sceneContainerPt.removeItem(l[0])
                    self.sceneContainerPt.removeItem(item)
                    self.moose.delete(item.mobj)
                    for key, value in self.layoutPt.object2line.items():
                        self.layoutPt.object2line[key] = filter( lambda tup: tup[1] != item ,value)
                    self.layoutPt.getMooseObj()
                    setupItem(self.instance,self.layoutPt.srcdesConnection,self.mesh,self.voxelIndex)

    def zoomSelections(self, x0, y0, x1, y1):
        self.fitInView(self.mapToScene(QtCore.QRect(x0, y0, x1 - x0, y1 - y0)).boundingRect(), Qt.Qt.KeepAspectRatio)
        self.deselectSelections()

    def wheelEvent(self,event):
        factor = 1.41 ** (event.delta() / 240.0)
        self.scale(factor, factor)


    def dragEnterEvent(self, event):
        if self.viewBaseType == "editorView":
            if event.mimeData().hasFormat('text/plain'):
                event.acceptProposedAction()
        else:
            pass

    def dragMoveEvent(self, event):
        if self.viewBaseType == "editorView":
            if event.mimeData().hasFormat('text/plain'):
                event.acceptProposedAction()
        else:
            pass

    def eventFilter(self, source, event):
        if self.viewBase == "editorView":
            if (event.type() == QtCore.QEvent.Drop):
                pass
        else:
            pass

    def dropEvent(self, event):
        """Insert an element of the specified class in drop location"""
        """ Pool and reaction should have compartment as parent, dropping outside the compartment is not allowed """
        """ Enz should be droped on the PoolItem which inturn will be under compartment"""
        if self.viewBaseType == "editorView":
            if not event.mimeData().hasFormat('text/plain'):
                return
            event_pos = event.pos()
            string = str(event.mimeData().text())
            createObj(self.viewBaseType,self,self.modelRoot,string,event_pos,self.layoutPt)

    def populate_srcdes(self,src,des):
        self.modelRoot = self.layoutPt.modelRoot
        callsetupItem = True
        #print " populate_srcdes ",src,des
        srcClass =  self.moose.element(src).className
        if 'Zombie' in srcClass:
            srcClass = srcClass.split('Zombie')[1]
        desClass = self.moose.element(des).className
        if 'Zombie' in desClass:
            desClass = desClass.split('Zombie')[1]
        if ( isinstance(self.moose.element(src),self.moose.PoolBase) and ( (isinstance(self.moose.element(des),self.moose.ReacBase) ) or isinstance(self.moose.element(des),self.moose.EnzBase) )):
            #If one to tries to connect pool to Reac/Enz (substrate to Reac/Enz), check if already (product to Reac/Enz) exist.
            #If exist then connection not allowed one need to delete the msg and try connecting back.
            found = False
            for msg in des.msgOut:
                if self.moose.element(msg.e2.path) == src:
                    if msg.srcFieldsOnE1[0] == "prdOut":
                        found = True
            if found == False:
                # moose.connect(src, 'reac', des, 'sub', 'OneToOne')
                self.moose.connect(des, 'sub', src, 'reac', 'OneToOne')

            else:
                srcdesString = srcClass+' is already connected as '+ '\'Product\''+' to '+desClass +' \n \nIf you wish to connect this object then first delete the exist connection'
                QtGui.QMessageBox.information(None,'Connection Not possible','{srcdesString}'.format(srcdesString = srcdesString),QtGui.QMessageBox.Ok)

        elif (isinstance (self.moose.element(src),self.moose.PoolBase) and (isinstance(self.moose.element(des),self.moose.Function))):
            numVariables = des.numVars
            des.numVars+=1
            expr = ""
            expr = (des.expr+'+'+'x'+str(numVariables))
            expr = expr.lstrip("0 +")
            expr = expr.replace(" ","")
            des.expr = expr
            self.moose.connect( src, 'nOut', des.x[numVariables], 'input' )
        elif ( isinstance(self.moose.element(src),self.moose.Function) and (self.moose.element(des).className=="Pool") ):
                if ((self.moose.element(des).parent).className != 'Enz'):
                    self.moose.connect(src, 'valueOut', des, 'increment', 'OneToOne')
                else:
                    srcdesString = self.moose.element(src).className+'-- EnzCplx'
                    QtGui.QMessageBox.information(None,'Connection Not possible','\'{srcdesString}\' not allowed to connect'.format(srcdesString = srcdesString),QtGui.QMessageBox.Ok)
                    callsetupItem = False
        elif ( isinstance(self.moose.element(src),self.moose.Function) and (self.moose.element(des).className=="BufPool") ):
                self.moose.connect(src, 'valueOut', des, 'setConcInit', 'OneToOne')
        elif ( isinstance(self.moose.element(src),self.moose.Function) and (isinstance(self.moose.element(des),self.moose.ReacBase) ) ):
                self.moose.connect(src, 'valueOut', des, 'setNumKf', 'OneToOne')
        elif (((isinstance(self.moose.element(src),self.moose.ReacBase))or (isinstance(self.moose.element(src),self.moose.EnzBase))) and (isinstance(self.moose.element(des),self.moose.PoolBase))):
            found = False
            for msg in src.msgOut:
                if self.moose.element(msg.e2.path) == des:
                    if msg.srcFieldsOnE1[0] == "subOut":
                        found = True
            if found == False:
                #moose.connect(src, 'prd', des, 'reac', 'OneToOne')
                self.moose.connect(src, 'prd', des, 'reac', 'OneToOne')
            else:
                srcdesString = desClass+' is already connected as '+'\'Substrate\''+' to '+srcClass +' \n \nIf you wish to connect this object then first delete the exist connection'
                QtGui.QMessageBox.information(None,'Connection Not possible','{srcdesString}'.format(srcdesString = srcdesString),QtGui.QMessageBox.Ok)
        # elif( isinstance(moose.element(src),ReacBase) and (isinstance(moose.element(des),PoolBase) ) ):
        #     moose.connect(src, 'prd', des, 'reac', 'OneToOne')
        # elif( isinstance(moose.element(src),EnzBase) and (isinstance(moose.element(des),PoolBase) ) ):
        #     moose.connect(src, 'prd', des, 'reac', 'OneToOne')
        elif( isinstance(self.moose.element(src),self.moose.StimulusTable) and (isinstance(self.moose.element(des),self.moose.PoolBase) ) ):
            self.moose.connect(src, 'output', des, 'setConcInit', 'OneToOne')
        else:
            srcString = self.moose.element(src).className
            desString = self.moose.element(des).className
            srcdesString = srcString+'--'+desString
            QtGui.QMessageBox.information(None,'Connection Not possible','\'{srcdesString}\' not allowed to connect'.format(srcdesString = srcdesString),QtGui.QMessageBox.Ok)
            callsetupItem = False

        if callsetupItem:
            self.layoutPt.getMooseObj()
            # setupItem(self.modelRoot,self.layoutPt.srcdesConnection)
            setupItem(self.instance,self.layoutPt.srcdesConnection,self.mesh,self.voxelIndex)
            self.layoutPt.drawLine_arrow(False)

