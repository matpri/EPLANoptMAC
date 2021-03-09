# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 12:23:15 2020

@author: MPrina
"""


from libeplan import Node
import pandas as pd
import time

ex = pd.ExcelFile("Input.xlsx")
dfDV = ex.parse("decision variables")
dfPS = ex.parse("Paths and steps")
dfO = ex.parse("Additional output")

dfDV=dfDV.set_index('labels')
dfPS=dfPS.set_index('labels')
# print(dfDV.columns)

list_output_keys=dfO['labels'].to_list()

INPUTFILE = dfPS.loc["Input file", 'values']
ENERGYPLAN = dfPS.loc["EnergyPLAN folder", 'values']
OUT_FOLDER = dfPS.loc['Output folder', 'values']

# print(INPUTFILE, ENERGYPLAN ,OUT_FOLDER)

STEPS = int(dfPS.loc["Number of steps", 'values'])
indice = list(range(STEPS))
df = pd.DataFrame(index=indice)
# print(STEPS)
Costs = []
CO2 = []

measures={}
iterable=[]
for a in dfDV.columns:
    measures[a]= [a, 0, dfDV.loc["Max potential", a], dfDV.loc["Additional step", a], dfDV.loc["EPLAN label", a]]
    iterable.append(measures[a])

print(measures)

# -----------------------------------------------------------------------------

#function to calculate cost-effectivness or Cost of Carbon abatement (CCA) 
def CE(dicREF, dic):
    """Cost effectiveness or CCA."""
    Cost_REF = dicREF['TOTAL ANNUAL COSTS']
    # print('Cost_REF', Cost_REF)
    CO2_REF = dicREF['CO2-emission (total)']
    # print('CO2_REF', CO2_REF)
    
    Cost = dic['TOTAL ANNUAL COSTS']
    # print('Cost = ', round(Cost, 2))
    CO2 = dic['CO2-emission (total)']
    # print('CO2 = ', round(CO2, 2))
    
    if CO2_REF-CO2 <= 0:
        CostEff = 100000
    else:
        CostEff = (Cost - Cost_REF)/(CO2_REF-CO2)

    CO2_pot = CO2_REF-CO2

    return CostEff, CO2_pot


def measure_def(data_act, data_start, measure):
    """Application of measure modifications."""

    existing = data_act[measure[4]]
    if existing+measure[3] > measure[2]:
        varEP = measure[2]
    else:
        varEP = existing+measure[3]
    data_act[measure[4]] = varEP

    return data_act


names = dfDV.columns
CE_trends = pd.DataFrame(None, index=indice, columns=names)

# CO2 trends
CO2_trends = pd.DataFrame(None, index=indice, columns=names)

# Output trends
Output_trends = pd.DataFrame()


# Relevant variable inizialization
Names_opt = []
C_effectiveness = []
CO2_abb = []
CO2_TOT_opt = []
C_eMob_opt = []
C_indv_heating_opt = []
en_eff_step = []
EV_diff_act = 0
EVgap_costs = 0
EV_diff_step = []
en_eff_act = 0

#  --------------------------------------
# Baseline setting

START = Node(INPUTFILE, ENERGYPLAN, OUT_FOLDER)
new_data = START.data

INPUTFILE = INPUTFILE.replace('.txt', 'new_node'+'.txt')
out_file = r'%s\out_new.txt' % (OUT_FOLDER)

new_node = Node(INPUTFILE, ENERGYPLAN, out_file, new_data)
new_node.write_input()
new_node.excute()

dicREF = new_node.read_All_outputs()

# MAC construction
data = new_data.copy()
dic_REFERE = dicREF.copy()


t0 = time.time()
for a in range(STEPS):
    print('STEP:', a)

    costE = {}
    collection = {}
    coll_data = {}
    coll_Ceff = {}
    coll_cost = {}
    coll_CO2_tot = {}
    
    if not iterable:
        Names_opt.append('-')
        C_effectiveness.append('-')
        CO2_abb.append('-')
        CO2_TOT_opt.append('-')
    else:
        for b in iterable:
    
            data_op = data.copy()
            dic_REFERE_op = dic_REFERE.copy()
    
            # Measure recalling
            name = b[0]
    
            new_data_mod = measure_def(data_op, new_data, b)
    
            new_node = Node(INPUTFILE, ENERGYPLAN, out_file, new_data_mod)
            new_node.write_input()
            new_node.excute()
    
            #dic = new_node.read_output_y()
            dic = new_node.read_All_outputs()
    
            # Energy efficiency costs
    
            dic['TOTAL ANNUAL COSTS'] = (dic['TOTAL ANNUAL COSTS'])
    
            COST = dic['TOTAL ANNUAL COSTS']
            CO2 = dic['CO2-emission (total)']
    
            Cost_Eff, CO2Potential = CE(dic_REFERE_op, dic)
    
            print('Evaluating: ', name)
    
            print('CCA = ', round(Cost_Eff, 2))
            print('CO2 potential reduction =', round(CO2Potential, 2))
            print('Annual Costs = ',round(COST, 2))
            print('Annual CO2 = ', round(CO2, 2))
    
            print('----------------------')
    
            costE[name] = Cost_Eff
            coll_cost[name] = COST
            collection[name] = dic
            coll_data[name] = new_data_mod
            coll_Ceff[name] = CO2Potential
            coll_CO2_tot[name] = CO2
    
    
        label_OPT = min(costE, key=costE.get)
    
    
        dic_REFERE = collection[label_OPT]
        data = coll_data[label_OPT]
        Names_opt.append(label_OPT)
    
        C_effectiveness.append(costE[label_OPT])
        CO2_abb.append(coll_Ceff[label_OPT])
        CO2_TOT_opt.append(coll_CO2_tot[label_OPT])
        
        # Cost effectiveness and CO2 abatement
        for b in iterable:
            CE_trends.loc[(a, b[0])] = costE[b[0]]
            CO2_trends.loc[(a, b[0])] = coll_Ceff[b[0]]
    
       
        #Outputs trends
        for b in list_output_keys:
            Output_trends.loc[(a, b)] = dic_REFERE[b]
    
        # Potential check used to remove a measure from iterable when the maximum potential is reached (only for short term approach)
        for m in iterable:
            # to_be_rem=m[:]
            for i in range(len(dfDV.columns)):
                if m[0] == dfDV.columns[i]:
                    m[1] = data[m[4]]
                    # for k in range(len(iterable)):
                    if m[1] == m[2]:
                        iterable.remove(m)


t1 = time.time()
elapsed_time = t1-t0
print ("The total time is.. ", elapsed_time)


df['Measure'] = Names_opt
df['C_effectiveness'] = C_effectiveness
df['CO2 abatement'] = CO2_abb
df['Total CO2'] = CO2_TOT_opt

CE_trends['Measure'] = Names_opt
CO2_trends['Measure'] = Names_opt


# Saving of all variables into an excel file
with pd.ExcelWriter('MAC.xlsx') as writer:
    df.to_excel(writer, sheet_name='MAC')
    CE_trends.to_excel(writer, sheet_name='Cost effectiveness trends')
    CO2_trends.to_excel(writer, sheet_name='CO2 trends')
    Output_trends.to_excel(writer, sheet_name='Output trends')
