# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 14:38:23 2024

@author: Trevor Gratz, trevormgratz@gmail.com

This file explores the performance of the top performing models found during
training. It then builds the conditional average treatement effects for some of 
the models. The code makes the plots for the conditional average treatment
effect kernel density plots.
"""

import sys
sys.path.append('../')
import scipy.sparse.linalg
from Build.Dictionaries import X_hoh_WOE, X_house_WOE, X_all_WOE, X_all_OHE
from Build.Dictionaries import ywoexmatch
import pickle
import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, cross_val_score
from sklearn.metrics import confusion_matrix
from copy import deepcopy
from sklearn.neighbors import KernelDensity
from matplotlib import pyplot as plt
import numpy as np
from Build.Dictionaries import ywoexmatch
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectFromModel, mutual_info_classif
from sklearn.preprocessing import StandardScaler



dpath = r'..\..\..\Data'
mpath = r'..\..\..\Output\models'

alldf = pd.read_csv(dpath + r'\train_allfeatures__2024-03-18.csv')
# Used for remapping the encoders
traindf = pd.read_pickle(dpath + r'\traindf_2024-03-07.pkl')

##############################################################################
# Helper Functions

# Construct the counterfactuals
def evalcounter(xs, ys, clfrf, tx='RRH'):
    '''
    Construct the differences in probability of exiting homelessness based on
    whether a household was or wasn't assigned a housing intervetnion.
    '''
    xs['RRH'] = 0
    xs['TSH'] = 0
    xs['PSH'] = 0
    y_0 = clfrf.predict_proba(xs)[:, 1]
    xs[tx] = 1
    y_1 = clfrf.predict_proba(xs)[:, 1]
    diff = (y_1 - y_0).reshape(len(y_1), 1)
    return diff

# Plot functions
def kdeprotectedclass(var, pdiff,  tempdf, rmcats='', title='', axval=0):
    '''
    This function plots kernel density plots of the difference in probability
    of exiting homelessness when assigned a treatment. It plots the KDE plot
    by levels of another variable, and for this code that other variable should
    be a protected class. 
    var = variable that contains protected class labels
    pdiff = difference in probabilities
    tempdf = dataframe with protected class info
    rmcats = a string for removing a level within the protected class variable.
             sometimes we don't need to plot the other/missing category
             
    IMPORTANT: pdiff and tempdf must be in order, that is the difference in 
               probabilities correspond to the rows in tempdf.
    '''
    levels = [v for v in tempdf[var].unique() if v not in rmcats]
    
    for l in levels :
        abool = tempdf[var] == l
        kde = KernelDensity( kernel='gaussian', bandwidth=0.03).fit(pdiff[abool])
        log_dens = kde.score_samples(X_plot)
        ax[axval].plot(X_plot[:, 0], np.exp(log_dens), label=l)

    ax[axval].legend(frameon=False)
    ax[axval].spines['top'].set_visible(False)
    ax[axval].spines['right'].set_visible(False)
    ax[axval].set_xlabel('Change in Probability')
    ax[axval].set_title(title)

def remapencoder(xvar, yvar, origdf, currdf):
    '''
    Frustratingly the WOE encoder doesn't have an inverse transform like the
    other encoders in this library. Therfore, we take the orgicinal data,
    encode it and map the encoded values back to the original ones. We then
    use this mapping to reverse the mapping for our current dataset.
    '''
    epath = dpath + r'\\components\\WOEEncoder'+ f'_{yvar}_{xvar}.pkl'
    enc = pickle.load(open(epath, "rb"))
    origdf[xvar+'_tranform'] = enc.transform(origdf[xvar])
    mapdf = origdf[[xvar+'_tranform', xvar]].drop_duplicates()
    area_dict = dict(zip(mapdf[xvar+'_tranform'], mapdf[xvar]))
    
    # Rounding means we can't do a replace
    for k, v in area_dict.items():
        currdf.loc[abs(currdf[f'woe_{yvar}_{xvar}'] - k) < 0.01, 
                   'Mapped'] = v
    return currdf['Mapped']

##############################################################################
# EDA - Mutual Information
midf = alldf[X_all_OHE].copy()
cvars = ['HoH_AgeAtEntry', 'ln_rmout_HoH_EmployedHoursWorkedLastWeek',
         'ln_rmout_AverageLHEventsInPast12Months', 'ln_N_Household']

discf = [True if i not in cvars else False for i in midf.columns]
y = alldf['success_180']
mi = mutual_info_classif(midf, y, discrete_features=discf)
fnames = midf.columns
midf = pd.DataFrame({'Names': fnames, 'Mutual Information': mi})

##############################################################################
# Establish the top performing models when the exit statis is and isn't used.
clfrf = RandomForestClassifier(max_depth=None,
                               n_estimators = 300,
                               max_features= 4,
                               min_samples_leaf = 5,
                               min_samples_split = 4,
                               random_state=0)

clflg = LogisticRegression(max_iter=1000,
                           solver='saga', C=0.37, l1_ratio=0.0611111111111111,
                           penalty='elasticnet',
                           random_state=0)

clfrfnx = RandomForestClassifier(max_depth=None,
                                 n_estimators = 500,
                                 max_features= 3,
                                 min_samples_leaf = 2,
                                 min_samples_split = 2,
                                 random_state=0)

clflgnx = LogisticRegression(max_iter=1000,
                             solver='saga', C=0.046, l1_ratio=0,
                             penalty='elasticnet',
                             random_state=0)
###############################################################################
# Exit status model build
# Prep variables
X_subset = X_house_WOE
yvar = 'success_180'
df = alldf.copy()
df = df.loc[~df[yvar].isna(),].copy()
y = df[yvar]

# Get X Variables
X_subset = ywoexmatch(yval=yvar, xlist=X_subset)
tempx = df[X_subset]

# Feature Selection
selector = SelectFromModel(
               estimator=LogisticRegression(C=1,
                   penalty='l1',solver='liblinear')).fit(tempx, y)
selector.estimator_.coef_
retaincols = selector.get_feature_names_out()
tempx_select = tempx[retaincols].copy()

cols_notx = retaincols.tolist().copy()
cols_notx.remove('RRH')
cols_notx.remove('TSH')
cols_notx.remove('PSH')
tempx_select_notx = tempx[cols_notx].copy()

# EDA - Mutual Information Before Models
discf = [True if i in ['RRH', 'TSH', 'PSH'] else False for i in tempx_select.columns]
mi = mutual_info_classif(tempx_select, y, discrete_features=discf)
fnames = tempx_select.columns
midf = pd.DataFrame({'Names': fnames, 'Mutual Information': mi})

############################################################################
# No Exit Model Build
X_subsetnx = X_hoh_WOE
yvarnx = 'success_noexit_730'
dfnx = alldf.copy()
dfnx = dfnx.loc[~dfnx[yvarnx].isna(),].copy()
ynx = dfnx[yvarnx]


# Get X Variables
X_subsetnx = ywoexmatch(yval=yvarnx, xlist=X_subsetnx)
tempxnx = dfnx[X_subsetnx]


# Feature Selection
selectornx = SelectFromModel(
               estimator=LogisticRegression(C=1,
               penalty='l1',solver='liblinear')).fit(tempxnx, ynx)
selectornx.estimator_.coef_
retaincolsnx = selectornx.get_feature_names_out()
tempx_selectnx = tempxnx[retaincolsnx].copy()

#############################################################################
# Evaluation of performance
np.random.seed(0)

# Random Forest
y_pred_rfc = cross_val_predict(clfrf, tempx_select, y, cv=5)
conf_mat_rfc = confusion_matrix(y, y_pred_rfc)

cross_val_score(clfrf, tempx_select, y, scoring='roc_auc', cv=5).mean()
cross_val_score(clfrf, tempx_select, y, scoring='accuracy', cv=5).mean()
cross_val_score(clfrf, tempx_select, y, scoring='precision', cv=5).mean()
cross_val_score(clfrf, tempx_select, y, scoring='recall', cv=5).mean()
cross_val_score(clfrf, tempx_select, y, scoring='f1', cv=5).mean()

# Elastic Net
y_pred_lg = cross_val_predict(clflg, tempx_select, y, cv=5)
conf_mat_lg = confusion_matrix(y, y_pred_lg)

cross_val_score(clflg, tempx_select, y, scoring='roc_auc', cv=5).mean()
cross_val_score(clflg, tempx_select, y, scoring='accuracy', cv=5).mean()
cross_val_score(clflg, tempx_select, y, scoring='precision', cv=5).mean()
cross_val_score(clflg, tempx_select, y, scoring='recall', cv=5).mean()
cross_val_score(clflg, tempx_select, y, scoring='f1', cv=5).mean()

# Random Forest, No Exit Destination
y_pred_rfcnx = cross_val_predict(clfrfnx, tempx_selectnx, ynx, cv=5)
conf_mat_rfcnx = confusion_matrix(ynx, y_pred_rfcnx)

cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='roc_auc', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='accuracy', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='precision', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='recall', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='f1', cv=5).mean()


# Elastic Net, No Exit Destination
y_pred_lgnx = cross_val_predict(clflgnx, tempx_selectnx, ynx, cv=5)
conf_mat_rfcnx = confusion_matrix(ynx, y_pred_rfcnx)

cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='roc_auc', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='accuracy', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='precision', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='recall', cv=5).mean()
cross_val_score(clfrfnx, tempx_selectnx, ynx, scoring='f1', cv=5).mean()

# Evaluation without TX
y_pred_rfc_notx = cross_val_predict(clfrf, tempx_select_notx, y, cv=5)
conf_mat_rfc_notx = confusion_matrix(y, y_pred_rfc_notx)

y_pred_lg_notx = cross_val_predict(clflg, tempx_select_notx, y, cv=5)
conf_mat_lg_notx = confusion_matrix(y, y_pred_lg_notx)

#############################################################################
# Feature Importance and Coefficients

# Fit the model
clfrf.fit(tempx_select,y)
clflg.fit(tempx_select,y)
clfrfnx.fit(tempx_selectnx, ynx)

coefs = clflg.coef_.flatten()
fnames = tempx.columns
lgcoefs = pd.DataFrame({'Names': fnames, 'Coefficients': coefs})

# Importance for models without tx
clfrfnotx = RandomForestClassifier(max_depth=None,
                               n_estimators = 300,
                               max_features= 4,
                               min_samples_leaf = 5,
                               min_samples_split = 4,
                               random_state=0)

clflgnotx = LogisticRegression(max_iter=1000,
                           solver='saga', C=0.37, l1_ratio=0.0611111111111111,
                           penalty='elasticnet',
                           random_state=0)

clfrfnotx.fit(tempx_select_notx,y)
clflgnotx.fit(tempx_select_notx,y)

importances = clfrfnotx.feature_importances_
fnames = tempx_select_notx.columns
featimpdf = pd.DataFrame({'Names': fnames, 'Importance': importances})

coefs = clflgnotx.coef_.flatten()
fnames = tempx_select_notx.columns
lgcoefs = pd.DataFrame({'Names': fnames, 'Abs Coefficients': abs(coefs)})

#############################################################################
# Error Analysis
y_pred_rfc = clfrf.predict(tempx_select)
y_pred_lg = clflg.predict(tempx_select)

fnrf = ((y == 1) & (y_pred_rfc == 0))
fprf = ((y == 0) & (y_pred_rfc == 1))
tprf = ((y == 1) & (y_pred_rfc == 1))
tnrf = ((y == 0) & (y_pred_rfc == 0))

fndfrf = tempx.loc[fnrf,]
fpdfrf = tempx.loc[fprf,]
tndfrf = tempx.loc[tnrf,]
tpdfrf = tempx.loc[tprf,]
(fndfrf[['RRH', 'TSH', 'PSH']].sum(axis=1)>=1).mean()
(fndfrf[['RRH']].sum(axis=1)>=1).mean()
erroranalysisrf = pd.concat([fndfrf.mean(), fpdfrf.mean(), tndfrf.mean(),
                             tpdfrf.mean()],
                          axis=1)
erroranalysisrf.columns = ['False Negative', 'False Positive',
                           'True Negative', 'True Positive']


fnlg = ((y == 1) & (y_pred_lg == 0))
fplg = ((y == 0) & (y_pred_lg == 1))
tplg = ((y == 1) & (y_pred_lg == 1))
tnlg = ((y == 0) & (y_pred_lg == 0))

fndflg = tempx.loc[fnlg,]
fpdflg = tempx.loc[fplg,]
tndflg = tempx.loc[tnlg,]
tpdflg = tempx.loc[tplg,]

erroranalysislg = pd.concat([fndflg.mean(), fpdflg.mean(), tndflg.mean(),
                             tpdflg.mean()],
                          axis=1)
erroranalysislg.columns = ['False Negative', 'False Positive',
                           'True Negative', 'True Positive']


###############################################################################
# Construct the Counterfactuals
# Probability of exit by whether or not a household was assigned a housing
# intervention
diff_tsh = evalcounter(xs=tempx_select.copy(), ys=y.copy(), clfrf=deepcopy(clfrf), tx='TSH')
diff_psh = evalcounter(xs=tempx_select.copy(), ys=y.copy(), clfrf=deepcopy(clfrf), tx='PSH')
diff_rrh = evalcounter(xs=tempx_select.copy(), ys=y.copy(), clfrf=deepcopy(clfrf), tx='RRH')

diff_tsh_lg = evalcounter(xs=tempx_select.copy(), ys=y.copy(), clfrf=deepcopy(clflg), tx='TSH')
diff_psh_lg = evalcounter(xs=tempx_select.copy(), ys=y.copy(), clfrf=deepcopy(clflg), tx='PSH')
diff_rrh_lg = evalcounter(xs=tempx_select.copy(), ys=y.copy(), clfrf=deepcopy(clflg), tx='RRH')


# KDE Plot  of the interventions
kde_tsh = KernelDensity( kernel='gaussian', bandwidth=0.05).fit(diff_tsh)
kde_psh = KernelDensity( kernel='gaussian', bandwidth=0.05).fit(diff_psh)
kde_rrh = KernelDensity( kernel='gaussian', bandwidth=0.05).fit(diff_rrh)

kde_tsh_lg = KernelDensity( kernel='gaussian', bandwidth=0.05).fit(diff_tsh_lg)
kde_psh_lg = KernelDensity( kernel='gaussian', bandwidth=0.05).fit(diff_psh_lg)
kde_rrh_lg = KernelDensity( kernel='gaussian', bandwidth=0.05).fit(diff_rrh_lg)

# Kde values at xplot values
X_plot = np.linspace(0, 1, 100)[:, np.newaxis]
log_dens_tsh = kde_tsh.score_samples(X_plot)
log_dens_psh = kde_psh.score_samples(X_plot)
log_dens_rrh = kde_rrh.score_samples(X_plot)

log_dens_tsh_lg = kde_tsh_lg.score_samples(X_plot)
log_dens_psh_lg = kde_psh_lg.score_samples(X_plot)
log_dens_rrh_lg = kde_rrh_lg.score_samples(X_plot)

# RF Plot
fig, ax = plt.subplots(figsize=(20,12))
ax.plot(X_plot[:, 0], np.exp(log_dens_tsh), label='TSH')
ax.plot(X_plot[:, 0], np.exp(log_dens_psh), label='PSH')
ax.plot(X_plot[:, 0], np.exp(log_dens_rrh), label='RRH')

ax.legend(frameon=False, fontsize=16)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_xlabel('Change in Probability', fontsize=20)
plt.xticks(fontsize=14)
plt.tick_params(left=False, labelleft=False)

plt.savefig(r'..\..\..\Output\figures\Counterfactuals\TX_CATE_04202024.png')
plt.close()

# Elastic Net Plot
fig, ax = plt.subplots(figsize=(20,12))
ax.plot(X_plot[:, 0], np.exp(log_dens_tsh_lg), label='TSH')
ax.plot(X_plot[:, 0], np.exp(log_dens_psh_lg), label='PSH')
ax.plot(X_plot[:, 0], np.exp(log_dens_rrh_lg), label='RRH')
ax.legend(frameon=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xlabel('Change in Probability')

# Model Differences
X_diffplot = np.linspace(-.5, .5, 100)[:, np.newaxis]
mdiff_rrh = diff_rrh-diff_rrh_lg
kde_rrh_mdiff = KernelDensity( kernel='gaussian', bandwidth=0.05).fit(mdiff_rrh)
log_dens_rrh_mdiff = kde_rrh_mdiff.score_samples(X_diffplot)
fig, ax = plt.subplots(figsize=(20,12))
ax.plot(X_diffplot[:, 0], np.exp(log_dens_rrh_mdiff), label='Model Differences')

#############################################################################
# CATE Plots
# Protected Classes and programmatic populations of intersts

# Veteran Status
tempx['Veteran'] =  remapencoder(xvar = 'Household_Veteran',
                                 yvar = 'success_180',
                                 origdf = traindf.copy(),
                                 currdf = tempx.copy())

tempx['Veteran'] = tempx['Veteran'].replace({'0': 'non-Veteran',
                                             '1': 'Missing/Other',
                                             '2': 'Veteran'})

# Race
tempx['Race'] =  remapencoder(xvar = 'HoH_RaceName',
                                 yvar = 'success_180',
                                 origdf = traindf.copy(),
                                 currdf = tempx.copy())
# Gender
tempx['Gender'] =  remapencoder(xvar = 'HoH_GenderName',
                                 yvar = 'success_180',
                                 origdf = traindf.copy(),
                                 currdf = tempx.copy())
# Sexual Orientation
tempx['SexualOrientation'] =  remapencoder(xvar = 'HoH_SexualOrientationName',
                                           yvar = 'success_180',
                                           origdf = traindf.copy(),
                                           currdf = tempx.copy())

# Disability
tempx['Disability'] =  remapencoder(xvar = 'Household_DisablingConditionMax',
                                    yvar = 'success_180',
                                    origdf = traindf.copy(),
                                    currdf = tempx.copy())

tempx['Disability'] = tempx['Disability'].replace({'0': 'non-Disabiled',
                                                   '1': 'Missing/Other',
                                                   '2': 'Disabled'})

# Family Size
tempx.loc[tempx['ln_N_Household'] <  0, 'FamilySize'] = '1' 
tempx.loc[((tempx['ln_N_Household'] >  0) & 
           (tempx['ln_N_Household'] <  1)), 'FamilySize'] = '2' 
tempx.loc[tempx['ln_N_Household'] >  1, 'FamilySize'] = '3+' 


tups = [('Veteran', 'RRH', diff_rrh, diff_rrh_lg, 'Missing/Other'),
        ('Veteran', 'PSH', diff_psh, diff_psh_lg, 'Missing/Other'),
        ('Veteran', 'TSH', diff_tsh, diff_tsh_lg, 'Missing/Other'),
        ('Race', 'RRH', diff_rrh, diff_rrh_lg, 'Missing_NoAnswer_DoesntKnow'),
        ('Race', 'PSH', diff_psh, diff_psh_lg, 'Missing_NoAnswer_DoesntKnow'),
        ('Race', 'TSH', diff_tsh, diff_tsh_lg, 'Missing_NoAnswer_DoesntKnow'),
        ('Gender', 'RRH', diff_rrh, diff_rrh_lg, 'Other_Missing'),
        ('Gender', 'PSH', diff_psh, diff_psh_lg, 'Other_Missing'),
        ('Gender', 'TSH', diff_tsh, diff_tsh_lg, 'Other_Missing'),
        ('SexualOrientation', 'RRH', diff_rrh, diff_rrh_lg, ''),
        ('SexualOrientation', 'PSH', diff_psh, diff_psh_lg, ''),
        ('SexualOrientation', 'TSH', diff_tsh, diff_tsh_lg, ''),
        ('Disability', 'RRH', diff_rrh, diff_rrh_lg, 'Missing/Other'),
        ('Disability', 'PSH', diff_psh, diff_psh_lg, 'Missing/Other'),
        ('Disability', 'TSH', diff_tsh, diff_tsh_lg, 'Missing/Other'),
        ('FamilySize', 'RRH', diff_rrh, diff_rrh_lg, 'Missing/Other'),
        ('FamilySize', 'PSH', diff_psh, diff_psh_lg, 'Missing/Other'),
        ('FamilySize', 'TSH', diff_tsh, diff_tsh_lg, 'Missing/Other')]

for i in tups:
    fig, ax = plt.subplots(1,2, figsize=(20,12))
    kdeprotectedclass(var=i[0], pdiff=i[2],  tempdf=tempx,
                      rmcats=i[4], axval=0, title='Random Forest')
    kdeprotectedclass(var=i[0], pdiff=i[3],  tempdf=tempx,
                      rmcats=i[4], axval=1, title='Elastic Net')
    plt.suptitle(f'{i[0]} {i[1]}')
    plt.savefig(r'..\..\..\Output\figures\Counterfactuals\\' + f'counter_{i[0]}_{i[1]}.png')
    plt.close()



Look = pd.DataFrame({'Veteran': tempx['Veteran'].values,
                     'RFCDiffP': diff_rrh.flatten(),
                     'ENDiffP': diff_rrh_lg.flatten()})

# RFC Gender Plot

fig, ax = plt.subplots(1,1, figsize=(20,12))
var = 'Gender'
pdiff = diff_rrh
levels = [v for v in tempx[var].unique() if v not in ['Other_Missing']]
for l in levels :
    abool = tempx[var] == l
    kde = KernelDensity( kernel='gaussian', bandwidth=0.03).fit(pdiff[abool])
    log_dens = kde.score_samples(X_plot)
    ax.plot(X_plot[:, 0], np.exp(log_dens), label=l)

ax.legend(frameon=False, fontsize=16)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_xlabel('Change in Probability', fontsize=20)
plt.xticks(fontsize=14)
plt.tick_params(left=False, labelleft=False)
plt.savefig(r'..\..\..\Output\figures\Counterfactuals\Gender_CATE_04202024.png')
plt.close()
###############################################################################
# Get TX effects 

# yname = 'success_noexit_730'
# tdf = pd.read_csv(r'..\..\..\Data\targettraindf_2024-03-07.csv')
# tdf = tdf.loc[~tdf[yname].isna(),]
# tdf = tdf.reset_index()

# diff_tsh_ntx = evalcounter(xs=tempx_selectnx.copy(), ys=ynx.copy(), clfrf=deepcopy(clfrfnx), tx='TSH')
# diff_psh_ntx = evalcounter(xs=tempx_selectnx.copy(), ys=ynx.copy(), clfrf=deepcopy(clfrfnx), tx='PSH')
# diff_rrh_ntx = evalcounter(xs=tempx_selectnx.copy(), ys=ynx.copy(), clfrf=deepcopy(clfrfnx), tx='RRH')

# hmm = pd.concat([tdf, pd.Series(diff_rrh_ntx[:,0])], axis=1)
