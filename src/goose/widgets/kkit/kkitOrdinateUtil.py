from common import *
import numpy as np
import networkx as nx
from collections import Counter
import time
import re

def xyPosition(objInfo,xory,moose):
    try:
        return(float(moose.element(objInfo).getField(xory)))
    except ValueError:
        return (float(0))

#def setupMeshObj(modelRoot):
def setupMeshObj(instance,mesh,voxelIndex):

    ''' Setup compartment and its members pool,reaction,enz cplx under self.meshEntry dictionaries \ 
    self.meshEntry with "key" as compartment, 
    value is key2:list where key2 represents moose object type,list of objects of a perticular type
    e.g self.meshEntry[meshEnt] = { 'reaction': reaction_list,'enzyme':enzyme_list,'pool':poollist,'cplx': cplxlist }
    '''
    #model = 
    xmin = 0.0
    xmax = 1.0
    ymin = 0.0
    ymax = 1.0
    modelRoot = instance['model'].path
    moose = instance['moose']
    positionInfoExist = True
    meshEntry = {}
    if meshEntry:
        meshEntry.clear()
    else:
        meshEntry = {}
    xcord = []
    ycord = []
    
    meshEntryWildcard = '/##[ISA=ChemCompt]'
    # DEBUG(mesh)

    if len(mesh) > 0:
        meshEnties = mesh
    else:
        if moose.element(modelRoot).className != "shell":
            if moose.element(modelRoot).className == "Neutral":
                meshEnties = moose.wildcardFind(modelRoot+meshEntryWildcard)
        else:
             meshEnties = moose.wildcardFind(meshEntryWildcard)       

    for meshEnt in meshEnties:
        mollist  = []
        realist  = []
        enzlist  = []
        cplxlist = []
        tablist  = []
        funclist = []

        if voxelIndex == None:
            combine = meshEnt[0].path+'/##[ISA=PoolBase]'
        else:
            combine = meshEnt[0].path+'/##['+str(meshEnt[1])+'][ISA=PoolBase]'
        s = time.time()
        mol_cpl = moose.wildcardFind(combine)
        funclist = moose.wildcardFind(meshEnt[0].path+'/##[ISA=Function]')
        enzlist  = moose.wildcardFind(meshEnt[0].path+'/##[ISA=EnzBase]')
        realist  = moose.wildcardFind(meshEnt[0].path+'/##[ISA=ReacBase]')
        tablist  = moose.wildcardFind(meshEnt[0].path+'/##[ISA=StimulusTable]')
        e = time.time()
        DEBUG(" wildcardFind ")
        DEBUG (e-s)
        DEBUG (len(mol_cpl))
        
        if mol_cpl or funclist or enzlist or realist or tablist:
            f = 0
            for m in mol_cpl:
                if isinstance(moose.element(m.parent),moose.CplxEnzBase):
                    cplxlist.append(m)
                    objInfo = m.parent.path+'/info'
                elif isinstance(moose.element(m),moose.PoolBase):
                    mollist.append(m)
                    # multiscale zeroth Voxel has x,y,color,bgcolor info and only pool have different
                    # voxel index.When accessing any information for Pool it has to be zeroth Voxel index
                    objInfo = m.vec[0].path+'/info'
                xcord.append(xyPosition(objInfo,'x',moose))
                ycord.append(xyPosition(objInfo,'y',moose))
                f1 = time.time()
                print " \t \t \t ", f1-f
                f = f1
            e1 = time.time()
            DEBUG(e1-e)
            #getxyCord(xcord,ycord,mollist,moose)
            getxyCord(xcord,ycord,funclist,moose)
            DEBUG (len(funclist))
            e2 = time.time()
            DEBUG(e2-e1)
            getxyCord(xcord,ycord,enzlist,moose)
            DEBUG (len(enzlist))
            e3 = time.time()
            DEBUG(e3-e2)
            getxyCord(xcord,ycord,realist,moose)
            DEBUG (len(realist))
            e4 = time.time()
            DEBUG(e4-e3)
            getxyCord(xcord,ycord,tablist,moose)

            meshEntry[meshEnt] = {'enzyme':enzlist,
                                  'reaction':realist,
                                  'pool':mollist,
                                  'cplx':cplxlist,
                                  'table':tablist,
                                  'function':funclist
                                  }
            xmin = min(xcord)
            xmax = max(xcord)
            ymin = min(ycord)
            ymax = max(ycord)
            positionInfoExist = not(len(np.nonzero(xcord)[0]) == 0 \
                and len(np.nonzero(ycord)[0]) == 0)
        DEBUG(time.time()-e)
    return(meshEntry,xmin,xmax,ymin,ymax,positionInfoExist)

