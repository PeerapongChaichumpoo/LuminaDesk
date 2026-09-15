import pandas as pd
from typing import List, Dict, Any, Optional
from recommenders.popularity import popularity_recommender
from recommenders.svd import svd_recommender
from recommenders.collaborative import cf_recommender
from recommenders.item_collaborative import item_cf_recommender
from recommenders.content_based import content_recommender
from recommenders.location_aware import location_recommender

class HybridRecommender:
    """
    Hybrid Recommender System implementing Chapter 10 strategies:
    1. Switching Hybrid:
       - Guest / Cold-Start User -> Switches to Popularity Recommender + optional Location affinity.
    2. Weighted Hybrid:
       - Returning User -> Combines normalized scores from:
         SVD (30%), Item-CF (25%), User-CF (20%), Content-Based (20%), and Location-Aware (5% default).
    """
    def __init__(
        self,
        w_svd: float = 0.30,
        w_user_cf: float = 0.20,
        w_item_cf: float = 0.25,
        w_content: float = 0.20,
        w_loc: float = 0.05
    ):
        self.w_svd = w_svd
        self.w_user_cf = w_user_cf
        self.w_item_cf = w_item_cf
        self.w_content = w_content
        self.w_loc = w_loc
        self.df_ref = None

    def fit(self, df: pd.DataFrame):
        import time
        self.df_ref = df
        
        t = time.time()
        popularity_recommender.fit(df)
        print(f"  [1/6] Popularity fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        svd_recommender.fit(df)
        print(f"  [2/6] SVD fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        cf_recommender.fit(df)
        print(f"  [3/6] User-Based Collaborative Filtering fitted in {round(time.time()-t, 3)}s")

        t = time.time()
        item_cf_recommender.fit(df)
        print(f"  [4/6] Item-Based Collaborative Filtering fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        content_recommender.fit(df)
        print(f"  [5/6] Content-Based fitted in {round(time.time()-t, 3)}s")
        
        t = time.time()
        location_recommender.fit(df)
        print(f"  [6/6] Location-Aware fitted in {round(time.time()-t, 3)}s")

    def get_recommendations(
        self,
        customer_key: Any,
        location: Optional[str] = "California",
        limit: int = 20,
        w_svd: Optional[float] = None,
        w_user_cf: Optional[float] = None,
        w_item_cf: Optional[float] = None,
        w_content: Optional[float] = None,
        w_loc: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Main recommendation entry point with support for dynamic custom weights.
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
                        if c_key_int in self.df_ref['CustomerKey'].values:
                            is_guest = False
                except (ValueError, TypeError):
                    is_guest = True

        has_location = (location is not None) and (str(location).strip().lower() not in ["", "none", "all", "all locations"])

        # Determine effective weights
        eff_svd = w_svd if w_svd is not None else self.w_svd
        eff_user_cf = w_user_cf if w_user_cf is not None else self.w_user_cf
        eff_item_cf = w_item_cf if w_item_cf is not None else self.w_item_cf
        eff_content = w_content if w_content is not None else self.w_content
        eff_loc = w_loc if w_loc is not None else (self.w_loc if has_location else 0.0)

        # Normalize weights to sum to 1.0 if total > 0
        total_w = eff_svd + eff_user_cf + eff_item_cf + eff_content + eff_loc
        if total_w > 0:
            eff_svd /= total_w
            eff_user_cf /= total_w
            eff_item_cf /= total_w
            eff_content /= total_w
            eff_loc /= total_w

        # ----------------------------------------------------
        # 1. SWITCHING HYBRID: Guest / Cold-Start User
        # ----------------------------------------------------
        if is_guest or c_key_int is None:
            pop_recs = popularity_recommender.get_recommendations(limit=limit)
            for item in pop_recs:
                loc_score = location_recommender.get_location_score(item["ProductKey"], item["CategoryName"], location) if has_location else 0.0
                item["svd_score"] = 0.0
                item["user_cf_score"] = 0.0
                item["item_cf_score"] = 0.0
                item["content_score"] = 0.0
                item["loc_score"] = loc_score
                item["popularity_score"] = item["score"]
                item["hybrid_score"] = round(0.95 * item["score"] + 0.05 * loc_score, 4)
            pop_recs.sort(key=lambda x: x["hybrid_score"], reverse=True)
            msg = f"Trending workspace picks (Guest Mode - Location Weight 5%)" if has_location else "Trending global marketplace picks (Popularity)"

            return {
                "hybrid_type": "switching_popularity_guest",
                "message": msg,
                "weights": {"popularity": 0.95, "location": 0.05 if has_location else 0.0},
                "recommendations": pop_recs
            }

        # ----------------------------------------------------
        # 2. WEIGHTED HYBRID: Returning Customer
        # ----------------------------------------------------
        svd_list = svd_recommender.get_user_recommendations(c_key_int, limit=50)
        user_cf_list = cf_recommender.predict_user_based(c_key_int, limit=50)
        item_cf_list = item_cf_recommender.predict_item_based(c_key_int, limit=50)
        content_list = content_recommender.get_user_content_recommendations(self.df_ref, c_key_int, limit=50)

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
                        "user_cf_score": 0.0,
                        "item_cf_score": 0.0,
                        "content_score": 0.0,
                        "loc_score": 0.0
                    }
                candidate_map[pk][tech_key] = float(item.get("score", 0.0))

        add_to_candidates(svd_list, "svd_score")
        add_to_candidates(user_cf_list, "user_cf_score")
        add_to_candidates(item_cf_list, "item_cf_score")
        add_to_candidates(content_list, "content_score")

        final_recs = []
        for pk, data in candidate_map.items():
            loc_s = location_recommender.get_location_score(pk, data["CategoryName"], location) if has_location else 0.0
            data["loc_score"] = round(loc_s, 4)

            combined_score = (
                eff_svd * data["svd_score"] +
                eff_user_cf * data["user_cf_score"] +
                eff_item_cf * data["item_cf_score"] +
                eff_content * data["content_score"] +
                eff_loc * loc_s
            )

            data["score"] = round(float(combined_score), 4)
            data["hybrid_score"] = data["score"]
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
            "hybrid_type": "weighted_hybrid",
            "message": f"Personalized Weighted Hybrid Recommendations for Customer #{c_key_int}",
            "weights": {
                "svd": round(eff_svd, 4),
                "user_cf": round(eff_user_cf, 4),
                "item_cf": round(eff_item_cf, 4),
                "content_based": round(eff_content, 4),
                "location_aware": round(eff_loc, 4)
            },
            "recommendations": final_recs[:limit]
        }

# Global singleton instance
hybrid_recommender = HybridRecommender()
