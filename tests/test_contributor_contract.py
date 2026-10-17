"""Unit tests for Person 2 SQL-to-JSON transformation functions."""
import unittest
from unittest.mock import patch
from services import analytics_service as company

class ContributorAnalyticsTests(unittest.TestCase):
    def test_company_counts_and_chart_series(self):
        rows=[
            {'company_id':1,'company_name':'Alpha','job_role':'Developer','offers_made':5,
             'students_placed':3,'offers_declined':1,'offers_pending':1},
            {'company_id':2,'company_name':'Beta','job_role':'Analyst','offers_made':4,
             'students_placed':2,'offers_declined':2,'offers_pending':0},
            {'company_id':3,'company_name':'Gamma','job_role':'Engineer','offers_made':0,
             'students_placed':0,'offers_declined':0,'offers_pending':0},
        ]
        with patch.object(company,'_query',return_value=rows):
            result=company.get_company_analytics()
        self.assertEqual(result['summary']['total_companies'],3)
        self.assertEqual(result['summary']['total_offers'],9)
        self.assertEqual(result['summary']['total_placements'],5)
        self.assertEqual(result['top_recruiters'][0]['company_name'],'Alpha')
        self.assertEqual(result['chart']['datasets'][0]['data'],[5,4,0])
        self.assertEqual(result['chart']['datasets'][1]['data'],[3,2,0])

    def test_branch_percentages_and_empty_placements(self):
        rows=[
            {'branch':'CSE','total_students':4,'placed_students':3,'unplaced_students':1,
             'placement_percentage':75},
            {'branch':'ECE','total_students':2,'placed_students':0,'unplaced_students':2,
             'placement_percentage':None},
        ]
        with patch.object(company,'_query',return_value=rows):
            result=company.get_branch_analytics()
        self.assertEqual(result['summary']['total_students'],6)
        self.assertEqual(result['summary']['placed_students'],3)
        self.assertEqual(result['summary']['overall_placement_percentage'],50)
        self.assertEqual(result['branches'][1]['placement_percentage'],0)
        self.assertEqual(result['chart']['datasets'][2]['data'],[75,0])

    def test_salary_comparison_and_no_accepted_offers(self):
        overall=[{'placements':5,'highest_package':21,'average_package':10,'lowest_package':6}]
        by_company=[{'company_name':'Alpha','placements':3,'highest_package':21,
                     'average_package':12,'lowest_package':7}]
        by_branch=[{'branch':'CSE','placements':3,'highest_package':21,
                    'average_package':12,'lowest_package':7}]
        with patch.object(company,'_query',side_effect=[overall,by_company,by_branch]):
            result=company.get_package_analytics()
        self.assertEqual(result['overall']['average_package'],10)
        self.assertEqual(result['by_company'][0]['diff_from_overall_average'],2)
        self.assertEqual(result['chart']['company_comparison']['datasets'][1]['data'],[12])
        with patch.object(company,'_query',side_effect=[
            [{'placements':0,'highest_package':None,'average_package':None,'lowest_package':None}],
            [],[]
        ]):
            empty=company.get_package_analytics()
        self.assertEqual(empty['overall']['highest_package'],0)
        self.assertEqual(empty['chart']['company_comparison']['labels'],[])

if __name__=='__main__':
    unittest.main()
