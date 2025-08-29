"""
Quantity Survey Module Utilities
Common utility functions for the Quantity Survey application
"""

import melon
from melon import _
from melon.utils import flt, cint, getdate, now_datetime
from typing import Dict, List, Optional, Any


def get_project_financial_summary(project: str) -> Dict[str, float]:
	"""
	Get comprehensive financial summary for a project
	
	Args:
		project (str): Project name
		
	Returns:
		Dict: Financial summary with totals
	"""
	if not project:
		melon.throw(_("Project is required"))
	
	try:
		summary = {
			'total_boq_value': 0.0,
			'total_valuations': 0.0,
			'total_variations': 0.0,
			'total_payments': 0.0,
			'outstanding_amount': 0.0,
			'completion_percentage': 0.0
		}
		
		# Get BOQ totals
		boq_data = melon.db.get_all('BOQ',
			filters={'project': project, 'docstatus': 1},
			fields=['total_amount']
		)
		summary['total_boq_value'] = sum(flt(d.total_amount) for d in boq_data)
		
		# Get valuation totals
		val_data = melon.db.get_all('Valuation',
			filters={'project': project, 'docstatus': 1},
			fields=['total_amount']
		)
		summary['total_valuations'] = sum(flt(d.total_amount) for d in val_data)
		
		# Get variation totals
		var_data = melon.db.get_all('Variation Order',
			filters={'project': project, 'docstatus': 1},
			fields=['total_amount']
		)
		summary['total_variations'] = sum(flt(d.total_amount) for d in var_data)
		
		# Get payment totals
		pay_data = melon.db.get_all('Payment Certificate',
			filters={'project': project, 'docstatus': 1},
			fields=['certificate_amount']
		)
		summary['total_payments'] = sum(flt(d.certificate_amount) for d in pay_data)
		
		# Calculate outstanding
		summary['outstanding_amount'] = summary['total_valuations'] - summary['total_payments']
		
		# Calculate completion percentage
		if summary['total_boq_value'] > 0:
			summary['completion_percentage'] = (summary['total_valuations'] / summary['total_boq_value']) * 100
		
		return summary
		
	except Exception as e:
		melon.log_error(f"Project financial summary error: {str(e)}", "QS Utilities")
		return {}


def validate_project_permissions(project: str, permission_type: str = "read") -> bool:
	"""
	Validate user permissions for a project
	
	Args:
		project (str): Project name
		permission_type (str): Permission type (read/write/create/delete)
		
	Returns:
		bool: True if user has permission
	"""
	if not project:
		return False
		
	try:
		return melon.has_permission("Project", permission_type, project)
	except Exception:
		return False


def get_item_rate_history(item_code: str, project: str = None, limit: int = 10) -> List[Dict]:
	"""
	Get rate history for an item
	
	Args:
		item_code (str): Item code
		project (str): Optional project filter
		limit (int): Maximum number of records
		
	Returns:
		List[Dict]: Rate history records
	"""
	if not item_code:
		return []
	
	try:
		conditions = {"item_code": item_code}
		if project:
			# Get BOQs for the project
			boq_names = melon.get_all('BOQ', 
				filters={'project': project}, 
				pluck='name'
			)
			if boq_names:
				conditions["parent"] = ["in", boq_names]
		
		return melon.get_all('BOQ Item',
			filters=conditions,
			fields=['rate', 'quantity', 'amount', 'parent', 'creation'],
			order_by='creation desc',
			limit=limit
		)
		
	except Exception as e:
		melon.log_error(f"Rate history error: {str(e)}", "QS Utilities")
		return []


def calculate_percentage_complete(boq_amount: float, valuation_amount: float) -> float:
	"""
	Calculate percentage completion
	
	Args:
		boq_amount (float): BOQ total amount
		valuation_amount (float): Valuation total amount
		
	Returns:
		float: Percentage completion
	"""
	if not boq_amount or boq_amount <= 0:
		return 0.0
		
	return min(100.0, (flt(valuation_amount) / flt(boq_amount)) * 100)


def validate_date_range(from_date: str, to_date: str) -> bool:
	"""
	Validate date range
	
	Args:
		from_date (str): From date
		to_date (str): To date
		
	Returns:
		bool: True if valid
	"""
	try:
		if not from_date or not to_date:
			return True  # Optional dates are valid
			
		from_dt = getdate(from_date)
		to_dt = getdate(to_date)
		
		return from_dt <= to_dt
		
	except Exception:
		return False


