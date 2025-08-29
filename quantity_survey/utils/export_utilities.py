"""
Export and Integration Utilities
Provides data export/import capabilities for various formats
"""

import melon
from melon import _
from melon.utils import now_datetime, cstr, flt
import json
import csv
import io
import xlsxwriter
from typing import Dict, List, Any, Optional
import base64

@melon.whitelist()
def export_final_account_excel(final_account_name: str) -> Dict:
    """
    Export Final Account to Excel format
    """
    try:
        # Get Final Account document
        doc = melon.get_doc('Final Account', final_account_name)
        
        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Create worksheets
        summary_sheet = workbook.add_worksheet('Summary')
        items_sheet = workbook.add_worksheet('Items')
        analysis_sheet = workbook.add_worksheet('Analysis')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        currency_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1
        })
        
        percentage_format = workbook.add_format({
            'num_format': '0.00%',
            'border': 1
        })
        
        border_format = workbook.add_format({'border': 1})
        
        # Write Summary Sheet
        write_summary_sheet(summary_sheet, doc, header_format, currency_format, border_format)
        
        # Write Items Sheet
        write_items_sheet(items_sheet, doc, header_format, currency_format, border_format)
        
        # Write Analysis Sheet
        write_analysis_sheet(analysis_sheet, doc, header_format, currency_format, percentage_format, border_format)
        
        workbook.close()
        output.seek(0)
        
        # Save file
        file_data = output.read()
        file_name = f"final_account_{doc.name}_{melon.utils.today()}.xlsx"
        
        # Create File document
        file_doc = melon.get_doc({
            'doctype': 'File',
            'file_name': file_name,
            'content': base64.b64encode(file_data).decode(),
            'decode': True,
            'is_private': 1
        })
        file_doc.insert(ignore_permissions=True)
        
        return {
            'success': True,
            'file_url': file_doc.file_url,
            'file_name': file_name,
            'message': f'Final Account exported successfully'
        }
        
    except Exception as e:
        melon.log_error(f"Excel export error: {str(e)}", "Export Utilities")
        return {'success': False, 'message': str(e)}

def write_summary_sheet(sheet, doc, header_format, currency_format, border_format):
    """Write summary information to Excel sheet"""
    
    # Document header
    sheet.write('A1', 'Final Account Summary', header_format)
    sheet.merge_range('A1:D1', 'Final Account Summary', header_format)
    
    # Basic information
    row = 3
    info_data = [
        ['Final Account', doc.name],
        ['Project', doc.project],
        ['Status', doc.status],
        ['Total Amount', doc.total_amount or 0],
        ['Creation Date', doc.creation.strftime('%Y-%m-%d') if doc.creation else ''],
        ['Modified Date', doc.modified.strftime('%Y-%m-%d') if doc.modified else '']
    ]
    
    for label, value in info_data:
        sheet.write(row, 0, label, border_format)
        if label == 'Total Amount':
            sheet.write(row, 1, value, currency_format)
        else:
            sheet.write(row, 1, value, border_format)
        row += 1
    
    # Items summary
    if doc.final_account_items:
        sheet.write(row + 1, 0, 'Items Summary', header_format)
        sheet.merge_range(f'A{row + 2}:D{row + 2}', 'Items Summary', header_format)
        
        row += 3
        sheet.write(row, 0, 'Total Items', border_format)
        sheet.write(row, 1, len(doc.final_account_items), border_format)
        
        row += 1
        total_quantity = sum(flt(item.quantity) for item in doc.final_account_items)
        sheet.write(row, 0, 'Total Quantity', border_format)
        sheet.write(row, 1, total_quantity, border_format)
        
        row += 1
        avg_rate = sum(flt(item.rate) for item in doc.final_account_items) / len(doc.final_account_items) if doc.final_account_items else 0
        sheet.write(row, 0, 'Average Rate', border_format)
        sheet.write(row, 1, avg_rate, currency_format)
    
    # Auto-fit columns
    sheet.set_column('A:A', 15)
    sheet.set_column('B:B', 20)

