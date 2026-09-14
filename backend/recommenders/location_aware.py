import pandas as pd
from typing import List, Dict, Any, Optional

from recommenders.cache_utils import load_cache, save_cache

class LocationAwareRecommender:
    """
    Location-Aware Recommender.
    Replaces time-context logic. Computes product and category affinity scores
    based on customer geographical regions, states, or shipping locations.
    """
    def __init__(self):
        self.df_ref = None
        self.location_cat_affinity = {}
        self.location_prod_affinity = {}
        self.global_pop = {}

    def fit(self, df: pd.DataFrame, use_cache: bool = True):
        if df.empty:
            return

        self.df_ref = df.copy()

        if use_cache:
            cached = load_cache("location_model")
            if cached and all(k in cached for k in ["location_cat_affinity", "location_prod_affinity"]):
                self.location_cat_affinity = cached["location_cat_affinity"]
                self.location_prod_affinity = cached["location_prod_affinity"]
                return

        # Check if 'State' or 'Region' or 'City' exists; if not, synthesize location mapping from CustomerKey
        if 'State' not in self.df_ref.columns and 'Region' not in self.df_ref.columns:
            states = ['California', 'New York', 'Texas', 'Florida', 'Washington', 'Illinois', 'Ohio', 'Georgia']
            # Map CustomerKey deterministically to a state
            self.df_ref['State'] = self.df_ref['CustomerKey'].apply(lambda cid: states[int(cid) % len(states)])

        location_col = 'State' if 'State' in self.df_ref.columns else 'Region'

        # Build location category affinity matrix
        loc_cat = self.df_ref.groupby([location_col, 'CategoryName'])['OrderQuantity'].sum().reset_index()
        loc_totals = loc_cat.groupby(location_col)['OrderQuantity'].sum().to_dict()

        for _, row in loc_cat.iterrows():
            loc = str(row[location_col])
            cat = str(row['CategoryName'])
            qty = float(row['OrderQuantity'])
            total = loc_totals.get(loc, 1.0)
            
            if loc not in self.location_cat_affinity:
                self.location_cat_affinity[loc] = {}
            self.location_cat_affinity[loc][cat] = round(qty / (total if total > 0 else 1.0), 4)

        # Build location product popularity scores
        loc_prod = self.df_ref.groupby([location_col, 'ProductKey'])['OrderQuantity'].sum().reset_index()
        loc_max_prod = loc_prod.groupby(location_col)['OrderQuantity'].max().to_dict()

        for _, row in loc_prod.iterrows():
            loc = str(row[location_col])
            pk = str(row['ProductKey'])
            qty = float(row['OrderQuantity'])
            max_q = loc_max_prod.get(loc, 1.0)

            if loc not in self.location_prod_affinity:
                self.location_prod_affinity[loc] = {}
            self.location_prod_affinity[loc][pk] = round(qty / (max_q if max_q > 0 else 1.0), 4)

        save_cache("location_model", {
            "location_cat_affinity": self.location_cat_affinity,
            "location_prod_affinity": self.location_prod_affinity
        })

    def get_location_score(self, product_key: str, category_name: str, location: Optional[str] = "California") -> float:
        if not location:
            location = "California"
        
        loc_str = str(location).strip()
        str_pk = str(product_key)

        # Lookup location-specific product score or fallback to category affinity
        prod_score = self.location_prod_affinity.get(loc_str, {}).get(str_pk, 0.0)
        cat_score = self.location_cat_affinity.get(loc_str, {}).get(category_name, 0.2)

        # Combine product location popularity (70%) and category affinity (30%)
        final_score = 0.7 * prod_score + 0.3 * cat_score
        return round(float(final_score), 4)

    def get_recommendations(self, location: str = "California", limit: int = 20) -> List[Dict[str, Any]]:
        if self.df_ref is None or self.df_ref.empty:
            return []

        unique_prods = self.df_ref.drop_duplicates(subset=["ProductKey"]).copy()
        
        recs = []
        for _, row in unique_prods.iterrows():
            pk = str(row["ProductKey"])
            cat = str(row["CategoryName"])
            score = self.get_location_score(pk, cat, location)
            recs.append({
                "ProductKey": pk,
                "ProductName": row["ProductName"],
                "CategoryName": cat,
                "SubcategoryName": row["SubcategoryName"],
                "UnitPrice": float(row["UnitPrice"]),
                "location": location,
                "score": score
            })

        recs.sort(key=lambda x: x["score"], reverse=True)
        return recs[:limit]

# Global singleton
location_recommender = LocationAwareRecommender()