def sizeHint(self):
    return QtCore.QSize(800,400)
#def getxyCord(xcord,ycord,list1)
def getxyCord(xcord,ycord,list1,instance):
    moose = instance
    for item in list1:
        # if isinstance(item,Function):
        #     objInfo = moose.moose.element(item.parent).path+'/info'
        # else:
        #     objInfo = item.path+'/info'
        if not isinstance(item,moose.Function):
            objInfo = item.path+'/info'

            xcord.append(xyPosition(objInfo,'x',moose))
            ycord.append(xyPosition(objInfo,'y',moose))

#def setupItem(modelPath,cntDict):
def setupItem(instance,cntDict,mesh,voxelIndex):
    '''This function collects information of what is connected to what. \
    eg. substrate and product connectivity to reaction's and enzyme's \
    sumtotal connectivity to its pool are collected '''
    moose = instance['moose']
    modelPath = instance['model'].path
    sublist = []
    prdlist = []
    modelPathList = []
    zombieType = ['ReacBase','EnzBase','Function','StimulusTable']
    if len(mesh)> 0:
        for m in mesh[:]:
            modelPath = m[0].path
            modelPathList.append(m[0].path)
        
    else:
        if moose.element(modelPath).className != "shell":
            if moose.element(modelPath).className == "Neutral":
                modelPath
                modelPathList.append(modelPath)
    for modelPath in modelPathList:
        for baseObj in zombieType:
            path = '/##[ISA='+baseObj+']'

            if modelPath != '/':
                path = modelPath+path
            if ( (baseObj == 'ReacBase') or (baseObj == 'EnzBase')):
                for items in moose.wildcardFind(path):
                    sublist = []
                    prdlist = []
                    uniqItem,countuniqItem = countitems(items,'subOut',moose)
                    for sub in uniqItem: 
                        sublist.append((moose.element(sub),'s',countuniqItem[sub]))

                    uniqItem,countuniqItem = countitems(items,'prd',moose)
                    for prd in uniqItem:
                        prdlist.append((moose.element(prd),'p',countuniqItem[prd]))
                    
                    if (baseObj == 'CplxEnzBase') :
                        uniqItem,countuniqItem = countitems(items,'toEnz',moose)
                        for enzpar in uniqItem:
                            sublist.append((moose.element(enzpar),'t',countuniqItem[enzpar]))
                        
                        uniqItem,countuniqItem = countitems(items,'cplxDest',moose)
                        for cplx in uniqItem:
                            prdlist.append((moose.element(cplx),'cplx',countuniqItem[cplx]))

                    if (baseObj == 'EnzBase'):
                        uniqItem,countuniqItem = countitems(items,'enzDest',moose)
                        for enzpar in uniqItem:
                            sublist.append((moose.element(enzpar),'t',countuniqItem[enzpar]))
                    cntDict[items] = sublist,prdlist
            elif baseObj == 'Function':
                for items in moose.wildcardFind(path):
                    sublist = []
                    prdlist = []
                    item = items.path+'/x[0]'
                    uniqItem,countuniqItem = countitems(item,'input',moose)
                    for funcpar in uniqItem:
                        sublist.append((moose.element(funcpar),'sts',countuniqItem[funcpar]))
                    
                    uniqItem,countuniqItem = countitems(items,'valueOut',moose)
                    for funcpar in uniqItem:
                        prdlist.append((moose.element(funcpar),'stp',countuniqItem[funcpar]))
                    cntDict[items] = sublist,prdlist

            # elif baseObj == 'Function':
            #     #ZombieSumFunc adding inputs
            #     inputlist = []
            #     outputlist = []
            #     funplist = []
            #     nfunplist = []
            #     for items in moose.wildcardFind(path):
            #         for funplist in moose.moose.element(items).neighbors['valueOut']:
            #             for func in funplist:
            #                 funcx = moose.moose.element(items.path+'/x[0]')
            #                 uniqItem,countuniqItem = countitems(funcx,'input')
            #                 for inPut in uniqItem:
            #                     inputlist.append((inPut,'st',countuniqItem[inPut]))
            #             cntDict[func] = inputlist
            else:
                for tab in moose.wildcardFind(path):
                    tablist = []
                    uniqItem,countuniqItem = countitems(tab,'output',moose)
                    for tabconnect in uniqItem:
                        tablist.append((moose.element(tabconnect),'tab',countuniqItem[tabconnect]))
                    cntDict[tab] = tablist

