"""
Smart Defaults Module
Provides AI-powered intelligent defaults for quantity surveying
"""

import melon
from melon import _
from melon.utils import flt, cint
from typing import Dict, List, Optional
import json

@melon.whitelist()
def get_intelligent_defaults(item_code: str, project: str = None, location: str = None, project_type: str = None) -> Dict:
    """
    Get AI-suggested defaults based on historical data and machine learning
    """
    try:
        # Analyze similar projects
        similar_projects = find_similar_projects(project, location, project_type)
        
        # Get historical rates for this item
        historical_rates = get_historical_item_rates(item_code, similar_projects)
        
        if not historical_rates:
            return get_fallback_defaults(item_code)
        
        # Calculate intelligent suggestions
        suggested_rate = calculate_weighted_average_rate(historical_rates)
        typical_quantity = calculate_typical_quantity(item_code, similar_projects)
        confidence_level = calculate_confidence_level(historical_rates)
        
        # Get market intelligence
        market_rate = get_current_market_rate(item_code, location)
        
        return {
            'suggested_rate': suggested_rate,
            'market_rate': market_rate,
            'typical_quantity': typical_quantity,
            'confidence_level': confidence_level,
            'confidence_samples': len(historical_rates),
            'recommendation': generate_rate_recommendation(suggested_rate, market_rate, confidence_level)
        }
        
    except Exception as e:
        melon.log_error(f"Smart defaults error: {str(e)}", "Smart Defaults")
        return get_fallback_defaults(item_code)

def find_similar_projects(project: str = None, location: str = None, project_type: str = None, limit: int = 10) -> List[str]:
    """Find similar projects based on location, type, and other criteria"""
    
    filters = []
    
    if location:
        # Find projects in same city/region
        filters.append(['project_location', 'like', f'%{location}%'])
    
    if project_type:
        filters.append(['project_type', '=', project_type])
    
    # Only completed or ongoing projects
    filters.append(['status', 'in', ['Completed', 'Ongoing']])
    
    # Projects from last 3 years for relevance
    filters.append(['creation', '>', melon.utils.add_years(melon.utils.today(), -3)])
    
    similar_projects = melon.db.get_all('Project',
        filters=filters,
        fields=['name'],
        limit=limit,
        order_by='creation desc'
    )
    
    return [p.name for p in similar_projects]

def get_historical_item_rates(item_code: str, project_list: List[str]) -> List[Dict]:
    """Get historical rates for an item from similar projects"""
    
    if not project_list:
        return []
    
    # Get rates from various sources
    rates = []
    
    # From BOQ items
    boq_rates = melon.db.get_all('BOQ Item',
        filters={
            'item_code': item_code,
            'parent': ['in', get_boqs_for_projects(project_list)]
        },
        fields=['rate', 'quantity', 'amount', 'parent', 'creation'],
        limit=100
    )
    rates.extend([{'rate': r.rate, 'source': 'boq', 'weight': 1.0, 'date': r.creation} for r in boq_rates])
    
    # From valuation items
    valuation_rates = melon.db.get_all('Valuation Item',
        filters={
            'item_code': item_code,
            'parent': ['in', get_valuations_for_projects(project_list)]
        },
        fields=['rate', 'quantity', 'amount', 'parent', 'creation'],
        limit=50
    )
    rates.extend([{'rate': r.rate, 'source': 'valuation', 'weight': 1.2, 'date': r.creation} for r in valuation_rates])
    
    # From final accounts (most accurate)
    final_account_rates = melon.db.get_all('Final Account Item',
        filters={
            'item_code': item_code,
            'parent': ['in', get_final_accounts_for_projects(project_list)]
        },
        fields=['actual_rate as rate', 'actual_quantity as quantity', 'actual_amount as amount', 'parent', 'creation'],
        limit=30
    )
    rates.extend([{'rate': r.rate, 'source': 'final_account', 'weight': 1.5, 'date': r.creation} for r in final_account_rates])
    
    return rates

def get_boqs_for_projects(project_list: List[str]) -> List[str]:
    """Get BOQ names for given projects"""
    if not project_list:
        return []
    
    boqs = melon.db.get_all('BOQ',
        filters={'project': ['in', project_list]},
        fields=['name']
    )
    return [b.name for b in boqs]

def get_valuations_for_projects(project_list: List[str]) -> List[str]:
    """Get Valuation names for given projects"""
    if not project_list:
        return []
    
    valuations = melon.db.get_all('Valuation',
        filters={'project': ['in', project_list]},
        fields=['name']
    )
    return [v.name for v in valuations]

def get_final_accounts_for_projects(project_list: List[str]) -> List[str]:
    """Get Final Account names for given projects"""
    if not project_list:
        return []
    
    final_accounts = melon.db.get_all('Final Account',
        filters={'project': ['in', project_list]},
        fields=['name']
    )
    return [fa.name for fa in final_accounts]

