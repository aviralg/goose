from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.inprocess import QtInProcessKernelManager
from PyQt4 import Qt, QtGui, QtCore
import sys

class IPythonConsole(RichIPythonWidget):

    def __init__(self, namespace = dict(), **kwargs):
        super(RichIPythonWidget, self).__init__()
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel = self.kernel_manager.kernel
        self.kernel.gui = 'qt4'
        self.kernel.user_ns = namespace
        self.kernel.shell.push(kwargs)
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()
        self.exit_requested.connect(self.exit)

    def update_namespace(self, **kwargs):
        self.kernel.shell.push(kwargs)

    def exit(self, *args):
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()
        sys.exit()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    namespace = globals()
    main = IPythonConsole(namespace)
    main.show()
    print(globals()["a"])
    # main2 = IPythonConsole()
    # main2.show()
    sys.exit(app.exec_())
