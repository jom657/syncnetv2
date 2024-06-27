import pandas as pd
import os
from Class import An, Agg
import logging


# shared_log_file = open("error_log.txt", "w")
# folder_path = r"D:\1Python Script\2024\SyncNet\Jom\Test Lab"
# self.script_directory = os.path.dirname(__file__)


class Main():
    def __init__(self,root,text_update,folder_path):
        self.logger = logging.getLogger()
        self.root = root
        self.text_update = text_update

        self.folder_path = folder_path
        self.script_directory = os.path.dirname(__file__)
        print(self.script_directory)

        logs = ['error_logs.log','shutdown_node.log']
        for log in logs:
            try:
                log_file_path = os.path.join(self.script_directory, log)
                os.remove(log_file_path)
            except FileNotFoundError:
                print(f"The file {log_file_path} does not exist.")
            except Exception as e:
                print(f"An error occurred: {e}")


# ---------------------------- AN ---------------------------------
    def get_details_from_an(self):
        db_folder_path = os.path.join(self.script_directory, 'Reference\WLN DB v2.csv')
        df_raw = pd.read_csv(db_folder_path, index_col=False, dtype='unicode')

        # an_folder_path = os.path.join(self.folder_path, 'Test AN')
        an_folder_path = self.folder_path

        self.df_raw = df_raw.dropna(how='all')
        # df_nodes = df_raw[['DE NIRO NAMING NMS NAME (NE NAME)','LOOP NAME','REGION']].values.tolist()
        df_nodes = df_raw[['DE NIRO NAMING NMS NAME (NE NAME)','LOOP NAME','REGION']]

        root_folder = os.walk(an_folder_path)
        trunk_list = []

        is_first_loop = True
        new_an_folder_path = an_folder_path
        for foldername, subfolders, filenames in root_folder:
            
            folder_name = os.path.basename(foldername)

            # check if only specific region is selected or whole folder
            if not trunk_list and is_first_loop:
                if subfolders:  
                    is_first_loop = False
            
            if not is_first_loop:
                new_an_folder_path = os.path.join(an_folder_path, folder_name)
            
            
            df_nodes_filtered = df_nodes[df_nodes['REGION'] == folder_name]
            
            if folder_name == 'AGG':
                continue

            # if empty, proceed to next loop
            if df_nodes_filtered.empty:
                continue

            self.log_value(f'------------- Initializing {folder_name} files -------------')
            self.root.update_idletasks()

            # loop within sub folder
            counter = 1
            for file_name in filenames:
                # Get only .txt or .log file
                load_an_file = An(file_name,new_an_folder_path)
                if (file_name.endswith('.txt') or file_name.endswith('.log')):

                    # --- update GUI
                    self.log_value(f'- Processing raw data at {(file_name)}')
                    self.text_update.set(f'{folder_name} - {counter}/{len(filenames)} ({int((counter/len(filenames))*100)}%)')
                    counter += 1
                    self.root.update_idletasks()

                    for row in df_nodes_filtered.values.tolist():
                        node_name = row[0]
                        area = row[2]
                        trunks = []
                        
                        dump_list = load_an_file.get_data_list_from("display interface description",node_name)
                        if dump_list:
                            vlan_list = load_an_file.vlan_array(dump_list,area)
                            trunks = load_an_file.get_trunk(node_name,vlan_list)
                        if trunks:
                            # get the ports per trunk if Eth-Trunk is present
                            if "Trunk" in trunks[3]:
                                new_trunk_name = load_an_file.get_ports_trunk(trunks)
                                trunks[3] = new_trunk_name

                            trunk_list.append(trunks) 

        if trunk_list:
            # combine similar Node Name
            trunk_list_final = load_an_file.combine_similar(trunk_list)   

            # -------- Merge file, Data the needs to be updated ------
            # df_final_merge = self.get_to_update(trunk_list_final,df_raw)
            # df_final_merge = df_final_merge[['Region','Node Name', 'Uplink','Uplink_NMS', 'Trunk','Trunk_NMS', 'OM','OM_NMS', 'SIP','SIP_NMS', 'HSI','HSI_NMS', 'IPOE','IPOE_NMS', 'SIGNALING','SIGNALING_NMS','MEDIA', 'MEDIA_NMS']]

            # ------- NMS Extraction only
            df_an_trunks = pd.DataFrame(trunk_list_final, columns=['Region','Node Name','Uplink','Trunk', 'OM', 'SIP', 'HSI', 'IPOE', 'H248', 'RTP', 'AG1', 'AG2','Auth IP', 'UnAuth IP', 'OM VCID', 'SIP VCID', 'HSI VCID'])
            df_an_trunks['SIP'] = df_an_trunks['SIP'].apply(lambda x: '\n'.join(map(str, x)))
            df_an_trunks['HSI'] = df_an_trunks['HSI'].apply(lambda x: '\n'.join(map(str, x)))  
            df_an_trunks['OM VCID'] = df_an_trunks['OM VCID'].apply(lambda x: '\n'.join(map(str, x)))
            df_an_trunks['SIP VCID'] = df_an_trunks['SIP VCID'].apply(lambda x: '\n'.join(map(str, x))) 
            df_an_trunks['HSI VCID'] = df_an_trunks['HSI VCID'].apply(lambda x: '\n'.join(map(str, x)))              

            # print(df_final_merge)
            # df_final_merge.to_csv('Merged.csv', encoding='utf-8', index=False)
            # df_an_trunks.to_csv('NMS extract.csv', encoding='utf-8', index=False)
            return df_an_trunks

    # ------------------------------------------------------------------
        

    # ---------------------------- AGG ---------------------------------
    #  -------- HSI -------
    def get_details_from_agg_hsi(self,current_folder):

        try:
            if current_folder == 'AGG':
                agg_folder_path = self.folder_path
            else:
                agg_folder_path = os.path.join(self.folder_path, 'AGG')
        
            db_folder_path = os.path.join(self.script_directory, 'Reference\AGG BNG Port.csv')
            df_agg_hsi_raw = pd.read_csv(db_folder_path, index_col=False)

            files = os.listdir(agg_folder_path)
        except Exception as e:
            self.log_value(f'- {e} Error: No AG folder found')
            self.root.update_idletasks()
            return

        df_agg_hsi_raw = df_agg_hsi_raw.dropna(how='all')
        df_agg_hsi = df_agg_hsi_raw[['AGG HOMING','PORT','AREA','BNG HOMING', 'BNG PORT']].values.tolist()

        hsi_array_final = pd.DataFrame()

        self.log_value('------------- Initializing HSI AGG files -------------')
        self.root.update_idletasks()

        counter = 1
        for file_name in files:
            # Get only .txt or .log file
            if ((file_name.endswith('.txt') or file_name.endswith('.log'))) and 'AGG' in file_name:

                # --- update GUI
                self.log_value(f'- Processing raw data at {(file_name)}')
                self.text_update.set(f'AGG - {counter}/{len(files)} ({int((counter/len(files))*100)}%)')
                counter += 1
                self.root.update_idletasks()
                
                for row in df_agg_hsi:
                    dump_list = []
                    agg_name = row[0]
                    agg_port =row[1]
                    agg_area =row[2]
                    agg_bng = row[3]
                    agg_bng_port = row[4]

                    if agg_name in file_name:
                        load_agg_file = Agg(file_name,agg_folder_path)

                        bng_homing = [agg_bng,agg_bng_port]
                        dump_list = load_agg_file.get_data_list_from("display interface description",agg_port)
                        vlan_hsi = load_agg_file.vlan_array(dump_list,agg_area)

                        # vlan_hsi_bng = [sublist + bng_homing for sublist in vlan_hsi]
                        # get the raw data from the start of the command
                        raw_data = load_agg_file.get_data_from('display current-configuration')
                        # get vsi and append BNG homing and port
                        vlan_hsi_bng = load_agg_file.get_vsi(raw_data,vlan_hsi,bng_homing)

                        if vlan_hsi:
                            new_df = pd.DataFrame(vlan_hsi_bng, columns=['Region','HSI AGG','HSI Interface', 'StatusPhysical', 'StatusProtocol', 'Description', 'HSI VLAN','BNG', 'BNG Port','HSI VSI'])
                            hsi_array_final = pd.concat([hsi_array_final, new_df], ignore_index=True)

        # hsi_array_final.to_csv('HSI.csv', encoding='utf-8', index=False)
        return hsi_array_final
        


    # -------- SIP --------
    def get_details_from_agg_sip(self,current_folder):
        try:
            if current_folder == 'AGG':
                agg_folder_path = self.folder_path
            else:
                agg_folder_path = os.path.join(self.folder_path, 'AGG')
        
            db_folder_path = os.path.join(self.script_directory, 'Reference\VOICE Port.csv')
            df_agg_sip_raw = pd.read_csv(db_folder_path, index_col=False)  

            files = os.listdir(agg_folder_path)
        except Exception as e:
            self.log_value(f'- {e} Error: No AG folder found')
            self.root.update_idletasks()
            return

        df_agg_sip_raw = df_agg_sip_raw.dropna(how='all')
        df_agg_sip = df_agg_sip_raw[['AG HOMING','PORT 1', 'PORT 2','AREA',]].values.tolist()

        sip_array_final = pd.DataFrame()

        self.log_value('------------- Initializing SIP AGG files -------------')
        self.root.update_idletasks()

        counter = 1
        for file_name in files:
            # Get only .txt or .log file
            if ((file_name.endswith('.txt') or file_name.endswith('.log'))) and 'AGG' in file_name:

                # --- update GUI
                self.log_value(f'- Processing raw data at {(file_name)}')
                self.text_update.set(f'AGG - {counter}/{len(files)} ({int((counter/len(files))*100)}%)')
                counter += 1
                self.root.update_idletasks()

                for row in df_agg_sip:
                    dump_list = []
                    agg_name = row[0]
                    agg_port1=row[1]
                    # agg_port2=row[2]
                    agg_area =row[3]

                    if agg_name in file_name:
                        load_agg_file = Agg(file_name,agg_folder_path)

                        agg_port1 = agg_port1.replace('Virtual-Ethernet', 'VE')
                        dump_list = load_agg_file.get_data_list_from("display interface description",agg_port1)
                        vlan_sip = load_agg_file.vlan_array(dump_list,agg_area)
                        raw_data = load_agg_file.get_data_from('display current-configuration')
                        # get vsi and append BNG homing and port
                        vlan_sip_agg = load_agg_file.get_vsi(raw_data,vlan_sip,'')
                        if vlan_sip:
                            new_df = pd.DataFrame(vlan_sip_agg, columns=['Region','SIP AGG','SIP Interface', 'StatusPhysical', 'StatusProtocol', 'Description', 'SIP VLAN','SIP VSI', 'SIP IP'])
                            sip_array_final = pd.concat([sip_array_final, new_df], ignore_index=True)

        # print(sip_array_final)
        # sip_array_final.to_csv('SIP.csv', encoding='utf-8', index=False)
        return sip_array_final
    # ------------------------------------------------------------------
        

        
    def get_to_update(self,nms_raw,df_raw):
        self.log_value('------------- Merging Files -------------')
        self.root.update_idletasks()

        selected_columns = ['REGION','DE NIRO NAMING NMS NAME (NE NAME)', 'ATNTYP.ATN Type', 'ATNPORT.ATN Port' ,'OMVLAN.OM VLAN', 'VOICEVLAN.SIP VLAN\n(GEMPORT Mapping)', 'DATAVLAN.Data VLAN', 'DATAVLAN.IPOE VLAN',
                            'SIGVLAN.Signaling VLAN', 'MEDIAVLAN.Media VLAN','Authorize IP Pool','UnAuthorize IP Pool']
        df_wlndb = df_raw[selected_columns]

        # convert to array the column with new line in excel
        columns_with_newline = ['VOICEVLAN.SIP VLAN\n(GEMPORT Mapping)', 'DATAVLAN.Data VLAN',]
        for column in columns_with_newline:
            df_wlndb = df_wlndb.copy()
            
            # convert columns_with_newline Values to int then sort, then convert back to str
            # df_wlndb[column] = df_wlndb[column].apply(lambda x: sorted([int(val) for val in x.split('\n') if val.isdigit()]) if isinstance(x, str) else x)
            df_wlndb[column] = df_wlndb[column].apply(lambda x: sorted([int(val.strip()) for val in x.split('\n') if val.strip().isdigit()]) if isinstance(x, str) else x)
            df_wlndb[column] = df_wlndb[column].apply(lambda x: '\n'.join(map(str, x)) if isinstance(x, list) else x)

        # Change Column name of excel file
        new_column_names = {
            'REGION': 'Region',
            'DE NIRO NAMING NMS NAME (NE NAME)': 'Node Name',
            'ATNTYP.ATN Type': 'Uplink',
            'ATNPORT.ATN Port': 'Trunk',
            'OMVLAN.OM VLAN': 'OM',
            'VOICEVLAN.SIP VLAN\n(GEMPORT Mapping)': 'SIP',
            'DATAVLAN.Data VLAN': 'HSI',
            'DATAVLAN.IPOE VLAN': 'IPOE',
            'SIGVLAN.Signaling VLAN': 'SIGNALING',
            'MEDIAVLAN.Media VLAN': 'MEDIA',
            'Authorize IP Pool': 'Auth IP',
            'UnAuthorize IP Pool': 'UnAuth IP'
        }
        # Rename columns
        df_wlndb = df_wlndb.rename(columns=new_column_names)


        # convert NMS raw data to dataframe
        columns = ['Region','Node Name', 'Uplink', 'Trunk', 'OM', 'SIP', 'HSI', 'IPOE', 'SIGNALING', 'MEDIA', 'AG1', 'AG2','Auth IP', 'UnAuth IP']
        df_nms = pd.DataFrame(nms_raw, columns=columns)  # Use the same column names as df_wlndb
        df_nms = df_nms[['Region','Node Name', 'Uplink', 'Trunk', 'OM', 'SIP', 'HSI', 'IPOE','SIGNALING', 'MEDIA','Auth IP', 'UnAuth IP']]

        # convert the array to string and sort the vlans in the array
        df_wlndb = df_wlndb.applymap(lambda x: '\n'.join(sorted(map(str, x), key=str)) if isinstance(x, list) else x)
        df_nms = df_nms.applymap(lambda x: '\n'.join(sorted(map(str, x), key=str)) if isinstance(x, list) else x)

        # convert df_wlndb to str
        df_wlndb = df_wlndb.astype(str)

        # Merge based on "Node Name" column
        merged_df = pd.merge(df_wlndb, df_nms, on='Node Name', how='outer', suffixes=('', '_NMS'))     

        # Replace matching values with "N/A"
        merged_df['OM_NMS'] = merged_df['OM_NMS'].where(merged_df['OM'] != merged_df['OM_NMS'], 'N/A')
        merged_df['SIP_NMS'] = merged_df['SIP_NMS'].where(merged_df['SIP'] != merged_df['SIP_NMS'], 'N/A')
        merged_df['HSI_NMS'] = merged_df['HSI_NMS'].where(merged_df['HSI'] != merged_df['HSI_NMS'], 'N/A')
        merged_df['IPOE_NMS'] = merged_df['IPOE_NMS'].where(merged_df['IPOE'] != merged_df['IPOE_NMS'], 'N/A')
        merged_df['SIGNALING_NMS'] = merged_df['SIGNALING_NMS'].where(merged_df['SIGNALING'] != merged_df['SIGNALING_NMS'], 'N/A')
        merged_df['MEDIA_NMS'] = merged_df['MEDIA_NMS'].where(merged_df['MEDIA'] != merged_df['MEDIA_NMS'], 'N/A')
        merged_df['Auth IP_NMS'] = merged_df['Auth IP_NMS'].where(merged_df['Auth IP'] != merged_df['Auth IP_NMS'], 'N/A')
        merged_df['UnAuth IP_NMS'] = merged_df['UnAuth IP_NMS'].where(merged_df['UnAuth IP'] != merged_df['UnAuth IP_NMS'], 'N/A')


        # filter Rows with no difference or no data at all
        merged_df = merged_df.fillna("")
        condition = ((merged_df['OM_NMS'].isin(["N/A", "-",""])) & (merged_df['SIP_NMS'].isin(["N/A", "-",""])) & (merged_df['HSI_NMS'].isin(["N/A", "-",""])) & 
                     (merged_df['IPOE_NMS'].isin(["N/A", "-",""]))  & (merged_df['SIGNALING_NMS'].isin(["N/A", "-",""])) & (merged_df['MEDIA_NMS'].isin(["N/A", "-",""])) &
                     (merged_df['Auth IP_NMS'].isin(["N/A", "-",""])) & (merged_df['UnAuth IP_NMS'].isin(["N/A", "-",""])) )
        merged_df = merged_df[~condition]

        return(merged_df)


    def merge_agg_details(self,main_db_arr, agg_arr,service):
        self.log_value(f'------------- Integrating {service} Data to Main Database -------------')
        self.root.update_idletasks()
        self.text_update.set('Finalizing Files')

        df_main_db_arr = pd.DataFrame(main_db_arr)
        df_service_arr = pd.DataFrame(agg_arr)

        # remove duplicate
        df_service_arr = df_service_arr.drop_duplicates(subset=[f'{service} AGG',f'{service} VLAN'])

        # Convert the values of Multiple SIP vlan to array
        main_db_expanded = df_main_db_arr.assign(VLAN_REF=df_main_db_arr[f'{service}'].str.split('\n')).explode(f'{service}').reset_index(drop=True)

        # Split rows with multiple SIP VLANs into separate rows
        main_db_exploded = main_db_expanded.explode('VLAN_REF')

        # Merge dataframes based on 'Region' and 'VLAN'
        merged_df = pd.merge(main_db_exploded, df_service_arr, left_on=['Region','VLAN_REF'] , right_on=['Region',f'{service} VLAN'], how = 'left')
        merged_df = merged_df.fillna('-')

        # combine/merge rows with same VLAN and Node name
        column_names = main_db_arr.columns
        column_names = list(column_names)

        self.text_update.set('Completed')

        if service == 'SIP':
            combined_df = merged_df.groupby(column_names)[['SIP IP', 'SIP AGG', 'SIP Interface', 'SIP VSI']].agg(lambda x: '\n'.join(x)).reset_index()
            return combined_df

        elif service == 'HSI':
            combined_df = merged_df.groupby(column_names)[['HSI AGG', 'HSI Interface', 'BNG','BNG Port', 'HSI VSI']].agg(lambda x: '\n'.join(x)).reset_index()
            return combined_df


    def merge_sip_hsi(self,col,hsi,sip):
        self.log_value('------------- End Task -------------')
        self.root.update_idletasks()
        self.text_update.set('Completed')
        merged_df = pd.merge(hsi, sip, on=col, how='inner')
        return merged_df
    
    def log_value(self, value):
        self.logger.info(value)


