"""Regression checks for the dashboard contract without requiring an Oracle instance."""
import unittest
from unittest.mock import patch
from app import app
from routes import dashboard_api_routes as dashboard


class FakeConnection:
    def close(self):
        pass


class DashboardRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_dashboard_loads_even_when_oracle_is_offline(self):
        with patch("database.get_db_connection", side_effect=RuntimeError("unavailable")):
            page = self.client.get("/analytics")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Placement intelligence", page.data)
        self.assertIn(b"/static/js/dashboard.js", page.data)

    def test_invalid_filters_return_400(self):
        for query in ["year=abc", "year=1920", "company=0", "company=1%20OR%201=1", "branch=" + "x"*21]:
            response = self.client.get("/analytics/dashboard-scoped?" + query)
            self.assertEqual(response.status_code, 400, query)

    def test_conditions_are_bound_not_interpolated(self):
        f={"branch":"CSE' OR '1'='1","company":2,"year":2026}
        where, params = dashboard._conditions(f)
        self.assertNotIn("CSE'", where)
        self.assertEqual(params["branch"], f["branch"])
        self.assertEqual(params["company_id"], 2)
        self.assertEqual(params["start_date"].year, 2026)
        self.assertEqual(params["end_date"].year, 2027)

    def test_interviews_exclude_open_interviews_from_success_rate(self):
        fake_results=[
            [{"status":"Passed","count":4},{"status":"Failed","count":1},
             {"status":"Scheduled","count":3},{"status":"Pending","count":2}],
            [{"round_number":1,"round_name":"Technical","total":10,"passed":4,"failed":1}],
        ]
        with patch("database.get_db_connection",return_value=FakeConnection()),patch.object(dashboard,"_query",side_effect=fake_results) as db:
            response=self.client.get("/analytics/interviews?branch=CSE&company=2&year=2026")
        self.assertEqual(response.status_code,200)
        data=response.get_json()["data"]
        self.assertEqual(data["total"],10)
        self.assertEqual(data["success_rate"],80)
        self.assertEqual(data["rounds"][0]["pass_rate"],80)
        sql,binds=db.call_args_list[0].args[1:]
        self.assertIn("i.interview_date >= :start_date",sql)
        self.assertIn("a.company_id = :company_id",sql)
        self.assertEqual(binds["branch"],"CSE")

    def test_scoped_analytics_returns_consistent_payload(self):
        observed=[]
        def query(_conn, sql, binds=None):
            observed.append((sql,binds))
            if "COUNT(*) AS total FROM STUDENT" in sql:return [{"total":10}]
            if "SELECT a.status, COUNT(*) AS count" in sql:
                return [{"status":"Selected","count":3},{"status":"Rejected","count":2},{"status":"Applied","count":5}]
            if "COUNT(DISTINCT p.student_id) AS placed," in sql:
                return [{"placed":3,"accepted_offers":3,"highest":16,"average":12,"lowest":7}]
            if "COUNT(DISTINCT s.student_id) AS total_students" in sql:
                return [{"branch":"CSE","total_students":10,"placed_students":3}]
            if "COUNT(*) AS offers_made" in sql:return [{"company_id":5,"company_name":"Demo Corp","offers_made":4,"students_placed":3,"average_package":12,"highest_package":16}]
            if "SELECT a.company_id, COUNT(*) AS applications" in sql:return [{"company_id":5,"applications":10}]
            if "SELECT a.application_id, s.student_name" in sql:return []
            if "SELECT i.status, COUNT(*) AS count" in sql:return [{"status":"Passed","count":2},{"status":"Failed","count":1}]
            if "SELECT i.round_number" in sql:return [{"round_number":1,"round_name":"Technical","total":3,"passed":2,"failed":1}]
            raise AssertionError("Unexpected query: " + sql)
        with patch("database.get_db_connection",return_value=FakeConnection()),patch.object(dashboard,"_query",side_effect=query):
            result=self.client.get("/analytics/dashboard-scoped?branch=CSE&company=5&year=2026")
        self.assertEqual(result.status_code,200,result.data)
        data=result.get_json()["data"]
        self.assertEqual(data["summary"]["students"],10)
        self.assertEqual(data["summary"]["placed"],3)
        self.assertEqual(data["summary"]["placement_rate"],30)
        self.assertEqual(data["summary"]["pending"],5)
        self.assertEqual(data["companies"][0]["applications"],10)
        self.assertEqual(data["interviews"]["success_rate"],66.67)
        for sql,binds in observed:
            if "INSERT" in sql or "DELETE" in sql:raise AssertionError("Unexpected write")
        self.assertTrue(any("EXISTS (SELECT 1 FROM APPLICATION" in sql for sql,_ in observed))

    def test_missing_oracle_returns_generic_service_error(self):
        with patch("database.get_db_connection",side_effect=RuntimeError("sensitive-credential-string")):
            response=self.client.get("/analytics/interviews")
        self.assertEqual(response.status_code,503)
        self.assertNotIn(b"sensitive-credential-string",response.data)


if __name__ == "__main__":
    unittest.main()