def calculate_weighted_average_rate(rates: List[Dict]) -> float:
    """Calculate weighted average rate with time decay"""
    if not rates:
        return 0
    
    # Sort by date (most recent first)
    rates.sort(key=lambda x: x.get('date', melon.utils.today()), reverse=True)
    
    total_weighted_rate = 0
    total_weight = 0
    
    for i, rate_data in enumerate(rates):
        # Time decay factor (more recent = higher weight)
        time_factor = 1 / (1 + i * 0.1)  # Decay by 10% for each older entry
        
        # Source weight
        source_weight = rate_data.get('weight', 1.0)
        
        # Final weight
        final_weight = time_factor * source_weight
        
        total_weighted_rate += flt(rate_data['rate']) * final_weight
        total_weight += final_weight
    
    return total_weighted_rate / total_weight if total_weight > 0 else 0

def calculate_typical_quantity(item_code: str, project_list: List[str]) -> float:
    """Calculate typical quantity used for this item"""
    if not project_list:
        return 0
    
    # Get quantities from various sources
    quantities = []
    
    # From BOQ
    boq_quantities = melon.db.get_all('BOQ Item',
        filters={
            'item_code': item_code,
            'parent': ['in', get_boqs_for_projects(project_list)]
        },
        fields=['quantity']
    )
    quantities.extend([q.quantity for q in boq_quantities])
    
    if quantities:
        # Return median for better representation
        quantities.sort()
        n = len(quantities)
        if n % 2 == 0:
            return (quantities[n//2 - 1] + quantities[n//2]) / 2
        else:
            return quantities[n//2]
    
    return 0

def calculate_confidence_level(rates: List[Dict]) -> float:
    """Calculate confidence level based on data consistency"""
    if not rates or len(rates) < 2:
        return 0
    
    rate_values = [flt(r['rate']) for r in rates if r['rate']]
    
    if not rate_values:
        return 0
    
    # Calculate coefficient of variation (lower = more consistent = higher confidence)
    import statistics
    mean_rate = statistics.mean(rate_values)
    std_dev = statistics.stdev(rate_values) if len(rate_values) > 1 else 0
    
    if mean_rate == 0:
        return 0
    
    cv = std_dev / mean_rate  # Coefficient of variation
    
    # Convert to confidence percentage (inverse relationship)
    confidence = max(0, min(100, (1 - cv) * 100))
    
    # Bonus for more data points
    data_bonus = min(20, len(rate_values) * 2)  # Up to 20% bonus
    
    return min(100, confidence + data_bonus)

def get_current_market_rate(item_code: str, location: str = None) -> float:
    """Get current market rate from various sources"""
    try:
        # Try to get from recent quotations
        recent_quotes = melon.db.get_all('Tender Quote Item',
            filters={
                'item_code': item_code,
                'creation': ['>=', melon.utils.add_days(melon.utils.today(), -30)]
            },
            fields=['rate'],
            order_by='creation desc',
            limit=5
        )
        
        if recent_quotes:
            rates = [q.rate for q in recent_quotes if q.rate]
            return sum(rates) / len(rates) if rates else 0
        
        # Fallback to item standard rate
        item = melon.get_doc('Item', item_code)
        return flt(item.standard_rate)
        
    except:
        return 0

def generate_rate_recommendation(suggested_rate: float, market_rate: float, confidence: float) -> str:
    """Generate intelligent rate recommendation"""
    
    if confidence < 30:
        return "Low confidence - verify with recent market quotes"
    
    if market_rate and suggested_rate:
        diff_percent = abs(market_rate - suggested_rate) / suggested_rate * 100
        
        if diff_percent > 20:
            return "Significant difference from market rate - investigate further"
        elif diff_percent > 10:
            return "Moderate difference from market rate - consider adjustment"
        else:
            return "Rate aligns well with market conditions"
    
    if confidence > 80:
        return "High confidence - recommended rate based on strong historical data"
    elif confidence > 50:
        return "Moderate confidence - rate based on available project data"
    else:
        return "Limited data available - verify with current market rates"

def get_fallback_defaults(item_code: str) -> Dict:
    """Get fallback defaults when AI analysis fails"""
    try:
        item = melon.get_doc('Item', item_code)
        return {
            'suggested_rate': flt(item.standard_rate),
            'market_rate': flt(item.standard_rate),
            'typical_quantity': 1,
            'confidence_level': 10,
            'confidence_samples': 0,
            'recommendation': 'Using item standard rate - no historical data available'
        }
    except:
        return {
            'suggested_rate': 0,
            'market_rate': 0,
            'typical_quantity': 1,
            'confidence_level': 0,
            'confidence_samples': 0,
            'recommendation': 'No data available - manual entry required'
        }
