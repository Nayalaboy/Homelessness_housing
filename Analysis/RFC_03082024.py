# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 10:30:26 2024

@author: Trevor Gratz, trevormgratz@gmail.com

This file performs 54 grid searchs for the best parameters for predicting 
exits from homelessness. It loops over 6 different definitions of outcomes, 3
different sets of features, and 3 feature selection/transformations. 

This is significantly fewer models than the Lasso/Ridge/Elastic Net regression
code becuase A) the random forest classifiers take much longer to run, and B)
I have some idea on how to narrow down the search space. First, RFCs perform
poorly with sparse categorical data in a One Hot Encoding setting, so I 
am not considering that encodeing. Second, rather than doing feature selection
and PCA at the same time I am only doing one or the other. If the linear models
with regularization show that these types of models are the best i.e. layered 
PCA and feature selection, then I will need to revisit this. 
"""
import sys
sys.path.append('../')
from Build.Dictionaries import X_hoh_WOE, X_house_WOE, X_all_WOE, X_notCat_WOE
from Build.Dictionaries import ywoexmatch
from sklearn.model_selection import GridSearchCV
import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
import numpy as np
from datetime import date
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import RandomForestClassifier

today = date.today()
mpath = r'..\..\..\Output\models'


def rfccv(df, yvar, X_subset, Xname, vtransform):
    '''
    Parameters
    ----------
    df : Pandas Dataset
        DESCRIPTION. Dataset to support the Random Forest Classifier
    yvar : String
        DESCRIPTION. Column name of the y variable
    X_subset : List
        DESCRIPTION. List of all column names to be used in the RFC.
    Xname : String
        DESCRIPTION. String name for subset of Xs passed in the X_subset
                    arguement.
    vtransform : String
        DESCRIPTION. String to indicate whether to apply "PCA" or 
                     feature selection, "SelectFeatures". Passing "none"
                     will not perform any feature selection.

    Returns
    -------
    From main folder, model results saved in: 
    \Output\models\RFC_{yvar}_{Xname}_Transform{vtransform}.pkl

    '''
    
    
    df = df.loc[~df[yvar].isna(),].copy()
    y = df[yvar]

    # Get X Variables
    tempx = df[X_subset]
    
    # Apply Variable Selections/Transforms
    if vtransform == 'SelectFeatures':
        selector = SelectFromModel(
                       estimator=LogisticRegression(C=1,
                           penalty='l1',solver='liblinear')).fit(tempx, y)
        selector.estimator_.coef_
        retaincols = selector.get_feature_names_out()
        tempx = tempx[retaincols]
    elif vtransform == "PCA":
        pca = PCA(n_components=0.95, svd_solver="full")
        tempx = pca.fit_transform(tempx)

    #######################################################
    # Grid Search 
    rf = RandomForestClassifier()
    grid_space={'max_depth':[3,5,10,None],
                'n_estimators':[10,100,200],
                'max_features':[1,3,5,7],
                'min_samples_leaf':[2,3],
                'min_samples_split':[2,3]
                }
    
    grid = GridSearchCV(rf ,param_grid=grid_space,cv=5,
                        scoring=['accuracy', 'roc_auc',
                                 'f1', 'precision', 'recall'],
                        refit='roc_auc')
    model_grid = grid.fit(tempx,y)
    
    
    ##########################################################
    # Store Results
    max_depth = model_grid.best_params_['max_depth']
    n_estimators = model_grid.best_params_['n_estimators']
    max_features = model_grid.best_params_['max_features']
    min_samples_leaf = model_grid.best_params_['min_samples_leaf']
    min_samples_split = model_grid.best_params_['min_samples_split']
    
    
    print('Best hyperparameters are: '+str(model_grid.best_params_))
    print('Best score is: '+str(model_grid.best_score_))
    
    cvbscore = model_grid.best_score_
    
    results = pd.DataFrame.from_dict(model_grid.cv_results_)
    auc = results.loc[results['rank_test_accuracy'] == 1,
                      'mean_test_roc_auc'].iloc[0]
    

    performdict = {'cv accuracy': cvbscore,
                   'ROCAUC': auc,
                   'max_depth': max_depth,
                   'n_estimators': n_estimators,
                   'max_features': max_features,
                   'min_samples_leaf': min_samples_leaf,
                   'min_samples_split': min_samples_split,
                   'Xvars': Xname,
                   'Variable Transform': vtransform,
                   'Model': model_grid}
    
    bestmodelpath = mpath + f'\\RFC_{yvar}_{Xname}_Transform{vtransform}.pkl'
    with open(bestmodelpath, 'wb') as f:
        pickle.dump(performdict, f)

###############################################################
# Run Analysis

alldf = pd.read_csv(r'..\..\..\Data\train_allfeatures__2024-03-18.csv')
counter = 0
# Different y outcomes
for y in ['success_180', 'success_365', 'success_730',
          'success_noexit_180', 'success_noexit_365', 'success_noexit_730']:
    
    # Different features
    for dfstr in ['all', 'hoh', 'household']:
        
        # Different transformations
        for vt in ['none', 'PCA', 'SelectFeatures']:
            
            # Get correct feature set
            if dfstr == 'all':
                Xvars = X_all_WOE
            elif dfstr == 'hoh':
                Xvars = X_hoh_WOE
            else:
                Xvars = X_house_WOE
            
            # WOE variables are specific to y. Adjust xs to reflect this.
            # Leave non-categorical variables unchanged.
            Xvars = ywoexmatch(yval=y, xlist=Xvars)
            
            if ((dfstr == 'all') & (vt =='none')):
                pass
            else: 
                print('\n################################################')
                print (f'Iteration {counter} of 48')
                print(y)
                print(f'Data: {dfstr}')
                print(f'Variable Transforms: {vt}')
                
                rfccv(df=alldf.copy(), yvar=y, X_subset=Xvars,
                      Xname = dfstr, vtransform =vt)
                counter += 1
                
