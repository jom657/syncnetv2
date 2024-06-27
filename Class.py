import re
import os
import ipaddress
import logging
import pandas as pd


# ---------------- Super Class ----------------------
class LoadFile():
    
    def __init__(self,file_name,folder_path):
        self.file_name = file_name
        self.folder_path = folder_path
        self.file_path = os.path.join(self.folder_path, self.file_name)
        self.equipment_name_raw = self.remove_ip_in_filename(file_name)
        self.equipment_name = self.equipment_name_raw.split('.')[0]

        # logging.basicConfig(filename='error_logs.log', level=logging.ERROR)
        self.errors = set()  # Keep track of nodes with errors
        
        # Get the list of nodes with exception (dili na iloop ang mga walay node_name sa description)
        self.df_exception = pd.read_csv(os.path.join(os.path.abspath(os.getcwd()),r'Reference\Exception.csv'), index_col=False, dtype='unicode')
        self.list_exception = self.df_exception['Node Name'].values.tolist()
        

    
    def remove_ip_in_filename(self,filename):
        # Define a regular expression pattern to match an IP address
        ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}_'
        # Use re.sub() to replace the matched IP address with an empty string
        new_filename = re.sub(ip_pattern, '', filename)
        return new_filename
    
    def log_value(self, value):
        self.logger.info(value)
    
    def vlan_array(self, list,area):  #----- 'list' should be the result of get_data_list_from()
        vlan_list = []
        check_loop = False
        for line in list:
            
            try:
                result_array=[]
                
                # check if PHY and Protocol is present (up or down)
                if ("up" in line) or ("down" in line):
                    # split the lines to create a new array
                    interface = re.split(r'\s{3,}', line)[0]
                    status_phy = re.split(r'\s{3,}', line)[1]
                    status_protocol = re.split(r'\s{3,}', line)[2]
                    desc = re.split(r'\s{3,}', line)[3]

                # In ATN910B AN has no PHY and Protocol (up or down)
                else: 
                    status_phy = 'up'
                    status_protocol = 'up'
                    interface = re.split(r'\s{3,}', line)[0]
                    desc = re.split(r'\s{3,}', line)[1]
                
                # Get only the interface that has VLAN with 'UP' status
                if len(interface.split('.')) > 1 and ("up" in status_phy):

                    vlan = interface.split('.')[1]
                    vlan = vlan.split('(')[0]
                    
                    result_array += [area,self.equipment_name,interface,status_phy,status_protocol,desc,vlan]

                    # store to the final array
                    vlan_list.append(result_array)
                else:
                    if "down" in status_phy and not check_loop:
                        check_loop = True
                        node_down = open("shutdown_node.log", "a")
                        node_down.write(f"{area}|{self.equipment_name}.{interface}|{desc}\n")
                        node_down.close()

            except Exception as e:
                error_message = f"Error on the file name: {self.file_name}\n"

                if error_message not in self.errors:
                    self.log_error(f"An error occurred: {e} -- {error_message}")
                    error_log = open("error_logs.log", "a")
                    error_log.write(f"An error occurred: {e} -- {error_message}\n")
                    error_log.close()
 
                    self.errors.add(error_message)

        
        return vlan_list
    
    def log_error(self, message):
        # Log the error
        logging.error(message)

    def subnet_mask_to_subnet(self,ip_param):
        try:
            subnet = ipaddress.IPv4Network(f"{ip_param[0]}/{ip_param[1]}", strict=False)
            return str(subnet.network_address) + '/' + str(subnet.prefixlen)
        except ValueError:
            return "Invalid subnet mask"  

