import datetime
from typing import Dict, Any, List

def get_time_context(hour: int = None) -> str:
    """
    Determines time context slot based on the hour of the day (0-23).
    """
    if hour is None:
        hour = datetime.datetime.now().hour
        
    if 6 <= hour < 11:
        return "Morning"
    elif 11 <= hour < 15:
        return "Midday"
    elif 15 <= hour < 18:
        return "Afternoon"
    elif 18 <= hour < 22:
        return "Evening"
    else:
        return "Night"

def get_category_time_relevance(category_name: str, time_context: str) -> float:
    """
    Returns time relevance factor based on item category and active time slot.
    Formula: Final_Score = Preference_Score * Time_Relevance
    """
    cat = (category_name or "").lower()
    
    # Category suitability matrix across time slots
    relevance_matrix = {
        "Morning": {
            "chairs": 1.2, "desks": 1.3, "lighting": 1.1, "monitors": 1.2
        },
        "Midday": {
            "chairs": 1.1, "desks": 1.1, "breakroom": 1.4, "tables": 1.3
        },
        "Afternoon": {
            "chairs": 1.3, "storage": 1.2, "accessories": 1.2
        },
        "Evening": {
            "lighting": 1.4, "lounge": 1.3, "chairs": 1.0
        },
        "Night": {
            "lighting": 1.5, "accessories": 1.1
        }
    }
    
    context_dict = relevance_matrix.get(time_context, {})
    for key, weight in context_dict.items():
        if key in cat:
            return weight
            
    return 1.0  # Baseline neutral relevance

def apply_context_aware_ranking(recommendations: List[Dict[str, Any]], hour: int = None) -> List[Dict[str, Any]]:
    """
    Adjusts recommendation scores by time relevance context factor.
    Score = Base_Preference * Time_Relevance
    """
    time_ctx = get_time_context(hour)
    
    for item in recommendations:
        base_score = item.get("score", 1.0)
        time_rel = get_category_time_relevance(item.get("CategoryName", ""), time_ctx)
        item["time_context"] = time_ctx
        item["time_relevance"] = time_rel
        item["final_score"] = round(base_score * time_rel, 4)
        
    recommendations.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    return recommendations
