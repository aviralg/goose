from common import *
from kkit import KineticsWidget

if __name__ == "__main__":
    import moose
    app = QtGui.QApplication(sys.argv)
    size = QtCore.QSize(1024 ,768)
    #modelPath = 'Kholodenko'
    modelPath = 'acc27'
    #modelPath = 'acc8'
    #modelPath = '3ARECB'
    #modelPath = '3AreacB'
    #modelPath = '5AreacB'
    itemignoreZooming = False
    try:
        filepath = '../../Demos/Genesis_files/'+modelPath+'.g'
        filepath = '/home/harsha/genesis_files/gfile/'+modelPath+'.g'
        print filepath
        f = open(filepath, "r")
        moose.loadModel(filepath,'/'+modelPath)

        #moose.le('/'+modelPath+'/kinetics')
        dt = KineticsWidget({ "moose" : moose
                            , "model" : moose.element('/'+modelPath)
                            }
                           )
        dt.modelRoot ='/'+modelPath
        ''' Loading moose signalling model in python '''
        #execfile('/home/harsha/BuildQ/Demos/Genesis_files/scriptKineticModel.py')
        #dt.modelRoot = '/model'

        # dt.updateModelView()
        dt.show()

    except  IOError, what:
      (errno, strerror) = what
      print "Error number",errno,"(%s)" %strerror
      sys.exit(0)
    sys.exit(app.exec_())