# ----------------- Child Class -----------------------------
class Agg(LoadFile):  

    def get_data_list_from(self,command,port):
        # ----- Get Description and Port
        dump_list = []
        capturing = False #True if the script will start to capture the line
        # port = "100GE1/1/16"
        
        # with open(f"{self.file_name}.txt", 'rt') as data:
        try:
            with open(self.file_path, 'rt') as data:
                for line in data:
                    if command in line:  
                        capturing = True
                        continue
                    # elif (f"<{self.equipment_name}>") in line and capturing:
                    elif ("display") in line and capturing:
                        capturing = False
                        break
                    elif capturing and port in line:
                            dump_list.append(line)
            
            return dump_list
          
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")
    
    def get_vsi(self,raw_data,vlan_array,homing):
        # vlan_hsi_bng = [sublist + bng_homing for sublist in vlan_hsi]
        dump_list = []

        for list in vlan_array:
            # find the vsi per interface
            interface = list[2]
            vsi = None
            capturing = False

            # if SIP
            if homing == '':
                interface = interface.replace('VE','Virtual-Ethernet')

            for line in raw_data:
                if f"interface {interface}" in line:  
                    capturing = True
                    continue
                elif '#\n' in line and capturing:
                    capturing = False
                    break
                elif capturing and 'vsi' in line:
                        match = re.search(r'vsi\s(.+)', line)
                        vsi = match.group(1)
                        if homing == '': # ---- for SIP
                            interface2 = interface.replace('/0.', '/1.')
                            ip = self.get_sip_ip(raw_data,interface2)
                            new_arr = list + [vsi] + [ip]
                        else: # --- for HSI
                            new_arr = list + homing + [vsi]
                        dump_list.append(new_arr)

        return(dump_list)
        
    
    # get the data from command
    def get_data_from(self,command):
        dump_list = []
        capturing = False #True if the script will start to capture the line
        
        try:
            with open(self.file_path, 'rt') as data:
                for line in data:
                    if command in line:  
                        capturing = True
                        continue
                    elif ("display") in line and capturing:
                        capturing = False
                        break
                    elif capturing:
                            dump_list.append(line)

            return dump_list
        
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")
    
    def get_sip_ip(self,raw_data,interface):
        capturing = False
        ip_array = []
        final_ip = []
        for line in raw_data:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)', line)
            
            if f"interface {interface}" in line:  
                capturing = True
                continue
            elif ('#\n' in line or re.search(r'#\s{5,}',line)) and capturing:
                capturing = False
                break
            elif capturing and 'ip address' in line and match:
                ip_array.append(line)
                

        if ip_array:
            if len(ip_array) == 1:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)', ip_array[0])
                ip_address = match.group(1)
                subnet = match.group(2)
                final_ip = [ip_address,subnet]
                # print(ip_array)
            
            else:
                for ip in ip_array:
                    if 'sub' in ip:
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)', ip)
                        ip_address = match.group(1)
                        subnet = match.group(2)
                        final_ip = [ip_address,subnet]

            final_ip = self.subnet_mask_to_subnet(final_ip)
            return final_ip                       
                    