def countitems(mitems,objtype,moose):
    items = []
    items = moose.element(mitems).neighbors[objtype]
    uniqItems = set(items)
    countuniqItems = Counter(items)
    return(uniqItems,countuniqItems)

def autoCoordinates(meshEntry,srcdesConnection, moose):
    xmin = 0.0
    xmax = 1.0
    ymin = 0.0
    ymax = 1.0
    G = nx.Graph()
    for cmpt,memb in meshEntry.items():
        for enzObj in find_index(memb,'enzyme'):
            G.add_node(enzObj.path)
    for cmpt,memb in meshEntry.items():
        for poolObj in find_index(memb,'pool'):
            G.add_node(poolObj.path)
        for cplxObj in find_index(memb,'cplx'):
            G.add_node(cplxObj.path)
            G.add_edge((cplxObj.parent).path,cplxObj.path)
        for reaObj in find_index(memb,'reaction'):
            G.add_node(reaObj.path)
        
    for inn,out in srcdesConnection.items():
        if (inn.className =='ZombieReac'): arrowcolor = 'green'
        elif(inn.className =='ZombieEnz'): arrowcolor = 'red'
        else: arrowcolor = 'blue'
        if isinstance(out,tuple):
            if len(out[0])== 0:
                print inn.className + ':' +inn.name + "  doesn't have input message"
            else:
                for items in (items for items in out[0] ):
                    G.add_edge(moose.element(items[0]).path,inn.path)
            if len(out[1]) == 0:
                print inn.className + ':' + inn.name + "doesn't have output mssg"
            else:
                for items in (items for items in out[1] ):
                    G.add_edge(inn.path,moose.element(items[0]).path)
        elif isinstance(out,list):
            if len(out) == 0:
                print "Func pool doesn't have sumtotal"
            else:
                for items in (items for items in out ):
                    G.add_edge(moose.element(items[0]).path,inn.path)
    
    nx.draw(G,pos=nx.spring_layout(G))
    #plt.savefig('/home/harsha/Desktop/netwrokXtest.png')
    xcord = []
    ycord = []
    position = nx.spring_layout(G)
    for item in position.items():
        xy = item[1]
        ann = moose.Annotator(item[0]+'/info')
        ann.x = xy[0]
        xcord.append(xy[0])
        ann.y = xy[1]
        ycord.append(xy[1])
    # for y in position.values():
    #     xcord.append(y[0])
    #     ycord.append(y[1])
    if xcord and ycord:
        xmin = min(xcord)
        xmax = max(xcord)
        ymin = min(ycord)
        ymax = max(ycord)    	    
    return(xmin,xmax,ymin,ymax,position)

def find_index(value, key):
    """ Value.get(key) to avoid expection which would raise if empty value in dictionary for a given key """
    if value.get(key) != None:
        return value.get(key)
    else:
        raise ValueError('no dict with the key found')