def write_items_sheet(sheet, doc, header_format, currency_format, border_format):
    """Write items details to Excel sheet"""
    
    # Headers
    headers = ['Item Code', 'Description', 'UOM', 'Quantity', 'Rate', 'Amount']
    for col, header in enumerate(headers):
        sheet.write(0, col, header, header_format)
    
    # Items data
    row = 1
    for item in doc.final_account_items or []:
        sheet.write(row, 0, item.item_code or '', border_format)
        sheet.write(row, 1, item.description or '', border_format)
        sheet.write(row, 2, item.uom or '', border_format)
        sheet.write(row, 3, flt(item.quantity), border_format)
        sheet.write(row, 4, flt(item.rate), currency_format)
        sheet.write(row, 5, flt(item.amount), currency_format)
        row += 1
    
    # Total row
    if doc.final_account_items:
        sheet.write(row, 0, 'TOTAL', header_format)
        sheet.merge_range(f'A{row + 1}:E{row + 1}', 'TOTAL', header_format)
        sheet.write(row, 5, doc.total_amount or 0, currency_format)
    
    # Auto-fit columns
    sheet.set_column('A:A', 12)
    sheet.set_column('B:B', 30)
    sheet.set_column('C:C', 8)
    sheet.set_column('D:D', 12)
    sheet.set_column('E:E', 12)
    sheet.set_column('F:F', 15)

def write_analysis_sheet(sheet, doc, header_format, currency_format, percentage_format, border_format):
    """Write analysis data to Excel sheet"""
    
    if not doc.final_account_items:
        sheet.write('A1', 'No items to analyze', border_format)
        return
    
    # Item analysis by category/type
    sheet.write('A1', 'Item Analysis', header_format)
    sheet.merge_range('A1:E1', 'Item Analysis', header_format)
    
    # Headers
    analysis_headers = ['Item Code', 'Quantity', 'Rate', 'Amount', '% of Total']
    for col, header in enumerate(analysis_headers):
        sheet.write(2, col, header, header_format)
    
    # Calculate percentages
    total_amount = doc.total_amount or 1  # Avoid division by zero
    row = 3
    
    # Sort items by amount (descending)
    sorted_items = sorted(doc.final_account_items, key=lambda x: flt(x.amount), reverse=True)
    
    for item in sorted_items:
        percentage = flt(item.amount) / total_amount if total_amount else 0
        
        sheet.write(row, 0, item.item_code or '', border_format)
        sheet.write(row, 1, flt(item.quantity), border_format)
        sheet.write(row, 2, flt(item.rate), currency_format)
        sheet.write(row, 3, flt(item.amount), currency_format)
        sheet.write(row, 4, percentage, percentage_format)
        row += 1
    
    # High-value items analysis
    row += 2
    sheet.write(row, 0, 'High Value Items (>10% of total)', header_format)
    sheet.merge_range(f'A{row + 1}:E{row + 1}', 'High Value Items (>10% of total)', header_format)
    
    row += 2
    high_value_items = [item for item in sorted_items if flt(item.amount) / total_amount > 0.1]
    
    if high_value_items:
        for col, header in enumerate(analysis_headers):
            sheet.write(row, col, header, header_format)
        row += 1
        
        for item in high_value_items:
            percentage = flt(item.amount) / total_amount
            sheet.write(row, 0, item.item_code or '', border_format)
            sheet.write(row, 1, flt(item.quantity), border_format)
            sheet.write(row, 2, flt(item.rate), currency_format)
            sheet.write(row, 3, flt(item.amount), currency_format)
            sheet.write(row, 4, percentage, percentage_format)
            row += 1
    else:
        sheet.write(row, 0, 'No high-value items found', border_format)
    
    # Auto-fit columns
    sheet.set_column('A:A', 12)
    sheet.set_column('B:B', 12)
    sheet.set_column('C:C', 12)
    sheet.set_column('D:D', 15)
    sheet.set_column('E:E', 12)

@melon.whitelist()
def export_boq_csv(boq_name: str) -> Dict:
    """
    Export BOQ to CSV format
    """
    try:
        # Get BOQ document
        doc = melon.get_doc('BOQ', boq_name)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Item Code', 'Description', 'UOM', 'Quantity', 'Rate', 'Amount'])
        
        # Write items
        for item in doc.boq_items or []:
            writer.writerow([
                item.item_code or '',
                item.description or '',
                item.uom or '',
                flt(item.quantity),
                flt(item.rate),
                flt(item.amount)
            ])
        
        # Write total
        writer.writerow(['', '', '', '', 'TOTAL', doc.total_amount or 0])
        
        # Create file
        csv_content = output.getvalue()
        output.close()
        
        file_name = f"boq_{doc.name}_{melon.utils.today()}.csv"
        
        # Create File document
        file_doc = melon.get_doc({
            'doctype': 'File',
            'file_name': file_name,
            'content': base64.b64encode(csv_content.encode()).decode(),
            'decode': True,
            'is_private': 1
        })
        file_doc.insert(ignore_permissions=True)
        
        return {
            'success': True,
            'file_url': file_doc.file_url,
            'file_name': file_name,
            'message': f'BOQ exported to CSV successfully'
        }
        
    except Exception as e:
        melon.log_error(f"CSV export error: {str(e)}", "Export Utilities")
        return {'success': False, 'message': str(e)}