class An(LoadFile):  

    def get_data_list_from(self,command,search):    
        # ----- Get Description and Port
        dump_list = []
        capturing = False #True if the script will start to capture the line
        try:
            with open(self.file_path, 'rt') as data:
                trunk = None
                for line in data:
                    if command in line:  
                        capturing = True
                        continue
                    # elif (f"<{self.equipment_name}>") in line and capturing:
                    elif ("display") in line and capturing:
                        capturing = False
                        break
                    elif capturing and search in line and ('Eth-Trunk' in line or 'GigabitEthernet' in line or 'GE' in line) and 'VE1/0' not in line and '100GE' not in line:
                        dump_list.append(line)
                        
                        # Get the Trunk
                        if trunk is None:
                            interface = re.split(r'\s{3,}', line)[0]

                            if len(interface.split('.')) > 1:
                                trunk = interface.split('.')[0]
                            else:
                                trunk = interface

                            if '(10G)' in trunk:
                                trunk = trunk.replace("(10G)", "")
            
                # Get the other VLAN based on its existing trunk
                if search in self.list_exception:
                    return dump_list

                if dump_list:                      
                    # get the vlans already capture
                    captured_vlan_list = []
                    for row in dump_list:
                        captured_vlan = re.split(r'\s{3,}', row)[0].split('.')

                        if len(captured_vlan) > 1:
                            captured_vlan_list.append(captured_vlan[1])

                    # get the VLANs not cpatured from the first loop
                    capturing = False
                    with open(self.file_path, 'rt') as data:
                        for line in data:
                            if command in line:  
                                capturing = True
                                continue
                            elif ("display") in line and capturing:
                                capturing = False
                                break
                            if capturing and (f'{trunk}.' in line):
                                vlan = re.split(r'\s{3,}', line)[0].split('.')
                                if len(vlan) > 1:
                                    if vlan[1] not in captured_vlan_list:
                                        dump_list.append(line)                                 

            return dump_list  
        
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")


    def get_trunk(self, node_name, vlan_list):
        trunk_array = []
        vlan_dump = []
        sip , hsi = [] , []
        ag_homing_list = []
        om, ipoe, h248, rtp = '-', '-', '-', '-'
        ag1, ag2 = '-', '-'
        vcid_dict = {}
    
        if (vlan_list): # if vlan_list has data
            for row in vlan_list:
                vlan = row[6]
                desc = row[5]
                trunk = row[2].split('.')[0]
                area = row[0]

                if "IPOE" in desc.upper():
                    if int(vlan) >= 400 and int(vlan) < 410 and not(ipoe == "400"):
                        ipoe = str(vlan)
                elif "SIP" in desc.upper() or "VOICE" in desc.upper():
                    sip.append(vlan)
                elif "H248" in desc.upper():
                    h248 = vlan
                elif "RTP" in desc.upper():
                    rtp = vlan
                elif " OM" in desc.upper() or "-OM" in desc.upper() or "OM-" in desc.upper() or "OM_" in desc.upper():
                    om = vlan
                elif "HSI" in desc.upper() or "DATA" in desc.upper() or "HIS" in desc.upper():
                    hsi.append(vlan)

            # Get AG Homing and vcids
            # vlan_dump += [om,sip,hsi]
            vlan_dump = {
                "om": [om],
                "sip": sip,
                "hsi": hsi,
            }

            for key, value in vlan_dump.items():
                # vlan_dump_list = self.to_list(value)
                vlan_dump_list = value
                vcids_dump = []

                # --- loop every vlan stored per services
                for vlan in vlan_dump_list:
                    try:
                        if("GE" in trunk):
                            trunk = trunk.replace('GE','GigabitEthernet')

                        # --- get the configured parameters (AG homing details, VCID and IP)
                        data_retrieved = self.get_ag_from(f"interface {trunk}.{vlan}","mpls")

                        # ---- get AG homing
                        if not ag_homing_list:                      
                            ag_homing_list = data_retrieved['ag_homing_list']
        
                            if len(ag_homing_list)>1:
                                ag1 = ag_homing_list[0][0]
                                ag2 = ag_homing_list[1][0]
                            elif len(ag_homing_list) == 1:
                                ag1 = ag_homing_list[0][0]

                        # ----  get the VCID per vlan
                        vcid_list = data_retrieved['vcid_list']

                        if len(vlan_dump_list) > 1:
                            if len(vcid_list)>1:
                                vcids_dump.append(f'{vlan}: {vcid_list[0][1]}|{vcid_list[1][1]}')
                            elif len(vcid_list) == 1:
                                vcids_dump.append(f'{vlan}: {vcid_list[0][1]}')
                        else:
                            if len(vcid_list)>1:
                                vcids_dump.append(f'{vcid_list[0][1]}|{vcid_list[1][1]}')
                            elif len(vcid_list) == 1:
                                vcids_dump.append(f'{vcid_list[0][1]}')

                    except Exception as e:
                        error_message = f"Error on the AG: {node_name} at {self.equipment_name}\t"
                        error_message += f"{ag_homing_list}\n"
                        if error_message not in self.errors:
                            self.log_error(f"An error occurred: {e} -- {error_message}")
                            self.errors.add(error_message)

                            error_log = open("error_logs.log", "a")
                            error_log.write(f"An error occurred: {e} -- {error_message}\n")
                            error_log.close()

                
                if not vcids_dump:
                    vcids_dump.append('-')

                vcid_dict[f'{key}_vcid'] = vcids_dump
                
            # ----- Get IPOE IP
            auth_ip = '-'
            unauth_ip = '-'          
            try:
                ipoe_ip = self.get_ipoe_ip(f"interface {trunk}.{ipoe}","ip address")
                auth_ip = self.subnet_mask_to_subnet(ipoe_ip[0]) 
                unauth_ip = self.subnet_mask_to_subnet(ipoe_ip[1])
            except Exception as e:             
                error_message = f"Error on the IPOE IP: {node_name} at {self.equipment_name} - IPOE VLAN interface {trunk}.{ipoe}\t"
                self.log_error(f"An error occurred: {e} -- {error_message}")

                error_log = open("error_logs.log", "a")
                error_log.write(f"An error occurred: {e} -- {error_message}\n")
                error_log.close()
                # print(f"An error occurred: {e} -- {error_message}")

            # Put all data to array
            trunk_array += [area,node_name,self.equipment_name,trunk,om,sip,hsi,ipoe,h248,rtp,ag1,ag2,auth_ip,unauth_ip,vcid_dict['om_vcid'],vcid_dict['sip_vcid'],vcid_dict['hsi_vcid']]
            
            
            return trunk_array

    def get_ipoe_ip(self,command,search):
        # ----- Get Description and Port
        ag_homing_list = []
        capturing = False #True if the script will start to capture the line
        try:
            with open(self.file_path, 'rt') as data:
                for line in data:
                    if command in line:  
                        capturing = True
                        continue
                    elif '#\n' in line and capturing:
                        capturing = False
                        break
                    elif capturing and search in line:
                            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                            ag_homing = re.findall(ip_pattern, line)
                            ag_homing_list.append(ag_homing)
            return ag_homing_list
        
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")


    def get_ag_from(self,command,search):
        # ----- Get Description and Port
        ag_homing_list = []
        vcid_list = []
        capturing = False #True if the script will start to capture the line
        
        try:
            with open(self.file_path, 'rt') as data:
                for line in data:
                    if command in line:  
                        capturing = True
                        continue
                    # elif (f"<{self.equipment_name}>") in line and capturing:
                    elif '#\n' in line and capturing:
                        capturing = False
                        break
                    elif capturing and search in line:
                            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                            ag_homing = re.findall(ip_pattern, line)
                            ag_homing_list.append(ag_homing)

                            # vcid_pattern = r'(?<=\s)\d+$'
                            vcid_pattern = r'\b\d+\b(?!\S)'
                            vcid = re.findall(vcid_pattern, line)
                            vcid_list.append(vcid)

                            
            parsed_data = {
                "ag_homing_list": ag_homing_list,
                "vcid_list": vcid_list
            }
             
            # return ag_homing_list
            return parsed_data

        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")

    def get_ports_trunk(self,trunk_list):
        
        trunk = trunk_list[3]
        command = "display interface brief"
        get_port = False
        capturing = False 
        trunk_ports = []
        try:
            with open(self.file_path, 'rt') as data:
                for line in data:
                    if command in line:  
                        capturing = True
                        continue
                    # elif (f"<{self.equipment_name}>") in line and capturing:
                    elif ("display") in line and capturing:
                        capturing = False
                        break
                    elif capturing and (trunk in line) and (not get_port) and (len(trunk_ports) == 0):
                        get_port = True
                    elif capturing and (trunk in line) and (get_port) and (len(trunk_ports) > 0):
                        get_port = False
                    elif get_port:
                        trunk_ports.append(line.split()[0])
                        
                new_trunk_name = f"{trunk}||{'|'.join(trunk_ports)}".replace("GigabitEthernet", "GE")

            return new_trunk_name
        
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")   
    
    def combine_similar(self,data_set):
        result_dict = {}

        for row in data_set:
            node_name = row[1]
            an_name = row[2]
            trunk = row[3]
            
            if node_name not in result_dict:
                result_dict[node_name] = row
                
            else:
                # check if there is a duplicate file (both .log and .txt but same name)
                if an_name == result_dict[node_name][2]: # pwede rani wala if walay duplicate na file (.log and .txt)
                    
                    if "GE" in trunk:
                        result_dict[node_name][3] = trunk
                    else:
                        continue 
                else:
                    if 'AGG' in result_dict[node_name][2] and 'AGG' not in an_name:
                        # if an_name1(exsiting in array) has AGG and an_name2 does not, consider the an_name1 as erratic 
                        # delete an_name1 then add the new with correct AN name
                        result_dict.pop(node_name)
                        result_dict[node_name] = row

                    elif 'AGG' not in result_dict[node_name][2] and 'AGG' in an_name:
                        # if an_name1(exsiting in array) does not have AGG and an_name2 has, consider the an_name2 as erratic 
                        # do nothing,
                        pass

                    else:
                        result_dict[node_name][2] += ' & ' + an_name
                        result_dict[node_name][3] += ' & ' + trunk

        # Convert the dictionary values to a list
        result_list = list(result_dict.values())
        
        return result_list
    

    def to_list(self,lst):
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(self.to_list(item))
            else:
                result.append(item)
        return result
    




    