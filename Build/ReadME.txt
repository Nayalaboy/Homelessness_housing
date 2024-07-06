The code in this folder builds the initial analytic data set used to train a model predicting successful exit and retention of housing from homelessness. 

Files
1) BuildFeatures_02132024.py
  *  This file pulls in three SQL queries, queries HMIS, then saves the output. The SQL lines are stored in the files:
     * HeadofHouseholdsSQL_01312024.py
	* Using e_prod, limiting to HoH and CE Enrollments, then pulls in data on disability status as well as income and benefits. 
     * HouseholdRollUpSQL_01312024.py
        * Using much of the same data as above, it does not limit to HoH initially. Instead pulls in data on all of the household
          and then aggregates to the Household ID level.
     * LiteralHomelessnessHistorySQL_01312024.py 
        * Gets all literal homeless events occurring prior to a CE enrollment. 

2) BuildInterventionsOutcomes_02132024.py
  * This file associates housing interventions with CE events, and using this data determines whether or not a household had a successful exit.
  * For details on how this is done see this file '..\..\..\Documentation\Project Generated\OutcomesInterventionDocumentation_02132024.xlsx'
  * Relies on some simple SQL pulls in the InterventionOutcomes_SQL_02122024.py file.

3) BuildAnalticDataSet_02142024.py
  * This file combines the data produced in 1) and 2) into an analytic dataset. It cleans categorical variables that are sparse and continuous 
    variables that have values that shouldn't be allowed (e.g. negative ages). It exports a training and testing dataset to ensure there is 
    is no leakage.

4) PreprocessAnalyticDataSet_02292024.py
  * This file gets simple imputers, one hot encoders, and standard scalars for all variables. It then uses these to build different
    datasets based on the variables chosen to be included. In other words, it takes a standard dataset for data analysis into an 
    array like object coded for ML.