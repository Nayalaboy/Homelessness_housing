# -*- coding: utf-8 -*-
"""
Created on Mon Feb 12 09:01:55 2024

@author: Trevor Gratz, trevormgratz@gmail.com
"""

sql_ceevents = '''
SELECT e1.EnrollmentID, e1.PersonalID, e1.HouseholdID, e1.EnrollmentEntryDate,
       e1.EnrollmentExitDate, e1.ExitDestinationGroup, e1.ExitDestinationName,
       e1.MoveInDate
FROM e_prod.Enrollment as e1
WHERE e1.Perspective = 'HeadOfHousehold'
AND e1.ProjectName IN ('Coordinated Entry - Priority Pool',
                       'Coordinated Entry - Chron Hmls Master List',
                       'Coordinated Entry - Veterans Master List'
                      )
ORDER BY e1.PersonalID, e1.EnrollmentEntryDate
'''

sql_ceeventsallpersons = '''
SELECT  e1.PersonalID, e1.HouseholdID 
FROM e_prod.Enrollment as e1
WHERE e1.Perspective = 'Client'
AND e1.ProjectName IN ('Coordinated Entry - Priority Pool',
                       'Coordinated Entry - Chron Hmls Master List',
                       'Coordinated Entry - Veterans Master List'
                      )
'''

sql_ceinterventions = '''
SELECT e1.EnrollmentID, e1.PersonalID, e1.HouseholdID, e1.EnrollmentEntryDate,
       e1.EnrollmentExitDate, e1.ExitDestinationGroup, e1.ExitDestinationName,
       e1.MoveInDate, e1.ProjectTypeName
FROM e_prod.Enrollment as e1
WHERE e1.Perspective = 'HeadOfHousehold'
AND e1.ProjectTypeName IN ('Transitional Housing',
                           'PH - Permanent Supportive Housing',
                           'PH - Rapid Re-Housing'
                      )
ORDER BY e1.PersonalID, e1.EnrollmentEntryDate
'''

sql_literalhomeless = '''

SELECT e.PersonalID, e.EnrollmentEntryDate
FROM e_PROD.Enrollment AS e
LEFT JOIN dw.EnrollmentNullMapping AS enm ON e.EnrollmentID = enm.EnrollmentID
LEFT JOIN dw.NullReport AS nr ON nr.EntryExitUID = enm.EntryExitUID
                       
        
WHERE  e.Perspective ='Client' AND
  -- See
   (e.ProjectTypeName IN ('Street Outreach', 'Emergency Shelter',
                        'Safe Haven'))
   OR(
        e.ProjectTypeName IN ('Transitional Housing',
                             'PH - Housing with Services',
                             'PH - Permanent Supportive Housing',
                             'PH - Housing Only', 'PH - Rapid Re-Housing') 
      AND (
            (
             e.LivingSituationName IN ('Place not meant for habitation',
                                       'Emergency shelter,  including hotel or motel paid for with emergency shelter voucher',
                                       'Safe Haven')
             OR (
                 e.LivingSituationName IN ('Foster care home or foster care group home',
                                            'Hospital or other residential non-psychiatric medical facility',
                                            'Jail,  prison or juvenile detention facility',
                                            'Long-term care facility or nursing home',
                                            'Psychiatric hospital or other psychiatric facility',
                                            'Substance abuse treatment facility or detox center')
                 AND
                 
                 nr.InstitutionStayLessThan90Days ='Yes'
                 
                 AND
                 
                 nr.HomelessBeforeInstitutionalStay = 'Yes'
                )
             OR (
                e.LivingSituationName IN ('Residential project or halfway house with no homeless criteria',
                                          'Hotel or motel paid for without emergency shelter voucher',
                                          'Transitional housing for homeless persons',
                                          'Staying or living in a friend''s room, apartment or house',
                                          'Staying or living in a family member''s room, apartment or house',
                                          'Rental by client, with ongoing housing subsidy',
                                          'Rental by client, no ongoing housing subsidy',
                                          'Owned by client, with ongoing housing subsidy',
                                          'Owned by client, no ongoing housing subsidy',
                                          'Host home (non-crisis)',
                                          'Client doesn''t know',
                                          'Client prefers not to answer',
                                          'Data not collected')
                AND
                nr.InstitutionalStayLessThan7Days = 'Yes'
                AND
                nr.HomelessBeforeInstitutionalStay = 'Yes'
                )
            )
         
           )
   )
GROUP BY e.PersonalID, e.EnrollmentID, e.HouseholdID, e.EnrollmentEntryDate
'''

sql_referrals = '''
SELECT 'PC_' + CAST(r.ClientUid AS varchar) PersonalID,
        r.ServiceReferDate,
        r.ServiceRefertoProviderProgramType 
FROM dbo.Referrals as r
WHERE r.ServiceProviderCreating IN ('Coordinated Entry - Priority Pool(402)',
                                    'Coordinated Entry - Chron Hmls Master List(410)')
  AND r.ServiceRefertoProviderProgramType IN ('PH - Permanent Supportive Housing',
                                              'PH - Rapid Re-Housing',
                                              'Transitional Housing')
'''