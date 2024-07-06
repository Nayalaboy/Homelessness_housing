# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 11:11:12 2024

@author: Trevor Gratz, trevormgratz@gmail.com

This file trains the best performing model using the training data set and 
generate preditions for the testing data. Performance metrics are recorded.
Next training and testing are stacked, the random forest model is retrained,
and individual household probabilties of exit are generated. The optimizatoin
dataset is created. 
"""

import sys
sys.path.append('../')
from Build.Dictionaries import X_hoh_WOE, X_house_WOE, X_all_WOE, X_all_OHE
from Build.Dictionaries import ywoexmatch
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score, precision_score, recall_score
from copy import deepcopy
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectFromModel
from sklearn.preprocessing import StandardScaler

import random
from datetime import timedelta

dpath = r'..\..\..\Data'
mpath = r'..\..\..\Output\models'

testdf = pd.read_csv(r'..\..\..\Data\test_allfeatures__2024-04-01.csv')
traindf = pd.read_csv(r'..\..\..\Data\train_allfeatures__2024-03-18.csv')


clfrf = RandomForestClassifier(max_depth=None,
                               n_estimators = 300,
                               max_features= 4,
                               min_samples_leaf = 5,
                               min_samples_split = 4,
                               random_state=0)

#############################################################################
# Train

X_subset = X_house_WOE
yvar = 'success_180'
df = traindf.copy()
df = df.loc[~df[yvar].isna(),].copy()
y = df[yvar]

# Get X Variables
X_subset = ywoexmatch(yval=yvar, xlist=X_subset)
tempx = df[X_subset]
# temp = StandardScaler().fit_transform(tempx)
# tempx = pd.DataFrame(temp, columns =tempx.columns)

# Feature Selection
selector = SelectFromModel(
               estimator=LogisticRegression(C=1,
                   penalty='l1',solver='liblinear')).fit(tempx, y)
selector.estimator_.coef_
retaincols = selector.get_feature_names_out()
tempx_select = tempx[retaincols].copy()

clfrf.fit(tempx_select,y)

##############################################################################
# Prep Testing Data
X_test = testdf[retaincols].copy()
y_test = testdf[yvar].copy()
y_test_pred = clfrf.predict(X_test)

# Perfomance Metrics
conf_mat_test = confusion_matrix(y_test, y_test_pred)
acc = (y_test == y_test_pred).mean()
auc = roc_auc_score(y_test, clfrf.predict_proba(X_test)[:,1])
precision_score(y_test, y_test_pred)
recall_score(y_test, y_test_pred)

##############################################################################
# Concatenate data and train on full data
X_all = pd.concat([tempx_select, X_test])
X_all = X_all.reset_index(drop=True)

y_all = pd.concat([y, y_test])
y_all = y_all.reset_index(drop=True)

clfrf_all = RandomForestClassifier(max_depth=None,
                                   n_estimators = 300,
                                   max_features= 4,
                                   min_samples_leaf = 5,
                                   min_samples_split = 4,
                                   random_state=0)
clfrf_all.fit(X_all, y_all)

##############################################################################
# Use fully trained model to generate predicted probabilits of exits 

def genp(xs, ys, clfrf, tx='RRH'):
    '''
    Construct the probability of exiting homelessness based on the housing
    intervention. 
    '''
    xs['RRH'] = 0
    xs['TSH'] = 0
    xs['PSH'] = 0
    if tx != 'NoTx':
        xs[tx] = 1
    y_1 = clfrf.predict_proba(xs)[:, 1]
    pval = y_1.reshape(len(y_1), 1)
    return pval

# Predicted probabilities
p_notx = genp(xs=X_all.copy(), ys=y_all.copy(), clfrf=deepcopy(clfrf_all), tx='NoTx')
p_tsh = genp(xs=X_all.copy(), ys=y_all.copy(), clfrf=deepcopy(clfrf_all), tx='TSH')
p_psh = genp(xs=X_all.copy(), ys=y_all.copy(), clfrf=deepcopy(clfrf_all), tx='PSH')
p_rrh = genp(xs=X_all.copy(), ys=y_all.copy(), clfrf=deepcopy(clfrf_all), tx='RRH')

diffps = pd.concat([pd.Series(p_rrh[:, 0]),
                    pd.Series(p_tsh[:, 0]),
                    pd.Series(p_psh[:, 0]),
                    pd.Series(p_notx[:, 0])],
                   axis=1) 
diffps = diffps.rename(columns={0: 'P_RRH',
                                1: 'P_TSH',
                                2: 'P_PSH',
                                3: 'P_NOTX'})
diffps = diffps.reset_index(drop=True)

##############################################################################
# Build Optimization Dataset

# Stack training and testing
traindfnotransform = pd.read_pickle(dpath + r'\traindf_2024-03-07.pkl')
testdfnotransform = pd.read_pickle(dpath + r'\testdf_2024-03-07.pkl')
piddf = pd.concat([traindf[['PersonalID']], traindfnotransform[['start_date', 'end_date', 'HoH_GenderName']]], axis=1)
piddftest = pd.concat([testdf[['PersonalID']], testdfnotransform[['start_date', 'end_date', 'HoH_GenderName']]], axis=1)
piddf = pd.concat([piddf, piddftest])
piddf = piddf.reset_index(drop=True)

# Add in predicted proabalities
piddf = pd.concat([piddf, diffps], axis=1)

# Create fake IDS
newid = piddf[['PersonalID']].copy()
newid = newid.drop_duplicates()
newid = newid.sample(frac = 1, random_state=0)
newid = newid.reset_index(drop=True)
newid = newid.reset_index()
newid = newid.rename(columns={'index': 'ID'})

piddf = pd.merge(piddf, newid, on='PersonalID')


# Add a slight date jitter.
np.random.seed(1)
jitter = [random.randint(-3,3) for i in range(len(piddf)) ]
piddf["start_date"] =pd.to_datetime(piddf["start_date"]) + pd.to_timedelta(pd.Series(jitter), unit='D')
piddf["end_date"] =pd.to_datetime(piddf["end_date"]) + pd.to_timedelta(pd.Series(jitter), unit='D')

# Prepare for export
outdf = piddf.drop(columns='PersonalID')
outdf = outdf.rename(columns = {'start_date':'intervention_eligibility_start',
                                'end_date': 'intervention_eligibility_end', 
                                'HoH_GenderName': 'subpopulation'
                                })
outdf = outdf.loc[outdf['subpopulation'] != 'Other_Missing', ].copy()
outdf['subpopulation'] = (outdf['subpopulation'] == 'Woman (Girl, if child)').astype(int)
outdf = outdf[['ID', 'intervention_eligibility_start', 'intervention_eligibility_end',
               'subpopulation', 'P_RRH', 'P_TSH', 'P_PSH', 'P_NOTX']]
outdf.to_csv(r'..\..\..\Data\OptimizationData_04012024.csv')


