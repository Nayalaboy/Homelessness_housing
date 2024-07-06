-------------------------------------------------------------------------------
-- Household Roll Up

-- Similar to the HoH Query above, this query pulls similar informaiton, but
-- does so for all members of the household. It then aggregates this 
-- household information back up to the single CE enrollment.

-- It is likely easiest to understand this query starting at line 199.
-- This subquery pulls in e_PROD, the Null Report, Income/Benefits, and Disability
-- data much like the above query, but for all clients, not just the HoH. In
-- the select statement there are many case statements that format these
-- categorical varialbes so that they can be aggregated over. This is all
-- considered the "Family" Data.

-- On line 188 there is a subquery that grabs all of the head of household 
-- enrollment data. This single row per HoH Enrollment is merged to the 
-- "Family" data. Once that is done we can finally aggregate back to the 
-- household level.

SELECT HHE.HouseholdID, 
       SUM(F.IncomeEarned_Entry) Household_IncomeEarnedEntry,
       SUM(F.IncomeNonEarned_Entry) Household_IncomeNonEarnedEntry,
       COUNT(F.PersonalID) N_Household,
       SUM(F.childrenpresent) Household_N_Children,
       MAX(F.AgeAtEntry) Household_OldestClient,
       MIN(F.AgeAtEntry) Household_YoungestClient,
       SUM(F.children0_3) Household_N_children0_3,
       SUM(F.children3_5) Household_N_children3_5,
       SUM(F.children5_10) Household_N_children5_10,
       SUM(F.children10_15) Household_N_children10_15,
       SUM(F.children15_17) Household_N_children15_17,
       -- Null Report Data
       MAX(F.HHVeteranStatus) Household_Veteran,
       MAX(F.HHHighestEducation) Household_Education,
       MAX(F.HHHighestEmployment) Household_Employment,
       SUM(F.EmployedHoursWorkedLastWeek) Household_HoursWorked,
       MAX(F.HHEmploymentTenure) Household_EmploymentTenure,
       MAX(F.HHHouseholdPercentofAMI) Household_PercentAMI,
       MAX(F.HHNonCashBenefitFromAnySource) Household_NonCashBenefitAnySource,
       AVG(F.HHCoveredByHealthInsurance) Household_AvgInsurance, -- Note that a lot of the 'uninsured' are missing values...
       MAX(F.HHPregnant) Household_Pregnant, 
       MAX(F.HHDisablingCondition_ordinal) Household_DisablingConditionMax,
       AVG(F.HHDisablingCondition_binary) Household_DisablingConditionAvg,
       MAX(F.HHDomesticViolenceSurvivor) Household_DomesticViolenceSurvivor,
       MAX(F.HHDomesticViolenceWhenOccurred) Household_MostRecentDomsticViolence,
       MAX(F.HHDomesticViolenceCurrentlyFleeing) Household_FleeingDomesticViolence,
       -- Disability Enrollment File
       MAX(F.HHEntry_PhysicalDisability) Household_PhysicalDisability,
       MAX(F.HHEntry_DevelopmentalDisability) Household_DevelopmentalDisability,
       MAX(F.HHEntry_ChronicHealthCondition) Household_ChronicHealthCondition,
       MAX(F.HHEntry_HIVAIDS) Household_HIVAIDS,
       MAX(F.HHEntry_MentalHealthPRoblem) Household_MentalHealthProblem,
       MAX(F.HHEntry_SubstanceAbuse) Household_SubstanceAbuse,
       -- Income and Benefits 
       MAX(F.Unemployment) Household_Unemployment,
       MAX(F.SSI) Household_SSI,
       MAX(F.SSDI) Household_SSDI,
       MAX(F.VADisabilityService) Household_VADisabilityService,
       MAX(F.VADisabilityNonService) Household_VADisabilityNonService,
       MAX(F.PrivateDisability) Household_PrivateDisability,
       MAX(F.WorkersComp) Household_WorkersComp,
       MAX(F.TANF) Household_TANF,
       MAX(F.GA) Household_GA,
       MAX(F.SocSecRetirement) Household_SocSecRetirement,
       MAX(F.Pension) Household_Pension,
       MAX(F.ChildSupport) Household_ChildSupport,
       MAX(F.Alimony) Household_Alimony,
       MAX(F.OtherIncomeSource) Household_OtherIncomeSource,
       MAX(F.SNAP) Household_SNAP,
       MAX(F.WIC) Household_WIC,
       MAX(F.TANFChildCare) Household_TANFChildCare,
       MAX(F.TANFTransportation) Household_TANFTransportation,
       MAX(F.OtherTANF) Household_OtherTANF,
       MAX(F.OtherBenefitsSource) Household_OtherBenefitsSource,
       
       -- What aggregates make sense for these?
       MAX(F.HHUnemployedAndLookingForWork) Household_UnemployedAndLookingForWork,
       MAX(F.HHEmployedAndLookingForWork) Household_EmployedAndLookingForWork
      
