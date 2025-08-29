# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import today, add_days, getdate

def archive_completed_projects():
    """Archive projects that have been completed for over 6 months"""
    try:
        six_months_ago = add_days(today(), -180)
        
        # Get completed projects older than 6 months
        completed_projects = melon.get_list("Project",
            filters={
                "status": "Completed",
                "actual_end_date": ["<", six_months_ago]
            },
            fields=["name", "project_name", "actual_end_date"]
        )
        
        for project in completed_projects:
            archive_project_data(project)
            
        melon.logger().info(f"Archived {len(completed_projects)} completed projects")
        
    except Exception as e:
        melon.log_error(f"Error archiving completed projects: {str(e)}")

def generate_monthly_summary():
    """Generate monthly summary reports for all projects"""
    try:
        # Get all projects with activity in the last month
        last_month = add_days(today(), -30)
        
        active_projects = melon.get_list("Project",
            filters={
                "qs_enabled": 1,
                "modified": [">=", last_month]
            },
            fields=["name", "project_name", "project_manager"]
        )
        
        # Generate monthly summary
        monthly_summary = generate_overall_monthly_summary()
        
        # Send summary to administrators
        send_monthly_summary_email(monthly_summary)
        
        melon.logger().info("Generated monthly summary reports")
        
    except Exception as e:
        melon.log_error(f"Error generating monthly summary: {str(e)}")

def archive_project_data(project):
    """Archive data for a completed project"""
    try:
        # Create archive entry
        archive = melon.new_doc("Project Archive")
        archive.project = project.name
        archive.project_name = project.project_name
        archive.archive_date = today()
        archive.completion_date = project.actual_end_date
        
        # Archive summary data
        summary = get_project_archive_summary(project.name)
        
        archive.total_boqs = summary.get("boqs", 0)
        archive.total_valuations = summary.get("valuations", 0)
        archive.total_certificates = summary.get("certificates", 0)
        archive.total_variations = summary.get("variations", 0)
        archive.final_contract_value = summary.get("contract_value", 0)
        archive.total_certified = summary.get("certified", 0)
        
        archive.save()
        
        # Mark project as archived
        melon.db.set_value("Project", project.name, "is_archived", 1)
        melon.db.commit()
        
    except Exception as e:
        melon.log_error(f"Error archiving project {project.name}: {str(e)}")

def get_project_archive_summary(project_name):
    """Get archive summary for project"""
    summary = {}
    
    try:
        # Count all documents
        summary["boqs"] = melon.db.count("Bill of Quantities", {"project": project_name})
        summary["valuations"] = melon.db.count("Valuation", {"project": project_name})
        summary["certificates"] = melon.db.count("Payment Certificate", {"project": project_name})
        summary["variations"] = melon.db.count("Variation Order", {"project": project_name})
        
        # Get final amounts
        contract_value = melon.db.sql("""
            SELECT IFNULL(SUM(total_amount), 0)
            FROM `tabBill of Quantities`
            WHERE project = %s AND docstatus = 1
        """, project_name)[0][0]
        
        certified = melon.db.sql("""
            SELECT IFNULL(SUM(certified_amount), 0)
            FROM `tabPayment Certificate`
            WHERE project = %s AND docstatus = 1
        """, project_name)[0][0]
        
        summary["contract_value"] = contract_value
        summary["certified"] = certified
        
    except Exception as e:
        melon.log_error(f"Error getting archive summary: {str(e)}")
    
    return summary