def format_currency_value(value: Any, currency: str = None) -> str:
	"""
	Format currency value with proper symbols
	
	Args:
		value: Value to format
		currency: Currency code
		
	Returns:
		str: Formatted currency string
	"""
	try:
		if currency:
			return melon.utils.fmt_money(flt(value), currency=currency)
		else:
			return melon.utils.fmt_money(flt(value))
	except Exception:
		return str(flt(value))


def get_default_company() -> str:
	"""
	Get default company for current user
	
	Returns:
		str: Company name
	"""
	try:
		return melon.defaults.get_user_default("Company") or melon.defaults.get_global_default("default_company")
	except Exception:
		return ""


def check_mandatory_fields(doc: Dict, mandatory_fields: List[str]) -> List[str]:
	"""
	Check if mandatory fields are present
	
	Args:
		doc (Dict): Document dictionary
		mandatory_fields (List[str]): List of mandatory field names
		
	Returns:
		List[str]: List of missing fields
	"""
	missing_fields = []
	
	for field in mandatory_fields:
		if not doc.get(field):
			missing_fields.append(field)
			
	return missing_fields


def sanitize_filter_value(value: Any) -> Any:
	"""
	Sanitize filter values for database queries
	
	Args:
		value: Filter value
		
	Returns:
		Any: Sanitized value
	"""
	if isinstance(value, str):
		# Remove potential SQL injection patterns
		return value.strip().replace(';', '').replace('--', '').replace('/*', '').replace('*/', '')
	
	return value


def get_user_projects(user: str = None) -> List[str]:
	"""
	Get projects accessible to user
	
	Args:
		user (str): User email (optional, defaults to current user)
		
	Returns:
		List[str]: Project names
	"""
	if not user:
		user = melon.session.user
		
	try:
		# Get projects where user has permission
		projects = melon.get_all('Project',
			filters={},  # Will be filtered by permissions
			fields=['name'],
			limit_page_length=0
		)
		
		return [p.name for p in projects]
		
	except Exception as e:
		melon.log_error(f"User projects error: {str(e)}", "QS Utilities")
		return []


def log_activity(doctype: str, docname: str, action: str, details: str = None):
	"""
	Log activity for audit trail
	
	Args:
		doctype (str): Document type
		docname (str): Document name
		action (str): Action performed
		details (str): Additional details
	"""
	try:
		activity_log = melon.get_doc({
			'doctype': 'Activity Log',
			'subject': f"{action} on {doctype} {docname}",
			'content': details or f"User {melon.session.user} performed {action}",
			'reference_doctype': doctype,
			'reference_name': docname,
			'status': 'Open'
		})
		activity_log.insert(ignore_permissions=True)
		
	except Exception as e:
		melon.log_error(f"Activity log error: {str(e)}", "QS Utilities")


@melon.whitelist()
def get_dashboard_data(project: str = None) -> Dict:
	"""
	Get dashboard data for quantity survey
	
	Args:
		project (str): Optional project filter
		
	Returns:
		Dict: Dashboard data
	"""
	try:
		filters = {}
		if project:
			filters['project'] = project
		
		# Get counts
		boq_count = melon.db.count('BOQ', filters)
		valuation_count = melon.db.count('Valuation', filters)
		variation_count = melon.db.count('Variation Order', filters)
		payment_count = melon.db.count('Payment Certificate', filters)
		
		# Get financial data
		financial_summary = {}
		if project:
			financial_summary = get_project_financial_summary(project)
		
		return {
			'counts': {
				'boq_count': boq_count,
				'valuation_count': valuation_count,
				'variation_count': variation_count,
				'payment_count': payment_count
			},
			'financial_summary': financial_summary,
			'timestamp': now_datetime()
		}
		
	except Exception as e:
		melon.log_error(f"Dashboard data error: {str(e)}", "QS Utilities")
		return {}


def cleanup_temp_data():
	"""
	Clean up temporary data (called by scheduler)
	"""
	try:
		# Clean up old activity logs (older than 6 months)
		old_date = melon.utils.add_months(now_datetime(), -6)
		
		old_logs = melon.get_all('Activity Log',
			filters={
				'creation': ['<', old_date],
				'reference_doctype': ['in', ['BOQ', 'Valuation', 'Payment Certificate', 'Variation Order']]
			},
			pluck='name'
		)
		
		for log_name in old_logs:
			melon.delete_doc('Activity Log', log_name, ignore_permissions=True)
		
		melon.db.commit()
		
		if old_logs:
			melon.logger().info(f"Cleaned up {len(old_logs)} old activity logs")
			
	except Exception as e:
		melon.log_error(f"Cleanup error: {str(e)}", "QS Utilities")
