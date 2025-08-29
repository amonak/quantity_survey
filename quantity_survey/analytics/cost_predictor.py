"""
Cost Predictor Module
Provides AI-powered cost prediction and market analysis
"""

import melon
from melon import _
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

@melon.whitelist()
def analyze_cost_trends(item_code: str, project_location: str = None, historical_months: int = 12) -> Dict:
    """
    Analyze cost trends and provide predictive insights
    """
    try:
        # Get historical data
        historical_data = get_historical_cost_data(item_code, project_location, historical_months)
        
        if not historical_data:
            return {
                'prediction': {
                    'predicted_cost': 0,
                    'confidence': 0,
                    'trend': 'No Data',
                    'recommendation': 'Insufficient historical data for prediction'
                }
            }
        
        # Perform trend analysis
        df = pd.DataFrame(historical_data)
        
        # Calculate moving averages and trends
        df['moving_avg_30'] = df['rate'].rolling(window=min(30, len(df))).mean()
        df['moving_avg_90'] = df['rate'].rolling(window=min(90, len(df))).mean()
        
        # Linear regression for trend
        from scipy import stats
        x = np.arange(len(df))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, df['rate'])
        
        # Predict next period cost
        predicted_cost = slope * len(df) + intercept
        confidence = abs(r_value * 100)  # R-squared as confidence
        
        # Determine trend
        trend = 'Rising' if slope > 0 else 'Falling' if slope < 0 else 'Stable'
        
        # Generate recommendation
        recommendation = generate_cost_recommendation(trend, confidence, df['rate'].iloc[-1], predicted_cost)
        
        return {
            'prediction': {
                'predicted_cost': max(0, predicted_cost),
                'confidence': min(100, confidence),
                'trend': trend,
                'recommendation': recommendation,
                'suggested_rate': predicted_cost * 0.95 if trend == 'Rising' else predicted_cost,
                'market_volatility': df['rate'].std(),
                'data_points': len(df)
            }
        }
        
    except Exception as e:
        melon.log_error(f"Cost prediction error: {str(e)}", "Cost Predictor")
        return {
            'prediction': {
                'predicted_cost': 0,
                'confidence': 0,
                'trend': 'Error',
                'recommendation': f'Analysis failed: {str(e)}'
            }
        }

def get_historical_cost_data(item_code: str, location: str = None, months: int = 12) -> List[Dict]:
    """Get historical cost data from various sources"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    # Query multiple sources for cost data
    sources = [
        get_valuation_data(item_code, start_date, end_date, location),
        get_purchase_data(item_code, start_date, end_date, location),
        get_quotation_data(item_code, start_date, end_date, location),
        get_market_data(item_code, start_date, end_date, location)
    ]
    
    # Combine and clean data
    combined_data = []
    for source_data in sources:
        combined_data.extend(source_data)
    
    # Remove duplicates and sort by date
    df = pd.DataFrame(combined_data)
    if not df.empty:
        df = df.drop_duplicates(['date', 'source']).sort_values('date')
        return df.to_dict('records')
    
    return []

def get_valuation_data(item_code: str, start_date: datetime, end_date: datetime, location: str = None) -> List[Dict]:
    """Get cost data from valuations"""
    filters = {
        'item_code': item_code,
        'creation': ['between', [start_date, end_date]]
    }
    
    if location:
        filters['parent.project_location'] = location
    
    data = melon.db.get_all('Valuation Item',
        filters=filters,
        fields=['rate', 'creation as date', 'parent as source_doc'],
        limit=1000
    )
    
    return [{'rate': d['rate'], 'date': d['date'], 'source': 'valuation', 'source_doc': d['source_doc']} for d in data]

def get_purchase_data(item_code: str, start_date: datetime, end_date: datetime, location: str = None) -> List[Dict]:
    """Get cost data from purchase orders/receipts"""
    try:
        filters = {
            'item_code': item_code,
            'creation': ['between', [start_date, end_date]]
        }
        
        data = melon.db.get_all('Purchase Order Item',
            filters=filters,
            fields=['rate', 'creation as date', 'parent as source_doc'],
            limit=500
        )
        
        return [{'rate': d['rate'], 'date': d['date'], 'source': 'purchase', 'source_doc': d['source_doc']} for d in data]
    except:
        return []

def get_quotation_data(item_code: str, start_date: datetime, end_date: datetime, location: str = None) -> List[Dict]:
    """Get cost data from quotations"""
    try:
        data = melon.db.get_all('Tender Quote Item',
            filters={
                'item_code': item_code,
                'creation': ['between', [start_date, end_date]]
            },
            fields=['rate', 'creation as date', 'parent as source_doc'],
            limit=500
        )
        
        return [{'rate': d['rate'], 'date': d['date'], 'source': 'quotation', 'source_doc': d['source_doc']} for d in data]
    except:
        return []

def get_market_data(item_code: str, start_date: datetime, end_date: datetime, location: str = None) -> List[Dict]:
    """Get market data from external sources or item master updates"""
    try:
        # Get item standard rate changes
        item_doc = melon.get_doc('Item', item_code)
        
        # For now, return current standard rate as baseline
        return [{
            'rate': item_doc.standard_rate or 0,
            'date': datetime.now(),
            'source': 'standard_rate',
            'source_doc': item_code
        }]
    except:
        return []

def generate_cost_recommendation(trend: str, confidence: float, current_rate: float, predicted_rate: float) -> str:
    """Generate intelligent cost recommendations"""
    
    change_percent = ((predicted_rate - current_rate) / current_rate * 100) if current_rate > 0 else 0
    
    if confidence < 30:
        return "Low confidence prediction. Consider gathering more market data."
    
    if trend == 'Rising':
        if change_percent > 10:
            return "Significant cost increase expected. Consider bulk purchasing or alternative suppliers."
        elif change_percent > 5:
            return "Moderate cost increase predicted. Monitor market closely."
        else:
            return "Slight cost increase expected. Current pricing strategy is acceptable."
    
    elif trend == 'Falling':
        if abs(change_percent) > 10:
            return "Significant cost decrease expected. Consider delaying purchases if possible."
        else:
            return "Cost decrease predicted. Good time for procurement."
    
    else:  # Stable
        return "Stable pricing expected. Current market conditions are favorable."

@melon.whitelist()
def get_variance_alerts(final_account: str) -> Dict:
    """Get variance alerts for final account"""
    
    doc = melon.get_doc('Final Account', final_account)
    alerts = []
    
    for item in doc.final_account_items:
        # High quantity variance
        if abs(item.get('variance_percentage', 0)) > 20:
            alerts.append({
                'type': 'High Quantity Variance',
                'item': item.item_name,
                'variance': f"{item.get('variance_percentage', 0):.1f}%",
                'severity': 'high',
                'recommendation': 'Investigate quantity differences with site team'
            })
        
        # High rate variance
        if item.get('boq_rate') and item.get('actual_rate'):
            rate_variance = ((item.actual_rate - item.boq_rate) / item.boq_rate) * 100
            if abs(rate_variance) > 15:
                alerts.append({
                    'type': 'High Rate Variance',
                    'item': item.item_name,
                    'variance': f"{rate_variance:.1f}%",
                    'severity': 'medium',
                    'recommendation': 'Review market rates and supplier agreements'
                })
    
    return {'alerts': alerts, 'total_alerts': len(alerts)}
