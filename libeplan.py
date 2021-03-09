# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 14:07:53 2015

@author: ufilippi, ggaregnani

EnergyPLAN input utility routines
"""

import os
from os import listdir
from os.path import isfile, join
import numpy as np
import pandas
import subprocess
from collections import OrderedDict
import os.path
import time
#from libfun import load_json
# from constants import HOURS_IN_LEAP_YEAR

def is_float_try(str):
    try:
        float(str)
        return True
    except ValueError:
        return False

def input2outputRES(inputRES):
    """
    read the json with the rules for the conversion
    from the input file name of RES into the output name
    and return the output name.
    >>> input2outputRES(['Photo Voltaic'])
    [u'PV']
    """
    # in2out = load_json('input2outputRES.json')
    in2out ={
        "Wind": "Wind",
        "Offshore Wind": "Offshore",
        "Photo Voltaic": "PV",
        "Wave Power": "Wave",
        "River Hydro": "River",
        "Tidal": "Tidal",
        "CSP Solar Power": "CSP"}

    outRES = []
    for inp in inputRES:
        for k in in2out.keys():
            if inp == k:
                outRES.append(in2out[k])
    return outRES


class Node(object):
    # of each node I have input values and input ditribution
    def __init__(self, inputfile, eplanfolder,
                 resultsfile=None, data=None, distributions=None,
                 ):

        #TODO: check that the distribution is an object Distribution

        self.inputfile = inputfile
        self.eplanfolder = eplanfolder
        self.resultsfile = resultsfile
        if data is None:
            self.data = self.get_data()
        else:
            self.data = data
        #TODO: data is an order dictionary, to check

        self.distributions = distributions

    def get_data(self):
        #FIXME: fix order dictionary for 3.3
        with open(self.inputfile, 'r') as f:

            # NOTE: make sure input files are ANSI. Input files found in
            # EnergyPLAN folder may be UCS-2 Little Endian.

            data = f.readlines()

            # remove newline character '\n'
            data = [row[:-1] for row in data]
        #import ipdb; ipdb.set_trace()
        od = OrderedDict()
        #print data
        od['Node name'] = self.inputfile  # first key is node name
        for k in np.arange(0, len(data), 2):  # even rows contain keys
            val = data[k + 1]
            # convert val into float/int
            try:
                val = float(val)
                if val.is_integer():
                    val = int(val)
            except:
                pass
            od[data[k].strip('=')] = val

        # remove 'xxx' key, if present
        if 'xxx' in od:
            del od['xxx']

        self.data = od
        return self.data

    def write_input(self):
        """lod --- list of ordered dictionaries with the inputs to write,
        one for each node"""

        od = self.data
        odi = od.items()
        with open(self.inputfile, 'w') as f:
            # 'EnergyPLAN version' is without ending '=', all following inputs
            # are (except for the 'xxx' lines)
            f.write(list(odi)[1][0] + '\n')
            f.write(str(list(odi)[1][1]) + '\n')
            for j in range(2, len(list(odi))):
                f.write(list(odi)[j][0] + '=\n')
                f.write(str(list(odi)[j][1]) + '\n')

                # NOTE: EnergyPLAN seems to ignore present or missing final
                # 'xxx' lines; therefore, we don't add them

    #FIXME: method to excute the node, EPLANFOLDER is it GLOBAL or not
    def excute(self):
        subprocess.call([os.path.join(self.eplanfolder,
                        'energyplan.exe'), '-i',
                         self.inputfile, '-ascii', self.resultsfile])

    def get_distributions(self):
        dfolder = os.path.join(self.eplanfolder,
                               r'energyPlan Data\Distributions')
        # list of the distribution in the eplanfolder
        l_txt = [f for f in self.data.values() if (isinstance(f, str) and
                 f.endswith('txt'))]
        onlyfiles = [f for f in listdir(dfolder) if isfile(join(dfolder, f))]
        l_distr = list(set(l_txt) & set(onlyfiles))
        self.distributions = Distributions(l_distr, self.eplanfolder)
        return self.distributions
        
    def read_annual_indicator(self):
        """read the output file of energyPLAN and return a dictionary
        with the main annual indicators"""
        while not os.path.exists(self.resultsfile):
            time.sleep(1)

        if os.path.isfile(self.resultsfile):
            raw_file = open(self.resultsfile)
            complete = raw_file.read()
            list_file = complete.split("\n")
            y_ind = load_json("out_dict.json")
#            keys = ('SHARE OF RES (incl. Biomass)',
#                    'ANNUAL CO2 EMISSIONS (kt)',
#                    'ANNUAL FUEL CONSUMPTIONS (GWh/year)')
            for k in y_ind.keys():
                if k in 'ANNUAL COSTS (1000 EUR)':
                    for i in y_ind[k].keys():
                        if i in 'TOTAL':
                            ind = 1
                        else:
                            ind = 2
                        for j in y_ind[k][i].keys():
                            val = [s for s in list_file[3:]
                                   if j in s][0].split('\00')[ind]
                            y_ind[k][i][j] = val
                else:
                    for i in y_ind[k].keys():
                        val = [s for s in list_file[3:]
                               if i in s][0].split('\00')[1]
                        y_ind[k][i] = val
            return y_ind
        else:
            raise ValueError("%s isn't a file!" % self.resultsfile)
        
    def read_annual_GWh(self):
        """ read energy demand and production from energyPLAN output file
        """
        while not os.path.exists(self.resultsfile):
            time.sleep(1)

        if os.path.isfile(self.resultsfile):
            raw_file = open(self.resultsfile)
            complete = raw_file.read()
            list_file = complete.split("\n")
            name = list_file[80].split('\x00')[1:]
            field = list_file[81].split('\x00')[1:]
            values = list_file[84].split('\x00')[1:]
            keys = zip(name, field)
            annual_GWh = {}
            for k, v in zip(keys, values):
                k = tuple([i.strip() for i in k])
                try:
                    val = float(v)
                except:
                    val = v
                annual_GWh[k] = val
            return annual_GWh

    def get_annual_GWh(self, inputRES):
        """ given a list with the RES source in the input file, return
        the GWh production
        :param inputRES: list of RES
        :type: list
        """
        annual_GWh = self.read_annual_GWh()
        outRES = input2outputRES(inputRES)
        out_RES_val = []
        for out in outRES:
            for k in annual_GWh.keys():
                if out.strip() == k[0].strip() and k[1].strip() == 'Electr.':
                    # This is done only for the electrical sources
                    out_RES_val.append(annual_GWh[k])
        return out_RES_val
        
    def read_output_y(self):
        # unit_CO2=float(list_file[16][38:46])
        # unit_Costs=float(list_file[16][38:46])
        raw_file=open(self.resultsfile)
        complete =raw_file.read()
        list_file= complete.split("\n")
        co2_emission =float(list_file[16][40:48])# float(list_file[16][38:46])
        total_annual_costs= float(list_file[67][40:48])#float(list_file[67][38:46])
        res_share_pes = float(list_file[20][40:46])
        res_share_el_prod = float(list_file[21][40:46])
        # res_share_el_prod = float(list_file[21][38:46])
        #export = float(list_file[86][745:753])
#         El_demand = float(list_file[84][16:24])
#         NG_consumption= float(list_file[32][38:46])
#         #adding point for Italy
#         El_demand_cooling = float(list_file[84][25:33])
# #        El_demand_transport = float(list_file[84][412:420])
#         El_demand_HH_EB = float(list_file[84][637:645])
#         El_imp_exp = float(list_file[84][34:42])
        
#         CHP_el = float(list_file[84][439:447])
#         CHP_waste = float(list_file[84][430:438])
#         Wind = float(list_file[84][52:60])
#         Geo = float(list_file[84][475:483])
#         PV = float(list_file[84][70:78])
#         River_Hydro = float(list_file[84][79:87])
#         Hydro = float(list_file[84][115:123])
#         Biogas_PP = float(list_file[84][448:456])
#         Tidal= float(list_file[84][88:96])
#         CSP=float(list_file[84][97:105])
# #        Tidal= float(list_file[84][88:96])
#         #
#         PP2 = float(list_file[84][457:465])
#         CHP2 = float(list_file[84][241:249])
#         HPs_DH = float(list_file[84][250:258])
# #        HPs_HH_el = float(list_file[84][250:258])
#         import_payment = float(list_file[84][817:825])
#         export_payment = float(list_file[84][826:834])
#         RES_share_of_PES = float(list_file[20][38:46])
#         DH_demand = float(list_file[84][43:51])
#         imp=float(list_file[84][736:744])
#         expor=float(list_file[84][745:753])
#         S_th=float(list_file[84][700:708])
#         BoilerDH=float(list_file[84][259:267])
#         el_demand_Hp_ind = float(list_file[84][619:627])
#         el_demand_Hp_DH = float(list_file[84][421:429])
#         el_demand_electric_Boiler = float(list_file[84][637:645])
#         el_demand_cooling = float(list_file[84][25:33])
#         el_demand_transport= float(list_file[84][412:420])
#         el_demand_transportPTGrid= float(list_file[84][556:564])
#         el_demand_PtG= float(list_file[84][601:609])
               
#         oiltot = float(list_file[31][38:46]) #########
#         oilHH =float(list_file[31][47:55]) #########
#         NGtot =float(list_file[32][38:46]) #########
#         NGHH = float (list_file[32][47:55]) ########
#         wastetot = float (list_file[84][205:213]) #######  
#         #costs
#         # adding point for Italy
  
#         cost_Geo_Inv = float(list_file[25][121:129])
#         cost_Geo_MO = float(list_file[25][130:138])
#         cost_GeoH_Inv = float(list_file[57][121:129])
#         cost_GeoH_MO = float(list_file[57][130:138])
#         cost_CHP_Inv = float(list_file[8][121:129]) #CHP
#         cost_CHP_MO = float(list_file[8][130:138]) #CHP
#         cost_PP_Inv = float(list_file[15][121:129])
#         cost_PP_MO = float(list_file[15][130:138])
#         cost_Boil_Inv = float(list_file[14][121:129])
#         cost_Boil_MO = float(list_file[14][130:138])
#         cost_Bio_Dies_Inv = float(list_file[43][121:129])
#         cost_Bio_Dies_MO = float(list_file[43][130:138])
#         cost_Bio_Petr_Inv = float(list_file[44][121:129])
#         cost_Bio_Petr_MO = float(list_file[44][130:138])
#         cost_Bio_Fuels =  cost_Bio_Petr_MO + cost_Bio_Petr_Inv + cost_Bio_Dies_MO + cost_Bio_Dies_Inv
#         cost_Gas_Sto_Inv = float(list_file[53][121:129])
#         cost_Gas_Sto_MO = float(list_file[53][130:138])
#         cost_Oil_Sto_Inv = float(list_file[54][121:129])
#         cost_Oil_Sto_MO = float(list_file[54][130:138])
#         cost_Fuel_Sto = cost_Oil_Sto_MO+ cost_Oil_Sto_Inv + cost_Gas_Sto_MO + cost_Gas_Sto_Inv 
#         cost_Wind_Inv = float(list_file[16][121:129])
#         cost_Wind_MO = float(list_file[16][130:138])
#         cost_PV_Inv = float(list_file[18][121:129])
#         cost_PV_MO = float(list_file[18][130:138])
#         cost_RH_Inv = float(list_file[20][121:129])
#         cost_RH_MO = float(list_file[20][130:138])
#         cost_ST_Inv = float(list_file[35][121:129])
#         cost_ST_MO = float(list_file[35][130:138])
#         cost_STsto_Inv = float(list_file[13][121:129])
#         cost_STsto_MO = float(list_file[13][130:138]) 
#         cost_PVUS = float(list_file[19][121:129])+float(list_file[19][130:138])
# #        cost_PVUS_MO = float(list_file[19][130:138])
        
#         cost_Coal = float(list_file[40][58:66])        
#         cost_Oil = float(list_file[41][58:66])
#         cost_GasOil = float(list_file[42][58:66])
#         cost_Petrol = float(list_file[43][58:66])
#         cost_Biomass = float(list_file[45][58:66])
#         cost_Gas_Handling = float(list_file[44][58:66])
#         cost_NG = float(list_file[49][47:55])
#         cost_NG_marginal = float(list_file[51][47:55])
        
#         cost_Vehicle = float(list_file[12][161:169])
#         cost_Vehicle_OM = float(list_file[12][170:178])
#         cost_El_Grid = float(list_file[18][161:169])
#         cost_El_Grid_OM = float(list_file[18][170:178])
#         cost_Ind_Cooling = float(list_file[24][161:169])
#         cost_Ind_Cooling_OM = float(list_file[24][170:178])
#         cost_Ind_Boil = float(list_file[31][121:129]) #Ind boilers
#         cost_Ind_Boil_OM = float(list_file[31][130:138])  #Ind boilers
#         cost_El_Heating = float(list_file[34][121:129])
#         cost_El_Heating_OM = float(list_file[34][130:138])
#         cost_HPind_DH_Inv = float(list_file[33][121:129])
#         cost_HPind_DH_MO = float(list_file[33][130:138])
#         cost_STO_th_Inv = float(list_file[10][121:129])
#         cost_STO_th_MO = float(list_file[10][130:138])
#         cost_pump_STO_Inv = float(list_file[30][121:129])
#         cost_pump_STO_MO = float(list_file[30][130:138])
#         cost_pump_T_Inv = float(list_file[29][121:129])
#         cost_pump_T_MO = float(list_file[29][130:138])
#         cost_pump_P_Inv = float(list_file[28][121:129])
#         cost_pump_P_MO = float(list_file[28][130:138])
#         cost_pump = cost_pump_STO_Inv + cost_pump_STO_MO + cost_pump_T_Inv + cost_pump_T_MO + cost_pump_P_Inv + cost_pump_P_MO
#         cost_STO = cost_pump_STO_Inv + cost_pump_STO_MO
        
#         cost_PHS_p=float(list_file[23][121:129])+float(list_file[23][130:138])
#         cost_PHS_t=float(list_file[21][121:129])+float(list_file[21][130:138])
#         cost_PHS_STO=float(list_file[22][121:129])+float(list_file[22][130:138])
#         cost_PHS= cost_PHS_p+ cost_PHS_t+ cost_PHS_STO
        
#         cost_Hydro_Inv = float(list_file[21][121:129])
#         cost_Hydro_MO = float(list_file[21][130:138])
#         cost_Hydro = cost_Hydro_Inv + cost_Hydro_MO
#         Elec_Exchange = float(list_file[53][47:55])
#         cost_IndCHP_Inv = float(list_file[32][121:129]) #DHW
#         cost_IndCHP_MO = float(list_file[32][130:138]) #DHW
        
#         cost_Tidal_Inv = float(list_file[46][121:129]) 
#         cost_Tidal_MO = float(list_file[46][130:138]) 

#         cost_PtG_Inv = float(list_file[48][121:129]) 
#         cost_PtG_MO = float(list_file[48][130:138]) 

#         cost_WCHP_Inv = float(list_file[39][121:129]) 
#         cost_WCHP_MO = float(list_file[39][130:138])
                
#         cost_HP_DH_Inv = float(list_file[9][121:129])
#         cost_HP_DH_MO = float(list_file[9][130:138])
        
#         cost_CO2 = float(list_file[59][47:55])
        
#         cost_CSP = float(list_file[47][121:129])+ float(list_file[47][130:138])
      
        
        dict_out={'CO2-emission (total)': co2_emission, 'TOTAL ANNUAL COSTS': total_annual_costs, 'RES share of PES': res_share_pes, 'RES share of elec. prod.': res_share_el_prod}#, 'PP2': PP2, 'import payment': import_payment,
                  # 'export payment': export_payment, 'RES share of PES': RES_share_of_PES, 'El demand': El_demand, 'CHP2': CHP2, 'HPs DH': HPs_DH, 'DH demand': DH_demand,
                  # 'import el': imp, 'export el': expor, 'Solar_th': S_th, 'Boiler_DH': BoilerDH, 'el_demand_Hp_ind': el_demand_Hp_ind, 'el_demand_Hp_DH': el_demand_Hp_DH,
                  # 'CHP_el': CHP_el, 'CHP_waste': CHP_waste, 'PV': PV, 'River_Hydro': River_Hydro, 'Biogas_PP': Biogas_PP, 'NG_consumption':NG_consumption,
                  # 'cost_PV_Inv': cost_PV_Inv, 'cost_PV_MO': cost_PV_MO,
                  # 'cost_RH_Inv':cost_RH_Inv, 'cost_RH_MO':cost_RH_MO, 'cost_ST_Inv': cost_ST_Inv, 'cost_ST_MO': cost_ST_MO, 'cost_Oil': cost_Oil, 'cost_GasOil': cost_GasOil,
                  # 'cost_Biomass': cost_Biomass, 'cost_Gas_Handling': cost_Gas_Handling, 'cost_NG': cost_NG, 'cost_NG_marginal': cost_NG_marginal,
                  # 'cost_HP_DH_Inv': cost_HP_DH_Inv,'cost_HP_DH_MO': cost_HP_DH_MO,'cost_HPind_DH_Inv': cost_HPind_DH_Inv,'cost_HPind_DH_MO': cost_HPind_DH_MO,
                  # 'cost_STO_th_Inv': cost_STO_th_Inv,'cost_STO_th_MO': cost_STO_th_MO, 'cost_pump': cost_pump, 'cost_Hydro': cost_Hydro,
                  # 'el_demand_heating' : El_demand_HH_EB, 'Wind' : Wind, 'Geo' : Geo, 'Hydro' : Hydro, 'imp/exp':El_imp_exp,
                  # 'cost_inv_geo':cost_Geo_Inv, 'cost_mo_geo':cost_Geo_MO, 'cost_inv_chp':cost_CHP_Inv, 'cost_mo_chp':cost_CHP_MO, 'cost_inv_PP':cost_PP_Inv, 'cost_mo_PP':cost_PP_MO, 'cost_inv_boil':cost_Boil_Inv, 'cost_mo_boil':cost_Boil_MO,
                  # 'cost_biofuels':cost_Bio_Fuels, 'cost_fuel_sto':cost_Fuel_Sto, 'cost_inv_wind':cost_Wind_Inv, 'cost_mo_wind':cost_Wind_MO, 'cost_petrol': cost_Petrol, 'cost_coal': cost_Coal,
                  # 'cost_vehicle': cost_Vehicle, 'cost_vehicle_om': cost_Vehicle_OM, 'cost_el_grid': cost_El_Grid, 'cost_el_grid_om': cost_El_Grid_OM,'cost_ind_cooling': cost_Ind_Cooling, 'cost_ind_cooling_om': cost_Ind_Cooling_OM, 
                  # 'cost_ind_boil': cost_Ind_Boil, 'cost_ind_boil_om': cost_Ind_Boil_OM, 'cost_el_heating': cost_El_Heating, 'cost_el_heating_om': cost_El_Heating_OM, 'elec_exchange' : Elec_Exchange,
                  # 'cost_IndCHP_Inv':cost_IndCHP_Inv, 'cost_IndCHP_MO': cost_IndCHP_MO, 'cost_WCHP_Inv':cost_WCHP_Inv, 'cost_WCHP_MO': cost_WCHP_MO,
                  # 'cost_Tidal_Inv':cost_Tidal_Inv, 'cost_Tidal_MO': cost_Tidal_MO, 'cost_PtG_Inv': cost_PtG_Inv, 'cost_PtG_MO': cost_PtG_MO,
                  # 'cost_STO': cost_STO, 'cost_CO2': cost_CO2,
                  # 'oiltot': oiltot, 'oilHH': oilHH, 'NGtot': NGtot, 'NGHH': NGHH , 'wastetot': wastetot,
                  # 'el_demand_electric_Boiler':el_demand_electric_Boiler, 'el_demand_cooling':el_demand_cooling, 'el_demand_transport': el_demand_transport, 'el_demand_PtG': el_demand_PtG, 
                  # 'cost_PHS':cost_PHS, 'cost_CSP':cost_CSP, 'STsto_Inv':cost_STsto_Inv, 'STsto_OM':cost_STsto_MO, 'cost_GeoH_Inv':cost_GeoH_Inv, 'cost_GeoH_MO':cost_GeoH_MO,
                  # 'el_demand_transportPTGrid':el_demand_transportPTGrid, 'Tidal':Tidal, 'CSP':CSP, 'costs PV US': cost_PVUS} 
        return dict_out
    
    def read_indicators(self):
        # unit_CO2=float(list_file[16][38:46])
        # unit_Costs=float(list_file[16][38:46])
        raw_file=open(self.resultsfile)
        complete =raw_file.read()
        list_file= complete.split("\n")
        lista=[]
        for a in range(len(list_file)):
            # row=[]
            list_file2= list_file[a].split("\t")
            lista.append([x.strip() for x in list_file2 if x])
        # print(lista[16:26])
        
        indicators=lista[16:69]
        dic={}
        for a in range(len(indicators)):
            if len(indicators[a])>2:
                if is_float_try(indicators[a][1]):
                    key=indicators[a][0]
                    obj=float(indicators[a][1])
                    if key!='' and obj!='':
                        dic[key]=obj
        return dic
    
    def read_costs_tech(self):
        raw_file=open(self.resultsfile)
        complete =raw_file.read()
        list_file= complete.split("\n")
        lista=[]
        for a in range(len(list_file)):
            # row=[]
            list_file2= list_file[a].split("\t")
            lista.append([x.strip() for x in list_file2 if x])
        # print(lista[16:26])
         
        #costs of the technologies
        dic2={}
        list_var=['Solar thermal', 'Small CHP units', 'Heat Pump gr. 2', 'Heat Storage CHP', 
                  'Large CHP units', 'Heat Pump gr. 3', 'Heat Storage Solar', 'Boilers gr. 2 and 3',
                  'Large Power Plants', 'Wind', 'Wind offshore', 'Photo Voltaic', 'Wave power',
                  'River of hydro', 'Hydro Power', 'Hydro Storage', 'Hydro Pump', 'Nuclear',
                  'Geothermal Electr.', 'Electrolyser', 'Hydrogen Storage', 'Charge el1 storage', 
                  'Discharge el1 storage', 'El1 storage cap', 'Indv. boilers', 'Indv. CHP', 
                  'Indv. Heat Pump', 'Indv. Electric heat','Indv. Solar thermal', 'BioGas Upgrade' ,'Gasification Upgrade',
                  'DHP Boiler group 1', 'Waste CHP', 'Absorp. HP (Waste)', 'Biogas Plant', 
                  'Gasification Plant', 'BioDiesel Plant', 'BioPetrol Plant', 'BioJPPlant', 
                  'Tidal Power', 'CSP Solar Power', 'Carbon Recycling', 'Methanation' ,'Liquidation + JP',
                  'Desalination Plant', 'Water storage', 'Gas Storage', 'Oil Storage' ,'Methanol Storage',
                  'Interconnection', 'Geothermal Heat', 'Indust. Excess Heat', 'Indust. CHP Electr.',
                  'Indust. CHP Heat', 'Electr Boiler Gr 2+3', 'Bicycles' ,'Motorbikes', 'Electric Cars',
                  'Conventional Cars', 'DME Buses', 'Diesel Buses', 'DME Trucks', 'Diesel Trucks', 
                  'El1 storage cap']
        costs_tech=lista[7:73]
        # print( costs_tech)
        list_found=[]
        for a in range(len(costs_tech)):
            for b in range(len(list_var)):
                if list_var[b] in costs_tech[a] and list_var[b] not in list_found:
                    indexList=costs_tech[a].index(list_var[b])
                    key2=costs_tech[a][indexList]
                    dic_temp={}
                    value1=float(costs_tech[a][indexList+1])
                    value2=float(costs_tech[a][indexList+2])
                    value3=float(costs_tech[a][indexList+3])
                    dic_temp['Total Inv. Costs']=value1
                    dic_temp['Annual Inv. Costs']=value2
                    dic_temp['Fixed O&M']=value3
                    dic2[key2]=dic_temp
                    list_found.append(list_var[b])
                elif list_var[b] in costs_tech[a] and list_var[b] in list_found:
                    indexList=costs_tech[a].index(list_var[b])
                    key2=costs_tech[a][indexList]+' doublekey'
                    dic_temp={}
                    value1=float(costs_tech[a][indexList+1])
                    value2=float(costs_tech[a][indexList+2])
                    value3=float(costs_tech[a][indexList+3])
                    dic_temp['Total Inv. Costs']=value1
                    dic_temp['Annual Inv. Costs']=value2
                    dic_temp['Fixed O&M']=value3
                    dic2[key2]=dic_temp
                    list_found.append(key2)
                        
        return dic2
    
    def read_TWh(self):
        raw_file=open(self.resultsfile)
        complete =raw_file.read()
        list_file= complete.split("\n")
        lista=[]
        for a in range(len(list_file)):
            # row=[]
            list_file2= list_file[a].split("\t")
            lista.append([x.strip() for x in list_file2 if x])
        # print(lista[16:26])
         
        #costs of the technologies
        dic3={}
        TWh=lista[80:86]
        # print(TWh)
        list_found=[]
        # list_keys=[]
        # list_values=[]
        for a in range(len(TWh[0])):
            if is_float_try(TWh[4][a]):
                if TWh[1][a]=='':
                    if TWh[0][a]+''+TWh[1][a] not in list_found:
                        dic3[TWh[0][a]+''+TWh[1][a]]=float(TWh[4][a])
                        list_found.append(TWh[0][a]+''+TWh[1][a])
                    else:
                        dic3[TWh[0][a]+''+TWh[1][a]+' doublekey']=float(TWh[4][a])
                        list_found.append(TWh[0][a]+''+TWh[1][a]+' doublekey')
                else:
                    if TWh[0][a]+' '+TWh[1][a] not in list_found:
                        dic3[TWh[0][a]+' '+TWh[1][a]]=float(TWh[4][a])
                        list_found.append(TWh[0][a]+' '+TWh[1][a])
                    else:
                        dic3[TWh[0][a]+' '+TWh[1][a]+' doublekey']=float(TWh[4][a])
                        list_found.append(TWh[0][a]+' '+TWh[1][a]+' doublekey')                    
                # list_keys.append(TWh[0][a]+' '+TWh[1][a])
                # list_values.append(TWh[4][a])
    
        return dic3

    def read_All_outputs(self):
        # unit_CO2=float(list_file[16][38:46])
        # unit_Costs=float(list_file[16][38:46])
        raw_file=open(self.resultsfile)
        complete =raw_file.read()
        list_file= complete.split("\n")
        lista=[]
        for a in range(len(list_file)):
            # row=[]
            list_file2= list_file[a].split("\t")
            lista.append([x.strip() for x in list_file2 if x])
        # print(lista[16:26])
        
        indicators=lista[16:69]
        dic={}
        for a in range(len(indicators)):
            if len(indicators[a])>2:
                if is_float_try(indicators[a][1]):
                    key=indicators[a][0]
                    obj=float(indicators[a][1])
                    if key!='' and obj!='':
                        dic[key]=obj
                        
        TWh=lista[80:86]
        # print(TWh)
        list_found=[]
        # list_keys=[]
        # list_values=[]
        for a in range(len(TWh[0])):
            if is_float_try(TWh[4][a]):
                if TWh[1][a]=='':
                    if TWh[0][a]+''+TWh[1][a] not in list_found:
                        dic[TWh[0][a]+''+TWh[1][a]]=float(TWh[4][a])
                        list_found.append(TWh[0][a]+''+TWh[1][a])
                    else:
                        dic[TWh[0][a]+''+TWh[1][a]+' doublekey']=float(TWh[4][a])
                        list_found.append(TWh[0][a]+''+TWh[1][a]+' doublekey')
                else:
                    if TWh[0][a]+' '+TWh[1][a] not in list_found:
                        dic[TWh[0][a]+' '+TWh[1][a]]=float(TWh[4][a])
                        list_found.append(TWh[0][a]+' '+TWh[1][a])
                    else:
                        dic[TWh[0][a]+' '+TWh[1][a]+' doublekey']=float(TWh[4][a])
                        list_found.append(TWh[0][a]+' '+TWh[1][a]+' doublekey')                    
                # list_keys.append(TWh[0][a]+' '+TWh[1][a])
                # list_values.append(TWh[4][a])
        return dic
    
    def read_output_h(self):
        with open(self.resultsfile, 'r') as f:
            hours_in_leap_years = 8784
            output_col_names = ['Electr. Demand', 'Elec.dem Cooling', 'Fixed Exp/Imp',
                    'DH Demand', 'Wind Electr.', 'Wave Electr.', 'PV Electr.', 
                    'River Electr.', 'Tidal Electr.',  'CSP Electr.',
                    'Offshore Electr.', 'Hydro Electr.', 'Hydro pump',
                    'Hydro storage', 'Hydro Wat-Sup', 'Hydro Wat-Loss',
                    'Solar Heat', 'CSHP 1 Heat', 'Waste 1 Heat',
                    'Boiler 1 Heat', 'CSHP 2 Heat', 'Waste 2 Heat',
                    'Geoth 2 Heat', 'Geoth 2 Steam', 'Geoth 2 Storage',
                    'CHP 2 Heat', 'HP 2 Heat', 'Boiler 2 Heat', 'EH 2 Heat',
                    'ELT 2 Heat', 'Storage2 Heat', 'Balance2 Heat',
                    'CSHP 3 Heat', 'Waste 3 Heat', 'Geoth 3 Heat',
                    'Geoth 3 Steam', 'Geoth 3 Storage', 'CHP 3 Heat',
                    'HP 3 Heat', 'Boiler 3 Heat', 'EH 3 Heat', 'ELT 3 Heat',
                    'Storage3 Heat', 'Balance3 Heat', 'Flexible Electr.',
                    'HP Electr.', 'CSHP Electr.', 'CHP Electr.', 'PP Electr.',
                    'PP2 Electr.', 'Nuclear Electr.', 'Geother. Electr.',
                    'Pump Electr.', 'Turbine Electr.', 'Pumped Storage',
                    'ELT 2 Electr.', 'ELT 2 H2 ELT 2', 'ELT 3 Electr.',
                    'ELT 3 H2 ELT 3', 'V2G Demand', 'V2G Charge',
                    'V2G Discha.', 'V2G Storage', 'Trans H2 Electr.',
                    'Trans H2 Storage', 'CO2Hydro Electr.', 'HH-CHP Electr.',
                    'HH-HP Electr.', 'HH-HP/EB Electr.', 'HH-EB Electr.',
                    'HH-H2 Electr.', 'HH-H2 Storage', 'HH-H2 Prices',
                    'HH Dem. Heat', 'HH CHP+HP Heat', 'HH Boil. Heat',
                    'HH Solar Heat', 'HH Store Heat', 'HH Balan Heat',
                    'Stabil. Load', 'Import Electr.', 'Export Electr.',
                    'CEEP Electr.', 'EEEP Electr.', 'Elmarket Prices',
                    'Elmarket Prod', 'System Prices', 'DKmarket Prices',
                    'Btl-neck Prices', 'Import Payment', 'Export Payment',
                    'Blt-neckPayment', 'Add-exp Payment', 'Boilers', 'CHP2+3',
                    'PP CAES', 'Indi- vidual', 'Transp.', 'Indust. Various',
                    'Demand Sum', 'Biogas', 'Syngas', 'CO2HyGas', 'SynHyGas',
                    'SynFuel', 'Storage', 'Storage Content', 'Sum',
                    'Import Gas', 'Export Gas']
                        
            rows = f.readlines()[105:]
            for k in range(hours_in_leap_years):
                rows[k] = rows[k].split('\x00')[1:-1]
                rows[k] = [float(col) for col in rows[k]]
                dr = pandas.date_range(start='20120101 0:00', end='20121231 23:00',
                               freq='H')
            values_distr = pandas.DataFrame(data=rows, index=dr, columns=output_col_names)
        return values_distr


# class Distributions(object):
#     """
#     :param dnames: list of distribution name
#     :type: list
#     :param eplanfolder: string with the path of EnergyPlan
#     :type: str
#     """

