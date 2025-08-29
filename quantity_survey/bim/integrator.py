"""
BIM Integrator Module
Provides direct import from Revit, AutoCAD, and other design tools
"""

import melon
from melon import _
from melon.utils import flt, cint, get_files_path
import os
import json
import tempfile
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET

@melon.whitelist()
def import_bim_file(file_path: str, file_type: str, project: str) -> Dict:
    """
    Import BIM file and extract quantity data
    """
    try:
        if not os.path.exists(file_path):
            return {'success': False, 'message': 'File not found'}
        
        if file_type.lower() == 'ifc':
            return import_ifc_file(file_path, project)
        elif file_type.lower() == 'dwg':
            return import_dwg_file(file_path, project)
        elif file_type.lower() == 'xml':
            return import_xml_file(file_path, project)
        elif file_type.lower() in ['xlsx', 'csv']:
            return import_excel_file(file_path, project)
        else:
            return {'success': False, 'message': f'Unsupported file type: {file_type}'}
            
    except Exception as e:
        melon.log_error(f"BIM import error: {str(e)}", "BIM Integrator")
        return {'success': False, 'message': f'Import failed: {str(e)}'}

def import_ifc_file(file_path: str, project: str) -> Dict:
    """Import IFC (Industry Foundation Classes) file"""
    try:
        # Try to use IfcOpenShell if available
        try:
            import ifcopenshell
            import ifcopenshell.util.element
            
            # Open IFC file
            ifc_file = ifcopenshell.open(file_path)
            
            # Extract building elements with quantities
            elements = []
            
            # Get all building elements
            building_elements = ifc_file.by_type("IfcBuildingElement")
            
            for element in building_elements:
                element_data = extract_ifc_element_data(element)
                if element_data:
                    elements.append(element_data)
            
            # Create BOQ from extracted data
            boq_doc = create_boq_from_bim_data(elements, project, 'IFC Import')
            
            return {
                'success': True,
                'message': f'Successfully imported {len(elements)} elements from IFC file',
                'boq': boq_doc.name,
                'elements_count': len(elements)
            }
            
        except ImportError:
            # Fallback to manual IFC parsing (limited functionality)
            return parse_ifc_manually(file_path, project)
            
    except Exception as e:
        return {'success': False, 'message': f'IFC import failed: {str(e)}'}

def extract_ifc_element_data(element) -> Optional[Dict]:
    """Extract quantity data from IFC element"""
    try:
        import ifcopenshell.util.element
        
        element_type = element.is_a()
        element_name = getattr(element, 'Name', '') or f"{element_type}_{element.id()}"
        
        # Get quantities
        quantities = {}
        
        # Try to get quantity sets
        psets = ifcopenshell.util.element.get_psets(element)
        
        # Extract relevant quantities
        for pset_name, pset_data in psets.items():
            if 'quantity' in pset_name.lower() or 'dimension' in pset_name.lower():
                for prop_name, prop_value in pset_data.items():
                    if isinstance(prop_value, (int, float)):
                        quantities[prop_name] = prop_value
        
        # Get material
        material = ""
        try:
            materials = ifcopenshell.util.element.get_material(element)
            if materials:
                material = str(materials)
        except:
            pass
        
        # Calculate quantities based on element type
        quantity_data = calculate_element_quantities(element_type, quantities)
        
        return {
            'element_id': element.id(),
            'element_type': element_type,
            'name': element_name,
            'material': material,
            'quantities': quantity_data,
            'properties': quantities
        }
        
    except Exception as e:
        melon.log_error(f"IFC element extraction error: {str(e)}", "BIM Integrator")
        return None