@melon.whitelist()
def import_items_from_excel(file_url: str, doctype: str, docname: str) -> Dict:
    """
    Import items from Excel file
    """
    try:
        # Get file content
        file_doc = melon.get_doc('File', {'file_url': file_url})
        file_content = file_doc.get_content()
        
        # Read Excel file
        import pandas as pd
        df = pd.read_excel(io.BytesIO(file_content))
        
        # Validate required columns
        required_columns = ['Item Code', 'Quantity', 'Rate']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'message': f'Missing required columns: {", ".join(missing_columns)}'
            }
        
        # Get target document
        doc = melon.get_doc(doctype, docname)
        
        # Clear existing items (optional)
        # doc.set('items', [])
        
        # Add items from Excel
        items_added = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Create item
                item_data = {
                    'item_code': str(row.get('Item Code', '')),
                    'description': str(row.get('Description', '')),
                    'uom': str(row.get('UOM', 'Each')),
                    'quantity': flt(row.get('Quantity', 0)),
                    'rate': flt(row.get('Rate', 0))
                }
                
                # Calculate amount
                item_data['amount'] = item_data['quantity'] * item_data['rate']
                
                # Add to document
                item_table_field = get_item_table_field(doctype)
                doc.append(item_table_field, item_data)
                items_added += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        # Save document
        doc.save()
        
        result = {
            'success': True,
            'items_added': items_added,
            'message': f'Successfully imported {items_added} items'
        }
        
        if errors:
            result['errors'] = errors[:10]  # Limit to first 10 errors
            result['message'] += f'. {len(errors)} errors occurred.'
        
        return result
        
    except Exception as e:
        melon.log_error(f"Excel import error: {str(e)}", "Import Utilities")
        return {'success': False, 'message': str(e)}

def get_item_table_field(doctype: str) -> str:
    """
    Get the child table fieldname for items based on doctype
    """
    field_mapping = {
        'BOQ': 'boq_items',
        'Final Account': 'final_account_items',
        'Valuation': 'valuation_items',
        'Cost Plan': 'cost_plan_items',
        'Variation Order': 'variation_order_items'
    }
    
    return field_mapping.get(doctype, 'items')

@melon.whitelist()
def export_project_summary_excel(project: str) -> Dict:
    """
    Export comprehensive project summary to Excel
    """
    try:
        # Get project document
        project_doc = melon.get_doc('Project', project)
        
        # Create Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'bg_color': '#2E75B6',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        currency_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1
        })
        
        border_format = workbook.add_format({'border': 1})
        
        # Create sheets
        overview_sheet = workbook.add_worksheet('Project Overview')
        boq_sheet = workbook.add_worksheet('BOQ Summary')
        valuations_sheet = workbook.add_worksheet('Valuations')
        variations_sheet = workbook.add_worksheet('Variations')
        payments_sheet = workbook.add_worksheet('Payments')
        
        # Write project overview
        write_project_overview(overview_sheet, project_doc, title_format, header_format, currency_format, border_format)
        
        # Write BOQ summary
        write_boq_summary(boq_sheet, project, header_format, currency_format, border_format)
        
        # Write valuations summary
        write_valuations_summary(valuations_sheet, project, header_format, currency_format, border_format)
        
        # Write variations summary
        write_variations_summary(variations_sheet, project, header_format, currency_format, border_format)
        
        # Write payments summary
        write_payments_summary(payments_sheet, project, header_format, currency_format, border_format)
        
        workbook.close()
        output.seek(0)
        
        # Save file
        file_data = output.read()
        file_name = f"project_summary_{project_doc.name}_{melon.utils.today()}.xlsx"
        
        file_doc = melon.get_doc({
            'doctype': 'File',
            'file_name': file_name,
            'content': base64.b64encode(file_data).decode(),
            'decode': True,
            'is_private': 1
        })
        file_doc.insert(ignore_permissions=True)
        
        return {
            'success': True,
            'file_url': file_doc.file_url,
            'file_name': file_name,
            'message': f'Project summary exported successfully'
        }
        
    except Exception as e:
        melon.log_error(f"Project export error: {str(e)}", "Export Utilities")
        return {'success': False, 'message': str(e)}

