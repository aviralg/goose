class Moose():
    def __init__(self, host = None, port = None, modelfilenames = []):

        self.models         = []
        self.start(host, port, pid)
        self.connect()
        self.acquire()
        [self.load(modelfilename) for modelfilename in modelfilenames]


    def connect():
        self.__dict__.update(self.connection.__dict__)

    def load(self, modelfilename):
        self.models.append(Model())
        pass

    def inspect(self):
        pass

    def acquire(self):
        pass

    def start(self, host, port, pid):
        if port != 0:
            self.port = port
            self.host = host
            self.pid  = pid
            return;
        self.port = get_free_port()
        self.host = host
        logfile = os.path.join(MOOSE_LOG_DIRECTORY, str(port) + ".log")
        open(logfile, "w").close()
        args    = ["python", GOOSE_DIRECTORY + "/moose_server.py", "-p", str(port), "--logfile", logfile]
        INFO("Starting Moose Server on " + self.host + ":" + str(port))
        self.pid = subprocess.Popen(args).pid

    def connect(self):
        try:
            DEBUG("Connecting to Moose server on " + self.host + ":" + str(self.port))
            self.connection = rpyc.classic.connect(self.host, self.port)
            INFO("Connected to Moose server on " + self.host + ":" + str(self.port))
            self.__dict__.update(self.connection.modules.moose.__dict__)
            self.thread = rpyc.BgServingThread(self.connection)
        except socket.error as serr:
            if serr.errno != errno.ECONNREFUSED:
                raise serr
            DEBUG("Failed to connect to Moose server on " + self.host + ":" + str(self.port))
            system.sleep(1.0)
            self.connect()
            # QTimer.singleShot(1000, lambda : self.connect())



            modelname = self.unique_modelname(filename)
            connection.modules.moose.loadModel(filename, modelname)
            INFO("Loaded " + modelname)
            self.current_model = self.models[modelname] = \
                { "conn"     :   connection
                , "moose"    :   connection.modules.moose
                , "pid"      :   pid
                , "host"     :   host
                , "port"     :   port
                , "model"    :   connection.modules.moose.element(modelname)
                , "service"  :   connection.root
                , "thread"   :   rpyc.BgServingThread(connection)
                }