def calculate_element_quantities(element_type: str, properties: Dict) -> Dict:
    """Calculate standard quantities based on element type"""
    quantities = {}
    
    if element_type in ['IfcWall', 'IfcWallStandardCase']:
        # Wall quantities
        length = properties.get('Length', 0) or properties.get('NetSideArea', 0) / properties.get('Height', 1)
        height = properties.get('Height', 0)
        width = properties.get('Width', 0) or properties.get('Thickness', 0)
        
        if length and height:
            quantities['area'] = length * height
            quantities['length'] = length
            quantities['height'] = height
            if width:
                quantities['volume'] = length * height * width
                quantities['width'] = width
    
    elif element_type in ['IfcSlab', 'IfcRoof']:
        # Slab/Roof quantities
        area = properties.get('GrossArea', 0) or properties.get('NetArea', 0)
        thickness = properties.get('Thickness', 0) or properties.get('Depth', 0)
        
        if area:
            quantities['area'] = area
            if thickness:
                quantities['volume'] = area * thickness
                quantities['thickness'] = thickness
    
    elif element_type in ['IfcBeam']:
        # Beam quantities
        length = properties.get('Length', 0)
        cross_section = properties.get('CrossSectionArea', 0)
        
        if length:
            quantities['length'] = length
            if cross_section:
                quantities['volume'] = length * cross_section
                quantities['cross_section_area'] = cross_section
    
    elif element_type in ['IfcColumn']:
        # Column quantities
        height = properties.get('Height', 0) or properties.get('Length', 0)
        cross_section = properties.get('CrossSectionArea', 0)
        
        if height:
            quantities['height'] = height
            quantities['length'] = height
            if cross_section:
                quantities['volume'] = height * cross_section
                quantities['cross_section_area'] = cross_section
    
    elif element_type in ['IfcDoor', 'IfcWindow']:
        # Door/Window quantities
        height = properties.get('OverallHeight', 0) or properties.get('Height', 0)
        width = properties.get('OverallWidth', 0) or properties.get('Width', 0)
        
        if height and width:
            quantities['area'] = height * width
            quantities['height'] = height
            quantities['width'] = width
            quantities['quantity'] = 1  # Number of units
    
    return quantities

def parse_ifc_manually(file_path: str, project: str) -> Dict:
    """Manual IFC parsing without IfcOpenShell (limited functionality)"""
    try:
        elements = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Basic parsing for wall, slab, and beam elements
        import re
        
        # Find IFC entities
        wall_pattern = r'#(\d+)=IFCWALL\((.*?)\);'
        slab_pattern = r'#(\d+)=IFCSLAB\((.*?)\);'
        beam_pattern = r'#(\d+)=IFCBEAM\((.*?)\);'
        
        walls = re.findall(wall_pattern, content, re.IGNORECASE)
        slabs = re.findall(slab_pattern, content, re.IGNORECASE)
        beams = re.findall(beam_pattern, content, re.IGNORECASE)
        
        # Process walls
        for wall_id, wall_data in walls:
            elements.append({
                'element_id': wall_id,
                'element_type': 'IFCWALL',
                'name': f'Wall_{wall_id}',
                'material': 'Concrete',
                'quantities': {'quantity': 1, 'unit': 'Nos'},
                'properties': {'raw_data': wall_data}
            })
        
        # Process slabs
        for slab_id, slab_data in slabs:
            elements.append({
                'element_id': slab_id,
                'element_type': 'IFCSLAB',
                'name': f'Slab_{slab_id}',
                'material': 'Concrete',
                'quantities': {'quantity': 1, 'unit': 'Nos'},
                'properties': {'raw_data': slab_data}
            })
        
        # Process beams
        for beam_id, beam_data in beams:
            elements.append({
                'element_id': beam_id,
                'element_type': 'IFCBEAM',
                'name': f'Beam_{beam_id}',
                'material': 'Concrete',
                'quantities': {'quantity': 1, 'unit': 'Nos'},
                'properties': {'raw_data': beam_data}
            })
        
        if elements:
            boq_doc = create_boq_from_bim_data(elements, project, 'Manual IFC Import')
            return {
                'success': True,
                'message': f'Successfully imported {len(elements)} elements (basic parsing)',
                'boq': boq_doc.name,
                'elements_count': len(elements)
            }
        else:
            return {'success': False, 'message': 'No elements found in IFC file'}
            
    except Exception as e:
        return {'success': False, 'message': f'Manual IFC parsing failed: {str(e)}'}