#     def __init__(self, dnames, eplanfolder, data=None):
#         self.dnames = dnames
#         self.eplanfolder = eplanfolder
#         self.data = self.get_distr()

#     def get_distr(self, year=2012):

#         dfolder = os.path.join(self.eplanfolder,
#                                r'energyPlan Data\Distributions')
#         #import ipdb; ipdb.set_trace()
#         c = lambda x: float(x.replace(',', '.'))

#         distr = np.zeros((HOURS_IN_LEAP_YEAR, len(self.dnames)))

#         for k in range(len(self.dnames)):
#             # I notice in the file Hour.eletricity / as comment
#             distr[:, k] = np.genfromtxt(os.path.join(dfolder,
#                                         self.dnames[k]),
#                                         converters={0: c},
#                                         comments='/')

#         dr = pandas.date_range(start=str(year)+'0101 0:00',
#                                end=str(year)+'1231 23:00',
#                                freq='H')
#         self.data = pandas.DataFrame(data=distr, index=dr, columns=self.dnames)
#         return self.data

#     def write_distr(self):

#         # convert series to dataframe
#         if isinstance(self.data, pandas.Series):
#             self.data = pandas.DataFrame(self.data)

#         dfolder = os.path.join(self.eplanfolder,
#                                r'energyPlan Data\Distributions')

#         for s in self.data:
#             self.data[s].to_csv(os.path.join(dfolder, s),
#                                 index=False, sep=';', decimal=',',
#                                 float_format='%.9f')

#     #TODO: can be usefull to have a method that changes values of a
#     # a distribution, maybe not because we have methods of dataframe
#     def change_distr(self):
#         pass


def recode(infile, outfile):
    #FIXME: rvaccaro function
    pass
#    output="impianti_2_ok.txt" #salvato as unicode text
#
#    f = open(output)
#
#    pippo= pd.read_csv(f,
#                     #skipinitialspace=True,
#                     sep=",", # or "\t" per tab
#                     names=["Codice","Indirizzo"],
#                     header=0,
#                     index_col=False)
#    f.close()
#    print(pippo.loc[120:160,:])