FROM 
    
    -- Grab all Head Of Household Enrollments
    (SELECT e1.PersonalID, e1.EnrollmentID, e1.HouseholdID
      FROM e_prod.Enrollment as e1
      WHERE e1.Perspective = 'HeadOfHousehold'
      GROUP BY e1.PersonalID, e1.EnrollmentID, e1.HouseholdID 
      -- These are distinct at this level : Single row per household enrollment
    ) AS HHE,
    
    -- Creates "Family" Data, goal is to get data on all household members
    -- for each CE Enrollment.
    -- Grab all CE Enrollments, regardless of HoH status.
    -- Converts Categorical into numeric for later aggregation.
    (SELECT e2.HouseholdID, e2.PersonalID, e2.IncomeEarned_Entry,
              e2.IncomeNonEarned_Entry, CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) AS AgeAtEntry,
              e2.LastGradeCompletedNameAtEntry,
              
              -- Children and age bins
              CASE 
                WHEN e2.RelationshipToHoH_Name = 'Child' THEN 1
                ELSE 0
              END AS childrenpresent,
              
              CASE 
                WHEN CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) >= 0 
                AND  CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) <= 3  THEN 1
                ELSE 0
              END AS children0_3,
              
              CASE 
                WHEN CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) > 3 
                AND  CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) <= 5  THEN 1
                ELSE 0
              END AS children3_5,
                    
              CASE 
                WHEN CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) > 5 
                AND  CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) <= 10  THEN 1
                ELSE 0
              END AS children5_10,    
                        
               CASE 
                WHEN CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) > 10 
                AND  CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) <= 15  THEN 1
                ELSE 0
              END AS children10_15,   
               
              CASE 
                WHEN CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) > 15 
                AND  CAST(REPLACE(e2.AgeAtEntry, ' yrs', '') AS numeric) < 18  THEN 1
                ELSE 0
              END AS children15_17,
              
              -- Education and employment
              CASE
                WHEN e2.LastGradeCompletedNameAtEntry IS NULL THEN 0
                WHEN e2.LastGradeCompletedNameAtEntry = 'Data not collected' THEN 1
                WHEN e2.LastGradeCompletedNameAtEntry = 'Client doesn''t know' THEN 2
                WHEN e2.LastGradeCompletedNameAtEntry = 'Client prefers not to answer' THEN 3
                WHEN e2.LastGradeCompletedNameAtEntry = 'Less than Grade 5' THEN 4
                WHEN e2.LastGradeCompletedNameAtEntry = 'Grades 5-6' THEN 5
                WHEN e2.LastGradeCompletedNameAtEntry = 'Grades 7-8' THEN 6
                WHEN e2.LastGradeCompletedNameAtEntry = 'Grades 9-11' THEN 7
                WHEN e2.LastGradeCompletedNameAtEntry = 'School program does not have grade levels' THEN 8
                WHEN e2.LastGradeCompletedNameAtEntry = 'GED' THEN 9
                WHEN e2.LastGradeCompletedNameAtEntry = 'Grade 12/High school diploma' THEN 10
                WHEN e2.LastGradeCompletedNameAtEntry = 'Some college' THEN 11
                WHEN e2.LastGradeCompletedNameAtEntry = 'Vocational certification' THEN 12
                WHEN e2.LastGradeCompletedNameAtEntry = 'Associate''s degree' THEN 13
                WHEN e2.LastGradeCompletedNameAtEntry = 'Bachelor''s degree' THEN 14
                WHEN e2.LastGradeCompletedNameAtEntry = 'Graduate degree' THEN 15
              END AS HHHighestEducation,
              
              CASE
                WHEN nr.Employed = 'No (HUD)' THEN 0
                WHEN nr.Employed IS NULL THEN 1
                WHEN nr.Employed IN ('Client doesn''t know (HUD)',
                                     'Client prefers not to answer (HUD)',
                                      'Data not collected (HUD)') THEN 1
                WHEN nr.Employed = 'Yes (HUD)' THEN 2
              END AS HHHighestEmployment,
              
              CASE
                WHEN nr.UnemployedAndLookingForWork = 'No (HUD)' THEN 0
                WHEN nr.UnemployedAndLookingForWork IS NULL THEN 1
                WHEN nr.UnemployedAndLookingForWork IN ('Client doesn''t know (HUD)',
                                     'Client prefers not to answer (HUD)',
                                      'Data not collected (HUD)') THEN 1
                WHEN nr.UnemployedAndLookingForWork = 'Yes (HUD)' THEN 2
              END AS HHUnemployedAndLookingForWork,
              
              CASE
                WHEN nr.EmployedAndLookingForWork = 'No (HUD)' THEN 0
                WHEN nr.EmployedAndLookingForWork IS NULL THEN 1
                WHEN nr.EmployedAndLookingForWork IN ('Client doesn''t know (HUD)',
                                     'Client prefers not to answer (HUD)',
                                      'Data not collected (HUD)') THEN 1
                WHEN nr.EmployedAndLookingForWork = 'Yes (HUD)' THEN 2
              END AS HHEmployedAndLookingForWork,
              
              CASE
                WHEN nr.EmployedHoursWorkedLastWeek > 112 THEN NULL -- 16*7
                ELSE nr.EmployedHoursWorkedLastWeek
              END AS EmployedHoursWorkedLastWeek, 
              
              CASE
                WHEN nr.EmploymentTenure IS NULL THEN 0
                WHEN nr.EmploymentTenure IN ('Client doesn''t know (HUD)',
                                             'Client refused (HUD)') THEN 1
                WHEN nr.EmploymentTenure = 'Temporary (HUD)' THEN 2
                WHEN nr.EmploymentTenure = 'Seasonal (HUD)' THEN 3
                WHEN nr.EmploymentTenure = 'Permanent (HUD)' THEN 4

              END AS HHEmploymentTenure,
              
              -- Income
              CASE
                WHEN nr.IncomeFromAnySource = 'No (HUD)' THEN 0
                WHEN nr.IncomeFromAnySource IS NULL THEN 1
                WHEN nr.IncomeFromAnySource IN ('Client doesn''t know (HUD)',
                                                'Client prefers not to answer (HUD)',
                                                'Data not collected (HUD)') THEN 1
                WHEN nr.IncomeFromAnySource = 'Yes (HUD)' THEN 2
              END AS HHIncomeFromAnySource,
              
              CASE
                WHEN nr.HouseholdPercentofAMI IS NULL THEN 0
                WHEN nr.HouseholdPercentofAMI = '< 10%' THEN 1
                WHEN nr.HouseholdPercentofAMI = '10% - <30%' THEN 2
                WHEN nr.HouseholdPercentofAMI = '30% - < 50%' THEN 3
                WHEN nr.HouseholdPercentofAMI = '50% - <80%' THEN 4
              END AS HHHouseholdPercentofAMI,
              
              CASE
                WHEN nr.NonCashBenefitFromAnySource = 'No (HUD)' THEN 0
                WHEN nr.NonCashBenefitFromAnySource IS NULL THEN 1
                WHEN nr.NonCashBenefitFromAnySource IN ('Client doesn''t know (HUD)',
                                                'Client prefers not to answer (HUD)',
                                                'Data not collected (HUD)') THEN 1
                WHEN nr.NonCashBenefitFromAnySource = 'Yes (HUD)' THEN 2
              END AS HHNonCashBenefitFromAnySource,
            
              -- Health and Disabilities
              CASE
                WHEN nr.CoveredByHealthInsurance = 'No (HUD)' THEN 0
                WHEN nr.CoveredByHealthInsurance IS NULL THEN 1
                WHEN nr.CoveredByHealthInsurance IN ('Client doesn''t know (HUD)',
                                                'Client prefers not to answer (HUD)',
                                                'Data not collected (HUD)') THEN 1
                WHEN nr.CoveredByHealthInsurance = 'Yes (HUD)' THEN 2
              END AS HHCoveredByHealthInsurance,
            
              CASE
                WHEN nr.DisablingCondition = 'No (HUD)' THEN 0
                WHEN nr.DisablingCondition IS NULL THEN 1
                WHEN nr.DisablingCondition IN ('Client doesn''t know (HUD)',
                                                'Client prefers not to answer (HUD)',
                                                'Data not collected (HUD)') THEN 1
                WHEN nr.DisablingCondition = 'Yes (HUD)' THEN 2
              END AS HHDisablingCondition_ordinal,
              
              CASE 
                WHEN nr.DisablingCondition = 'Yes (HUD)' THEN 1
                ELSE 0
              END HHDisablingCondition_binary,

              CASE
                WHEN nr.Pregnant = 'No (HUD)' THEN 0
                WHEN nr.Pregnant IS NULL THEN 1
                WHEN nr.Pregnant IN ('Client doesn''t know (HUD)',
                                                'Client prefers not to answer (HUD)',
                                                'Data not collected (HUD)') THEN 1
                WHEN nr.Pregnant = 'Yes (HUD)' THEN 2
              END AS HHPregnant,
              
              -- DV
              CASE
                WHEN nr.DomesticViolenceSurvivor = 'No (HUD)' THEN 0
                WHEN nr.DomesticViolenceSurvivor IS NULL THEN 1
                WHEN nr.DomesticViolenceSurvivor IN ('Client doesn''t know (HUD)',
                                                'Client prefers not to answer (HUD)',
                                                'Data not collected (HUD)') THEN 1
                WHEN nr.DomesticViolenceSurvivor = 'Yes (HUD)' THEN 2
              END AS HHDomesticViolenceSurvivor,
             
             CASE
                WHEN nr.DomesticViolenceWhenOccurred IS NULL THEN 0
                WHEN nr.DomesticViolenceWhenOccurred IN ('Client doesn''t know (HUD)',
                                                         'Client prefers not to answer (HUD)',
                                                         'Data not collected (HUD)') THEN 1
                WHEN nr.DomesticViolenceWhenOccurred = 'More than a year ago (HUD)' THEN 2
                WHEN nr.DomesticViolenceWhenOccurred = 'From six to twelve months ago (HUD)' THEN 3
                WHEN nr.DomesticViolenceWhenOccurred = 'Three to six months ago (HUD)' THEN 4
                WHEN nr.DomesticViolenceWhenOccurred = 'Within the past three months (HUD)' THEN 5
              END AS HHDomesticViolenceWhenOccurred,
             
              CASE
                WHEN nr.DomesticViolenceCurrentlyFleeing = 'No (HUD)' THEN 0
                WHEN nr.DomesticViolenceCurrentlyFleeing IS NULL THEN 1
                WHEN nr.DomesticViolenceCurrentlyFleeing IN ('Client doesn''t know (HUD)',
                                                             'Client prefers not to answer (HUD)',
                                                             'Data not collected (HUD)') THEN 1
                WHEN nr.DomesticViolenceCurrentlyFleeing = 'Yes (HUD)' THEN 2
              END AS HHDomesticViolenceCurrentlyFleeing,
              
              -- Veterans
              CASE
                WHEN nr.VeteranStatus = 'No (HUD)' THEN 0
                WHEN nr.VeteranStatus IS NULL THEN 1
                WHEN nr.VeteranStatus IN ('Client doesn''t know (HUD)',
                                          'Client prefers not to answer (HUD)',
                                          'Data not collected (HUD)') THEN 1
                WHEN nr.VeteranStatus = 'Yes (HUD)' THEN 2
              END AS HHVeteranStatus,
              
              -- Disabilities
             CASE
                WHEN de.Entry_PhysicalDisability = 'No' THEN 0
                WHEN de.Entry_PhysicalDisability IS NULL THEN 1
                WHEN de.Entry_PhysicalDisability IN ('Client doesn''t know',
                                                             'Client prefers not to answer',
                                                             'Data not collected') THEN 1
                WHEN de.Entry_PhysicalDisability = 'Yes' THEN 2
              END AS HHEntry_PhysicalDisability,
              
             CASE
                WHEN de.Entry_DevelopmentalDisability = 'No' THEN 0
                WHEN de.Entry_DevelopmentalDisability IS NULL THEN 1
                WHEN de.Entry_DevelopmentalDisability IN ('Client doesn''t know',
                                                             'Client prefers not to answer',
                                                             'Data not collected') THEN 1
                WHEN de.Entry_DevelopmentalDisability = 'Yes' THEN 2
              END AS HHEntry_DevelopmentalDisability,
             
             CASE
                WHEN de.Entry_ChronicHealthCondition = 'No' THEN 0
                WHEN de.Entry_ChronicHealthCondition IS NULL THEN 1
                WHEN de.Entry_ChronicHealthCondition IN ('Client doesn''t know',
                                                             'Client prefers not to answer',
                                                             'Data not collected') THEN 1
                WHEN de.Entry_ChronicHealthCondition = 'Yes' THEN 2
              END AS HHEntry_ChronicHealthCondition,
              
             CASE
                WHEN de.[Entry_HIV/AIDS] = 'No' THEN 0
                WHEN de.[Entry_HIV/AIDS] IS NULL THEN 1
                WHEN de.[Entry_HIV/AIDS] IN ('Client doesn''t know',
                                                             'Client prefers not to answer',
                                                             'Data not collected') THEN 1
                WHEN de.[Entry_HIV/AIDS] = 'Yes' THEN 2
              END AS HHEntry_HIVAIDS,
              
             CASE
                WHEN de.Entry_MentalHealthProblem = 'No' THEN 0
                WHEN de.Entry_MentalHealthProblem IS NULL THEN 1
                WHEN de.Entry_MentalHealthProblem IN ('Client doesn''t know',
                                                             'Client prefers not to answer',
                                                             'Data not collected') THEN 1
                WHEN de.Entry_MentalHealthProblem = 'Yes' THEN 2
              END AS HHEntry_MentalHealthProblem,
              
             CASE
                WHEN de.Entry_SubstanceAbuse = 'No' THEN 0
                WHEN de.Entry_SubstanceAbuse IS NULL THEN 1
                WHEN de.Entry_SubstanceAbuse IN ('Alcohol abuse', 'Both alcohol and drug abuse', 'Drug abuse') THEN 2
              END AS HHEntry_SubstanceAbuse,
              
              -- Income data is already in 0/1 format
             ib.Unemployment, ib.SSI, ib.SSDI, ib.VADisabilityService,
             ib.VADisabilityNonService , ib.PrivateDisability,
             ib.WorkersComp, ib.TANF, ib.GA, ib.SocSecRetirement, ib.Pension , 
             ib.ChildSupport , ib.Alimony, ib.OtherIncomeSource, ib.SNAP,
             ib.WIC, ib.TANFChildCare, ib.TANFTransportation, ib.OtherTANF, 
             ib.OtherBenefitsSource
                   
        FROM e_prod.Enrollment as e2
        
        -- Join e_Prod to the Null report, income and benefits, and disabilities
        -- data
        LEFT JOIN dw.EnrollmentNullMapping AS enm ON e2.EnrollmentID = enm.EnrollmentID
        LEFT JOIN dw.NullReport AS nr ON nr.EntryExitUID = enm.EntryExitUID
        LEFT JOIN (SELECT CONCAT('PC_', de.EnrollmentID) EnrollmentID, 
                  CONCAT('PC_', de.PersonalID) PersonalID,
                   de.Entry_PhysicalDisability, de.Entry_DevelopmentalDisability,
                   de.Entry_ChronicHealthCondition, de.[Entry_HIV/AIDS],
                   de.Entry_MentalHealthProblem, de.Entry_SubstanceAbuse    
           FROM C_STAGE.Disabilities_byEnrollment de) AS de 
         ON de.EnrollmentID = e2.EnrollmentID
         AND de.PersonalID = e2.PersonalID
        LEFT JOIN (SELECT TOP 1000 -- REMOVE THIS WHEN READY
                  CONCAT('PC_', ib.EnrollmentID) EnrollmentID, 
                  CONCAT('PC_', ib.PersonalID) PersonalID,
                   ib.Unemployment, ib.SSI, ib.SSDI,
                   ib.VADisabilityService,
                   ib.VADisabilityNonService ,
                   ib.PrivateDisability,
                   ib.WorkersComp, ib.TANF, ib.GA,
                   ib.SocSecRetirement, ib.Pension , 
                   ib.ChildSupport , ib.Alimony,
                   ib.OtherIncomeSource, ib.SNAP,
                   ib.WIC, ib.TANFChildCare,
                   ib.TANFTransportation, ib.OtherTANF, 
                   ib.OtherBenefitsSource
                   FROM C_STAGE.IncomeBenefits ib
                   WHERE ib.IncomeBenefitsID LIKE '%_1'
                   ) AS ib 
           ON ib.EnrollmentID = e2.EnrollmentID
           AND ib.PersonalID = e2.PersonalID
                                                 
        WHERE e2.Perspective ='Client'
        AND e2.ProjectName IN ( 'Coordinated Entry - Priority Pool',
                                'Coordinated Entry - Chron Hmls Master List',
                                'Coordinated Entry - Veterans Master List'
                                )
        GROUP BY e2.HouseholdID, e2.PersonalID, e2.IncomeEarned_Entry,
                 e2.IncomeNonEarned_Entry, e2.RelationshipToHoH_Name, 
                 e2.AgeAtEntry, e2.LastGradeCompletedNameAtEntry,
                 e2.LastGradeCompletedNameAtEntry, nr.employed,
                 nr.UnemployedAndLookingForWork, nr.EmployedAndLookingForWork,
                 nr.EmployedHoursWorkedLastWeek, nr.EmploymentTenure,
                 nr.IncomeFromAnySource,  nr.HouseholdPercentofAMI,
                 nr.NonCashBenefitFromAnySource, nr.CoveredByHealthInsurance,
                 nr.DisablingCondition, nr.Pregnant, nr.DomesticViolenceSurvivor,
                 nr.DomesticViolenceWhenOccurred, nr.DomesticViolenceCurrentlyFleeing,
                 nr.VeteranStatus, de.Entry_PhysicalDisability,
                 de.Entry_DevelopmentalDisability, de.Entry_ChronicHealthCondition,
                 de.[Entry_HIV/AIDS], de.Entry_MentalHealthProblem,
                 de.Entry_SubstanceAbuse,
                 ib.Unemployment, ib.SSI, ib.SSDI, ib.VADisabilityService,
                 ib.VADisabilityNonService , ib.PrivateDisability,
                 ib.WorkersComp, ib.TANF, ib.GA, ib.SocSecRetirement, ib.Pension , 
                 ib.ChildSupport , ib.Alimony, ib.OtherIncomeSource, ib.SNAP,
                 ib.WIC, ib.TANFChildCare, ib.TANFTransportation, ib.OtherTANF, 
                 ib.OtherBenefitsSource
                 
                 -- There are 66 duplicates at the household and personal id level. Boo.
    ) AS F -- Get Family Attributes

-- Merge Household Data to Head of Household observation.      
WHERE HHE.HouseholdID = F.HouseholdID
GROUP BY HHE.HouseholdID
GO
