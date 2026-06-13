import json
import os
"""
GOAL:
TAKE a full smart home episode JSON,
parse it and return complete graph 
with all nodes and edges for all rooms and devices

keys: location_node,user_node,device_node,cluster_node. state_interval_node,events_node,and all_edges
"""

class UserNode:

    def __init__(self,user_id:str=None,user_name:str=None,location:str=None):
        self.user_id=user_id
        self.user_name=user_name
        self.location=location
    
    def get_node(self):
        return {"user_id":self.user_id,"user_name":self.user_name,"location":self.location}
class DeviceNode:
    def __init__(self,device_id:str=None,device_name:str=None,room_id:str=None,vendor_name:str=None,clusters:list=None):
        self.device_id=device_id
        self.device_name=device_name
        self.room_id=room_id
        self.vendor_name=vendor_name
        self.clusters=clusters
    def get_node(self):
        return {"device_id":self.device_id,"device_name":self.device_name,"room_id":self.room_id,"vendor_name":self.vendor_name,"clusters":self.clusters}

class LocationNode:
    def __init__(self,location_id:str=None,location_name:str=None,temperature:str=None,humidity:str=None,illuminance:str=None,pm10:str=None,devices:list=None):
        self.location_id=location_id
        self.location_name=location_name
        self.temperature=temperature
        self.humidity=humidity
        self.illuminance=illuminance
        self.pm10=pm10
        self.devices=devices
    def get_node(self):
        return {"location_id":self.location_id,"location_name":self.location_name,"temperature":self.temperature,"humidity":self.humidity,"illuminance":self.illuminance,"pm10":self.pm10,"devices":self.devices}
    
class clusterNode:
    def __init__(self,cluster_id:str=None,cluster_name:str=None,endpoint_id:str=None,device_id:str=None):
        self.cluster_id=cluster_id
        self.cluster_name=cluster_name
        self.endpoint_id=endpoint_id
        self.device_id=device_id
    def get_node(self):
        return {"cluster_id":self.cluster_id,"cluster_name":self.cluster_name,"endpoint_id":self.endpoint_id,"device_id":self.device_id}
class stateIntervalNode:
    def __init__(self,state_interval_id:str=None,cluster_id:str=None,attribute_name:str=None,value:str=None,start_time:str=None,end_time:str=None):
        self.state_interval_id=state_interval_id
        self.cluster_id=cluster_id
        self.attribute_name=attribute_name
        self.value=value
        self.start_time=start_time
        self.end_time=end_time
    def get_node(self):
        return {"state_interval_id":self.state_interval_id,"cluster_id":self.cluster_id,"attribute_name":self.attribute_name,"value":self.value,"start_time":self.start_time,"end_time":self.end_time}
class eventNode:
    def __init__(self,event_id,event_type,timestamp,description,source_id):
        self.event_id=event_id
        self.event_type=event_type
        self.timestamp=timestamp
        self.description=description
        self.source_id=source_id
    def get_node(self):
        return {"event_id":self.event_id,"event_type":self.event_type,"timestamp":self.timestamp,"description":self.description,"source_id":self.source_id}
class edges:
    pass

def parse_episode(episode_json:json)->json:
    BASE_TIME=episode_json["initial_home_config"]["base_time"]

    #user node

    pass



DATA=os.path.join(os.getcwd(),"src","data","qt1_feasible_seed_1.json")

if __name__=="__main__":
    with open(DATA) as f:
        episode_json=json.load(f)
    
    print(episode_json.keys())

    print(episode_json["initial_home_config"]["rooms"]["bathroom"]["devices"])

