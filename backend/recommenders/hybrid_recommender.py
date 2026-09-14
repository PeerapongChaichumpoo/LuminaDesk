import pandas as pd
from typing import List, Dict, Any, Optional
from recommenders.popularity import popularity_recommender
from recommenders.svd import svd_recommender
from recommenders.collaborative import cf_recommender
from recommenders.content_based import content_recommender
from recommenders.location_aware import location_recommender

class HybridRecommender:
    """
    Hybrid Recommender System implementing Chapter 10 strategies:
    1. Switching Hybrid:
       - Guest / Cold-Start User -> Switches to Popularity Recommender.
    2. Weighted Hybrid:
       - Returning User -> Combines normalized scores from:
         SVD (35%), Collaborative Filtering (25%), Content-Based (25%), and Location-Aware (15%).
    """
    def __init__(self, w_svd: float = 0.35, w_cf: float = 0.25, w_content: float = 0.25, w_loc: float = 0.15):
        self.w_svd = w_svd
        self.w_cf = w_cf
        self.w_content = w_content
        self.w_loc = w_loc
        self.df_ref = None

    def fit(self, df: pd.DataFrame):
        import time
        self.df_ref = df  # reference, no copy needed here — sub-modules copy if needed
        
        t = time.time()
        popularity_recommender.fit(df)
        print(f"  [1/5] Popularity fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        svd_recommender.fit(df)
        print(f"  [2/5] SVD fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        cf_recommender.fit(df)
        print(f"  [3/5] Collaborative Filtering fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        content_recommender.fit(df)
        print(f"  [4/5] Content-Based fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        location_recommender.fit(df)
        print(f"  [5/5] Location-Aware fitted in {round(time.time()-t, 3)}s")

    def get_recommendations(
        self,
        customer_key: Any,
        location: Optional[str] = "California",
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Main recommendation entry point.
        """
        # Parse customer key safely
        is_guest = True
        c_key_int = None

        if customer_key is not None:
            str_key = str(customer_key).strip().lower()
            if str_key not in ["guest", "none", "0", ""]:
                try:
                    c_key_int = int(customer_key)
                    if self.df_ref is not None and not self.df_ref.empty:
                        # Check if customer has transaction history
                        if c_key_int in self.df_ref['CustomerKey'].values:
                            is_guest = False
                except (ValueError, TypeError):
                    is_guest = True

        has_location = (location is not None) and (str(location).strip().lower() not in ["", "none", "all", "all locations"])

        # ----------------------------------------------------
        # 1. SWITCHING HYBRID: Guest / Cold-Start User
        # ----------------------------------------------------
        if is_guest or c_key_int is None:
            pop_recs = popularity_recommender.get_recommendations(limit=limit)
            if has_location:
                for item in pop_recs:
                    loc_score = location_recommender.get_location_score(item["ProductKey"], item["CategoryName"], location)
                    item["location_score"] = loc_score
                    item["hybrid_score"] = round(0.8 * item["score"] + 0.2 * loc_score, 4)
                pop_recs.sort(key=lambda x: x["hybrid_score"], reverse=True)
                msg = f"Trending marketplace picks popular in {location} (New Guest Mode)"
            else:
                for item in pop_recs:
                    item["location_score"] = 0.0
                    item["hybrid_score"] = item["score"]
                msg = "Trending global marketplace picks (Popularity)"

            return {
                "hybrid_type": "switching_popularity_guest",
                "message": msg,
                "weights": {"popularity": 0.8, "location": 0.2 if has_location else 0.0},
                "recommendations": pop_recs
            }

        # ----------------------------------------------------
        # 2. WEIGHTED HYBRID: Returning Customer
        # ----------------------------------------------------
        svd_list = svd_recommender.get_user_recommendations(c_key_int, limit=50)
        cf_list = cf_recommender.predict_user_based(c_key_int, limit=50)
        content_list = content_recommender.get_user_content_recommendations(self.df_ref, c_key_int, limit=50)

        # Dynamic weights based on whether location context is active
        w_svd = 0.35 if has_location else 0.40
        w_cf = 0.25 if has_location else 0.30
        w_content = 0.25 if has_location else 0.30
        w_loc = 0.15 if has_location else 0.00

        candidate_map = {}

        def add_to_candidates(item_list, tech_key):
            for item in item_list:
                pk = str(item["ProductKey"])
                if pk not in candidate_map:
                    candidate_map[pk] = {
                        "ProductKey": pk,
                        "ProductName": item["ProductName"],
                        "CategoryName": item["CategoryName"],
                        "SubcategoryName": item["SubcategoryName"],
                        "UnitPrice": float(item["UnitPrice"]),
                        "svd_score": 0.0,
                        "cf_score": 0.0,
                        "content_score": 0.0,
                        "loc_score": 0.0
                    }
                candidate_map[pk][tech_key] = float(item.get("score", 0.0))

        add_to_candidates(svd_list, "svd_score")
        add_to_candidates(cf_list, "cf_score")
        add_to_candidates(content_list, "content_score")

        final_recs = []
        for pk, data in candidate_map.items():
            loc_s = location_recommender.get_location_score(pk, data["CategoryName"], location) if has_location else 0.0
            data["loc_score"] = loc_s

            combined_score = (
                w_svd * data["svd_score"] +
                w_cf * data["cf_score"] +
                w_content * data["content_score"] +
                w_loc * loc_s
            )

            data["score"] = round(float(combined_score), 4)
            final_recs.append(data)

        if not final_recs:
            fallback = popularity_recommender.get_recommendations(limit=limit)
            return {
                "hybrid_type": "switching_fallback_popularity",
                "message": f"Featured recommendations for Customer #{c_key_int}",
                "weights": {"popularity": 1.0},
                "recommendations": fallback
            }

        final_recs.sort(key=lambda x: x["score"], reverse=True)

        return {
            "hybrid_type": "weighted_hybrid" if has_location else "weighted_hybrid_no_location",
            "message": f"Personalized Weighted Hybrid Recommendations for Customer #{c_key_int}",
            "weights": {
                "svd": w_svd,
                "collaborative": w_cf,
                "content_based": w_content,
                "location_aware": w_loc
            },
            "recommendations": final_recs[:limit]
        }

# Global singleton instance
hybrid_recommender = HybridRecommender()
