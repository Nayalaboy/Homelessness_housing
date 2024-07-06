# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 13:12:12 2024

@author: Trevor Gratz, trevormgratz@gmail.com

This file loads the training and testing data set aside in the 
"BuildAnalyticDataSet_02142024.py" file and performs feature scaling 
and encoding based on the training data values.

"""
import pandas as pd
import numpy as np
from datetime import date
import pickle
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import category_encoders as ce

##############################################################################
# Globals
##############################################################################
today = date.today()
dpath = r'..\..\..\Data'

all_cont_vars = ['HoH_AgeAtEntry', 'HoH_EmployedHoursWorkedLastWeek',
                 'AverageLHEventsInPast12Months',
                 'AverageLHEventsInPast6Months',
                 'Household_IncomeEarnedEntry',
                 'Household_IncomeNonEarnedEntry',
                 'N_Household', 'Household_N_Children',
                 'Household_OldestClient',
                 'Household_YoungestClient', 'Household_HoursWorked',
                 'ln_HoH_EmployedHoursWorkedLastWeek',
                 'ln_AverageLHEventsInPast12Months',
                 'ln_N_Household', 'ln_Household_N_Children',
                 'ln_rmout_AverageLHEventsInPast12Months',
                 'ln_rmout_HoH_EmployedHoursWorkedLastWeek']


hoh_cont_vars = ['HoH_AgeAtEntry', 'HoH_EmployedHoursWorkedLastWeek',
                 'AverageLHEventsInPast12Months',
                 'AverageLHEventsInPast6Months',        
                 'N_Household', 'Household_N_Children',
                 'ln_HoH_EmployedHoursWorkedLastWeek',
                 'ln_AverageLHEventsInPast12Months',
                 'ln_N_Household', 'ln_Household_N_Children',
                 'ln_rmout_AverageLHEventsInPast12Months',
                 'ln_rmout_HoH_EmployedHoursWorkedLastWeek']

household_cont_vars = ['AverageLHEventsInPast12Months',
                       'AverageLHEventsInPast6Months',
                       'Household_IncomeEarnedEntry',
                       'Household_IncomeNonEarnedEntry',
                       'N_Household', 'Household_N_Children',
                       'Household_OldestClient',
                       'Household_YoungestClient', 'Household_HoursWorked',
                       'ln_HoH_EmployedHoursWorkedLastWeek',
                       'ln_AverageLHEventsInPast12Months',
                       'ln_N_Household', 'ln_Household_N_Children',
                       'ln_rmout_AverageLHEventsInPast12Months',
                       'ln_rmout_HoH_EmployedHoursWorkedLastWeek']

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

hoh_cat_vars = ['HoH_LengthOfStayName', 'HoH_RaceName', 'HoH_EthnicityName',
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
                'HoH_OtherIncomeCombined']
    
household_cat_vars = ['HoH_LengthOfStayName', 'HoH_RaceName',
                      'HoH_EthnicityName',
                      'HoH_GenderName', 'HoH_SexualOrientationName',
                      'HoH_TimesHomelessPastThreeYearsName',
                      'HoH_SNAP', 'Household_N_children0_3',
                      'Household_N_children3_5', 'Household_N_children5_10',
                      'Household_N_children10_15',
                      'Household_N_children15_17',
                      'Household_Veteran', 'Household_Education',
                      'Household_Employment',
                      'Household_PercentAMI',
                      'Household_NonCashBenefitAnySource',
                      'Household_AvgInsurance', 'Household_Pregnant',
                      'Household_DisablingConditionMax',
                      'Household_DomesticViolenceSurvivor',
                      'Household_MostRecentDomsticViolence',
                      'Household_FleeingDomesticViolence',
                      'Household_PhysicalDisability',
                      'Household_DevelopmentalDisability',
                      'Household_ChronicHealthCondition', 'Household_HIVAIDS',
                      'Household_MentalHealthProblem',
                      'Household_SubstanceAbuse',
                      'Household_Unemployment', 'Household_SSI',
                      'Household_SSDI', 'Household_VADisabilityService',
                      'Household_TANF',
                      'Household_GA', 'Household_SocSecRetirement',
                      'Household_ChildSupport',
                      'Household_SNAP',
                      'Household_OtherIncomeCombined']

keepvars = ['PersonalID', 'success_730', 'success_365', 'success_180',
            'success_noexit_730', 'success_noexit_365', 'success_noexit_180',
            'RRH', 'TSH', 'PSH', 'HoH_RRH_Month_1',
            'HoH_RRH_Month_2', 'HoH_RRH_Month_3plus', 'HoH_TSH_Month_1',
            'HoH_TSH_Month_2', 'HoH_TSH_Month_3plus', 'HoH_PSH_Month_1',
            'HoH_PSH_Month_2', 'HoH_PSH_Month_3plus']

##############################################################################
# Load Training data
##############################################################################

traindf = pd.read_pickle(dpath + r'\traindf_2024-03-07.pkl')
testdf = pd.read_pickle(dpath + r'\testdf_2024-03-07.pkl')

##############################################################################
# Create Encoders and Save them
##############################################################################
def encodesave(temp, c):
    
    # Fit
    enc = OneHotEncoder()
    enc.fit(temp[c].values.reshape(-1, 1))
    
    # Save
    epath = dpath + r'\\components\\Encoder'+ f'_{c}.pkl'
    with open(epath, 'wb') as f:
        pickle.dump(enc, f)
        
    # Given a column c and the correct encoder then transform the data with
    # enc.transform(temp[[c]].to_numpy())
    
  
def WOEencodesave(temp, c, y):
    temp = temp.loc[~temp[y].isna(),]
    woe = ce.WOEEncoder()
    woe.fit(temp[c], temp[y])
    
    # Save
    epath = dpath + r'\\components\\WOEEncoder'+ f'_{y}_{c}.pkl'
    with open(epath, 'wb') as f:
        pickle.dump(woe, f)
    
    
for c in all_cat_vars:
    encodesave(temp=traindf, c=c)
    for y in ['success_730', 'success_365', 'success_180',
              'success_noexit_730', 'success_noexit_365',
              'success_noexit_180']:
        WOEencodesave(temp=traindf.copy(), c=c, y=y)

###############################################################################
# Get imputers
###############################################################################
# The majority of continous data with missing values assumes that the missing
# values are 0 e.b. hours worked last week. However, some variables such
# as the age variables need to be imputed. This is a small subset for each 
# variable (<10), so simple imputers should work fine.

def trainimputer(temp):
    '''

    Parameters
    ----------
    temp : TYPE Pandas Dataframe
        DESCRIPTION.

    Returns
    -------
    imputertuple : Tupe
        DESCRIPTION. Columns in order, Trained median imputer

    '''
    
    imputer = SimpleImputer(strategy='median')
    imputer.fit(temp)
    imputertuple = (temp.columns, imputer)

    # Save it
    with open(dpath + r'\\components\\ImputerTuple'+ f'_{today}.pkl', 'wb') as f:
        pickle.dump(imputertuple, f)
        
    return imputertuple

def transformimputer(temp, imputertuple):
    '''
    

    Parameters
    ----------
    temp : TYPE Pandas Data frame
        DESCRIPTION.
    imputertuple : Tuple containing the column names to impute on and the 
                   imputation object.
        DESCRIPTION.

    Returns
    -------
    tempdf : TYPE Pandas data frame
        DESCRIPTION.

    '''
    
    X_imputed = imputertuple[1].transform(temp[imputertuple[0]])
    tempdf = pd.DataFrame(data=X_imputed, columns=imputertuple[0])
    return tempdf

# Train and Save the Imputer
imputertuple = trainimputer(temp=traindf[['HoH_AgeAtEntry',
                                          'Household_YoungestClient',
                                          'Household_OldestClient']])
# Apply
trainximputed = transformimputer(temp=traindf[['HoH_AgeAtEntry',
                                               'Household_YoungestClient',
                                               'Household_OldestClient']],
                                 imputertuple=imputertuple)

testximputed = transformimputer(temp=testdf[['HoH_AgeAtEntry',
                                             'Household_YoungestClient',
                                             'Household_OldestClient']],
                                 imputertuple=imputertuple)

# Replace original data
for c in imputertuple[0]:
   # Check order SimpleImputer Returns data in
   #print((traindf[c].reset_index(drop=True) != trainximputed[c].reset_index(drop=True)).sum())    
   traindf[c] = trainximputed[c]
   testdf[c] = testximputed[c]

##############################################################################
# Get Scalers for continuous data
##############################################################################

def scalesave(temp, c):
    
    # Fit
    scalar = StandardScaler()
    scalar.fit(temp[c].values.reshape(-1, 1))
    
    # Save
    spath = dpath + r'\\components\\Scaler'+ f'_{c}.pkl'
    with open(spath, 'wb') as f:
        pickle.dump(scalar, f)
        
for c in all_cont_vars:
    scalesave(temp=traindf, c=c)
    
##############################################################################
# Apply Transformations to Testing
##############################################################################

# testximputed = transformimputer(temp=testdf[['HoH_AgeAtEntry',
#                                                'Household_YoungestClient',
#                                                'Household_OldestClient']],
#                                  imputertuple=imputertuple)

# # Replace original data
# for c in imputertuple[0]:
#    # Check order SimpleImputer Returns data in
#    #print((testdf[c].reset_index(drop=True) != testximputed[c].reset_index(drop=True)).sum())    
#    testdf[c] = testximputed[c]
   


##############################################################################
# Build versions of the X, y data fully processed for modelling
##############################################################################

def buildXY(temp, keeplist=[], catlist=[], contlist=[], catencodtype = 'OneHot'):
    '''
    The function takes data from in the format produced from the 
    'BuildAnalyticDataSet_02122024.py' file, lets the user select the 
    variables desired for analysis, and transforms the dataset using 
    stored one hot encoders and standard scalars. Ideally, this function can
    be used when we get new draws of the data.

    Parameters
    ----------
    temp : TYPE Pandas DataFrame
        DESCRIPTION. Dataset from BuildAnalyticDataSet_02122024.py
    keeplist : TYPE, list optional
        DESCRIPTION. A list of variables to leave as is i.e. do not apply any
                     transformation. For example, this should have the 0/1 
                     treatement and outcome indicators in it, but there may be
                     other variables, such as PersonalID, which will be used
                     in constructin Group-k folds. The default is [].
    catlist : TYPE, list optional
        DESCRIPTION. List of categorical variables. These must be categorical
                     variables that have had a One Hot Encoder stored. 
                     The default is [].
    contlist : TYPE, List of continous variables. These must be continuous
                 variables that have had a standard scalar stored. 
                 The default is [].
    Returns
    -------
    X : TYPE
        DESCRIPTION. Output Dataframe ready for ML models.

    '''
    # Coninous Variables Present
    if contlist:
        # Variables present to keep as is
        if keeplist:
            # Initialize
            X = temp[keeplist]
            # Take data for each continous variable and apply the appropriate
            # scaler
            for c in contlist:
                spath = dpath + r'\\components\\Scaler' + f'_{c}.pkl'
                scaler = pickle.load(open(spath, 'rb'))
                look = pd.DataFrame(scaler.transform(temp[[c]].to_numpy()),
                                    columns=[c])
                X = pd.concat([X, look], axis=1)
        else:
            # Similar, but no variables to keep as is.
            X = pd.DataFrame()
            for c in contlist:
                spath = dpath + r'\\components\\Scaler' + f'_{c}.pkl'
                scaler = pickle.load(open(spath, 'rb'))
                look = pd.DataFrame(scaler.transform(temp[[c]].to_numpy()).toarray(),
                                    columns=c)
                X = pd.concat([X, look], axis=1)
    else:
        if keeplist:
            X = temp[keeplist]
        else:
            X = pd.DataFrame()

    # Given the list of categorical variables, pull in the matching encoder,
    # encode the categorical data, and concatenate to X.
    if catlist:
        for c in catlist:
            
            # One Hot Encoding
            epath = dpath + r'\\components\\Encoder' + f'_{c}.pkl'
            enc = pickle.load(open(epath, 'rb'))
            
            # Unfortunately, these encoders were built with sklearn 1.2.2, 
            # will need to downgrade version to use.
            cols = list(enc.get_feature_names_out([c]))
            look = pd.DataFrame(enc.transform(temp[[c]].to_numpy()).toarray(),
                                columns=cols)
            X = pd.concat([X, look], axis=1)

            # WOE Encoding
            for y in ['success_730', 'success_365', 'success_180',
                      'success_noexit_730', 'success_noexit_365',
                      'success_noexit_180']:
                epath = dpath + r'\\components\\WOEEncoder' + f'_{y}_{c}.pkl'
                woe = pickle.load(open(epath, 'rb'))
                look = woe.transform(temp[[c]])
                look = look.rename(columns={f'{c}': f'woe_{y}_{c}'})
                X = pd.concat([X, look], axis=1)

    return X

##############################################################################
# Build Datasets

# The head of household and household variables are highely correlated. For
# this reason we will build three seperate datasets:

# 1) Build a dataset with all chosen features.
# 2) Build a dataset with all chosen features taken from the HoH when possible
# 3) Build a dataset with all chosen features aggregated from the household 
#    when possible.

# Note, that this says when possible. In many instances, it may not make sense
# or be possible to construct a dataset from the head of the household
# (e.g. number in family) or aggregage up from the household (e.g. race). 


fulldf = buildXY(temp=traindf, keeplist=keepvars,
                 catlist=all_cat_vars,
                 contlist=all_cont_vars)

fulltestdf = buildXY(temp=testdf, keeplist=keepvars,
                 catlist=all_cat_vars,
                 contlist=all_cont_vars)


hohdf = buildXY(temp=traindf, keeplist=keepvars,
                catlist=hoh_cat_vars,
                contlist=hoh_cont_vars)

householddf = buildXY(temp=traindf, keeplist=keepvars,
                      catlist=household_cat_vars,
                      contlist=household_cont_vars)

# Output
fullpath = dpath + r'\\train_allfeatures_'+ f'_{today}.csv'
fulltestpath = dpath + r'\\test_allfeatures_'+ f'_{today}.csv'

hohpath = dpath + r'\\train_hohfeatures_'+ f'_{today}.csv'
householdpath = dpath + r'\\train_householdfeatures_'+ f'_{today}.csv'

fulldf.to_csv(fullpath)
fulltestdf.to_csv(fulltestpath)

hohdf.to_csv(hohpath)
householddf.to_csv(householdpath)
