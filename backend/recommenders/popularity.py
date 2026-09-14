import pandas as pd
from typing import List, Dict, Any

from recommenders.cache_utils import load_cache, save_cache

class PopularityRecommender:
    """
    Popularity-Based Recommender.
    Computes global product popularity based on total sales volume (OrderQuantity)
    and transaction frequency. Used as fallback and cold-start for new/guest users.
    """
    def __init__(self):
        self.df_ref = None
        self.popular_items = []

    def fit(self, df: pd.DataFrame, use_cache: bool = True):
        if df.empty:
            return

        self.df_ref = df.copy()

        if use_cache:
            cached = load_cache("popularity_model")
            if cached and "popular_items" in cached:
                self.popular_items = cached["popular_items"]
                return

        # Aggregate total quantity and transaction count per product
        pop_df = df.groupby(
            ['ProductKey', 'ProductName', 'CategoryName', 'SubcategoryName', 'UnitPrice']
        ).agg(
            total_quantity=('OrderQuantity', 'sum'),
            sales_count=('SalesOrderNumber', 'nunique')
        ).reset_index()

        pop_df['ProductKey'] = pop_df['ProductKey'].astype(str)

        max_qty = pop_df['total_quantity'].max() if not pop_df.empty and pop_df['total_quantity'].max() > 0 else 1.0

        # Calculate normalized popularity score [0, 1]
        pop_df['popularity_score'] = (pop_df['total_quantity'] / max_qty).round(4)
        pop_df = pop_df.sort_values(by='popularity_score', ascending=False)

        self.popular_items = pop_df.to_dict(orient="records")
        save_cache("popularity_model", {"popular_items": self.popular_items})

    def get_recommendations(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.popular_items:
            return []
        
        recs = []
        for item in self.popular_items[:limit]:
            recs.append({
                "ProductKey": str(item["ProductKey"]),
                "ProductName": item["ProductName"],
                "CategoryName": item["CategoryName"],
                "SubcategoryName": item["SubcategoryName"],
                "UnitPrice": float(item["UnitPrice"]),
                "total_quantity": int(item["total_quantity"]),
                "sales_count": int(item["sales_count"]),
                "score": float(item["popularity_score"])
            })
        return recs

# Global singleton
popularity_recommender = PopularityRecommender()
