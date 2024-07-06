# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 15:46:34 2024

@author: Trevor Gratz, trevormgratz@gmail.com
"""

from HouseholdRollUpSQL_01312024 import sql_households
from HeadofHouseholdsSQL_01312024 import sql_hoh
from LiteralHomelessnessHistorySQL_01312024 import sql_lh

import pandas as pd
import pyodbc
from datetime import date


today = date.today()

cnxn = {'XXX'}

##############################################################################

# Household Features
hhoutpath = r'..\..\..\Data\HouseholdFeatures'
hhoutpath += f'_{today}.pkl'
df_households = pd.read_sql(sql_households,cnxn)
df_households.to_pickle(hhoutpath)

# Head of Household Features
hohoutpath = r'..\..\..\Data\HeadofHousholdFeatures'
hohoutpath += f'_{today}.pkl'
df_hoh = pd.read_sql(sql_hoh,cnxn)
df_hoh.to_pickle(hohoutpath)
#df_hoh[['HoH_EnrollmentID', 'HoH_PersonalID']].duplicated().sum()
#df_hoh = df_hoh.sort_values(['HoH_EnrollmentID', 'HoH_PersonalID'])

# Literal Homeless History
lhoutpath = r'..\..\..\Data\HouseholdLiteralHomelessnessHistory'
lhoutpath += f'_{today}.pkl'
df_lh = pd.read_sql(sql_lh,cnxn)
df_lh.to_pickle(lhoutpath)
