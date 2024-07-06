# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 15:46:34 2024

@author: Trevor Gratz, trevormgratz@gmail.com

The method to link interventions, outcomes, and coordinated entry events is
detailed in the folling file.
'..\..\..\Documentation\Project Generated\OutcomesInterventionDocumentation_02132024.xlsx'
The numbered steps from the above file are indicated in comments.


PSH = Permanent Supportive Housing
RRH = Rapid Re-housing
TSH = Transitional Housing
HoH = Head of Household
"""


from InterventionOutcomes_SQL_02122024 import sql_ceevents, sql_ceinterventions, sql_literalhomeless, sql_ceeventsallpersons

import pandas as pd
import pyodbc
from datetime import date, datetime
import datetime as dtother
import numpy as np

cnxn = {'XXX'}

today = date.today()

##############################################################################
# Load and conduct initial processing
##############################################################################


def prepdata(df):
    '''
    Cleans dates for enrollment data.
    '''
    df['EnrollmentEntryDate'] = pd.to_datetime(df['EnrollmentEntryDate'])
    df['EnrollmentExitDate'] = pd.to_datetime(df['EnrollmentExitDate'])
    df['MoveInDate'] = pd.to_datetime(df['MoveInDate'])
    df['ExitDestinationGroup'] = df['ExitDestinationGroup'].str.replace("Permanent’", "Permanent")

    # If exit date is missing use the moveindate
    movedate = ((df['EnrollmentExitDate'].isna()) &
                (~df['MoveInDate'].isna()))

    df.loc[movedate, 'EnrollmentExitDate'] = df.loc[movedate, 'MoveInDate']
    df.loc[movedate, 'ExitDestinationGroup'] = "Permanent"
    df.loc[movedate, 'ExitDestinationName'] = "Permanent"

    # If the exit date is missing, use today's date plus one, then correct at
    # the end
    todayplusone = date.today() + dtother.timedelta(days=1)
    todayplusone = dtother.datetime.fromordinal(todayplusone.toordinal())
    misdate = ((df['EnrollmentExitDate'].isna()) &
               (df['MoveInDate'].isna()))

    df.loc[misdate, 'EnrollmentExitDate'] = todayplusone
    df.loc[misdate, 'ExitDestinationGroup'] = 'Missing'

    return df

# Step 1
# Coordinated Entry Enrollments of the Head of Household
df_ce = pd.read_sql(sql_ceevents, cnxn)

# Step 2
# RRH, PSH, and TSH Interventions linked to the Head of Household.
df_int = pd.read_sql(sql_ceinterventions, cnxn)


# Step 3
# All Literal Homeless events, regardless of HoH status.
df_lh = pd.read_sql(sql_literalhomeless, cnxn)
df_lh['EnrollmentEntryDate'] = pd.to_datetime(df_lh['EnrollmentEntryDate'])
df_lh = df_lh.rename(columns={'PersonalID': 'PersonalID_all',
                              'EnrollmentEntryDate': 'LH_EnrollmentEntryDate'})

# Step 4
# All PersonIDs associated with a Household ID.
df_allpid = pd.read_sql(sql_ceeventsallpersons, cnxn)
df_allpid = df_allpid.rename(columns={'PersonalID': 'PersonalID_all'})

# Step 5 - Clean Exit Dates
cdf = prepdata(df=df_ce)
idf = prepdata(df=df_int)
idf = idf.rename(columns={'EnrollmentEntryDate': 'int_EnrollmentEntryDate',
                          'EnrollmentExitDate': 'int_EnrollmentExitDate',
                          'ExitDestinationGroup': 'int_ExitDestinationGroup',
                          'ExitDestinationName': 'int_ExitDestinationName',
                          'MoveInDate': 'int_MoveInDate'})
##############################################################################
# STEP 6 : Create CE Events
##############################################################################

# Loop over individual persons, make a list of CE Events.
# The main idea is to consider CE enrollments that are overlapping or within
# 14 days between exit and the next entry as the same event.
# The edge cases that need to be handled are
# people with only one CE enrollment and the last row of the data.

cdf = cdf.sort_values(by=['PersonalID', 'EnrollmentEntryDate',
                          'EnrollmentExitDate'])
grouped = cdf.groupby('PersonalID')
ceevents = []


def loopceevents(grouped=grouped):
    '''
    Loop over individual persons, make a list of CE Events.
    The main idea is to consider CE enrollments that are overlapping or within
    14 days between exit and the next entry as the same event.
    The edge cases that need to be handled are
    people with only one CE enrollment and the last row of the data.

    Parameters
    ----------
    grouped : Pandas Group By Object
        DESCRIPTION. Grouped by PersonalID from a dataset of CE enrollments. 
        The dataset should be filtered to head of households.
        The default is grouped.

    Returns
    -------
    ceevents : Dataframe
        DESCRIPTION. A dataframe of "CE Events". See the description in the 
        header or in the OutcomesInterventionDocumentation_02132024.xlsx file.

    '''
    ceevents = []
    for personid, data in grouped:
        # Loop over rows of individual
        data = data.reset_index()

        # Initialize
        cepid = data.loc[0, 'PersonalID']
        ceenrollid = data.loc[0, 'EnrollmentID']
        cehousholdid = data.loc[0, 'HouseholdID']
        cestart = data.loc[0, 'EnrollmentEntryDate']
        ceend = data.loc[0, 'EnrollmentExitDate']
        ceexitgroup = data.loc[0, 'ExitDestinationGroup']
        ceexitname = data.loc[0, 'ExitDestinationName']
        cemovein = data.loc[0, 'MoveInDate']

        # Person only has one CE Enrollment.
        if len(data) == 1:
            ceevents.append([cepid, ceenrollid, cehousholdid, cestart, ceend,
                             ceexitgroup, ceexitname, cemovein])
        else:
            # Multiple CE Enrollments
            for i in range(1, len(data)):

                # Overlapping CE Enrollments == Same CE EVENT
                if (data.loc[i, 'EnrollmentEntryDate'] - ceend).days <= 14:
                    # only update exit data if the current row exit occurs
                    # after the past rows exit.
                    if ceend < data.loc[i, 'EnrollmentExitDate']:
                        ceend = data.loc[i, 'EnrollmentExitDate']
                        ceexitgroup = data.loc[i, 'ExitDestinationGroup']
                        ceexitname = data.loc[i, 'ExitDestinationName']

                    # Update Housing Move in if more recent
                    if cemovein < data.loc[i, 'MoveInDate']:
                        cemovein = data.loc[i, 'MoveInDate']

                    # If the current row is the last row add it
                    if len(data) == i+1:
                        ceevents.append([cepid, ceenrollid, cehousholdid,
                                         cestart, ceend, ceexitgroup,
                                         ceexitname, cemovein])

                # Non-Overlapping CE Enrollments
                # 1) Add CE Enrollment as Event.
                # 2) Update to current row
                # 3) If the current row is the last row of the data, add it.
                else:
                    # Store past CE Event
                    ceevents.append([cepid, ceenrollid, cehousholdid, cestart,
                                     ceend, ceexitgroup, ceexitname, cemovein])
                    # Update to current row
                    cepid = data.loc[i, 'PersonalID']
                    ceenrollid = data.loc[i, 'EnrollmentID']
                    cehousholdid = data.loc[i, 'HouseholdID']
                    cestart = data.loc[i, 'EnrollmentEntryDate']
                    ceend = data.loc[i, 'EnrollmentExitDate']
                    ceexitgroup = data.loc[i, 'ExitDestinationGroup']
                    ceexitname = data.loc[i, 'ExitDestinationName']
                    cemovein = data.loc[i, 'MoveInDate']

                    # Store if it is also the last row
                    if len(data) == i+1:
                        ceevents.append([cepid, ceenrollid, cehousholdid,
                                         cestart, ceend, ceexitgroup,
                                         ceexitname, cemovein])
                        
    ceeventsdf = pd.DataFrame(ceevents, columns=['PersonalID',
                                                 'EnrollmentID',
                                                 'HouseholdID',
                                                 'EnrollmentEntryDate',
                                                 'EnrollmentExitDate',
                                                 'ExitDestinationGroup',
                                                 'ExitDestinationName',
                                                 'MoveInDate'])

    return ceeventsdf

ceeventsdf = loopceevents(grouped=grouped)


###############################################################################
# Step 7:  Merge CE Events and Potential Interventions
###############################################################################

# Steps
# 1) Perform one to many merge.
# 2) Filter to rows with interventions that overlap the ce event.
# 3) Left merge accepted matches to original ceeventsdf
# 4) Non-matches mean there was no intervention.

def addinterventions(events, interventions):
    '''
    Takes in a dataset of CE events and one of housing interventions and 
    creates a wide datase with all interventions that overlap  in date ranges
    with the CE event matched to that event.

    Parameters
    ----------
    events : Dataset
        DESCRIPTION. Dataset of CE Events. See step 6.
    interventions : Dataset
        DESCRIPTION. Dataset of housing interventions (RRH, TSH, and PSH). See
                     step 5.

    Returns
    -------
    ceint : Dataset
        DESCRIPTION.Dataset of CE events matched to intervention with added
                    the following variables:
                    RRH: 0/1 indicator for RRH intervention
                    RRH_Entry: Earliest RRH enrollment date.
                    RRH_Exit: Latest RRH enrollment exit date.
                    TSH: 0/1 indicator for TSH intervention
                    TSH_Entry: Earliest TSH enrollment date.
                    TSH_Exit: Latest TSH exit date.
                    PSH: 0/1 indicator for PSH intervention
                    PSH_Entry: Earliest PSH enrollment date.
                    PSH_Exit: Latest PSH exit date.
                    IntMoveInDate: Earliest move-in date associated with
                                   with an intervetnion.
                    LastIntExitDate: Last exit date across all interventions.
                    LastIntExitDestinationGroup: Last exit destination across
                                                 intervetions.
                    LastIntExitDestinationName: Last exit names across 
                                                interventions. 
                    start_date: The minimum enrollment date acros CE events
                                and intervetnions.
                    end_date: The maximum exit date across CE events and
                              interventions.
                    intervention_start_date: The minimum enrollment date of
                                             intervetnions. 
                                             
    '''
    # one CE event may be matched to none, one, or many intervetions.
    temp = pd.merge(events, interventions[['PersonalID', 'int_EnrollmentEntryDate',
                                           'int_EnrollmentExitDate',
                                           'int_ExitDestinationGroup',
                                           'int_ExitDestinationName', 'int_MoveInDate',
                                           'ProjectTypeName']],
                    on=['PersonalID'], how='left')

    # Keep overlapping observations.
    tokeep = (
              # Intervention entry is before CE enrollment, but intervention exit occurs after CE enrollment 
              ((temp['int_EnrollmentEntryDate'] <= temp['EnrollmentEntryDate']) &
               (temp['int_EnrollmentExitDate'] >= temp['EnrollmentEntryDate'])) |
              # Intervention entry occurs after CE enrollment, but occurs before the CE enrollment exit.
              ((temp['int_EnrollmentEntryDate'] >= temp['EnrollmentEntryDate']) &
               (temp['int_EnrollmentEntryDate'] <= temp['EnrollmentExitDate'])) |
              # Intervention entry occurs 14 days after exit from CE
              (((temp['int_EnrollmentEntryDate'] - temp['EnrollmentExitDate']).dt.days <= 14 ) &
               ((temp['int_EnrollmentEntryDate'] - temp['EnrollmentExitDate']).dt.days >= 0 ))
             )
    temp = temp.loc[tokeep,].copy()

    # Generate RRH, TSH, PSH indicators and dates in a wide format
    # for aggregateing
    temp['RRH'] = (temp['ProjectTypeName'] == 'PH - Rapid Re-Housing').astype(int)
    temp.loc[temp['RRH'] == 1, 'RRH_Entry'] = temp.loc[temp['RRH'] == 1, 'int_EnrollmentEntryDate']
    temp.loc[temp['RRH'] == 1, 'RRH_Exit'] = temp.loc[temp['RRH'] == 1, 'int_EnrollmentExitDate']
    
    temp['TSH'] = (temp['ProjectTypeName'] == 'Transitional Housing').astype(int)
    temp.loc[temp['TSH'] == 1, 'TSH_Entry'] = temp.loc[temp['TSH'] == 1, 'int_EnrollmentEntryDate']
    temp.loc[temp['TSH'] == 1, 'TSH_Exit'] = temp.loc[temp['TSH'] == 1, 'int_EnrollmentExitDate']
    
    temp['PSH'] = (temp['ProjectTypeName'] == 'PH - Permanent Supportive Housing').astype(int)
    temp.loc[temp['PSH'] == 1, 'PSH_Entry'] = temp.loc[temp['PSH'] == 1, 'int_EnrollmentEntryDate']
    temp.loc[temp['PSH'] == 1, 'PSH_Exit'] = temp.loc[temp['PSH'] == 1, 'int_EnrollmentExitDate']
    
    # Collapse back to the PersonalID and EnrollmentID observation. Given the
    # the data this is for the HoH.
    temp = temp.sort_values(['PersonalID', 'EnrollmentID',
                             'int_EnrollmentExitDate'])
    itdf = temp.groupby(['PersonalID','EnrollmentID'],
                        as_index=False).agg(RRH=('RRH', 'max'),
                                            RRH_Entry=('RRH_Entry', 'min'),
                                            RRH_Exit=('RRH_Exit', 'max'),
                                            TSH=('TSH', 'max'),
                                            TSH_Entry=('TSH_Entry', 'min'),
                                            TSH_Exit=('TSH_Exit', 'max'),
                                            PSH=('PSH', 'max'),
                                            PSH_Entry=('PSH_Entry', 'min'),
                                            PSH_Exit=('PSH_Exit', 'max'),
                                            IntMoveInDate = ('int_MoveInDate', 'min'),
                                            LastIntExitDate = ('int_EnrollmentExitDate', 'last'),
                                            LastIntExitDestinationGroup=('int_ExitDestinationGroup', 'last'),
                                            LastIntExitDestinationName=('int_ExitDestinationName', 'last'))

    # Merge interventions back to the original CE events data
    ceint = pd.merge(events, itdf, on=['PersonalID', 'EnrollmentID'],
                     how='left')

    # Calculate the start and end date across the CE events and the
    # interventions.
    ceint['start_date'] = ceint[['EnrollmentEntryDate', 'RRH_Entry',
                                 'TSH_Entry', 'PSH_Entry']].min(axis=1)
    ceint['end_date'] = ceint[['EnrollmentExitDate', 'RRH_Exit', 'TSH_Exit',
                               'PSH_Exit']].max(axis=1)
    ceint['intervention_start_date'] = ceint[['RRH_Entry', 'TSH_Entry',
                                              'PSH_Entry']].min(axis=1)

    # Fill in Tx Indicators
    ceint['RRH'] = ceint['RRH'].fillna(0)
    ceint['TSH'] = ceint['TSH'].fillna(0)
    ceint['PSH'] = ceint['PSH'].fillna(0)
    return ceint


ceint = addinterventions(events=ceeventsdf, interventions=idf)

#############################################################################
# Step 8: Determine Exit Status
#############################################################################
# Boolean for whether the CE Event has the last exit date. If it doesn't, then
# the last exit date is from the intervetnions.


def exitstatus(ceint=ceint):
    '''
    Determines the final exit status of the dataset produced in step 7.
    '''
    cebool = (ceint['EnrollmentExitDate'] == ceint['end_date'])
    ceintbool = (ceint['LastIntExitDate'] == ceint['end_date'])

    ceint.loc[cebool, 'ExitStatus'] = ceint.loc[cebool, 'ExitDestinationGroup']
    ceint.loc[ceintbool, 'ExitStatus'] = ceint.loc[ceintbool, 'LastIntExitDestinationGroup']
    
    ceint.loc[cebool, 'ExitStatusName'] = ceint.loc[cebool, 'ExitDestinationName']
    ceint.loc[ceintbool, 'ExitStatusName'] = ceint.loc[ceintbool, 'LastIntExitDestinationName']
    return ceint


ceint = exitstatus(ceint=ceint)

###############################################################################
# Step 9: Merge CE Events and Literal Homelessness
#############################################################################

# Expand the ceint data to include all people linked to that CE event.
def addliteralhomeless(eventinter, allids, literalhomeless):
    '''
    Matches literal homeless events from all personalIDs linked to the
    household id (note, not just the head of household, which is currently
    how the ceint dataset is structured). Keeps the most recent literal
    homeless event taken among all household members occuring after the exit
    date for the household. 

    Parameters
    ----------
    eventinter : Dataset
        DESCRIPTION. Dataset from step 8
    allids : dataset
            DESCRIPTION. Dataset from step 4
    literalhomeless : dataset
        DESCRIPTION. Dataset from step 3

    Returns
    -------
    eventinter : Dataset
        DESCRIPTION. The ceint dataset from step 8 with an added variable
                     for the households most recent literal homeless event
                     occuring after the household exit.
    '''
    expand = pd.merge(eventinter, allids, on='HouseholdID')
    # Add Literal Homeless Events
    expand = pd.merge(expand, literalhomeless, on='PersonalID_all')
    # Keep LH observations that occured after exit status date.
    lhafterexit = expand.loc[expand['end_date'] < expand['LH_EnrollmentEntryDate'], ].copy()
    # Get most recent LH event.
    temp = lhafterexit.groupby(['PersonalID', 'EnrollmentID'], as_index=False)['LH_EnrollmentEntryDate'].min()
    # Merge back to original data
    eventinter = pd.merge(eventinter, temp,
                     on=['PersonalID', 'EnrollmentID'], how='left')
    return eventinter


ceintlh = addliteralhomeless(eventinter=ceint, allids=df_allpid, 
                             literalhomeless=df_lh)

###############################################################################
# step 10 Determine Success
###############################################################################


def defsuccess(temp, daystosuccess):
    '''
    Success is determined by an exit to a permanent destination without a reentry 
    since two years after exit. Days to success is a list of the number of 
    days needed to be deemed a successful exit. A second definition of success
    relies exclusively on whether or not a literal homelessness event occurs
    after an exit, regardless of the exit type (exit type is frequently
    unknown).
    '''
    
    for d in daystosuccess:
        temp[f'success_{d}'] = ((temp['ExitStatus'] == 'Permanent') &
                                ((temp['LH_EnrollmentEntryDate'].isna()) |
                                 ((temp['LH_EnrollmentEntryDate'] - temp['end_date']).dt.days > d)
                                 )
                                ).astype(int)

        temp[f'success_noexit_{d}'] = (
                                       ((temp['LH_EnrollmentEntryDate'].isna()) |
                                        ((temp['LH_EnrollmentEntryDate'] - temp['end_date']).dt.days > d)
                                        )
                                       ).astype(int)        
        # Less than 2 years have passed since exit.
        temp.loc[(pd.to_datetime("now")-temp['end_date']).dt.days < d, f'success_{d}'] = np.nan
        temp.loc[(pd.to_datetime("now")-temp['end_date']).dt.days < d, f'success_noexit_{d}'] = np.nan

    return temp

ceintlhsuc = defsuccess(temp=ceintlh.copy(), daystosuccess = [365*2, 365, 180])

# Output
today = date.today()
path = r'..\..\..\Data\InterventionOutcomes'
path +=  f'_{today}.pkl'
ceintlhsuc.to_pickle(path)

###############################################################################
# Temporary. Put here to facilitate comparison to raw data and documented steps.

path = r'..\..\..\Data\CEInterventionSample_Outcomes.csv'
ceint.to_csv(path)

#ceintlhsuc.loc[ceintlhsuc['start_date'].dt.year >= 2017, 'success'].value_counts()

# ((temp['LH_EnrollmentEntryDate'] - temp['end_date']).dt.days > d)

# # 67% of exit destinations are unknown or other
# ceintlhsuc['ExitStatusName'].value_counts(normalize=True)
# ceintlhsuc['ExitStatus'].value_counts(normalize=True)