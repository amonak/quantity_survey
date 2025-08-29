"""
Bulk Operations Module
Provides bulk editing and operations for quantity survey documents
"""

import melon
from melon import _
from melon.utils import flt, cint
from typing import Dict, List, Any
import json

@melon.whitelist()
def execute_bulk_operation(final_account: str, operation: str, filters: Dict, parameters: Dict) -> Dict:
    """
    Execute bulk operations on final account items
    """
    try:
        doc = melon.get_doc('Final Account', final_account)
        
        # Get filtered items
        items_to_update = get_filtered_items(doc, filters)
        
        if not items_to_update:
            return {'success': False, 'message': 'No items match the specified criteria'}
        
        # Execute the operation
        updated_count = 0
        errors = []
        
        for item in items_to_update:
            try:
                if operation == 'Update Rate':
                    update_item_rate(item, parameters)
                    updated_count += 1
                
                elif operation == 'Apply Variance %':
                    apply_variance_percentage(item, parameters)
                    updated_count += 1
                
                elif operation == 'Update UOM':
                    update_item_uom(item, parameters)
                    updated_count += 1
                
                elif operation == 'Bulk Delete':
                    if can_delete_item(item):
                        doc.remove(item)
                        updated_count += 1
                    else:
                        errors.append(f"Cannot delete {item.item_name} - has dependencies")
                
            except Exception as e:
                errors.append(f"Error updating {item.item_name}: {str(e)}")
        
        # Save the document
        doc.save()
        
        return {
            'success': True,
            'updated_count': updated_count,
            'total_items': len(items_to_update),
            'errors': errors,
            'message': f'Successfully updated {updated_count} items'
        }
        
    except Exception as e:
        melon.log_error(f"Bulk operation error: {str(e)}", "Bulk Operations")
        return {'success': False, 'message': f'Operation failed: {str(e)}'}

def get_filtered_items(doc, filters: Dict) -> List:
    """Get items that match the specified filters"""
    filtered_items = []
    
    for item in doc.final_account_items:
        if matches_filter(item, filters):
            filtered_items.append(item)
    
    return filtered_items

def matches_filter(item, filters: Dict) -> bool:
    """Check if item matches the filter criteria"""
    
    # Filter by item category
    if filters.get('item_category'):
        item_doc = melon.get_cached_doc('Item', item.item_code)
        if item_doc.item_group != filters['item_category']:
            return False
    
    # Filter by variance threshold
    if filters.get('variance_threshold'):
        variance = abs(flt(item.get('variance_percentage', 0)))
        if variance < flt(filters['variance_threshold']):
            return False
    
    # Add more filter criteria as needed
    
    return True

def update_item_rate(item, parameters: Dict):
    """Update item rate"""
    if parameters.get('new_value'):
        item.actual_rate = flt(parameters['new_value'])
    elif parameters.get('percentage_adjustment'):
        current_rate = flt(item.actual_rate)
        adjustment = flt(parameters['percentage_adjustment']) / 100
        item.actual_rate = current_rate * (1 + adjustment)
    
    # Recalculate amount
    item.actual_amount = flt(item.actual_quantity) * flt(item.actual_rate)

def apply_variance_percentage(item, parameters: Dict):
    """Apply variance percentage to quantity"""
    if parameters.get('percentage_adjustment') and item.boq_quantity:
        adjustment = flt(parameters['percentage_adjustment']) / 100
        item.actual_quantity = flt(item.boq_quantity) * (1 + adjustment)
        
        # Recalculate amount and variance
        item.actual_amount = flt(item.actual_quantity) * flt(item.actual_rate)
        item.quantity_variance = flt(item.actual_quantity) - flt(item.boq_quantity)

def update_item_uom(item, parameters: Dict):
    """Update item UOM"""
    if parameters.get('new_uom'):
        # Convert quantities if needed
        old_uom = item.uom
        new_uom = parameters['new_uom']
        
        if old_uom != new_uom:
            conversion_factor = get_uom_conversion_factor(old_uom, new_uom)
            if conversion_factor:
                item.actual_quantity = flt(item.actual_quantity) * conversion_factor
                item.boq_quantity = flt(item.boq_quantity) * conversion_factor
                item.uom = new_uom

def can_delete_item(item) -> bool:
    """Check if item can be deleted"""
    # Add business logic to check if item has dependencies
    # For now, allow all deletions
    return True

