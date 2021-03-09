# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 08:40:59 2020

@author: MPrina
"""
from matplotlib import pyplot as plt
from matplotlib import pylab
from termcolor import colored
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib as mpl
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches

ex_hist = pd.ExcelFile("MAC.xlsx")
df = ex_hist.parse("MAC")
print(df)
df = df[df.Measure != '-']
larghezza=df['CO2 abatement'].tolist()

yy=df['C_effectiveness'].tolist()
cc=df['Measure'].tolist()
df['xcum']=df['CO2 abatement'].cumsum()
df['xcum2']=[0]+df['xcum'].tolist()[:-1]

xx=df['xcum2'].tolist()


fig, ax = plt.subplots(figsize=(13,6))
plt.rcParams["font.family"] = "Calibri"

dic_col={'PV': '#F9DB61', 'W':'#EB8627', 'Offshore': '#9C3121'}

col=[]
for a in range(len(cc)):
    col.append(dic_col[cc[a]])

plt.bar(xx, yy, width=larghezza,  align='edge', color=col, edgecolor='black', linewidth=0.4)

PV_patch = mpatches.Patch(facecolor='#F9DB61', edgecolor='black', label='Residential PV')

W_patch = mpatches.Patch(facecolor='#EB8627', edgecolor='black',label='Wind power')
 
W_off_patch = mpatches.Patch(facecolor='#9C3121', edgecolor='black',label='Offshore Wind power')                           
                          

plt.legend(handles=[PV_patch,  W_patch, W_off_patch], loc=2, fontsize=12) 

plt.ylim(-100, 1500)
plt.ylabel('Cost of Carbon abatement [Eur/t saved $\mathregular{CO_2}$]', fontsize=14)
plt.xlabel('[Mt $\mathregular{CO_2}$]', fontsize=14)
plt.grid(linestyle='dotted')
plt.show()

pylab.savefig("MAC.png", bbox_inches="tight", dpi=300)