# ----------------------------------------------------
def run(root,text_update,folder):
    # main = Main(root,text_update,r"D:\1Python Script\2024\SyncNet\Jom\Test Lab")
    hsi_data = pd.DataFrame()
    sip_data = pd.DataFrame()
    merged_hsi = pd.DataFrame()
    merged_sip = pd.DataFrame()
    an_data = pd.DataFrame()

    main = Main(root,text_update,folder)
    an_data = main.get_details_from_an()

    # convert to array the column with new line in excel
    columns_with_newline = ['SIP', 'HSI',]
    an_data = an_data.copy()
    for column in columns_with_newline:
        # convert columns_with_newline Values to int then sort, then convert back to str
        an_data[column] = an_data[column].apply(lambda x: sorted([int(val) for val in x.split('\n') if val.isdigit()]) if isinstance(x, str) else x)
        an_data[column] = an_data[column].apply(lambda x: '\n'.join(map(str, x)) if isinstance(x, list) else x)

    print(an_data)

    subfolders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder,f))]
    current_folder = os.path.basename(folder)

    if 'AGG' in subfolders or current_folder == 'AGG':
        hsi_data = main.get_details_from_agg_hsi(current_folder)
        hsi_data.to_csv('hsi_homing.csv', encoding='utf-8', index=False)
        # print(hsi_data)

        sip_data = main.get_details_from_agg_sip(current_folder)
        sip_data.to_csv('sip_homing.csv', encoding='utf-8', index=False)
        # print(sip_data)

    if not an_data.empty:
        if not hsi_data.empty:
            merged_hsi = main.merge_agg_details(an_data, hsi_data,'HSI')
            # merged_hsi.to_csv('final_hsi.csv', encoding='utf-8', index=False)
            

        if not sip_data.empty:
            merged_sip = main.merge_agg_details(an_data, sip_data,'SIP')
            # merged_sip.to_csv('final_sip.csv', encoding='utf-8', index=False)
            

        if not merged_hsi.empty and not merged_sip.empty:
            col = an_data.columns
            col = list(col)

            final_output = main.merge_sip_hsi(col,merged_hsi,merged_sip)
            final_output.to_csv('final_output.csv', encoding='utf-8', index=False)
            print(final_output)
        else:
            an_data.to_csv('an_extraction.csv', encoding='utf-8', index=False)

        # get the duplicates of Uplink AN and Trunks
        an_data_duplicates = an_data[an_data.duplicated(subset=['Uplink','Trunk'])]
        an_data_duplicates.to_csv('Duplicate Uplink.csv', encoding='utf-8', index=False)


        # --------- Get the Output that needs to be updated by region
        # an_data = pd.read_csv('final_output - Copy.csv', index_col=False, dtype='unicode')

        df_final_merge = main.get_to_update(an_data,main.df_raw)
        df_final_merge = df_final_merge[['Region','Node Name', 'Uplink','Uplink_NMS', 'Trunk','Trunk_NMS', 'OM','OM_NMS', 'SIP','SIP_NMS', 'HSI','HSI_NMS', 'IPOE','IPOE_NMS', 'SIGNALING','SIGNALING_NMS','MEDIA', 'MEDIA_NMS','Auth IP','Auth IP_NMS', 'UnAuth IP','UnAuth IP_NMS']]
        print(df_final_merge)
        df_final_merge.to_csv('Merged File.csv', encoding='utf-8', index=False)


   


