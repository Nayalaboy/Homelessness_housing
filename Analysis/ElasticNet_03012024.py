# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 10:30:26 2024


@author: Trevor Gratz, trevormgratz@gmail.com

This file performs 54 grid searchs for the best parameters for predicting 
exits from homelessness. It loops over 


    * 6 different definitions of outcomes: One set relies on the use of exit
      status verus just examining reentries. We also look for reentries within
      6 months, 12 months, and 14 months.
    * 3 different sets of features: features primarily from the head of the
      household, features aggregated from the household, and both.
    * 2 different feature encodings: Weight of Evidence and One Hot.
    * 3 different algorithms: Lasso, Ridge, and Elastic Net
    * 3 feature selection/transformations: PCA, feature importance, both. 

A dictionary saving the trained models and their crossvalidation metrics 
is saved.

"""
import sys
sys.path.append('../')
# These lists define the features sets and the encodings.
# hoh = Head of Houshold
# house = Aggregated features from households
# WOE = Weight of Evidence
# OHE = One hot encoding
from Build.Dictionaries import X_hoh_OHE, X_house_OHE, X_all_OHE
from Build.Dictionaries import X_hoh_WOE, X_house_WOE, X_all_WOE

from sklearn.model_selection import GridSearchCV
import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
import numpy as np
from datetime import date
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectFromModel


today = date.today()
mpath = r'..\..\..\Output\models'


def lassoridgecv(df, yvar, pcabool, X_subset, ElasticNetBool,
                 dataset, encoding, varsel):
    '''
    This function takes a dataframe (df), an outcome variable (yvar), a boolean 
    for whether or not to perform PCA (pcabool), the X features as a list
    (X_subset), whether to perform elastic net regression (ElasticNetBool),
    a string name for the feature set used (dataset), a string for the 
    encoding used (encoding), and a boolean for whether variable selection was
    used (varsel).
    '''
    df = df.loc[~df[yvar].isna(),].copy()
    y = df[yvar]

    # Get X Variables
    tempx = df[X_subset]
    
    # Apply Variable Selections
    if varsel == True:
        selector = SelectFromModel(
                       estimator=LogisticRegression(C=1,
                           penalty='l1',solver='liblinear')).fit(tempx, y)
        selector.estimator_.coef_
        retaincols = selector.get_feature_names_out()
        tempx = tempx[retaincols]
    
    # Apply PCA
    if pcabool:
        pca = PCA(n_components=0.95, svd_solver="full")
        tempx = pca.fit_transform(tempx)

    #######################################################
    # Initial Grid Search - Ridge/Lasso or Elastic Net
    if ElasticNetBool == True:
        lg_grid_space={"C":np.logspace(-3,3,7),
                       "penalty": ['elasticnet'],
                       'l1_ratio': np.linspace(0,1,10)}
    else:
        lg_grid_space={"C":np.logspace(-3,3,7),
                       "penalty": ['l1', 'l2']}
    
    model = LogisticRegression(max_iter=1000,
        solver='saga')
    lg_grid = GridSearchCV(model,param_grid=lg_grid_space,cv=5,
                           scoring='roc_auc', refit=False)
    lg_model_grid = lg_grid.fit(tempx,y)
    
    #######################################################
    # Refined Grid Search
    C = lg_model_grid.best_params_['C']
    penalty = lg_model_grid.best_params_['penalty']
    cgrid = np.concatenate([np.linspace(C/10, C, 11),
                            np.linspace(C, C*10, 11)])
    
    
    if ElasticNetBool == True:
        
        l1 = lg_model_grid.best_params_['l1_ratio']
        l1ll = l1 - 0.1
        if l1ll <0: l1ll =0
        l1up = l1 + 0.1
        if l1up >1: l1up =1

        lg_grid_space={"C": cgrid,
                   "penalty": [penalty],
                   "l1_ratio": np.linspace(l1ll, l1up,5)}
        
    else:
        lg_grid_space={"C": cgrid,
                   "penalty": [penalty]}
    
    model = LogisticRegression(max_iter=1000,
        solver='saga')
    
    lg_grid = GridSearchCV(model,param_grid=lg_grid_space,cv=5,
                           scoring=['accuracy', 'roc_auc'],
                           refit='roc_auc')
    lg_model_grid = lg_grid.fit(tempx,y)
    
    ##########################################################
    # Store Results
    cbest = lg_model_grid.best_params_['C']
    pbest = lg_model_grid.best_params_['penalty']
    print('Best hyperparameters are: '+str(lg_model_grid.best_params_))
    print('Best score is: '+str(lg_model_grid.best_score_))
    cvbscore = lg_model_grid.best_score_
    results = pd.DataFrame.from_dict(lg_grid.cv_results_)
    acc = results.loc[results['rank_test_roc_auc'] == 1,
                      'mean_test_accuracy'].iloc[0]
    
    if ElasticNetBool == True:
        l1 = lg_model_grid.best_params_['l1_ratio']
        performdict = {'cv ROCAUC': cvbscore,
                       'accuracy': acc,
                       'C': cbest,
                       'penalty': pbest,
                       'PCA': pcabool,
                       'l1_Ratio': l1,
                       'Data': dataset,
                       'Variable Encoding': encoding,
                       'Variable Selection': varsel,
                       'Model': lg_model_grid}
    else:
        performdict = {'cv ROCAUC': cvbscore,
                       'accuracy': acc,
                       'C': cbest,
                       'penalty': pbest,
                       'outcome': yvar,
                       'PCA': pcabool,
                       'Data': dataset,
                       'Variable Encoding': encoding,
                       'Variable Selection': varsel,
                       'Model': lg_model_grid}
    
    bestmodelpath = mpath + f'\\LassoRidgeEN_{yvar}_{dataset}_{encoding}_EN{enb}_VarSel{varsel}_PCA{pcabool}.pkl'
    with open(bestmodelpath, 'wb') as f:
        pickle.dump(performdict, f)

###############################################################
# Run the analysis
alldf = pd.read_csv(r'..\..\..\Data\train_allfeatures__2024-03-07.csv')


counter = 0
for y in ['success_180', 'success_365', 'success_730',
          'success_noexit_180', 'success_noexit_365', 'success_noexit_730']:
    for b in [True, False]:
        for e in ['WOE', 'OHE']:
            for enb in [True, False]:
                for dfstr in ['all', 'hoh', 'household']:
                    for vs in [True, False]:
                    
                        # Get the correct variables
                        if e == 'WOE':
                            if dfstr == 'all':
                                Xvars = X_all_WOE
                            elif dfstr == 'hoh':
                                Xvars = X_hoh_WOE
                            else:
                                Xvars = X_house_WOE
                        else:
                            if dfstr == 'all':
                                Xvars = X_all_OHE
                            elif dfstr == 'hoh':
                                Xvars = X_hoh_OHE
                            else:
                                Xvars = X_house_OHE
                                
                        if ((b == False) and (vs==False) and (dfstr == 'all')
                            and (enb==True)):
                            # Too colinear
                            pass
                        else:
                            print('\n################################################')
                            print (f'Iteration {counter} of 288')
                            print(y)
                            print(f'PCA: {b}')
                            print(f'Encoding: {e}')
                            print(f'Elastic Net: {enb}')
                            print(f'Data: {dfstr}')
                            print(f'Variable Selection: {vs}')
                            
                            lassoridgecv(df=alldf.copy(), yvar=y, pcabool = b,
                                         X_subset=Xvars, encoding=e, ElasticNetBool = enb,
                                         dataset = dfstr, varsel =vs)
                        counter += 1
            

