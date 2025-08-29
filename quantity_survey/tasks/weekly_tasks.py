# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import today, add_days

def generate_progress_reports():
    """Generate weekly progress reports for all active projects"""
    try:
        # Get all active projects
        projects = melon.get_list("Project",
            filters={
                "status": ["in", ["Open", "Overdue"]],
                "qs_enabled": 1
            },
            fields=["name", "project_name", "project_manager"]
        )
        
        for project in projects:
            generate_project_progress_report(project)
            
        melon.logger().info(f"Generated progress reports for {len(projects)} projects")
        
    except Exception as e:
        melon.log_error(f"Error generating progress reports: {str(e)}")

def cleanup_temp_files():
    """Cleanup temporary files and logs"""
    try:
        # Clean up old measurement photos
        cleanup_old_measurement_photos()
        
        # Clean up old progress photos
        cleanup_old_progress_photos()
        
        # Clean up old notification logs
        cleanup_old_notifications()
        
        melon.logger().info("Completed weekly cleanup tasks")
        
    except Exception as e:
        melon.log_error(f"Error in weekly cleanup: {str(e)}")

def generate_project_progress_report(project):
    """Generate progress report for a single project"""
    try:
        # Get project summary data
        summary = get_project_weekly_summary(project.name)
        
        # Create progress report document
        report = melon.new_doc("Progress Report")
        report.project = project.name
        report.project_name = project.project_name
        report.report_date = today()
        report.report_type = "Weekly"
        
        # Add summary data
        report.total_boqs = summary.get("boqs", 0)
        report.total_valuations = summary.get("valuations", 0)
        report.total_certificates = summary.get("certificates", 0)
        report.total_work_done = summary.get("work_done", 0)
        report.total_certified = summary.get("certified", 0)
        
        # Calculate progress
        if summary.get("contract_value", 0) > 0:
            report.progress_percentage = (summary.get("work_done", 0) / summary.get("contract_value", 0)) * 100
        
        report.save()
        
        # Send email to project manager if configured
        if project.get("project_manager"):
            send_progress_report_email(project, report)
            
    except Exception as e:
        melon.log_error(f"Error generating progress report for {project.name}: {str(e)}")

def get_project_weekly_summary(project_name):
    """Get weekly summary data for project"""
    summary = {}
    
    try:
        # Count documents created this week
        week_start = add_days(today(), -7)
        
        summary["boqs"] = melon.db.count("Bill of Quantities", {
            "project": project_name,
            "creation": [">=", week_start]
        })
        
        summary["valuations"] = melon.db.count("Valuation", {
            "project": project_name,
            "creation": [">=", week_start]
        })
        
        summary["certificates"] = melon.db.count("Payment Certificate", {
            "project": project_name,
            "creation": [">=", week_start]
        })
        
        # Get amounts
        work_done = melon.db.sql("""
            SELECT IFNULL(SUM(total_work_done), 0)
            FROM `tabValuation`
            WHERE project = %s AND docstatus = 1
        """, project_name)[0][0]
        
        certified = melon.db.sql("""
            SELECT IFNULL(SUM(certified_amount), 0)
            FROM `tabPayment Certificate`
            WHERE project = %s AND docstatus = 1
        """, project_name)[0][0]
        
        contract_value = melon.db.sql("""
            SELECT IFNULL(SUM(total_amount), 0)
            FROM `tabBill of Quantities`
            WHERE project = %s AND docstatus = 1
        """, project_name)[0][0]
        
        summary["work_done"] = work_done
        summary["certified"] = certified
        summary["contract_value"] = contract_value
        
    except Exception as e:
        melon.log_error(f"Error getting project summary: {str(e)}")
    
    return summary

def cleanup_old_measurement_photos():
    """Clean up measurement photos older than 6 months"""
    try:
        six_months_ago = add_days(today(), -180)
        
        old_photos = melon.get_list("Measurement Entry",
            filters={"creation": ["<", six_months_ago]},
            fields=["name", "photo_attachment"]
        )
        
        for photo in old_photos:
            if photo.photo_attachment:
                # Archive or delete old photo files
                pass  # Implement based on storage policy
                
    except Exception as e:
        melon.log_error(f"Error cleaning up measurement photos: {str(e)}")

def cleanup_old_progress_photos():
    """Clean up progress photos older than 1 year"""
    try:
        one_year_ago = add_days(today(), -365)
        
        old_photos = melon.get_list("Progress Photo",
            filters={"creation": ["<", one_year_ago]},
            fields=["name", "image"]
        )
        
        for photo in old_photos:
            if photo.image:
                # Archive or delete old photo files
                pass  # Implement based on storage policy
                
    except Exception as e:
        melon.log_error(f"Error cleaning up progress photos: {str(e)}")

def cleanup_old_notifications():
    """Clean up old notification logs"""
    try:
        thirty_days_ago = add_days(today(), -30)
        
        # Delete old notification logs
        melon.db.sql("""
            DELETE FROM `tabNotification Log`
            WHERE creation < %s
            AND read = 1
        """, thirty_days_ago)
        
        melon.db.commit()
        
    except Exception as e:
        melon.log_error(f"Error cleaning up notifications: {str(e)}")

def send_progress_report_email(project, report):
    """Send progress report email to project manager"""
    try:
        project_manager = melon.get_doc("User", project.project_manager)
        
        if not project_manager.email:
            return
            
        subject = f"Weekly Progress Report - {project.project_name}"
        message = f"""
        Weekly Progress Report for {project.project_name}
        
        Report Date: {report.report_date}
        Progress: {report.progress_percentage:.1f}%
        
        This Week:
        - BoQs Created: {report.total_boqs}
        - Valuations: {report.total_valuations}
        - Certificates: {report.total_certificates}
        
        Totals:
        - Work Done: {report.total_work_done}
        - Certified: {report.total_certified}
        
        View full report: {melon.utils.get_url()}/app/progress-report/{report.name}
        """
        
        melon.sendmail(
            recipients=[project_manager.email],
            subject=subject,
            message=message
        )
        
    except Exception as e:
        melon.log_error(f"Error sending progress report email: {str(e)}")
