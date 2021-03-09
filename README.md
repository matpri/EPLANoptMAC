# EPLANoptMAC #
EPLANoptMAC allows the creation of the Marginal Abatement Cost (MAC) curve based on the EnergyPLAN software and by means of an optimization process. https://www.youtube.com/watch?v=0jXJhxtK_FY&t=3s
![](MAC.gif)

## Requirements ##
- EnergyPLAN version >=15.1

## How to run the example ##
The example presented in this repository is based on the Scenario DK2020_2018edition_cost update.txt provided with the download of the EnergyPLAN software. This file is saved in the input_folder together its ANSI version. To produce the ANSI version needed by the code, you just need to follow these simple instructions: 1) Open the DK2020_2018edition_cost update.txt file, 2) File, Save as..., 3) on the bottom change the encoding from Unicode to ANSI, 4) change the name of the file in order to remember that it is the ANSI version and click on Save. This is just to let you know the steps you have to go through if you want to change the EnergyPLAN input file. In the folder you can already find the ANSI version for the considered example: DK2020_2018edition_cost update_ANSI.txt
In the excel file called Input.xlsx you can find and set the following input of the model:
1) Decision variables. In this Sheet the decision variable are defined with labels, EPLAN label, Max potential and Additional step. The labels can be chosen by the user. The EPLAN label is the EnergyPLAN label that can be found in the DK2020_2018edition_cost update.txt regarding the related decision variable (for example for wind power in this case is 'input_RES1_capacity'). The Max potential is the maximum potential or upper bound of the decision variable for the expansion capacity opzimisation (in this example the are invented but reasonable numbers. However, a proper evaluation of this potential should be included in the analysis). The Additional step is the incremental value (in terms of installed power, capacity, additional share, etc.) of each decision variable on which is implemented the expansion capacity optimisation. 