def import_dwg_file(file_path: str, project: str) -> Dict:
    """Import DWG (AutoCAD) file"""
    try:
        # For DWG files, we would need a library like ezdxf or similar
        # For now, we'll implement a basic structure
        
        return {
            'success': False,
            'message': 'DWG import requires additional libraries (ezdxf, ODA File Converter). Please convert to DXF format.'
        }
        
    except Exception as e:
        return {'success': False, 'message': f'DWG import failed: {str(e)}'}

def import_xml_file(file_path: str, project: str) -> Dict:
    """Import XML file (Generic or specific format)"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        elements = []
        
        # Try to parse common XML structures
        if root.tag.lower() in ['project', 'building', 'model']:
            elements = parse_building_xml(root)
        elif root.tag.lower() in ['quantities', 'boq', 'takeoff']:
            elements = parse_quantities_xml(root)
        else:
            # Generic XML parsing
            elements = parse_generic_xml(root)
        
        if elements:
            boq_doc = create_boq_from_bim_data(elements, project, 'XML Import')
            return {
                'success': True,
                'message': f'Successfully imported {len(elements)} elements from XML',
                'boq': boq_doc.name,
                'elements_count': len(elements)
            }
        else:
            return {'success': False, 'message': 'No valid elements found in XML file'}
            
    except Exception as e:
        return {'success': False, 'message': f'XML import failed: {str(e)}'}

def parse_building_xml(root) -> List[Dict]:
    """Parse building model XML"""
    elements = []
    
    # Look for common element tags
    element_tags = ['wall', 'slab', 'beam', 'column', 'door', 'window', 'element', 'component']
    
    for tag in element_tags:
        for elem in root.iter(tag):
            element_data = {
                'element_id': elem.get('id', f'{tag}_{len(elements)}'),
                'element_type': tag.upper(),
                'name': elem.get('name', f'{tag}_{len(elements)}'),
                'material': elem.get('material', ''),
                'quantities': {},
                'properties': {}
            }
            
            # Extract quantity attributes
            for attr, value in elem.attrib.items():
                try:
                    numeric_value = float(value)
                    element_data['quantities'][attr] = numeric_value
                except ValueError:
                    element_data['properties'][attr] = value
            
            # Extract child element quantities
            for child in elem:
                try:
                    numeric_value = float(child.text or 0)
                    element_data['quantities'][child.tag] = numeric_value
                except ValueError:
                    element_data['properties'][child.tag] = child.text
            
            elements.append(element_data)
    
    return elements

def parse_quantities_xml(root) -> List[Dict]:
    """Parse quantities-specific XML"""
    elements = []
    
    for item in root.iter('item'):
        element_data = {
            'element_id': item.get('id', f'item_{len(elements)}'),
            'element_type': item.get('type', 'ITEM'),
            'name': item.get('description', f'Item_{len(elements)}'),
            'material': item.get('material', ''),
            'quantities': {},
            'properties': {}
        }
        
        # Common quantity fields
        qty_fields = ['quantity', 'length', 'width', 'height', 'area', 'volume', 'weight']
        
        for field in qty_fields:
            value = item.get(field) or (item.find(field).text if item.find(field) is not None else None)
            if value:
                try:
                    element_data['quantities'][field] = float(value)
                except ValueError:
                    pass
        
        # Get unit of measurement
        unit = item.get('unit') or (item.find('unit').text if item.find('unit') is not None else 'Nos')
        element_data['quantities']['unit'] = unit
        
        elements.append(element_data)
    
    return elements

def parse_generic_xml(root) -> List[Dict]:
    """Generic XML parsing"""
    elements = []
    
    # Try to find any element with quantity-related attributes
    for elem in root.iter():
        if elem.text and elem.text.strip():
            continue  # Skip text elements
        
        has_quantities = any(attr in ['quantity', 'length', 'width', 'height', 'area', 'volume'] 
                           for attr in elem.attrib.keys())
        
        if has_quantities:
            element_data = {
                'element_id': elem.get('id', f'{elem.tag}_{len(elements)}'),
                'element_type': elem.tag.upper(),
                'name': elem.get('name', f'{elem.tag}_{len(elements)}'),
                'material': elem.get('material', ''),
                'quantities': {},
                'properties': {}
            }
            
            # Extract all attributes
            for attr, value in elem.attrib.items():
                try:
                    numeric_value = float(value)
                    element_data['quantities'][attr] = numeric_value
                except ValueError:
                    element_data['properties'][attr] = value
            
            elements.append(element_data)
    
    return elements

def import_excel_file(file_path: str, project: str) -> Dict:
    """Import Excel/CSV file with quantity data"""
    try:
        import pandas as pd
        
        # Read the file
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        elements = []
        
        # Map common column names
        column_mapping = {
            'item': 'name',
            'description': 'name',
            'element': 'name',
            'type': 'element_type',
            'category': 'element_type',
            'qty': 'quantity',
            'quantity': 'quantity',
            'length': 'length',
            'width': 'width',
            'height': 'height',
            'area': 'area',
            'volume': 'volume',
            'material': 'material',
            'unit': 'unit',
            'uom': 'unit'
        }
        
        # Rename columns based on mapping
        df.columns = [column_mapping.get(col.lower(), col.lower()) for col in df.columns]
        
        for index, row in df.iterrows():
            element_data = {
                'element_id': f'excel_item_{index}',
                'element_type': str(row.get('element_type', 'ITEM')).upper(),
                'name': str(row.get('name', f'Item_{index}')),
                'material': str(row.get('material', '')),
                'quantities': {},
                'properties': {}
            }
            
            # Extract quantities
            qty_fields = ['quantity', 'length', 'width', 'height', 'area', 'volume', 'weight']
            for field in qty_fields:
                if field in row and pd.notna(row[field]):
                    try:
                        element_data['quantities'][field] = float(row[field])
                    except (ValueError, TypeError):
                        pass
            
            # Add unit
            if 'unit' in row and pd.notna(row['unit']):
                element_data['quantities']['unit'] = str(row['unit'])
            
            # Add other properties
            for col in df.columns:
                if col not in ['name', 'element_type', 'material'] + qty_fields:
                    if pd.notna(row[col]):
                        element_data['properties'][col] = str(row[col])
            
            elements.append(element_data)
        
        if elements:
            boq_doc = create_boq_from_bim_data(elements, project, 'Excel Import')
            return {
                'success': True,
                'message': f'Successfully imported {len(elements)} elements from Excel/CSV',
                'boq': boq_doc.name,
                'elements_count': len(elements)
            }
        else:
            return {'success': False, 'message': 'No valid elements found in file'}
            
    except Exception as e:
        return {'success': False, 'message': f'Excel import failed: {str(e)}'}

def create_boq_from_bim_data(elements: List[Dict], project: str, import_source: str) -> object:
    """Create BOQ document from BIM data"""
    
    # Create BOQ document
    boq_doc = melon.new_doc('BOQ')
    boq_doc.project = project
    boq_doc.boq_title = f'BIM Import - {import_source}'
    boq_doc.description = f'Automatically generated from {import_source} on {melon.utils.now()}'
    boq_doc.status = 'Draft'
    
    # Process elements and create items
    for element in elements:
        # Map BIM element to construction item
        item_code = map_bim_element_to_item(element)
        
        if not item_code:
            continue  # Skip if no mapping found
        
        # Calculate primary quantity
        primary_qty = calculate_primary_quantity(element)
        
        if primary_qty == 0:
            continue  # Skip if no quantity
        
        # Add item to BOQ
        boq_item = boq_doc.append('boq_items', {})
        boq_item.item_code = item_code
        boq_item.item_name = element['name']
        boq_item.description = f"{element['element_type']}: {element['name']}"
        boq_item.quantity = primary_qty
        boq_item.uom = element['quantities'].get('unit', 'Nos')
        boq_item.rate = get_standard_rate(item_code)
        boq_item.amount = boq_item.quantity * boq_item.rate
        
        # Add BIM metadata
        boq_item.bim_element_id = element['element_id']
        boq_item.bim_element_type = element['element_type']
        
        # Store additional quantities as JSON
        if len(element['quantities']) > 1:
            boq_item.additional_quantities = json.dumps(element['quantities'])
        
        # Store properties as JSON
        if element['properties']:
            boq_item.bim_properties = json.dumps(element['properties'])
    
    # Calculate totals
    total_amount = sum(item.amount for item in boq_doc.boq_items)
    boq_doc.total_amount = total_amount
    
    # Save BOQ
    boq_doc.insert()
    melon.db.commit()
    
    return boq_doc

def map_bim_element_to_item(element: Dict) -> str:
    """Map BIM element to existing construction item"""
    
    element_type = element['element_type'].upper()
    material = element.get('material', '').lower()
    
    # Define mapping rules
    mapping_rules = {
        'IFCWALL': ['WALL', 'MASONRY', 'CONCRETE WALL'],
        'IFCWALLSTANDARDCASE': ['WALL', 'MASONRY', 'CONCRETE WALL'],
        'IFCSLAB': ['SLAB', 'CONCRETE SLAB', 'FLOOR SLAB'],
        'IFCBEAM': ['BEAM', 'CONCRETE BEAM', 'STEEL BEAM'],
        'IFCCOLUMN': ['COLUMN', 'CONCRETE COLUMN', 'STEEL COLUMN'],
        'IFCDOOR': ['DOOR', 'WOODEN DOOR', 'STEEL DOOR'],
        'IFCWINDOW': ['WINDOW', 'GLASS WINDOW', 'ALUMINUM WINDOW'],
        'IFCROOF': ['ROOF', 'ROOFING', 'ROOF SLAB'],
        'IFCFOUNDATION': ['FOUNDATION', 'FOOTING', 'CONCRETE FOUNDATION']
    }
    
    # Get possible item names for this element type
    possible_items = mapping_rules.get(element_type, [element_type])
    
    # Try to find matching item
    for item_name in possible_items:
        # Search for item with similar name
        items = melon.db.get_all('Item', 
            filters={
                'item_name': ['like', f'%{item_name}%'],
                'is_construction_item': 1,
                'disabled': 0
            },
            fields=['item_code', 'item_name'],
            limit=1
        )
        
        if items:
            return items[0].item_code
    
    # If no exact match, try by material
    if material:
        material_keywords = ['concrete', 'steel', 'wood', 'brick', 'block']
        for keyword in material_keywords:
            if keyword in material:
                items = melon.db.get_all('Item',
                    filters={
                        'item_name': ['like', f'%{keyword}%'],
                        'is_construction_item': 1,
                        'disabled': 0
                    },
                    fields=['item_code'],
                    limit=1
                )
                if items:
                    return items[0].item_code
    
    # Last resort: create a generic item
    return create_generic_construction_item(element)

def create_generic_construction_item(element: Dict) -> str:
    """Create a generic construction item for unmapped BIM elements"""
    
    item_code = f"BIM_{element['element_type']}_{melon.utils.random_string(5)}"
    
    # Check if item already exists
    if melon.db.exists('Item', item_code):
        return item_code
    
    # Create new item
    item_doc = melon.new_doc('Item')
    item_doc.item_code = item_code
    item_doc.item_name = f"{element['element_type']}: {element['name']}"
    item_doc.item_group = 'Construction Materials'
    item_doc.is_construction_item = 1
    item_doc.stock_uom = element['quantities'].get('unit', 'Nos')
    item_doc.description = f"Imported from BIM model: {element['element_type']}"
    item_doc.standard_rate = 0  # Will be set later
    
    # Add BIM metadata
    item_doc.bim_element_type = element['element_type']
    if element.get('material'):
        item_doc.material_type = element['material']
    
    item_doc.insert(ignore_permissions=True)
    melon.db.commit()
    
    return item_code

def calculate_primary_quantity(element: Dict) -> float:
    """Calculate the primary quantity for an element"""
    
    quantities = element['quantities']
    element_type = element['element_type'].upper()
    
    # Define primary quantity by element type
    if element_type in ['IFCWALL', 'IFCWALLSTANDARDCASE']:
        return quantities.get('area', quantities.get('length', quantities.get('quantity', 0)))
    
    elif element_type in ['IFCSLAB', 'IFCROOF']:
        return quantities.get('area', quantities.get('volume', quantities.get('quantity', 0)))
    
    elif element_type in ['IFCBEAM', 'IFCCOLUMN']:
        return quantities.get('length', quantities.get('volume', quantities.get('quantity', 0)))
    
    elif element_type in ['IFCDOOR', 'IFCWINDOW']:
        return quantities.get('quantity', quantities.get('area', 1))
    
    else:
        # Default priority: quantity > area > volume > length > 1
        return (quantities.get('quantity') or 
                quantities.get('area') or 
                quantities.get('volume') or 
                quantities.get('length') or 1)

def get_standard_rate(item_code: str) -> float:
    """Get standard rate for an item"""
    try:
        item = melon.get_doc('Item', item_code)
        return flt(item.standard_rate)
    except:
        return 0.0

@melon.whitelist()
def get_bim_import_template() -> str:
    """Generate BIM import template"""
    try:
        import xlsxwriter
        import tempfile
        import os
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, 'bim_import_template.xlsx')
        
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet('BIM Import Template')
        
        # Headers
        headers = [
            'Element Type',
            'Element Name/Description',
            'Material',
            'Quantity',
            'Unit',
            'Length',
            'Width',
            'Height',
            'Area',
            'Volume',
            'Notes'
        ]
        
        # Sample data
        sample_data = [
            ['WALL', 'External Wall', 'Concrete', 100, 'Sqm', 10, 0.2, 3, 100, 6, 'External perimeter wall'],
            ['SLAB', 'Ground Floor Slab', 'Concrete', 250, 'Sqm', 0, 0, 0.15, 250, 37.5, 'Ground floor concrete slab'],
            ['BEAM', 'Main Beam', 'Concrete', 50, 'Lm', 50, 0.3, 0.6, 0, 9, 'Main structural beam'],
            ['COLUMN', 'Column C1', 'Concrete', 12, 'Nos', 3, 0.3, 0.3, 0, 3.24, 'Reinforced concrete column']
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
        instructions.write(0, 0, 'BIM Import Instructions:', workbook.add_format({'bold': True}))
        instructions.write(1, 0, '1. Fill in the Element Type (WALL, SLAB, BEAM, COLUMN, etc.)')
        instructions.write(2, 0, '2. Provide Element Name/Description for identification')
        instructions.write(3, 0, '3. Specify Material (Concrete, Steel, Wood, etc.)')
        instructions.write(4, 0, '4. Enter Quantity as the primary unit for pricing')
        instructions.write(5, 0, '5. Specify Unit (Nos, Sqm, Cum, Lm, etc.)')
        instructions.write(6, 0, '6. Provide dimensions for validation')
        instructions.write(7, 0, '7. Remove sample rows before importing')
        instructions.write(8, 0, '8. Save as Excel file and upload using BIM Import function')
        
        workbook.close()
        
        # Save file to Melon
        with open(file_path, 'rb') as f:
            file_doc = melon.get_doc({
                'doctype': 'File',
                'file_name': 'bim_import_template.xlsx',
                'content': f.read(),
                'is_private': 1
            })
            file_doc.save()
        
        # Cleanup
        os.remove(file_path)
        os.rmdir(temp_dir)
        
        return file_doc.file_url
        
    except Exception as e:
        melon.log_error(f"Template generation error: {str(e)}", "BIM Integrator")
        return None