def write_project_overview(sheet, project_doc, title_format, header_format, currency_format, border_format):
    """Write project overview to Excel sheet"""
    
    # Title
    sheet.merge_range('A1:F1', f'Project Summary: {project_doc.project_name}', title_format)
    
    # Basic information
    row = 3
    sheet.write('A3', 'Project Information', header_format)
    sheet.merge_range('A3:B3', 'Project Information', header_format)
    
    info_data = [
        ['Project Name', project_doc.project_name],
        ['Status', project_doc.status],
        ['Start Date', project_doc.expected_start_date],
        ['End Date', project_doc.expected_end_date],
        ['Company', project_doc.company],
        ['Customer', project_doc.customer]
    ]
    
    for label, value in info_data:
        row += 1
        sheet.write(row, 0, label, border_format)
        sheet.write(row, 1, str(value) if value else '', border_format)
    
    # Financial summary
    row += 3
    sheet.write(row, 0, 'Financial Summary', header_format)
    sheet.merge_range(f'A{row + 1}:B{row + 1}', 'Financial Summary', header_format)
    
    # Get financial data
    financial_data = get_project_financial_summary(project_doc.name)
    
    fin_info = [
        ['Total BOQ Value', financial_data.get('total_boq_value', 0)],
        ['Total Valuations', financial_data.get('total_valuations', 0)],
        ['Total Variations', financial_data.get('total_variations', 0)],
        ['Total Payments', financial_data.get('total_payments', 0)],
        ['Outstanding Amount', financial_data.get('outstanding_amount', 0)]
    ]
    
    for label, value in fin_info:
        row += 1
        sheet.write(row, 0, label, border_format)
        sheet.write(row, 1, flt(value), currency_format)
    
    # Auto-fit columns
    sheet.set_column('A:A', 20)
    sheet.set_column('B:B', 25)

def write_boq_summary(sheet, project, header_format, currency_format, border_format):
    """Write BOQ summary to Excel sheet"""
    
    # Get BOQ data
    boqs = melon.get_all('BOQ', 
        filters={'project': project},
        fields=['name', 'total_amount', 'status', 'creation']
    )
    
    # Headers
    headers = ['BOQ', 'Total Amount', 'Status', 'Date']
    for col, header in enumerate(headers):
        sheet.write(0, col, header, header_format)
    
    # Data
    row = 1
    total_boq_value = 0
    
    for boq in boqs:
        sheet.write(row, 0, boq.name, border_format)
        sheet.write(row, 1, flt(boq.total_amount), currency_format)
        sheet.write(row, 2, boq.status, border_format)
        sheet.write(row, 3, boq.creation.strftime('%Y-%m-%d') if boq.creation else '', border_format)
        total_boq_value += flt(boq.total_amount)
        row += 1
    
    # Total row
    if boqs:
        sheet.write(row, 0, 'TOTAL', header_format)
        sheet.write(row, 1, total_boq_value, currency_format)
    
    # Auto-fit columns
    sheet.set_column('A:A', 15)
    sheet.set_column('B:B', 15)
    sheet.set_column('C:C', 12)
    sheet.set_column('D:D', 12)

def write_valuations_summary(sheet, project, header_format, currency_format, border_format):
    """Write valuations summary to Excel sheet"""
    
    # Get Valuation data
    valuations = melon.get_all('Valuation', 
        filters={'project': project},
        fields=['name', 'total_amount', 'status', 'valuation_date']
    )
    
    # Headers
    headers = ['Valuation', 'Amount', 'Status', 'Date']
    for col, header in enumerate(headers):
        sheet.write(0, col, header, header_format)
    
    # Data
    row = 1
    total_valuations = 0
    
    for val in valuations:
        sheet.write(row, 0, val.name, border_format)
        sheet.write(row, 1, flt(val.total_amount), currency_format)
        sheet.write(row, 2, val.status, border_format)
        sheet.write(row, 3, val.valuation_date.strftime('%Y-%m-%d') if val.valuation_date else '', border_format)
        total_valuations += flt(val.total_amount)
        row += 1
    
    # Total row
    if valuations:
        sheet.write(row, 0, 'TOTAL', header_format)
        sheet.write(row, 1, total_valuations, currency_format)

