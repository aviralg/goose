import sys
import posixpath
from kkitOrdinateUtil import setupMeshObj
from kkitViewcontrol import *
from kkitCalcArrow import *
from kkitQGraphics import *
from collections import defaultdict

from PyQt4 import QtGui, QtCore, Qt

class  KineticsWidget(QtGui.QWidget):
    def __init__(self, instance, parent=None):
        QtGui.QWidget.__init__(self)
        self.instance   = instance
        self.moose = instance["moose"]
        self.model = instance["model"]
        self.modelRoot  = self.model.path
        self.border     = 5
        self.comptPen   = 6
        self.iconScale  = 1
        self.arrowsize  = 2
        self.size = None
        self.createdItem      = {}
        self.srcdesConnection = {}
        self.autoCordinatepos = {}
        self.xyCord           = {}
        self.object2line      = defaultdict(list)
        self.lineItem_dict    = {}

        hLayout = QtGui.QGridLayout(self)
        self.setLayout(hLayout)
        self.sceneContainer = QtGui.QGraphicsScene(self)
        self.sceneContainer.setBackgroundBrush(QtGui.QColor(230,220,219,120))
        #self.sceneContainer.setSceneRect(10,10,1210,1210)

        # if model exist and atleast finds one compartment, then it goes inside
        # else a empty View/scence is show for model building

        if self.moose.wildcardFind(self.modelRoot+'/##[ISA=ChemCompt]'):
            #compartment and its members are setup
            self.meshEntry,self.xmin,self.xmax,self.ymin,self.ymax,self.positionInfoExist = setupMeshObj(self.modelRoot)
            print(self.meshEntry)
            #This function collects information of what is connected to what. e.g which Sub/Prd connected to Enz/Reac \
            setupItem(self.modelRoot,self.srcdesConnection)
            if not self.positionInfoExist:
                self.xmin,self.xmax,self.ymin,self.ymax,self.autoCordinatepos = autoCoordinates(self.meshEntry,self.srcdesConnection)

    def resizeEvent(event):
        self.size = event.size
        if moose.wildcardFind(self.modelRoot+'/##[ISA=ChemCompt]'):
            if self.xmax-self.xmin != 0:
                self.xratio = (self.size.width()-10)/(self.xmax-self.xmin)
            else: self.xratio = self.size.width()-10

            if self.ymax-self.ymin:
                self.yratio = (self.size.height()-10)/(self.ymax-self.ymin)
            else:
                self.yratio = (self.size.height()-10)

            self.xratio = int(self.xratio)
            self.yratio = int(self.yratio)
            self.mooseObjOntoscene()
            self.drawLine_arrow()

        self.view = GraphicalView(self.modelRoot,self.sceneContainer,self.border,self,self.createdItem)
        self.view.setAcceptDrops(True)
        self.view.fitInView(self.sceneContainer.itemsBoundingRect().x()-10,self.sceneContainer.itemsBoundingRect().y()-10,self.sceneContainer.itemsBoundingRect().width()+20,self.sceneContainer.itemsBoundingRect().height()+20,Qt.Qt.IgnoreAspectRatio)
        self.view.show()
        self.layout().addWidget(self.view)

    def mooseObjOntoscene(self):
        #  All the compartments are put first on to the scene \
        #  Need to do: Check With upi if empty compartments exist
        self.qGraCompt   = {}
        self.mooseId_GObj = {}

        for cmpt in sorted(self.meshEntry.iterkeys()):
            self.createCompt(cmpt)
            self.qGraCompt[cmpt]
            #comptRef = self.qGraCompt[cmpt]

        #Enzymes of all the compartments are placed first, \
        #     so that when cplx (which is pool object) queries for its parent, it gets its \
        #     parent enz co-ordinates with respect to QGraphicsscene """

        for cmpt,memb in self.meshEntry.items():
            for enzObj in find_index(memb,'enzyme'):
                enzinfo = enzObj.path+'/info'
                if enzObj.className == 'Enz':
                    enzItem = EnzItem(enzObj,self.qGraCompt[cmpt])
                else:
                    enzItem = MMEnzItem(enzObj,self.qGraCompt[cmpt])
                self.mooseId_GObj[self.moose.element(enzObj.getId())] = enzItem
                self.setupDisplay(enzinfo,enzItem,"enzyme")

                #self.setupSlot(enzObj,enzItem)
        for cmpt,memb in self.meshEntry.items():
            for poolObj in find_index(memb,'pool'):
                poolinfo = poolObj.path+'/info'
                #depending on Editor Widget or Run widget pool will be created a PoolItem or PoolItemCircle
                poolItem = self.makePoolItem(poolObj,self.qGraCompt[cmpt])
                self.mooseId_GObj[self.moose.element(poolObj.getId())] = poolItem
                self.setupDisplay(poolinfo,poolItem,"pool")

            for reaObj in find_index(memb,'reaction'):
                reainfo = reaObj.path+'/info'
                reaItem = ReacItem(reaObj,self.qGraCompt[cmpt])
                self.setupDisplay(reainfo,reaItem,"reaction")
                self.mooseId_GObj[self.moose.element(reaObj.getId())] = reaItem

            for tabObj in find_index(memb,'table'):
                tabinfo = tabObj.path+'/info'
                tabItem = TableItem(tabObj,self.qGraCompt[cmpt])
                self.setupDisplay(tabinfo,tabItem,"tab")
                self.mooseId_GObj[self.moose.element(tabObj.getId())] = tabItem

            for funcObj in find_index(memb,'function'):
                funcinfo = self.moose.element(funcObj.parent).path+'/info'
                funcParent =self.mooseId_GObj[self.moose.element(funcObj.parent)]
                funcItem = FuncItem(funcObj,funcParent)
                self.mooseId_GObj[self.moose.element(funcObj.getId())] = funcItem
                self.setupDisplay(funcinfo,funcItem,"Function")

            for cplxObj in find_index(memb,'cplx'):
                cplxinfo = (cplxObj.parent).path+'/info'
                p = self.moose.element(cplxObj).parent
                cplxItem = CplxItem(cplxObj,self.mooseId_GObj[self.moose.element(cplxObj).parent])
                self.mooseId_GObj[self.moose.element(cplxObj.getId())] = cplxItem
                self.setupDisplay(cplxinfo,cplxItem,"cplx")

        # compartment's rectangle size is calculated depending on children
        self.comptChilrenBoundingRect()

    def createCompt(self,key):
        self.new_Compt = ComptItem(self,0,0,0,0,key)
        self.qGraCompt[key] = self.new_Compt
        self.new_Compt.setRect(10,10,10,10)
        self.sceneContainer.addItem(self.new_Compt)

    def makePoolItem(self, poolObj, qGraCompt):
        return PoolItem(poolObj, qGraCompt)

    def setupDisplay(self,info,graphicalObj,objClass):
        Annoinfo = Annotator(info)
        # For Reaction and Complex object I have skipped the process to get the facecolor and background color as \
        #    we are not using these colors for displaying the object so just passing dummy color white
        if( objClass == "reaction"  or objClass == "cplx" or objClass == "Function" or objClass == "StimulusTable"):
            textcolor,bgcolor = "white","white"
        else:
            textcolor,bgcolor = getColor(info)
            if bgcolor.name() == "#ffffff" or bgcolor == "white":
                bgcolor = getRandColor()
                Annoinfo.color = str(bgcolor.name())

        xpos,ypos = self.positioninfo(info)
        self.xylist = [xpos,ypos]
        self.xyCord[self.moose.element(info).parent] = [xpos,ypos]
        graphicalObj.setDisplayProperties(xpos,ypos,textcolor,bgcolor)

    def positioninfo(self,iteminfo):
        Anno = self.moose.Annotator(self.modelRoot+'/info')
        if not self.positionInfoExist:
            try:
                # kkit does exist item's/info which up querying for parent.path gives the information of item's parent
                x,y = self.autoCordinatepos[(self.moose.element(iteminfo).parent).path]
            except:
                # But in Cspace reader doesn't create item's/info, up on querying gives me the error which need to change\
                # in ReadCspace.cpp, at present i am taking care b'cos i don't want to pass just the item where I need to check\
                # type of the object (rea,pool,enz,cplx,tab) which I have already done.

                parent, child = posixpath.split(iteminfo)
                print "iteminfo ",iteminfo,child, ' a ',parent
                x,y = self.autoCordinatepos[parent]
            ypos = (y-self.ymin)*self.yratio
        else:
            x = float(self.moose.element(iteminfo).getField('x'))
            y = float(self.moose.element(iteminfo).getField('y'))
            #Qt origin is at the top-left corner. The x values increase to the right and the y values increase downwards \
            #as compared to Genesis codinates where origin is center and y value is upwards, that is why ypos is negated
            if Anno.modeltype == "kkit":
                ypos = 1.0-(y-self.ymin)*self.yratio
            else:
                ypos = (y-self.ymin)*self.yratio

        xpos = (x-self.xmin)*self.xratio
        return(xpos,ypos)

    def comptChilrenBoundingRect(self):
        for k, v in self.qGraCompt.items():
            # compartment's rectangle size is calculated depending on children
            rectcompt = v.childrenBoundingRect()
            v.setRect(rectcompt.x()-10,rectcompt.y()-10,(rectcompt.width()+20),(rectcompt.height()+20))
            v.setPen(QtGui.QPen(Qt.QColor(66,66,66,100), self.comptPen, Qt.Qt.SolidLine, Qt.Qt.RoundCap, Qt.Qt.RoundJoin))

    def drawLine_arrow(self, itemignoreZooming=False):
        for inn,out in self.srcdesConnection.items():
            #print "inn ",inn, " out ",out
            # self.srcdesConnection is dictionary which contains key,value \
            #    key is Enzyme or Reaction  and value [[list of substrate],[list of product]] (tuple)
            #    key is Function and value is [list of pool] (list)

            #src = self.mooseId_GObj[inn]
            if isinstance(out,tuple):
                src = self.mooseId_GObj[inn]
                if len(out[0])== 0:
                    print inn.className + ' : ' +inn.name+ " doesn't output message"
                else:
                    for items in (items for items in out[0] ):
                        des = self.mooseId_GObj[self.moose.element(items[0])]
                        self.lineCord(src,des,items,itemignoreZooming)
                if len(out[1]) == 0:
                    print inn.className + ' : ' +inn.name+ " doesn't output message"
                else:
                    for items in (items for items in out[1] ):
                        des = self.mooseId_GObj[self.moose.element(items[0])]
                        self.lineCord(src,des,items,itemignoreZooming)
            elif isinstance(out,list):
                if len(out) == 0:
                    print "Func pool doesn't have sumtotal"
                else:
                    src = self.mooseId_GObj[inn]
                    for items in (items for items in out ):
                        des = self.mooseId_GObj[self.moose.element(items[0])]
                        self.lineCord(src,des,items,itemignoreZooming)
    def lineCord(self,src,des,type_no,itemignoreZooming):
        srcdes_list = []
        endtype = type_no[1]
        line = 0
        if (src == "") and (des == ""):
            print "Source or destination is missing or incorrect"
            return
        srcdes_list = [src,des,endtype,line]
        arrow = calcArrow(srcdes_list,itemignoreZooming,self.iconScale)
        self.drawLine(srcdes_list,arrow)

        while(type_no[2] > 1 and line <= (type_no[2]-1)):
            srcdes_list =[src,des,endtype,line]
            arrow = calcArrow(srcdes_list,itemignoreZooming,self.iconScale)
            self.drawLine(srcdes_list,arrow)
            line = line +1

        if type_no[2] > 5:
            print "Higher order reaction will not be displayed"

    def drawLine(self,srcdes_list,arrow):
        src = srcdes_list[0]
        des = srcdes_list[1]
        endtype = srcdes_list[2]
        line = srcdes_list[3]
        source = self.moose.element(next((k for k,v in self.mooseId_GObj.items() if v == src), None))
        for l,v,o in self.object2line[src]:
            if v == des and o ==line:
                l.setPolygon(arrow)
                arrowPen = l.pen()
                arrowPenWidth = self.arrowsize*self.iconScale
                arrowPen.setColor(l.pen().color())
                arrowPen.setWidth(arrowPenWidth)
                l.setPen(arrowPen)
                return
        qgLineitem = self.sceneContainer.addPolygon(arrow)
        qgLineitem.setParentItem(src.parentItem())
        pen = QtGui.QPen(QtCore.Qt.green, 0, Qt.Qt.SolidLine, Qt.Qt.RoundCap, Qt.Qt.RoundJoin)
        pen.setWidth(self.arrowsize)
        # Green is default color moose.ReacBase and derivatives - already set above
        if  isinstance(source, self.moose.EnzBase):
            if ( (endtype == 's') or (endtype == 'p')):
                pen.setColor(QtCore.Qt.red)
            elif(endtype != 'cplx'):
                p1 = (next((k for k,v in self.mooseId_GObj.items() if v == src), None))
                pinfo = p1.path+'/info'
                color,bgcolor = getColor(pinfo)
                #color = QColor(color[0],color[1],color[2])
                pen.setColor(color)
        elif isinstance(source, self.moose.PoolBase) or isinstance(source,self.moose.Function):
            pen.setColor(QtCore.Qt.blue)
        elif isinstance(source,self.moose.StimulusTable):
            pen.setColor(QtCore.Qt.yellow)
        self.lineItem_dict[qgLineitem] = srcdes_list
        self.object2line[ src ].append( ( qgLineitem, des,line,) )
        self.object2line[ des ].append( ( qgLineitem, src,line, ) )
        qgLineitem.setPen(pen)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    size = QtCore.QSize(624 ,468)
    modelPath = 'Kholodenko'
    itemignoreZooming = False
    try:
        filepath = '../../Demos/Genesis_files/'+modelPath+'.g'
        print filepath
        f = open(filepath, "r")
        loadModel(filepath,'/'+modelPath)
        # readSBML('/home/harsha/trunk/Demos/Genesis_files/reaction10dec.xml','/reac')
        # modelPath = "reac"
        dt = KineticsWidget(size,'/'+modelPath)
        dt.modelRoot ='/'+modelPath
        ''' Loading moose signalling model in python '''
        dt.show()

    except  IOError, what:
      (errno, strerror) = what
      print "Error number",errno,"(%s)" %strerror
      sys.exit(0)
    sys.exit(app.exec_())
