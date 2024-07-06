# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 15:57:46 2024

@author: Trevor Gratz, trevormgratz@gmail.com

This file assembles data from four primary intermediary data sources:
    InterventionOutcomes_2024-04-18.pkl
    HouseholdFeatures_2024-04-18.pkl
    HouseholdLiteralHomelessnessHistory_2024-04-18.pkl
    HeadofHousholdFeatures_2024-04-18.pkl

It cleans the merged data and then performs a panel-based 80/20 train test
split.
"""
import pandas as pd
import numpy as np
from datetime import date
import pickle
from Dictionaries import remap

# Load data
iodf = pd.read_pickle(r'..\..\..\Data\InterventionOutcomes_2024-04-18.pkl')
hsdf = pd.read_pickle(r'..\..\..\Data\HouseholdFeatures_2024-04-18.pkl')
lhhxdf = pd.read_pickle(r'..\..\..\Data\HouseholdLiteralHomelessnessHistory_2024-04-18.pkl') 
hohdf = pd.read_pickle(r'..\..\..\Data\HeadofHousholdFeatures_2024-04-18.pkl')

# Globals
today = date.today()
dpath = r'..\..\..\Data'
##############################################################################
# Merge

def mergefeatures(iodftemp, hohdftemp, hsdftemp, lhhxdftemp):
    hohdftemp = hohdftemp.drop(columns=['HoH_ProjectName',
                                        'HoH_ExitDestinationName',
                                        'HoH_ExitDestinationGroup',
                                        'HoH_ExitDestinationType',
                                        'HoH_EnrollmentEntryDate',
                                        'HoH_LivingSituationName',
                                        'HoH_LivingSituationGroup'])
            
    lhhxdftemp = lhhxdftemp[['CEHouseholdID', 'AverageLHEventsInPast12Months',
                             'AverageLHEventsInPast6Months' ]]
    
    # Minimum, will need to adjust data for other longer success windows
    adf = iodftemp.loc[((~iodftemp['success_180'].isna()) &
                        (iodftemp['start_date'].dt.year >= 2017)),]
    
    adf = adf[['PersonalID', 'EnrollmentID', 'HouseholdID', 'RRH', 'TSH',
               'PSH', 'start_date', 'end_date', 'RRH_Entry',
               'TSH_Entry', 'PSH_Entry', 'success_730', 'success_365',
               'success_180', 'success_noexit_730', 'success_noexit_365',
               'success_noexit_180', 'MoveInDate', 'RRH_Exit',
               'TSH_Exit', 'PSH_Exit', 'ExitStatusName']]
    
    adf = pd.merge(adf, hohdftemp, left_on=['PersonalID', 'EnrollmentID'],
                   right_on=['HoH_PersonalID', 'HoH_EnrollmentID'],
                   how='inner')

    adf = pd.merge(adf, lhhxdftemp,  left_on=['HouseholdID'],
                   right_on=['CEHouseholdID'],
                   how='left')
    
    adf = pd.merge(adf, hsdftemp, on='HouseholdID')
    return adf

adf =  mergefeatures(iodftemp=iodf, hohdftemp=hohdf, hsdftemp=hsdf,
                     lhhxdftemp=lhhxdf)

###############################################################################
# Variable Processing

def cleanvarsbyrow(temp):
    '''
    Cleans varibles where cleaning depends only on that variable or that row.
    Imputers are computed later.
    '''
    
    # No LH events present
    temp['AverageLHEventsInPast12Months'] = temp['AverageLHEventsInPast12Months'].fillna(0)
    temp['AverageLHEventsInPast6Months'] = temp['AverageLHEventsInPast6Months'].fillna(0)
    
    ###
    other = ['HoH_DomesticViolenceWhenOccurred', 'HoH_DomesticViolenceCurrentlyFleeing',
             'HoH_UnemployedAndLookingForWork', 'HoH_EmployedAndLookingForWork',
             'HoH_EmployedHoursWorkedLastWeek', 'HoH_EmploymentTenure']
    
    
    # Converts categorical missings to the same category
    rdict = {'Client prefers not to answer': 'Missing_NoAnswer_DoesntKnow',
             'Data not collected': 'Missing_NoAnswer_DoesntKnow',
             "Client doesn't know": 'Missing_NoAnswer_DoesntKnow',
             'Unknown': 'Missing_NoAnswer_DoesntKnow',
             'School program does not have grade levels': 'Missing_NoAnswer_DoesntKnow',
             'Data not collected (HUD)': 'Missing_NoAnswer_DoesntKnow',
             'Client prefers not to answer (HUD)': 'Missing_NoAnswer_DoesntKnow',
             "Client doesn't know (HUD)": 'Missing_NoAnswer_DoesntKnow',
             'Client refused (HUD)': 'Missing_NoAnswer_DoesntKnow',
             }
    
    for c in ['HoH_LengthOfStayName', 'HoH_RaceName', 'HoH_RaceGroup',
              'HoH_EthnicityName', 'HoH_GenderName', 'HoH_GenderGroup',
              'HoH_SexualOrientationName', 'HoH_VeteranStatusName',
              'HoH_TimesHomelessPastThreeYearsName',
              'HoH_LastGradeCompletedNameAtEntry', 'HoH_Employed', 
              'HoH_IncomeFromAnySource', 'HoH_HouseholdPercentofAMI',
              'HoH_NonCashBenefitFromAnySource', 'HoH_CoveredByHealthInsurance',
              'HoH_DisablingCondition', 'HoH_Pregnant',
              'HoH_DomesticViolenceSurvivor', 'HoH_PhysicalDisability',
              'HoH_DevelopmentalDisability', 'HoH_ChronicHealthCondition',
              'HoH_HIVAIDS', 'HoH_MentalHealth', 'HoH_SubstanceAbuse',
              'HoH_Unemployment', 'HoH_SSI', 'HoH_SSDI', 'HoH_VADisabilityService',
              'HoH_VADisabilityNonService', 'HoH_PrivateDisability',
              'HoH_WorkersComp', 'HoH_TANF', 'HoH_GA', 'HoH_SocSecRetirement',
              'HoH_Pension', 'HoH_ChildSupport', 'HoH_Alimony',
              'HoH_OtherIncomeSource', 'HoH_SNAP', 'HoH_WIC',
              'HoH_TANFChildCare', 'HoH_TANFTransportaion', 'HoH_OtherTANF',
              'HoH_OtherBenefitsSource']:

        temp.loc[temp[c].isna(), c] = 'Missing_NoAnswer_DoesntKnow'
        temp[c] = temp[c].replace(rdict)
    
    # Date Processing
    temp['start_date'] = pd.to_datetime(temp['start_date'])
    temp['RRH_Entry'] = pd.to_datetime(temp['RRH_Entry'])
    temp['TSH_Entry'] = pd.to_datetime(temp['TSH_Entry'])
    temp['PSH_Entry'] = pd.to_datetime(temp['PSH_Entry'])

    temp['HoH_Age_DOB'] = pd.to_datetime(temp['HoH_Age_DOB'])
    temp['HoH_Age_days'] = (temp['start_date'] - temp['HoH_Age_DOB']).dt.days
    temp['HoH_AgeAtEntry'] = temp['HoH_AgeAtEntry'].str.split(' ').str[0].astype(float)

    # Build Indicators for when TX's were assigned. 
    temp['HoH_DaysTo_RRH'] = (temp['RRH_Entry'] - temp['start_date']).dt.days
    temp['HoH_DaysTo_TSH'] = (temp['TSH_Entry'] - temp['start_date']).dt.days
    temp['HoH_DaysTo_PSH'] = (temp['PSH_Entry'] - temp['start_date']).dt.days
    
    for tx in ['RRH', 'TSH', 'PSH']:
        temp[f'HoH_{tx}_Month_1'] = (temp[f'HoH_DaysTo_{tx}'] < 30).astype(int)
        temp[f'HoH_{tx}_Month_2'] = ((temp[f'HoH_DaysTo_{tx}'] >= 30) &
                                     (temp[f'HoH_DaysTo_{tx}'] < 60)).astype(int)
        temp[f'HoH_{tx}_Month_3plus'] = (temp[f'HoH_DaysTo_{tx}'] >= 60).astype(int)

    # Clean Youngest Household Member Data
    # 7 less than 0, use child indicators (2 don't have any, use HoH Age then,
    # though this might be fixed in the new SQL, missed 3 years old exactly),
    # 3 have missing values (Use HOH_Age)
    temp = temp.rename(columns={'Household_N_children15_18': 'Household_N_children15_17'}) 
    for c in [('Household_N_children0_3', 1.5),
              ('Household_N_children3_5', 4),
              ('Household_N_children5_10', 7.5),
              ('Household_N_children10_15', 12.5),
              ('Household_N_children15_17', 16)]:
        rbool = (((temp['Household_YoungestClient'] < 0) |
                  (temp['Household_YoungestClient'].isna())
                  ) &
                 (temp[c[0]] > 0)
                 )
        temp.loc[rbool, 'Household_YoungestClient'] = c[1]
    temp.loc[temp['Household_YoungestClient']< 0,'Household_YoungestClient'] = temp.loc[temp['Household_YoungestClient']< 0,'HoH_AgeAtEntry'] 

    # Convert Ages less than 0 to missing. NaN will be handled by imputer later
    # on
    temp.loc[temp['HoH_AgeAtEntry']<0, 'HoH_AgeAtEntry'] = np.nan
    temp.loc[(temp['Household_OldestClient']<0), 'Household_OldestClient'] = np.nan
    temp.loc[(temp['Household_YoungestClient']<0), 'Household_YoungestClient'] = np.nan


    # 99.85% of people work less than 80 hours and there are some clear
    # data entry errors (e.g. working more hours than available in a week)
    temp.loc[temp['HoH_EmployedHoursWorkedLastWeek'] > 80,
             'HoH_EmployedHoursWorkedLastWeek'] = 80

    # Many Households Have missing Hours Worked because they answered
    # unemployed to the previous CE employment question.
    temp['Household_HoursWorked'] = temp['Household_HoursWorked'].fillna(0)
    temp['HoH_EmployedHoursWorkedLastWeek'] = temp['HoH_EmployedHoursWorkedLastWeek'].fillna(0)
    
    # Log Transforms for skewed data
    temp['ln_HoH_EmployedHoursWorkedLastWeek'] = np.log(temp['HoH_EmployedHoursWorkedLastWeek'] +1)
    temp['ln_AverageLHEventsInPast12Months'] = np.log(temp['AverageLHEventsInPast12Months'] +1)          
    temp['ln_N_Household'] = np.log(temp['N_Household'] +1)          
    temp['ln_Household_N_Children'] = np.log(temp['Household_N_Children'] +1)                                               
    
    # Still have outliers throwing off convergence
    temp['rmout_AverageLHEventsInPast12Months'] = temp['AverageLHEventsInPast12Months']
    cut=temp['AverageLHEventsInPast12Months'].quantile(.99)
    temp.loc[temp['AverageLHEventsInPast12Months'] > cut, 'rmout_AverageLHEventsInPast12Months'] = cut
    temp['ln_rmout_AverageLHEventsInPast12Months'] = np.log(temp['rmout_AverageLHEventsInPast12Months'] +1)
    
    temp['rmout_HoH_EmployedHoursWorkedLastWeek'] = temp['HoH_EmployedHoursWorkedLastWeek']
    cut=temp['HoH_EmployedHoursWorkedLastWeek'].quantile(.99)                                              
    temp.loc[temp['HoH_EmployedHoursWorkedLastWeek'] > cut, 'rmout_HoH_EmployedHoursWorkedLastWeek'] = cut
    temp['ln_rmout_HoH_EmployedHoursWorkedLastWeek'] = np.log(temp['rmout_HoH_EmployedHoursWorkedLastWeek'] +1)
    
    # Many Income and Benefits Categories are Sparse. Combine them into an
    # Other Group if any are present.
    temp['HoH_OtherIncomeCombined'] = '0' 
    for c in ['HoH_VADisabilityNonService', 'HoH_PrivateDisability',
              'HoH_WorkersComp', 'HoH_Pension', 'HoH_Alimony',
              'HoH_WIC', 'HoH_TANFChildCare', 'HoH_TANFTransportaion',
              'HoH_OtherTANF', 'HoH_OtherBenefitsSource']:
        temp.loc[temp[c] == 1, 'HoH_OtherIncomeCombined'] = '1'
    
    # Convert Number of Children by age to categories. Many numeric values are
    # sparse above 2 children.
    for c in ['Household_N_children0_3', 'Household_N_children3_5',
              'Household_N_children5_10', 'Household_N_children10_15', 
              'Household_N_children15_17']:
        temp.loc[temp[c] >= 2, c] = 2
        temp[c] = temp[c].astype(str)
        temp.loc[temp[c] == '2', c] = r'2+'
        
    # Cast some household as categorical
    for c in ['Household_Veteran', 'Household_Education',
              'Household_Employment', 'Household_PercentAMI',
              'Household_NonCashBenefitAnySource', 'Household_AvgInsurance',
              'Household_Pregnant', 'Household_DisablingConditionMax'
              ]:
        temp[c] = temp[c].astype(str)

    # Many Income and Benefits Categories are Sparse. Combine them into an
    # Other Group if any are present.
    temp['Household_OtherIncomeCombined'] = '0' 
    for c in ['Household_VADisabilityNonService',
              'Household_PrivateDisability', 'Household_WorkersComp',
              'Household_Pension', 'Household_Alimony', 'Household_WIC',
              'Household_TANFChildCare', 'Household_TANFTransportation',
               'Household_OtherTANF', 'Household_OtherBenefitsSource']:
        temp.loc[temp[c] == 1, 'Household_OtherIncomeCombined'] = '1'  
     
    # Remap similar sparse categories to the same bin
    for m in remap:
        temp[m] = temp[m].replace(remap[m])
    
    # Remove unneeded vars
    temp = temp.drop(columns=['CEHouseholdID', 'HoH_Age_DOB', 'HoH_PersonalID',
                              'HoH_EnrollmentID', 'HoH_RaceGroup',
                              'HoH_GenderGroup',
                              'HoH_UnemployedAndLookingForWork',
                              'HoH_EmployedAndLookingForWork',
                              'HoH_EmploymentTenure',
                              'HoH_VADisabilityNonService',
                              'HoH_PrivateDisability', 'HoH_WorkersComp',
                              'HoH_Pension', 'HoH_Alimony', 'HoH_WIC',
                              'HoH_TANFChildCare', 'HoH_TANFTransportaion',
                              'HoH_OtherTANF', 'HoH_OtherBenefitsSource',
                              'Household_EmploymentTenure',
                              'Household_DisablingConditionAvg',
                              'Household_VADisabilityNonService',
                              'Household_PrivateDisability',
                              'Household_WorkersComp', 'Household_Pension',
                              'Household_Alimony', 'Household_WIC', 
                              'Household_TANFChildCare',
                              'Household_TANFTransportation',
                              'Household_OtherTANF',
                              'Household_OtherBenefitsSource',
                              'Household_UnemployedAndLookingForWork',
                              'Household_EmployedAndLookingForWork',
                              'HoH_Age_days',
                              'HoH_DaysTo_RRH',
                              'HoH_DaysTo_TSH',
                              'HoH_DaysTo_PSH'
                              ])
    all_cat_vars = ['HoH_LengthOfStayName', 'HoH_RaceName', 'HoH_EthnicityName',
                    'HoH_GenderName', 'HoH_SexualOrientationName',
                    'HoH_VeteranStatusName', 'HoH_TimesHomelessPastThreeYearsName',
                    'HoH_LastGradeCompletedNameAtEntry', 'HoH_Employed',
                    'HoH_IncomeFromAnySource', 'HoH_HouseholdPercentofAMI',
                    'HoH_NonCashBenefitFromAnySource',
                    'HoH_CoveredByHealthInsurance', 'HoH_DisablingCondition',
                    'HoH_Pregnant', 'HoH_DomesticViolenceSurvivor',
                    'HoH_DomesticViolenceWhenOccurred',
                    'HoH_DomesticViolenceCurrentlyFleeing',
                    'HoH_PhysicalDisability', 'HoH_DevelopmentalDisability',
                    'HoH_ChronicHealthCondition', 'HoH_HIVAIDS', 'HoH_MentalHealth',
                    'HoH_SubstanceAbuse', 'HoH_Unemployment',
                    'HoH_SSI', 'HoH_SSDI', 'HoH_VADisabilityService', 'HoH_TANF',
                    'HoH_GA', 'HoH_SocSecRetirement', 'HoH_ChildSupport',
                    'HoH_SNAP', 'Household_N_children0_3',
                    'Household_N_children3_5', 'Household_N_children5_10',
                    'Household_N_children10_15', 'Household_N_children15_17',
                    'Household_Veteran', 'Household_Education',
                    'Household_Employment',
                    'Household_PercentAMI', 'Household_NonCashBenefitAnySource',
                    'Household_AvgInsurance', 'Household_Pregnant',
                    'Household_DisablingConditionMax',
                    'Household_DomesticViolenceSurvivor',
                    'Household_MostRecentDomsticViolence',
                    'Household_FleeingDomesticViolence',
                    'Household_PhysicalDisability',
                    'Household_DevelopmentalDisability',
                    'Household_ChronicHealthCondition', 'Household_HIVAIDS',
                    'Household_MentalHealthProblem', 'Household_SubstanceAbuse',
                    'Household_Unemployment', 'Household_SSI',
                    'Household_SSDI', 'Household_VADisabilityService',
                    'Household_TANF',
                    'Household_GA', 'Household_SocSecRetirement',
                    'Household_ChildSupport',
                    'Household_SNAP',
                    'Household_OtherIncomeCombined', 'HoH_OtherIncomeCombined']
    for c in all_cat_vars:
        temp[c] = temp[c].astype(str)

    temp.loc[temp['Household_MostRecentDomsticViolence'] =='nan', 'Household_MostRecentDomsticViolence'] = '0.0'
    return temp

adf = cleanvarsbyrow(temp=adf)

# #############################################################################
# Get "Intervention Dates"

# intdates = adf.copy()
# intdates = intdates.loc[~intdates['MoveInDate'].isna(),['RRH', 'TSH', 'PSH',
#                                                         'RRH_Entry', 'TSH_Entry',
#                                                         'PSH_Entry', 
#                                                         'RRH_Exit', 'TSH_Exit',
#                                                         'PSH_Exit','MoveInDate']].copy()
# rrhdf = pd.DataFrame(intdates['RRH_Entry'])
# rrhdf = rrhdf.dropna()
# rrhdf['ProjectTypeName'] = 'PH - Rapid Re-Housing' 
# rrhdf = rrhdf.rename(columns={'RRH_Entry': 'EnrollmentDate'})

# pshdf = pd.DataFrame(intdates['PSH_Entry'])
# pshdf = pshdf.dropna()
# pshdf['ProjectTypeName'] = 'PH - Permanent Supportive Housing' 
# pshdf = pshdf.rename(columns={'PSH_Entry': 'EnrollmentDate'})

# tshdf = pd.DataFrame(intdates['TSH_Entry'])
# tshdf = tshdf.dropna()
# tshdf['ProjectTypeName'] = 'Transitional Housing' 
# tshdf = tshdf.rename(columns={'TSH_Entry': 'EnrollmentDate'})

# interdates = pd.concat([rrhdf, pshdf, tshdf])
# interdates.to_csv(r'..\..\Code\prioritization\Exploratory\Archive\InterventionData_04182024.csv',
#                   index=False)

##############################################################################
# Train Test Split, sample at the PersonalID level to handle the panel
# structure of the data.
def traintestsplitpanel(temp, panelid='PersonalID', tsplit=0.8, seed=0):
    temp = temp.sort_values(panelid)
    pid = list(temp[panelid].unique())
    nids = len(pid)
    ntrain = round(nids*tsplit, 0)
    np.random.seed(seed)
    rval = np.random.uniform(0, 1, size = nids)
    iddf = pd.DataFrame({'PID': pid, 'Rval': rval})
    iddf = iddf.sort_values('Rval')
    iddf = iddf.reset_index(drop=True)
    trainlist = iddf.loc[0:ntrain, 'PID'].to_list()
    testlist = iddf.loc[ntrain+1:, 'PID'].to_list()
    return trainlist, testlist


trainlist, testlist = traintestsplitpanel(temp=adf, panelid='PersonalID',
                                          tsplit=0.8, seed=0)

traindf = adf.loc[adf['PersonalID'].isin(trainlist),].copy()
traindf = traindf.reset_index(drop =True)

testdf = adf.loc[adf['PersonalID'].isin(testlist),].copy()
testdf = testdf.reset_index(drop =True)



###############################################################################
# Save list results
###############################################################################

with open(dpath + r'\\components\\trainlistpid'+ f'_{today}.pkl', 'wb') as f:
    pickle.dump(trainlist, f)    

with open(dpath + r'\\components\\testlistpid'+ f'_{today}.pkl', 'wb') as f:
    pickle.dump(testlist, f)    

# Output Results
traindf.to_pickle(dpath + r'\\traindf' + f'_{today}.pkl')
traindf.to_csv(dpath + r'\\traindf' + f'_{today}.csv')

testdf.to_pickle(dpath + r'\\testdf' + f'_{today}.pkl')

