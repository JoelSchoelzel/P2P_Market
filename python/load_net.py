#import pandapower as pp
import pandapower.networks as nw
from pandapower.plotting import simple_plot
from pandapower.plotting import pf_res_plotly
import gurobipy as gp
import pandas as pd

def create_net(options):

    # %% create network
    if options["Dorfnetz"]:
        net = nw.create_kerber_dorfnetz()
    else:
        net = nw.create_kerber_vorstadtnetz_kabel_2()

    simple_plot(net, show_plot=True)
    #pf_res_plotly(net)

    # %% extract node and line information from network
    # extract existing lines
    nodeLines = []
    for i in range(len(net.line['from_bus'])):
        nodeLines.append((net.line['from_bus'][i], net.line['to_bus'][i]))
    nodeLines = gp.tuplelist(nodeLines)

    # extract maximal current for lines
    # multiply with 400 V to get maximal power in kW
    # powerLine is positive, if the power flows into the net, out of the trafo ('from bus n to bus m'), trafo is bus 0
    powerLine_max = {}
    for [n,m] in nodeLines:
        powerLine_max[n,m] = (net.line['max_i_ka'][nodeLines.index((n,m))]) * 400

    # empty dict to store net data
    net_data = {}

    # set trafo bounds due to technichal limits
    net_data["trafo_max"] = float(net.trafo.sn_mva * 1000.)

    # specify grid nodes for whole grid and trafo; choose and allocate load, injection and battery nodes
    net_data["net_nodes"] = {}
    net_data["net_nodes"]["grid"] = net.bus.index.values
    net_data["net_nodes"]["trafo"] = net.trafo['lv_bus'].values
    net_data["net_nodes"]["load"] = net.load['bus'].values
    net_data["gridnodes"] = list(net_data["net_nodes"]["grid"])

    # allocate building nodes to gridnodes
    node_list = list(range(len(net.load['bus'])))
    net_data["grid_allo"] = pd.DataFrame(node_list, columns=["nodes"])
    net_data["grid_allo"]["gridnodes"] = net_data["net_nodes"]["load"]

    # extract existing lines
    net_data["nodeLines"] = []
    for i in range(len(net.line['from_bus'])):
        net_data["nodeLines"].append((net.line['from_bus'][i],net.line['to_bus'][i]))
        net_data["nodeLines"] = gp.tuplelist(net_data["nodeLines"])

    # extract maximal current for lines
    # multiply with 400 V to get maximal power in kW
    net_data["powerLine_max"] = {}
    for [n,m] in net_data["nodeLines"]:
        net_data["powerLine_max"][n,m] = (net.line['max_i_ka'][net_data["nodeLines"].index((n,m))]) * 400

    return net_data

if __name__ == "__main__":

    # Set options
    options = {"Dorfnetz": True}
    net_data = create_net(options)