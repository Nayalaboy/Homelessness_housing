-------------------------------------------------------------------------------
-- Head of Household Information
-- Pulles from e_PROD, Null Report, Disabilities, and Benefits/Income.
-- Query is filtered to Coordinated Entry Enrollments.

SELECT e.EnrollmentID HoH_EnrollmentID, e.PersonalID HoH_PersonalID , 
       e.LengthOfStayName HoH_LengthOfStayName, 
       e.LivingSituationName HoH_LivingSituationName,
       e.LivingSituationGroup HoH_LivingSituationGroup, e.RaceName HoH_RaceName,
       e.RaceGroup HoH_RaceGroup, e.EthnicityName HoH_EthnicityName,
       e.GenderName HoH_GenderName, e.GenderGroup HoH_GenderGroup, 
       e.SexualOrientationName HoH_SexualOrientationName,
       e.VeteranStatusName HoH_VeteranStatusName, 
       e.TimesHomelessPastThreeYearsName HoH_TimesHomelessPastThreeYearsName,
       e.Age_DOB HoH_Age_DOB, e.AgeAtEntry HoH_AgeAtEntry, 
       e.ProjectName HoH_ProjectName,
       e.LastGradeCompletedNameAtEntry HoH_LastGradeCompletedNameAtEntry, 
       e.ExitDestinationName HoH_ExitDestinationName,
       e.ExitDestinationGroup HoH_ExitDestinationGroup, 
       e.ExitDestinationType HoH_ExitDestinationType, 
       e.EnrollmentEntryDate HoH_EnrollmentEntryDate,
       e.IncomeEarned_Entry HoH_IncomeEarned_Entry,
       
       nr.Employed HoH_Employed, 
       nr.UnemployedAndLookingForWork HoH_UnemployedAndLookingForWork,
       nr.EmployedAndLookingForWork HoH_EmployedAndLookingForWork,
       nr.EmployedHoursWorkedLastWeek HoH_EmployedHoursWorkedLastWeek,
       nr.EmploymentTenure HoH_EmploymentTenure,
       nr.IncomeFromAnySource HoH_IncomeFromAnySource,
       nr.HouseholdPercentofAMI HoH_HouseholdPercentofAMI,
       nr.NonCashBenefitFromAnySource HoH_NonCashBenefitFromAnySource, 
       nr.CoveredByHealthInsurance HoH_CoveredByHealthInsurance,
       nr.DisablingCondition HoH_DisablingCondition, nr.Pregnant HoH_Pregnant,
       nr.DomesticViolenceSurvivor HoH_DomesticViolenceSurvivor,
       nr.DomesticViolenceWhenOccurred HoH_DomesticViolenceWhenOccurred,
       nr.DomesticViolenceCurrentlyFleeing HoH_DomesticViolenceCurrentlyFleeing,
       
       de.Entry_PhysicalDisability HoH_PhysicalDisability,
       de.Entry_DevelopmentalDisability HoH_DevelopmentalDisability,
       de.Entry_ChronicHealthCondition HoH_ChronicHealthCondition,
       de.[Entry_HIV/AIDS] HoH_HIVAIDS,
       de.Entry_MentalHealthProblem HoH_MentalHealth,
       de.Entry_SubstanceAbuse HoH_SubstanceAbuse,
       
       ib.Unemployment HoH_Unemployment, ib.SSI HoH_SSI, ib.SSDI HoH_SSDI,
       ib.VADisabilityService HoH_VADisabilityService,
       ib.VADisabilityNonService HoH_VADisabilityNonService,
       ib.PrivateDisability HoH_PrivateDisability,
       ib.WorkersComp HoH_WorkersComp, ib.TANF HoH_TANF, ib.GA HoH_GA,
       ib.SocSecRetirement HoH_SocSecRetirement, ib.Pension HoH_Pension, 
       ib.ChildSupport HoH_ChildSupport, ib.Alimony HoH_Alimony,
       ib.OtherIncomeSource HoH_OtherIncomeSource, ib.SNAP HoH_SNAP,
       ib.WIC HoH_WIC, ib.TANFChildCare HoH_TANFChildCare,
       ib.TANFTransportation HoH_TANFTransportaion, ib.OtherTANF HoH_OtherTANF, 
       ib.OtherBenefitsSource HoH_OtherBenefitsSource
       
       
       
FROM e_PROD.Enrollment as e

-- Add Null Report
LEFT JOIN dw.EnrollmentNullMapping AS enm ON e.EnrollmentID = enm.EnrollmentID
LEFT JOIN dw.NullReport AS nr ON nr.EntryExitUID = enm.EntryExitUID

-- Disability Data
-- Subquerty just selects the desired variables and formates the Enrollment
-- and PersonalIDs for the merge.
LEFT JOIN (SELECT CONCAT('PC_', de.EnrollmentID) EnrollmentID, 
                  CONCAT('PC_', de.PersonalID) PersonalID,
                   de.Entry_PhysicalDisability, de.Entry_DevelopmentalDisability,
                   de.Entry_ChronicHealthCondition, de.[Entry_HIV/AIDS],
                   de.Entry_MentalHealthProblem, de.Entry_SubstanceAbuse    
           FROM C_STAGE.Disabilities_byEnrollment de) AS de 
     ON de.EnrollmentID = e.EnrollmentID
     AND de.PersonalID = e.PersonalID

-- Income and Benefits Data
-- Subquerty selects the desired variables, formats the Enrollment
-- and PersonalIDs for the merge, and filters to data entered upon entry (
-- see the IncomeBenefitsID filter).
LEFT JOIN (SELECT 
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
           WHERE ib.IncomeBenefitsID LIKE '%_1' -- Entry rows
            ) AS ib 
           ON ib.EnrollmentID = e.EnrollmentID
           AND ib.PersonalID = e.PersonalID
WHERE e.ProjectName IN ('Coordinated Entry - Priority Pool',
                        'Coordinated Entry - Chron Hmls Master List',
                        'Coordinated Entry - Veterans Master List'
                        )
  AND e.Perspective = 'HeadOfHousehold'
GO

