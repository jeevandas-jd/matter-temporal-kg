

import json
# NOTE: BasicInformation cluster is retained in cluster_nodes and edges
# intentionally — vendor name and product identity may be useful
# for device-level filtering in future query functions.
# StateIntervals for BasicInformation are skipped (static metadata).
def parse_device(device:dict,room_id=str,base_time=str)->json:


    """
    GOAL:
    Takes one device dict from SimuHome JSON,
    the room it belongs to, and the episode base_time.
    Returns a dict with keys: device_node, cluster_nodes, state_intervals, edges
    """


    output={

    }
    STATIC_CLUSTERS = {"BasicInformation", "Descriptor", "Identify"}
    output["device_node"]={"device_id":device["device_id"],"device_name":device["attributes"]["0.BasicInformation.ProductName"],
                           "room_id":room_id,"vendor_name":device["attributes"]["0.BasicInformation.VendorName"]
                           }
    
    #get clusters 
    cluster_key=device["attributes"].keys()
    clusters=list(set([k.split(".")[1] for k in cluster_key]))

    output["device_node"]["clusters"]=clusters
    cluster_nodes=[] 
    attributes=device["attributes"]
    device_id=device["device_id"]
    """"each cluster node have :-
    cluster_id eg:bathroom_air_conditioner_1.1.Thermostat
    cluster_name eg:Termostat
    endpiont_id eg:1
    device_id  eg:bathroom_air_conditioner_1
    """

    for cluster in clusters:
        if cluster in STATIC_CLUSTERS:
            continue 
        cluster_node={}
        cluster_node["cluster_id"]=device_id+"."+cluster    
        cluster_node["cluster_name"]=cluster
        for key in attributes.keys():
            if key.split(".")[1] == cluster:
                cluster_node["endpoint_id"] = int(key.split(".")[0])
                break
        cluster_node["device_id"]=device_id
        cluster_nodes.append(cluster_node)
    output["cluster_nodes"]=cluster_nodes
    # find any key belonging to this cluster and take the first part

    """
    state interval node :-
    - state_interval_id eg:\"si_001\"
    - cluster_id eg:bathroom_air_conditioner_1.1.Thermostat
    - attribute_name:OnOff
    - value:True
    - start_time: 2025-08-23 10:01:47
    - end_time : Null
    """

    state_intervals=[]
    for key in attributes.keys():
        if key.split(".")[1] in STATIC_CLUSTERS:
            continue 
        else:
            state_interval={}
            state_interval["state_interval_id"]="si_"+key.replace(".","_")
            state_interval["cluster_id"]=device_id+"."+key.split(".")[1]
            state_interval["attribute_name"]=key.split(".")[2]
            state_interval["value"]=attributes[key]
            state_interval["start_time"]=base_time
            state_interval["end_time"]=None
            NORMALIZE_ATTRS = {"Temperature", "MeasuredValue", "Setpoint"}
            attr_name = key.split(".")[2]
            if any(n in attr_name for n in NORMALIZE_ATTRS):
                state_interval["value"] = state_interval["value"] / 100 if state_interval["value"] is not None else None
            state_intervals.append(state_interval)
    output["state_intervals"]=state_intervals

    """edges :-
    exapmle:
    (bathroom_air_conditioner_1) -[INSTALLED_IN]->  (bathroom)
(bathroom_air_conditioner_1) -[HAS_CLUSTER]->   (1.Thermostat)
(bathroom_air_conditioner_1) -[HAS_CLUSTER]->   (1.FanControl)
(bathroom_air_conditioner_1) -[HAS_CLUSTER]->   (1.OnOff)
(1.Thermostat)              -[HAS_STATE]->     (si_001)
(1.OnOff)                    -[HAS_STATE]->     (si_002)
    """
    edges=[]
    #device to room edge
    edges.append({"source":device_id,"target":room_id,"edge_type":"INSTALLED_IN"})
    #device to cluster edge
    for cluster in clusters:
        if cluster in STATIC_CLUSTERS:
            continue
        edges.append({"source":device_id,"target":device_id+"."+cluster,"edge_type":"HAS_CLUSTER"})
    #cluster to state interval edge
    for key in attributes.keys():
        edges.append({"source":device_id+"."+key.split(".")[1],"target":"si_"+key.replace(".","_"),"edge_type":"HAS_STATE"})
    
    output["edges"]=edges
    #output={"device_node":output["device_node"],"cluster_nodes":output["cluster_nodes"],"state_intervals":output["state_intervals"],"edges":output["edges"]}
    output=json.dumps(output,indent=4)
    return output
if __name__=="__main__":
    device={
            "device_id": "utility_room_dehumidifier_1",
            "device_type": "dehumidifier",
            "attributes": {
              "0.BasicInformation.ProductID": 7,
              "0.BasicInformation.ProductName": "Dehumidifier",
              "0.BasicInformation.VendorID": 1,
              "0.BasicInformation.VendorName": "LG Electronics",
              "1.FanControl.FanMode": 1,
              "1.FanControl.FanModeSequence": 1,
              "1.FanControl.PercentCurrent": 3,
              "1.FanControl.PercentSetting": 3,
              "1.OnOff.OnOff":True,
              "2.RelativeHumidityMeasurement.MaxMeasuredValue": 9500,
              "2.RelativeHumidityMeasurement.MeasuredValue": 6445,
              "2.RelativeHumidityMeasurement.MinMeasuredValue": 1000,
              "2.RelativeHumidityMeasurement.Tolerance": None
            }
          }
    out=parse_device(device=device,room_id="bathroom",base_time="10-36-54")
    print(out)