def get_uom_conversion_factor(from_uom: str, to_uom: str) -> float:
    """Get conversion factor between UOMs"""
    try:
        # Try to get conversion from UOM Conversion Detail
        conversion = melon.db.get_value('UOM Conversion Detail', 
            {'parent': from_uom, 'uom': to_uom}, 'value')
        
        if conversion:
            return flt(conversion)
        
        # Try reverse conversion
        conversion = melon.db.get_value('UOM Conversion Detail',
            {'parent': to_uom, 'uom': from_uom}, 'value')
        
        if conversion:
            return 1 / flt(conversion)
        
        return 1  # Default to 1 if no conversion found
        
    except:
        return 1

@melon.whitelist()
def export_to_excel(final_account: str, filters: Dict = None) -> str:
    """Export final account items to Excel"""
    try:
        import xlsxwriter
        import tempfile
        import os
        
        doc = melon.get_doc('Final Account', final_account)
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f'final_account_{doc.name}.xlsx')
        
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet('Final Account Items')
        
        # Headers
        headers = [
            'Item Code', 'Item Name', 'Description', 'UOM',
            'BOQ Quantity', 'BOQ Rate', 'BOQ Amount',
            'Actual Quantity', 'Actual Rate', 'Actual Amount',
            'Quantity Variance', 'Amount Variance', 'Variance %'
        ]
        
        # Write headers
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Get filtered items
        items = get_filtered_items(doc, filters or {})
        
        # Write data
        for row, item in enumerate(items, 1):
            data = [
                item.item_code,
                item.item_name,
                item.description,
                item.uom,
                item.boq_quantity,
                item.boq_rate,
                item.boq_amount,
                item.actual_quantity,
                item.actual_rate,
                item.actual_amount,
                item.get('quantity_variance', 0),
                item.get('amount_variance', 0),
                item.get('variance_percentage', 0)
            ]
            
            for col, value in enumerate(data):
                worksheet.write(row, col, value)
        
        workbook.close()
        
        # Save file to Melon's file system
        with open(file_path, 'rb') as f:
            file_doc = melon.get_doc({
                'doctype': 'File',
                'file_name': f'final_account_{doc.name}.xlsx',
                'content': f.read(),
                'is_private': 1
            })
            file_doc.save()
        
        # Cleanup
        os.remove(file_path)
        os.rmdir(temp_dir)
        
        return file_doc.file_url
        
    except Exception as e:
        melon.log_error(f"Excel export error: {str(e)}", "Bulk Operations")
        return None

@melon.whitelist()
def get_import_template() -> str:
    """Generate import template for final account items"""
    try:
        import xlsxwriter
        import tempfile
        import os
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, 'final_account_import_template.xlsx')
        
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet('Import Template')
        
        # Headers with instructions
        headers = [
            'Item Code (Required)',
            'Actual Quantity',
            'Actual Rate',
            'UOM',
            'Description',
            'Notes'
        ]
        
        # Sample data
        sample_data = [
            ['ITEM001', 100, 50.0, 'Nos', 'Sample item description', 'Sample notes'],
            ['ITEM002', 200, 75.5, 'Kg', 'Another sample item', '']
        ]
        
        # Write headers
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write sample data
        for row, data in enumerate(sample_data, 1):
            for col, value in enumerate(data):
                worksheet.write(row, col, value)
        
        # Add instructions sheet
        instructions = workbook.add_worksheet('Instructions')
        instructions.write(0, 0, 'Import Instructions:', workbook.add_format({'bold': True}))
        instructions.write(1, 0, '1. Fill in the required fields (Item Code is mandatory)')
        instructions.write(2, 0, '2. Actual Quantity and Rate will update the final account')
        instructions.write(3, 0, '3. UOM should match the item master UOM')
        instructions.write(4, 0, '4. Remove sample rows before importing')
        instructions.write(5, 0, '5. Save as Excel file and upload using Import function')
        
        workbook.close()
        
        # Save file to Melon
        with open(file_path, 'rb') as f:
            file_doc = melon.get_doc({
                'doctype': 'File',
                'file_name': 'final_account_import_template.xlsx',
                'content': f.read(),
                'is_private': 1
            })
            file_doc.save()
        
        # Cleanup
        os.remove(file_path)
        os.rmdir(temp_dir)
        
        return file_doc.file_url
        
    except Exception as e:
        melon.log_error(f"Template generation error: {str(e)}", "Bulk Operations")
        return None
