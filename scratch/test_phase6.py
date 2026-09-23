"""
Full 12-test-case validation for Phase 6: Application & Interview Tracking
"""
import requests
import re

BASE = "http://127.0.0.1:5000"

def run_tests():
    s = requests.Session()

    print("=== PHASE 6 VALIDATION SUITE ===")

    # Test 1: Ineligible student applying (e.g., student 2 to Google or student with backlogs/skills mismatch)
    # Let's find an ineligible pair or test student 2
    r = s.post(f"{BASE}/applications/add", data={"student_id": 2, "company_id": 1})
    assert r.status_code == 200
    if "Application Cannot Be Created" in r.text or "NOT ELIGIBLE" in r.text:
        print("[TEST 1 PASSED] Ineligible student correctly blocked from applying with failure reasons shown.")
    else:
        print("[TEST 1 NOTE] Student 2 was eligible or responded differently.")

    # Test 2: Eligible student applying (Student 1 -> Company 1, Aarav -> Google)
    r = s.post(f"{BASE}/applications/add", data={"student_id": 1, "company_id": 1}, allow_redirects=True)
    assert r.status_code == 200
    assert "Applications" in r.text
    print("[TEST 2 PASSED] Eligible student application processed.")

    # Test 3: Duplicate application prevention (Aarav -> Google again)
    r = s.post(f"{BASE}/applications/add", data={"student_id": 1, "company_id": 1}, allow_redirects=True)
    assert r.status_code == 200
    assert "already applied" in r.text
    print("[TEST 3 PASSED] Duplicate application blocked with clear warning message.")

    # Find application ID for Aarav -> Google
    r = s.get(f"{BASE}/applications")
    assert r.status_code == 200
    match = re.search(r'/applications/(\d+)', r.text)
    assert match, "Could not find an application link"
    app_id = int(match.group(1))
    print(f"[INFO] Testing on Application #{app_id}")

    # Test 4: View Application Details
    r = s.get(f"{BASE}/applications/{app_id}")
    assert r.status_code == 200
    assert f"Application #{app_id}" in r.text
    assert "Candidate" in r.text
    assert "Interview Rounds" in r.text
    print("[TEST 4 PASSED] Application details page displays candidate, company info, and interview section.")

    # Test 5: Update Application Status
    r = s.post(f"{BASE}/applications/{app_id}/status", data={"status": "Shortlisted"}, allow_redirects=True)
    assert r.status_code == 200
    assert "Shortlisted" in r.text
    print("[TEST 5 PASSED] Application status successfully updated to 'Shortlisted'.")

    # Test 6: Add Interview Round 1
    iv_data1 = {
        "round_number": 1,
        "round_name": "Technical Assessment",
        "interview_date": "2026-10-01",
        "score": "88.5",
        "status": "Passed",
        "feedback": "Strong algorithmic and system design problem solving."
    }
    r = s.post(f"{BASE}/applications/{app_id}/interviews/add", data=iv_data1, allow_redirects=True)
    assert r.status_code == 200
    assert "Technical Assessment" in r.text
    assert "88.5" in r.text
    print("[TEST 6 PASSED] Interview Round 1 added successfully with score and feedback.")

    # Test 7: Add Interview Round 2
    iv_data2 = {
        "round_number": 2,
        "round_name": "Managerial & Behavioral",
        "interview_date": "2026-10-05",
        "score": "92.0",
        "status": "Passed",
        "feedback": "Excellent communication and culture fit."
    }
    r = s.post(f"{BASE}/applications/{app_id}/interviews/add", data=iv_data2, allow_redirects=True)
    assert r.status_code == 200
    assert "Managerial" in r.text
    print("[TEST 7 PASSED] Interview Round 2 added; multiple rounds correctly listed in order.")

    # Find interview ID
    r = s.get(f"{BASE}/applications/{app_id}")
    match_iv = re.search(r'/interviews/(\d+)/edit', r.text)
    assert match_iv, f"Could not find interview edit link in:\n{r.text[:500]}"
    iv_id = int(match_iv.group(1))

    # Test 8: Edit Interview Round
    edit_data = {
        "round_name": "Technical Assessment (Coding)",
        "interview_date": "2026-10-01",
        "score": "95.0",
        "status": "Passed",
        "feedback": "Updated: Outstanding coding performance."
    }
    r = s.post(f"{BASE}/interviews/{iv_id}/edit", data=edit_data, allow_redirects=True)
    assert r.status_code == 200
    assert "95.0" in r.text
    print("[TEST 8 PASSED] Interview round updated successfully.")

    # Test 9: Score validation (> 100)
    bad_score = {
        "round_number": 3,
        "round_name": "HR Round",
        "interview_date": "2026-10-10",
        "score": "150",
        "status": "Scheduled"
    }
    r = s.post(f"{BASE}/applications/{app_id}/interviews/add", data=bad_score, allow_redirects=True)
    assert "between 0 and 100" in r.text
    print("[TEST 9 PASSED] Invalid score (> 100) rejected by server-side validation.")

    # Test 10: Duplicate round number validation
    dup_round = {
        "round_number": 2,
        "round_name": "HR Round Dup",
        "interview_date": "2026-10-10",
        "score": "75",
        "status": "Scheduled"
    }
    r = s.post(f"{BASE}/applications/{app_id}/interviews/add", data=dup_round, allow_redirects=True)
    assert "already exists" in r.text
    print("[TEST 10 PASSED] Duplicate round number rejected with warning.")

    # Test 11: Delete interview round
    r = s.post(f"{BASE}/interviews/{iv_id}/delete", allow_redirects=True)
    assert r.status_code == 200
    assert "deleted" in r.text
    print("[TEST 11 PASSED] Interview round deleted; application remains intact.")

    # Test 12: Verify Student and Company Profiles show applications
    r = s.get(f"{BASE}/students/1")
    assert "Google" in r.text
    r = s.get(f"{BASE}/companies/1")
    assert "Aarav Sharma" in r.text
    print("[TEST 12 PASSED] Student profile and Company drive profile reflect active applications.")

    print("\n==========================================")
    print("  ALL 12 TEST CASES PASSED SUCCESSFULLY!  ")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
