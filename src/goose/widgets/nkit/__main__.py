from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from goose import *
import moogli
import moogli.simulator
from moogli import simulator
from moogli import NetworkViewer
import operator
import math



class NeuroKitWidget(NetworkViewer) :

    def __init__(self, instance, signals = None, parent = None, slot = None, details = 0):
        self.slot = slot
        self.instance = instance
        self.moose    = instance["moose"]
        self.signals  = signals
        self.model    = instance["model"]
        self._setup_menus()
        print("Doing what needs to be done.")
        network = moogli.simulator.moose.read_network(path = self.model.path, moose = self.moose, details = details)
        NetworkViewer.__init__(self, network, id, id, id)
        print("Done what needed to be done.")
        # #print(neurons)
        # #print(compartments)
        # #print(voxels)
        # #print(spines)
        # self.neurons["neurons"] = neurons
        # self.compartments["compartments"] = compartments
        # self.voxels["voxels"] = voxels
        # self.spines["spines"] = spines
        QtCore.QObject.connect(self, QtCore.SIGNAL('selected(const char *)'), self.visualized_object_selected_slot);


    def _setup_menus(self):
        self.chemical_compartment_menu      = QMenu()
        self.electrical_compartment_menu    = QMenu()
        self.neuron_menu                    = QMenu()

        self.chemical_compartment_menu.addAction("Show Chemical Signalling")
        self.chemical_compartment_menu.addAction("Switch to Electrical View")
        self.chemical_compartment_menu.addAction("Properties" )

        self.electrical_compartment_menu.addAction("Switch to Chemical View")
        self.electrical_compartment_menu.addAction("Electrical Compartment Properties")

        self.neuron_menu.addAction("Show Chemical Signaling")
        self.neuron_menu.addAction("Switch to Electrical View")
        self.neuron_menu.addAction("Simplified View")
        self.neuron_menu.addAction("Detailed View")
        self.neuron_menu.addAction("Properties")


    @pyqtSlot(str)
    def visualized_object_selected_slot(self, name):
        cursor_position = QCursor().pos()
        if self.moose.exists(name):
            if isinstance(self.moose.element(name), self.moose.Neuron):
                self.neuron_menu.exec_(cursor_position)
            else:
                self.electrical_compartment_menu.exec_(cursor_position)
        else:
            pieces = name.split("/")
            voxel_index = int(pieces[-1])
            compartment_path = "/".join(pieces[0:-1])
            print("Clicked on " + compartment_path + " : " + str(voxel_index))
            self.slot(compartment_path, voxel_index)
            # self.chemical_compartment_menu.exec_(cursor_position)


    # def _compartment_parameters(self, moose_compartment):
    #     distal_radius = moose_compartment.diameter / 2.0
    #     distal = [ moose_compartment.x * 10000000
    #              , moose_compartment.y * 10000000
    #              , moose_compartment.z * 10000000
    #              , distal_radius       * 10000000
    #              ]
    #     try:
    #         parent_compartment = moose_compartment.neighbors["raxial"][0][0]
    #         proximal_radius  = parent_compartment.diameter / 2.0
    #         proximal = [ moose_compartment.x0 * 10000000
    #                    , moose_compartment.y0 * 10000000
    #                    , moose_compartment.z0 * 10000000
    #                    , proximal_radius      * 10000000
    #                    ]
    #         center = [ (proximal[0] + distal[0]) / 2.0
    #                  , (proximal[1] + distal[1]) / 2.0
    #                  , (proximal[2] + distal[2]) / 2.0
    #                  , distal[3]
    #                  ]
    #     except IndexError:
    #         center   = distal
    #         proximal = None

    #     return (proximal, distal, center)


    # def read_network(self, name = "", path = "", track_parent = True):
    #     neuron_map      = {}
    #     compartment_map = {}
    #     voxel_map       = {}
    #     network = moogli.Network(name)
    #     compartments = self.moose.wildcardFind(path + "/##[ISA=CompartmentBase]")
    #     neuron_ids = set( map( lambda compartment : "" if compartment.parent.path == "/" else compartment.parent.path
    #                          , compartments
    #                          )
    #                     )
    #     for neuron_id in neuron_ids:
    #         neuron = moogli.Neuron(neuron_id)
    #         neuron_map[neuron_id] = neuron
    #         soma_center = None
    #         moose_compartments = self.moose.wildcardFind(neuron_id + "/#[ISA=CompartmentBase]")
    #         for moose_compartment in moose_compartments:
    #             parent_direction = None
    #             compartment = moogli.Compartment(moose_compartment.path)
    #             compartment_map[moose_compartment.path] = compartment
    #             (proximal, distal, center) = self._compartment_parameters(moose_compartment)
    #             if proximal is None :
    #                 soma_center = distal
    #             else:
    #                 parent_compartment = moose_compartment.neighbors["raxial"][0][0]
    #                 (parent_proximal, parent_distal, parent_center) = self._compartment_parameters(parent_compartment)
    #                 if parent_proximal is None:
    #                     parent_direction = None
    #                 else:
    #                     parent_direction = map(operator.sub, parent_distal, parent_proximal)
    #                     parent_height = math.sqrt(sum(map(lambda x : x * x, parent_direction)))
    #                     parent_direction = [dim/parent_height for dim in parent_direction][0:3]
    #             #print(parent_direction)
    #             compartment.add_geometry(distal, proximal, parent_direction)
    #             neuron.add_compartment(compartment)
    #             compartment.show_geometry(1, True)
    #         neuron.add_geometry(soma_center)
    #         neuron.show_geometry(0, True)
    #         network.add_neuron(neuron)
    #     return ( network
    #            , neuron_map.values()
    #            , [compartment_map[key.path] for key in self.moose.wildcardFind(path + "/##[ISA=CompartmentBase]")]
    #            , []
    #            , []
    #            )


    #         #neuron.show_geometry(0, True)

    #     meshes = self.moose.wildcardFind(path + "/##[ISA=NeuroMesh]")
    #     # print(path + "/##[ISA=NeuroMesh]")
    #     for mesh in meshes:
    #         for i in range(len(mesh.elecComptList)):
    #             soma = False
    #             average_direction = [0.0, 0.0, 0.0, 0.0]
    #             moose_compartment = mesh.elecComptList[i][0]
    #             neuron      = network.get_neuron(moose_compartment.parent.path)
    #             compartment = neuron.get_compartment(moose_compartment.path)
    #             voxel_count = mesh.endVoxelInCompt[i] - mesh.startVoxelInCompt[i]
    #             (proximal, distal, center) = self._compartment_parameters(moose_compartment)
    #             # print(proximal, distal, center)
    #             if proximal is None:
    #                 soma = True
    #                 for child in moose_compartment.neighbors["axial"]:
    #                     (child_proximal, child_distal, child_center) = self._compartment_parameters(child[0])
    #                     average_direction = map( operator.add
    #                                            , average_direction
    #                                            , map( operator.sub
    #                                                 , child_distal
    #                                                 , child_proximal
    #                                                 )
    #                                            )
    #                     #print(average_direction)
    #                 total_height = average_direction
    #                 total_height[3] = 0.0 # radius will be recomputed in the for loop below
    #                 magnitude = math.sqrt(sum([dim * dim for dim in total_height]))
    #                 total_height = [ 2.0 * distal[3] * dim / magnitude for dim in total_height ]
    #                 proximal = previous_distal = map(operator.sub, distal, [dim / 2.0 for dim in total_height])
    #                 for j in range(0, voxel_count):
    #                     phi1 = 1 - (j + 0.0) / voxel_count
    #                     phi2 = 1 - (j + 1.0) / voxel_count
    #                     r1 = distal[3] * math.sin( math.pi * phi1)
    #                     r2 = distal[3] * math.sin( math.pi * phi2)
    #                     voxel_proximal = previous_distal
    #                     temp = [ (j + 1) * dim / voxel_count
    #                              for dim in total_height
    #                            ]
    #                     previous_distal = voxel_distal  = map(operator.add, proximal, temp)
    #                     voxel_distal[3] = r2
    #                     voxel_proximal[3] = r2
    #                     # print(voxel_proximal, voxel_distal)
    #                     voxel = moogli.Voxel(moose_compartment.path + "/" + str(j + mesh.startVoxelInCompt[i]))
    #                     voxel_map[mesh.startVoxelInCompt[i] + j] = voxel
    #                     voxel.set_geometry(voxel_distal, voxel_proximal)
    #                     compartment.add_voxel(voxel)
    #                 compartment.show_geometry(1, True)
    #             else:
    #                 total_height    = map(operator.sub, distal, proximal)
    #                 previous_distal = proximal
    #                 for j in range(0, voxel_count):
    #                     voxel_proximal = previous_distal
    #                     temp = [ (j + 1) * dim / voxel_count
    #                              for dim in total_height
    #                            ]
    #                     previous_distal = voxel_distal  = map(operator.add, proximal, temp)
    #                     # print(voxel_proximal, voxel_distal)
    #                     voxel = moogli.Voxel(moose_compartment.path + "/" + str(j + mesh.startVoxelInCompt[i]))
    #                     voxel.set_geometry(voxel_distal, voxel_proximal)
    #                     voxel_map[mesh.startVoxelInCompt[i] + j] = voxel
    #                     compartment.add_voxel(voxel)
    #             compartment.show_geometry(1, True)

    #     # SPINES

    #     meshes = self.moose.wildcardFind(path + "/##[ISA=SpineMesh]")
    #     spine_map = {}
    #     for mesh in meshes:
    #         for i in range(len(mesh.elecComptList)):
    #             soma = False
    #             average_direction = [0.0, 0.0, 0.0, 0.0]
    #             moose_compartment = mesh.elecComptList[i][0]
    #             neuron      = network.get_neuron(moose_compartment.parent.path)
    #             compartment = neuron.get_compartment(moose_compartment.path)
    #             voxel_count = mesh.endVoxelInCompt[i] - mesh.startVoxelInCompt[i]
    #             (proximal, distal, center) = self._compartment_parameters(moose_compartment)
    #             # print(proximal, distal, center)
    #             if proximal is None:
    #                 soma = True
    #                 for child in moose_compartment.neighbors["axial"]:
    #                     (child_proximal, child_distal, child_center) = self._compartment_parameters(child[0])
    #                     average_direction = map( operator.add
    #                                            , average_direction
    #                                            , map( operator.sub
    #                                                 , child_distal
    #                                                 , child_proximal
    #                                                 )
    #                                            )
    #                     #print(average_direction)
    #                 total_height = average_direction
    #                 total_height[3] = 0.0 # radius will be recomputed in the for loop below
    #                 magnitude = math.sqrt(sum([dim * dim for dim in total_height]))
    #                 total_height = [ 2.0 * distal[3] * dim / magnitude for dim in total_height ]
    #                 proximal = previous_distal = map(operator.sub, distal, [dim / 2.0 for dim in total_height])
    #                 for j in range(0, voxel_count):
    #                     phi1 = 1 - (j + 0.0) / voxel_count
    #                     phi2 = 1 - (j + 1.0) / voxel_count
    #                     r1 = distal[3] * math.sin( math.pi * phi1)
    #                     r2 = distal[3] * math.sin( math.pi * phi2)
    #                     voxel_proximal = previous_distal
    #                     temp = [ (j + 1) * dim / voxel_count
    #                              for dim in total_height
    #                            ]
    #                     previous_distal = voxel_distal  = map(operator.add, proximal, temp)
    #                     voxel_distal[3] = r2
    #                     voxel_proximal[3] = r2
    #                     # print(voxel_proximal, voxel_distal)
    #                     voxel = moogli.Voxel(moose_compartment.path + "/" + str(j + mesh.startVoxelInCompt[i]))
    #                     spine_map[mesh.startVoxelInCompt[i] + j] = voxel
    #                     voxel.set_geometry(voxel_distal, voxel_proximal)
    #                     compartment.add_voxel(voxel)
    #                 compartment.show_geometry(1, True)
    #             else:
    #                 total_height    = map(operator.sub, distal, proximal)
    #                 previous_distal = proximal
    #                 for j in range(0, voxel_count):
    #                     voxel_proximal = previous_distal
    #                     temp = [ (j + 1) * dim / voxel_count
    #                              for dim in total_height
    #                            ]
    #                     previous_distal = voxel_distal  = map(operator.add, proximal, temp)
    #                     # print(voxel_proximal, voxel_distal)
    #                     voxel = moogli.Voxel(moose_compartment.path + "/" + str(j + mesh.startVoxelInCompt[i]))
    #                     voxel.set_geometry(voxel_distal, voxel_proximal)
    #                     spine_map[mesh.startVoxelInCompt[i] + j] = voxel
    #                     compartment.add_voxel(voxel)
    #             compartment.show_geometry(1, True)



    #     return ( network
    #            , neuron_map.values()
    #            , [compartment_map[key.path] for key in self.moose.wildcardFind(path + "/##[ISA=CompartmentBase]")]
    #            , [voxel_map[key] for key in sorted(voxel_map.keys())]
    #            , [spine_map[key] for key in sorted(spine_map.keys())]
    #            )
