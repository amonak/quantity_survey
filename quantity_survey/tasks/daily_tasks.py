# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import today, add_days, getdate

def send_payment_reminders():
    """Send payment reminders for overdue certificates"""
    try:
        # Get overdue payment certificates
        overdue_certificates = melon.get_list("Payment Certificate",
            filters={
                "docstatus": 1,
                "status": ["!=", "Paid"],
                "due_date": ["<", today()]
            },
            fields=["name", "project", "certified_amount", "due_date", "contractor"]
        )
        
        for cert in overdue_certificates:
            send_payment_reminder_email(cert)
            
        if overdue_certificates:
            melon.logger().info(f"Sent {len(overdue_certificates)} payment reminders")
            
    except Exception as e:
        melon.log_error(f"Error sending payment reminders: {str(e)}")

def update_project_progress():
    """Update project progress based on latest valuations"""
    try:
        # Get all active projects with quantity survey enabled
        projects = melon.get_list("Project",
            filters={
                "status": ["in", ["Open", "Overdue"]],
                "qs_enabled": 1
            },
            fields=["name"]
        )
        
        for project in projects:
            update_single_project_progress(project.name)
            
        melon.logger().info(f"Updated progress for {len(projects)} projects")
        
    except Exception as e:
        melon.log_error(f"Error updating project progress: {str(e)}")

def send_payment_reminder_email(certificate):
    """Send payment reminder email for certificate"""
    try:
        # Get project manager email
        project_doc = melon.get_doc("Project", certificate.project)
        
        if not project_doc.get("project_manager_email"):
            return
            
        subject = f"Payment Reminder: Certificate {certificate.name}"
        message = f"""
        Dear Project Manager,
        
        This is a reminder that Payment Certificate {certificate.name} is overdue.
        
        Project: {certificate.project}
        Amount: {certificate.certified_amount}
        Due Date: {certificate.due_date}
        Days Overdue: {(getdate(today()) - getdate(certificate.due_date)).days}
        
        Please process the payment at your earliest convenience.
        
        Best regards,
        Quantity Survey System
        """
        
        melon.sendmail(
            recipients=[project_doc.project_manager_email],
            subject=subject,
            message=message
        )
        
    except Exception as e:
        melon.log_error(f"Error sending payment reminder email: {str(e)}")

def update_single_project_progress(project_name):
    """Update progress for a single project"""
    try:
        project_doc = melon.get_doc("Project", project_name)
        
        # Calculate progress from valuations
        valuations = melon.get_list("Valuation",
            filters={"project": project_name, "docstatus": 1},
            fields=["total_work_done", "contract_value"]
        )
        
        if valuations:
            total_work_done = sum([v.total_work_done for v in valuations])
            total_contract_value = sum([v.contract_value for v in valuations])
            
            if total_contract_value > 0:
                progress = min((total_work_done / total_contract_value) * 100, 100)
                
                # Update project if progress changed significantly
                if abs(project_doc.percent_complete - progress) > 1:
                    melon.db.set_value("Project", project_name, "percent_complete", progress)
                    melon.db.commit()
                    
    except Exception as e:
        melon.log_error(f"Error updating project {project_name} progress: {str(e)}")

def check_certificate_approvals():
    """Check for certificates pending approval"""
    try:
        pending_certificates = melon.get_list("Payment Certificate",
            filters={
                "docstatus": 0,
                "status": "Pending Approval",
                "creation": ["<", add_days(today(), -7)]
            },
            fields=["name", "project", "creation"]
        )
        
        # Send notification for certificates pending approval for more than 7 days
        for cert in pending_certificates:
            send_approval_reminder(cert)
            
    except Exception as e:
        melon.log_error(f"Error checking certificate approvals: {str(e)}")

def send_approval_reminder(certificate):
    """Send approval reminder for certificate"""
    try:
        # Create notification for approvers
        notification = melon.new_doc("Notification Log")
        notification.subject = f"Certificate {certificate.name} pending approval"
        notification.email_content = f"Payment Certificate {certificate.name} has been pending approval for more than 7 days"
        notification.document_type = "Payment Certificate"
        notification.document_name = certificate.name
        notification.for_user = "Administrator"  # Or get actual approver
        notification.save()
        
    except Exception as e:
        melon.log_error(f"Error sending approval reminder: {str(e)}")
