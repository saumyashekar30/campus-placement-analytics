"""TEST-ONLY Flask server. Reuses team routes with substituted Oracle aggregation results.

No change to production APIs or DB credentials. For development contract tests:
    python tests/fixture_server.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import jsonify
from app import app
from routes import analytics_routes as person_one
from routes import dashboard_api_routes as frontend
from services import analytics_service as person_two

branch_rows=[
    {'branch':'CSE','total_students':6,'placed_students':4,'unplaced_students':2,'placement_percentage':66.67},
    {'branch':'ECE','total_students':4,'placed_students':3,'unplaced_students':1,'placement_percentage':75},
]
company_rows=[
    {'company_id':1,'company_name':'Alpha Labs','offers_made':5,'students_placed':4,'offers_declined':1,'offers_pending':0},
    {'company_id':2,'company_name':'Beta Systems','offers_made':4,'students_placed':3,'offers_declined':1,'offers_pending':0},
]
package_rows=[
    {'company_name':'Alpha Labs','average_package':12,'highest_package':21,'lowest_package':7,'placements':4},
    {'company_name':'Beta Systems','average_package':8,'highest_package':10,'lowest_package':6,'placements':3},
]
interviews={
    'total':14,'passed':9,'failed':3,'scheduled':1,'pending':1,'success_rate':75,
    'status_distribution':[
        {'status':'Passed','count':9},{'status':'Failed','count':3},
        {'status':'Pending','count':1},{'status':'Scheduled','count':1}
    ],
    'rounds':[
        {'round_name':'Technical','round_number':1,'total':8,'passed':6,'failed':2,'pass_rate':75},
        {'round_name':'HR','round_number':2,'total':4,'passed':3,'failed':1,'pass_rate':75}
    ]
}

person_one._fetch_overview_data=lambda:{
    'summary_cards': {
      'total_students':10,'uniquely_placed_students':7,'unplaced_students':3,
      'placement_percentage':70,'total_applications':20,
      'selected_applications':8,'rejected_applications':5,'pending_applications':7,
      'total_companies':2,
      'package_stats':{'highest_package_lpa':21,'avg_package_lpa':10.29,
                       'lowest_package_lpa':6,'median_package_lpa':10}
    },
    'application_status_summary':{'selected':8,'rejected':5,'pending':7},
    'status_distribution':[]
}
person_one._fetch_application_analytics_data=lambda:{
    'total_applications':20,
    'status_distribution':[
        {'status':'Selected','count':8,'percentage':40},
        {'status':'Rejected','count':5,'percentage':25},
        {'status':'Applied','count':7,'percentage':35}
    ],
    'company_distribution':[
        {'company_name':'Alpha Labs','total_applicants':12},
        {'company_name':'Beta Systems','total_applicants':8}
    ],
    'recent_applications':[
        {'student_name':'Candidate Alpha','branch':'CSE','company_name':'Alpha Labs',
         'status':'Selected','application_date':'2026-01-10'}
    ]
}
person_one._fetch_placement_summary_data=lambda:{
    'total_students':10,'uniquely_placed_students':7,'placement_percentage':70,
    'branch_summary':branch_rows,'company_hiring_funnel':[]
}
person_two.get_company_analytics=lambda:{
    'summary':{'total_companies':2,'total_offers':9,'total_placements':7},
    'companies':company_rows,
    'top_recruiters':[],
    'chart':{'labels':['Alpha Labs','Beta Systems'],'datasets':[]}
}
person_two.get_branch_analytics=lambda:{
    'summary':{'total_students':10,'placed_students':7,'overall_placement_percentage':70},
    'branches':branch_rows,
    'chart':{'labels':['CSE','ECE'],'datasets':[]}
}
person_two.get_package_analytics=lambda:{
    'overall':{'placements':7,'highest_package':21,'average_package':10.29,'lowest_package':6},
    'by_company':package_rows,'by_branch':[],
    'chart':{'company_comparison':{},'branch_comparison':{}}
}
class FakeConn:
    def close(self): pass
frontend.database.get_db_connection=lambda:FakeConn()
frontend._interview_data=lambda conn,filters:interviews
app.view_functions['dashboard_api.filters'] = lambda: jsonify({
    'success':True,'data':{
        'branches':['CSE','ECE'],'companies':[
            {'company_id':1,'company_name':'Alpha Labs'},
            {'company_id':2,'company_name':'Beta Systems'}],
        'years':[2026]
    }
})
app.view_functions['dashboard_api.scoped_analytics'] = lambda: jsonify({
    'success':True,'data':{
        'summary':{'students':6,'placed':4,'placement_rate':66.67,
                   'applications':12,'selected':5,'rejected':3,'pending':4,
                   'highest_package':21,'average_package':12,'lowest_package':7},
        'statuses':[{'status':'Selected','count':5},{'status':'Rejected','count':3},{'status':'Applied','count':4}],
        'branches':[branch_rows[0]],
        'companies':[
            {'company_id':1,'company_name':'Alpha Labs','offers_made':5,'students_placed':4,
             'average_package':12,'highest_package':21}
        ],
        'interviews':interviews,
        'recent':[{'student_name':'Candidate Alpha','branch':'CSE','company_name':'Alpha Labs',
                   'status':'Selected','application_date':'2026-01-10'}]
    }
})
if __name__=='__main__':
    app.run(host='127.0.0.1',port=5077,debug=False,threaded=True)
