"""
Run this whenever you want a CSV snapshot of your results for analysis.
It does NOT touch the live app or the Supabase tables — read-only export.

Usage:
    pip install supabase pandas
    export SUPABASE_URL="https://YOUR-PROJECT-ID.supabase.co"
    export SUPABASE_KEY="YOUR-ANON-PUBLIC-KEY"
    python export_results.py
"""

import os
import pandas as pd
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL") or "PASTE_YOUR_URL_HERE"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "PASTE_YOUR_KEY_HERE"

OUTPUT_DIR = "."  # change if you want the CSVs saved elsewhere

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 🔹 Export raw evaluations (one row per rating)
# ==========================================
evaluations = supabase.table("evaluations").select("*").execute().data
evaluations_df = pd.DataFrame(evaluations)
evaluations_path = os.path.join(OUTPUT_DIR, "evaluations_raw.csv")
evaluations_df.to_csv(evaluations_path, index=False)
print(f"✅ Saved {len(evaluations_df)} raw evaluation rows to {evaluations_path}")

# ==========================================
# 🔹 Export participants (demographics)
# ==========================================
participants = supabase.table("participants").select("*").execute().data
participants_df = pd.DataFrame(participants)
participants_path = os.path.join(OUTPUT_DIR, "participants.csv")
participants_df.to_csv(participants_path, index=False)
print(f"✅ Saved {len(participants_df)} participant rows to {participants_path}")

# ==========================================
# 🔹 Export per-image average scores (from the image_scores SQL view)
# ==========================================
image_scores = supabase.table("image_scores").select("*").execute().data
image_scores_df = pd.DataFrame(image_scores)
image_scores_path = os.path.join(OUTPUT_DIR, "image_scores.csv")
image_scores_df.to_csv(image_scores_path, index=False)
print(f"✅ Saved {len(image_scores_df)} per-image average scores to {image_scores_path}")