def write_variations_summary(sheet, project, header_format, currency_format, border_format):
    """Write variations summary to Excel sheet"""
    
    # Get Variation Order data
    variations = melon.get_all('Variation Order', 
        filters={'project': project},
        fields=['name', 'total_amount', 'status', 'date']
    )
    
    # Headers
    headers = ['Variation Order', 'Amount', 'Status', 'Date']
    for col, header in enumerate(headers):
        sheet.write(0, col, header, header_format)
    
    # Data
    row = 1
    total_variations = 0
    
    for var in variations:
        sheet.write(row, 0, var.name, border_format)
        sheet.write(row, 1, flt(var.total_amount), currency_format)
        sheet.write(row, 2, var.status, border_format)
        sheet.write(row, 3, var.date.strftime('%Y-%m-%d') if var.date else '', border_format)
        total_variations += flt(var.total_amount)
        row += 1
    
    # Total row
    if variations:
        sheet.write(row, 0, 'TOTAL', header_format)
        sheet.write(row, 1, total_variations, currency_format)

def write_payments_summary(sheet, project, header_format, currency_format, border_format):
    """Write payments summary to Excel sheet"""
    
    # Get Payment Certificate data
    payments = melon.get_all('Payment Certificate', 
        filters={'project': project},
        fields=['name', 'certificate_amount', 'status', 'certificate_date']
    )
    
    # Headers
    headers = ['Payment Certificate', 'Amount', 'Status', 'Date']
    for col, header in enumerate(headers):
        sheet.write(0, col, header, header_format)
    
    # Data
    row = 1
    total_payments = 0
    
    for payment in payments:
        sheet.write(row, 0, payment.name, border_format)
        sheet.write(row, 1, flt(payment.certificate_amount), currency_format)
        sheet.write(row, 2, payment.status, border_format)
        sheet.write(row, 3, payment.certificate_date.strftime('%Y-%m-%d') if payment.certificate_date else '', border_format)
        total_payments += flt(payment.certificate_amount)
        row += 1
    
    # Total row
    if payments:
        sheet.write(row, 0, 'TOTAL', header_format)
        sheet.write(row, 1, total_payments, currency_format)

def get_project_financial_summary(project: str) -> Dict:
    """
    Get comprehensive financial summary for a project
    """
    try:
        summary = {
            'total_boq_value': 0,
            'total_valuations': 0,
            'total_variations': 0,
            'total_payments': 0,
            'outstanding_amount': 0
        }
        
        # BOQ totals
        boq_total = melon.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM `tabBOQ` 
            WHERE project = %s AND docstatus = 1
        """, [project])
        
        if boq_total:
            summary['total_boq_value'] = flt(boq_total[0][0])
        
        # Valuation totals
        val_total = melon.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM `tabValuation` 
            WHERE project = %s AND docstatus = 1
        """, [project])
        
        if val_total:
            summary['total_valuations'] = flt(val_total[0][0])
        
        # Variation totals
        var_total = melon.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM `tabVariation Order` 
            WHERE project = %s AND docstatus = 1
        """, [project])
        
        if var_total:
            summary['total_variations'] = flt(var_total[0][0])
        
        # Payment totals
        pay_total = melon.db.sql("""
            SELECT COALESCE(SUM(certificate_amount), 0) as total
            FROM `tabPayment Certificate` 
            WHERE project = %s AND docstatus = 1
        """, [project])
        
        if pay_total:
            summary['total_payments'] = flt(pay_total[0][0])
        
        # Calculate outstanding
        summary['outstanding_amount'] = summary['total_valuations'] - summary['total_payments']
        
        return summary
        
    except Exception as e:
        melon.log_error(f"Financial summary error: {str(e)}", "Export Utilities")
        return {'error': str(e)}

@melon.whitelist()
def get_export_templates() -> Dict:
    """
    Get available export templates
    """
    try:
        templates = {
            'excel': [
                {
                    'name': 'Final Account Excel',
                    'description': 'Complete Final Account with analysis',
                    'method': 'export_final_account_excel',
                    'fields': ['final_account_name']
                },
                {
                    'name': 'Project Summary Excel',
                    'description': 'Comprehensive project financial summary',
                    'method': 'export_project_summary_excel',
                    'fields': ['project']
                }
            ],
            'csv': [
                {
                    'name': 'BOQ CSV',
                    'description': 'Simple BOQ items in CSV format',
                    'method': 'export_boq_csv',
                    'fields': ['boq_name']
                }
            ],
            'import': [
                {
                    'name': 'Excel Items Import',
                    'description': 'Import items from Excel file',
                    'method': 'import_items_from_excel',
                    'fields': ['file_url', 'doctype', 'docname']
                }
            ]
        }
        
        return {'success': True, 'templates': templates}
        
    except Exception as e:
        melon.log_error(f"Templates error: {str(e)}", "Export Utilities")
        return {'success': False, 'message': str(e)}