def generate_overall_monthly_summary():
    """Generate overall monthly summary across all projects"""
    summary = {
        "active_projects": 0,
        "completed_projects": 0,
        "new_projects": 0,
        "total_boqs": 0,
        "total_valuations": 0,
        "total_certificates": 0,
        "total_work_done": 0,
        "total_certified": 0
    }
    
    try:
        last_month = add_days(today(), -30)
        
        # Count active projects
        summary["active_projects"] = melon.db.count("Project", {
            "status": ["in", ["Open", "Overdue"]],
            "qs_enabled": 1
        })
        
        # Count completed projects this month
        summary["completed_projects"] = melon.db.count("Project", {
            "status": "Completed",
            "actual_end_date": [">=", last_month]
        })
        
        # Count new projects this month
        summary["new_projects"] = melon.db.count("Project", {
            "creation": [">=", last_month],
            "qs_enabled": 1
        })
        
        # Count documents created this month
        summary["total_boqs"] = melon.db.count("Bill of Quantities", {
            "creation": [">=", last_month]
        })
        
        summary["total_valuations"] = melon.db.count("Valuation", {
            "creation": [">=", last_month]
        })
        
        summary["total_certificates"] = melon.db.count("Payment Certificate", {
            "creation": [">=", last_month]
        })
        
        # Get amounts for this month
        work_done = melon.db.sql("""
            SELECT IFNULL(SUM(total_work_done), 0)
            FROM `tabValuation`
            WHERE creation >= %s AND docstatus = 1
        """, last_month)[0][0]
        
        certified = melon.db.sql("""
            SELECT IFNULL(SUM(certified_amount), 0)
            FROM `tabPayment Certificate`
            WHERE creation >= %s AND docstatus = 1
        """, last_month)[0][0]
        
        summary["total_work_done"] = work_done
        summary["total_certified"] = certified
        
    except Exception as e:
        melon.log_error(f"Error generating monthly summary: {str(e)}")
    
    return summary

def send_monthly_summary_email(summary):
    """Send monthly summary email to administrators"""
    try:
        # Get system managers
        managers = melon.get_list("User",
            filters={"role_profile_name": "System Manager"},
            fields=["email"]
        )
        
        if not managers:
            return
            
        recipients = [m.email for m in managers if m.email]
        
        if not recipients:
            return
            
        subject = f"Monthly Quantity Survey Summary - {today()}"
        
        message = f"""
        Monthly Quantity Survey Summary
        
        Project Statistics:
        - Active Projects: {summary['active_projects']}
        - Projects Completed This Month: {summary['completed_projects']}
        - New Projects This Month: {summary['new_projects']}
        
        Document Activity This Month:
        - BoQs Created: {summary['total_boqs']}
        - Valuations Created: {summary['total_valuations']}
        - Certificates Created: {summary['total_certificates']}
        
        Financial Summary:
        - Total Work Done: {summary['total_work_done']:,.2f}
        - Total Certified: {summary['total_certified']:,.2f}
        
        Generated on: {today()}
        """
        
        melon.sendmail(
            recipients=recipients,
            subject=subject,
            message=message
        )
        
    except Exception as e:
        melon.log_error(f"Error sending monthly summary email: {str(e)}")

def cleanup_archived_data():
    """Clean up very old archived data"""
    try:
        # Clean up archived projects older than 5 years
        five_years_ago = add_days(today(), -1825)
        
        old_archives = melon.get_list("Project Archive",
            filters={"archive_date": ["<", five_years_ago]},
            fields=["name"]
        )
        
        for archive in old_archives:
            # Move to deep archive or delete based on policy
            pass  # Implement based on data retention policy
            
    except Exception as e:
        melon.log_error(f"Error cleaning up archived data: {str(e)}")

def generate_annual_report():
    """Generate annual report if it's end of year"""
    try:
        from datetime import datetime
        
        # Check if it's December (month 12)
        if datetime.now().month == 12:
            # Generate annual report
            annual_summary = generate_annual_summary()
            save_annual_report(annual_summary)
            
    except Exception as e:
        melon.log_error(f"Error generating annual report: {str(e)}")

def generate_annual_summary():
    """Generate annual summary data"""
    # Implementation for annual summary
    pass

def save_annual_report(summary):
    """Save annual report to file"""
    # Implementation for saving annual report
    pass
