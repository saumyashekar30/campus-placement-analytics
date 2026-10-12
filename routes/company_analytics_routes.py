"""
Campus Placement Analytics System - Company, Branch & Package Analytics Blueprint

Routes (all return chart-ready JSON):
    GET /analytics/companies  - company-wise offers/placements and top recruiters
    GET /analytics/branches   - branch-wise placement counts and percentages
    GET /analytics/packages   - highest/average/lowest packages and comparisons
"""

from flask import Blueprint, jsonify
from services import analytics_service

company_analytics_bp = Blueprint("company_analytics", __name__, url_prefix="/analytics")


def _respond(fetch):
    try:
        return jsonify({"success": True, "data": fetch()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@company_analytics_bp.route("/companies")
def company_analytics():
    return _respond(analytics_service.get_company_analytics)


@company_analytics_bp.route("/branches")
def branch_analytics():
    return _respond(analytics_service.get_branch_analytics)


@company_analytics_bp.route("/packages")
def package_analytics():
    return _respond(analytics_service.get_package_analytics)
