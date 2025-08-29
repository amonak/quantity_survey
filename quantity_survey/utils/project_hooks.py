# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _

def validate_project(doc, method):
    """Validate project for quantity survey integration"""
    if doc.is_new():
        # Set default values for quantity survey projects
        if not doc.get("qs_enabled"):
            doc.qs_enabled = 1
        
        # Create default cost plan if enabled
        if doc.get("auto_create_cost_plan"):
            create_default_cost_plan(doc)

def update_project_status(doc, method):
    """Update project status based on quantity survey progress"""
    if doc.get("qs_enabled"):
        update_qs_project_progress(doc)

def create_default_cost_plan(project_doc):
    """Create default cost plan for project"""
    try:
        cost_plan = melon.new_doc("Cost Plan")
        cost_plan.project = project_doc.name
        cost_plan.project_name = project_doc.project_name
        cost_plan.cost_plan_name = f"Default Cost Plan - {project_doc.project_name}"
        cost_plan.planned_start_date = project_doc.expected_start_date
        cost_plan.planned_end_date = project_doc.expected_end_date
        cost_plan.total_budget = project_doc.estimated_costing
        cost_plan.status = "Draft"
        cost_plan.save()
        
        melon.msgprint(_("Default Cost Plan created for project: {0}").format(cost_plan.name))
    except Exception as e:
        melon.log_error(f"Error creating default cost plan: {str(e)}")

def update_qs_project_progress(project_doc):
    """Update project progress based on quantity survey data"""
    try:
        # Get all valuations for this project
        valuations = melon.get_list("Valuation",
            filters={"project": project_doc.name, "docstatus": 1},
            fields=["name", "total_work_done", "contract_value"]
        )
        
        if valuations:
            total_work_done = sum([v.total_work_done for v in valuations])
            total_contract_value = sum([v.contract_value for v in valuations])
            
            if total_contract_value > 0:
                progress_percent = (total_work_done / total_contract_value) * 100
                project_doc.percent_complete = min(progress_percent, 100)
                
        # Update project status based on progress
        if project_doc.percent_complete >= 100:
            project_doc.status = "Completed"
        elif project_doc.percent_complete > 0:
            project_doc.status = "Open"
            
    except Exception as e:
        melon.log_error(f"Error updating project progress: {str(e)}")

def get_project_summary(project):
    """Get quantity survey summary for project"""
    summary = {
        "boqs": 0,
        "valuations": 0,
        "payment_certificates": 0,
        "variation_orders": 0,
        "total_contract_value": 0,
        "total_work_done": 0,
        "total_certified": 0,
        "total_paid": 0
    }
    
    try:
        # Count documents
        summary["boqs"] = melon.db.count("Bill of Quantities", {"project": project})
        summary["valuations"] = melon.db.count("Valuation", {"project": project})
        summary["payment_certificates"] = melon.db.count("Payment Certificate", {"project": project})
        summary["variation_orders"] = melon.db.count("Variation Order", {"project": project})
        
        # Sum amounts
        boq_total = melon.db.sql("""
            SELECT IFNULL(SUM(total_amount), 0)
            FROM `tabBill of Quantities`
            WHERE project = %s AND docstatus = 1
        """, project)[0][0]
        
        valuation_total = melon.db.sql("""
            SELECT IFNULL(SUM(total_work_done), 0)
            FROM `tabValuation`
            WHERE project = %s AND docstatus = 1
        """, project)[0][0]
        
        certificate_total = melon.db.sql("""
            SELECT IFNULL(SUM(certified_amount), 0)
            FROM `tabPayment Certificate`
            WHERE project = %s AND docstatus = 1
        """, project)[0][0]
        
        summary["total_contract_value"] = boq_total
        summary["total_work_done"] = valuation_total
        summary["total_certified"] = certificate_total
        
    except Exception as e:
        melon.log_error(f"Error getting project summary: {str(e)}")
    
    return summary
