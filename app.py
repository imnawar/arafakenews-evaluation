# AraFakeNews human-evaluation Streamlit app — Supabase-backed version
#
# Storage design:
#   - Item metadata (title, image path, caption) stays in a local CSV,
#     since it's static and never written to concurrently.
#   - Evaluator demographics -> Supabase "participants" table
#   - Ratings                -> Supabase "evaluations" table
# This avoids any concurrent read/modify/write on a shared CSV file,
# which is unsafe on platforms like Streamlit Community Cloud where
# the filesystem is ephemeral and shared across sessions.

import streamlit as st
import pandas as pd
import os
import random
import uuid
from datetime import datetime, timezone
from supabase import create_client

st.set_page_config(page_title="تقييم واقعية الصور", layout="centered")

# ==========================================
# 🔹 RTL fix for sliders
# ==========================================
# Streamlit's slider is LTR by default (min on the left), which feels
# backwards in an Arabic-language form. This mirrors the slider track
# so the minimum value sits on the right, matching RTL reading order.
st.markdown(
    """
    <style>
    div[data-testid="stSlider"] {
        direction: rtl;
    }
    div[data-testid="stSlider"] label {
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📰 تقييم مدى واقعية صور الأخبار المزيفة")
st.caption("ملاحظة: جميع الأخبار المعروضة في هذا الاستبيان **مُولّدة اصطناعياً (مزيفة)**. المطلوب هو تقييم مدى واقعية الصورة، وليس تحديد ما إذا كانت حقيقية أم لا.")

# ==========================================
# 🔹 CONFIG
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "GeneratedImagesToEvaluate")

# Static item metadata only (title, image path, caption). No evaluation
# columns live here anymore — those are all in Supabase.
ITEMS_CSV_PATH = os.path.join(IMAGES_DIR, "generated_image_dataset_filtered.csv")

MAX_IMAGES_PER_USER = 25
MAX_EVALS_PER_IMAGE = 3

# ==========================================
# 🔹 Supabase client
# ==========================================
# Requires SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml
# (locally) or in the app's "Secrets" settings (Streamlit Cloud).
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase = get_supabase_client()

# ==========================================
# 🔹 Auto-generated user ID
# ==========================================
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{str(uuid.uuid4())[:8]}"

user_id = st.session_state.user_id

st.markdown(f"👤 المستخدم الحالي: `{user_id}`")

# ==========================================
# 🔹 Demographics form (once per user, before evaluation starts)
# ==========================================
if "demographics_done" not in st.session_state:
    st.session_state.demographics_done = False

if not st.session_state.demographics_done:

    st.markdown("### 👋 قبل البدء، أخبرنا قليلاً عن نفسك")
    st.caption("هذه المعلومات تساعدنا في تحليل النتائج، ولن تُستخدم إلا لأغراض البحث العلمي.")

    with st.form("demographics_form"):

        age_group = st.selectbox(
            "الفئة العمرية",
            [
                "أقل من 18",
                "18 - 24",
                "25 - 34",
                "35 - 44",
                "45 - 54",
                "55 فأكثر",
            ]
        )

        gender = st.radio(
            "الجنس",
            ["ذكر", "أنثى"],
            horizontal=True
        )

        education_stage = st.selectbox(
            "المرحلة الدراسية",
            [
                "أقل من ثانوي",
                "ثانوي",
                "بكالوريوس / جامعي",
                "ماجستير",
                "دكتوراه",
                "أخرى",
            ]
        )

        field_of_study = st.selectbox(
            "المجال العلمي / التخصص",
            [
                "علمي / تقني (هندسة، حاسب، علوم، طب...)",
                "إنساني / اجتماعي (أدب، إعلام، تربية، شريعة...)",
                "إداري / اقتصادي",
                "أخرى",
                "لا ينطبق",
            ]
        )

        social_media_usage = st.selectbox(
            "ما مدى استخدامك لوسائل التواصل الاجتماعي؟",
            [
                "يومياً",
                "عدة مرات أسبوعياً",
                "نادراً",
                "لا أستخدمها",
            ]
        )

        media_trust = st.radio(
            "بشكل عام، ما مدى ثقتك بوسائل الإعلام ومصادر الأخبار؟",
            ["منخفضة جداً", "منخفضة", "متوسطة", "عالية", "عالية جداً"],
            horizontal=True
        )

        news_verification_habit = st.radio(
            "هل تتحقق عادةً من صحة الأخبار قبل تصديقها أو مشاركتها؟",
            ["دائماً", "أحياناً", "نادراً", "أبداً"],
            horizontal=True
        )

        submitted = st.form_submit_button("ابدأ التقييم")

        if submitted:

            try:
                supabase.table("participants").insert({
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "age_group": age_group,
                    "gender": gender,
                    "education_stage": education_stage,
                    "field_of_study": field_of_study,
                    "social_media_usage": social_media_usage,
                    "media_trust": media_trust,
                    "news_verification_habit": news_verification_habit,
                }).execute()

                st.session_state.demographics_done = True
                st.rerun()

            except Exception as e:
                st.error(f"⚠️ حدث خطأ أثناء حفظ البيانات، الرجاء المحاولة مرة أخرى.\n\n{e}")

    st.stop()

# ==========================================
# 🔹 Load static item metadata (title, image path, caption)
# ==========================================
@st.cache_data
def load_items():
    _items_df = pd.read_csv(ITEMS_CSV_PATH)
    _items_df = _items_df[_items_df["generated_image_path"].notna()].copy()

    # Stable identifier for each item — filename of the image.
    _items_df["image_id"] = _items_df["generated_image_path"].apply(
        lambda p: os.path.basename(str(p))
    )

    return _items_df.set_index("image_id", drop=False)


items_df = load_items()

# ==========================================
# 🔹 Fetch current evaluation counts from Supabase
# ==========================================
@st.cache_data(ttl=5)
def fetch_eval_counts():
    """Returns {image_id: count} for all evaluations recorded so far."""
    response = supabase.table("evaluations").select("image_id").execute()
    rows = response.data or []
    counts = pd.Series([r["image_id"] for r in rows]).value_counts()
    return counts.to_dict()


@st.cache_data(ttl=5)
def fetch_user_rated_image_ids(uid):
    """Image IDs this specific user has already rated (avoids duplicates)."""
    response = (
        supabase.table("evaluations")
        .select("image_id")
        .eq("user_id", uid)
        .execute()
    )
    rows = response.data or []
    return {r["image_id"] for r in rows}


eval_counts = fetch_eval_counts()
already_rated_by_user = fetch_user_rated_image_ids(user_id)

items_df["eval_count"] = items_df["image_id"].map(eval_counts).fillna(0).astype(int)

# ==========================================
# 🔹 Keep rows with < MAX_EVALS_PER_IMAGE evaluations,
#    excluding ones this user already rated
# ==========================================
remaining = items_df[
    (items_df["eval_count"] < MAX_EVALS_PER_IMAGE)
    & (~items_df["image_id"].isin(already_rated_by_user))
]

# ==========================================
# 🔹 Global completion check — every image has reached the max evaluations
# ==========================================
if (items_df["eval_count"] >= MAX_EVALS_PER_IMAGE).all():

    st.balloons()
    st.success("🎉 شكرًا لمشاركتكم، تم تقييم جميع الصور")
    st.stop()

# ==========================================
# 🔹 Initialize random batch of images for this user
# ==========================================
if "assigned_ids" not in st.session_state:

    available_ids = remaining["image_id"].tolist()

    sample_size = min(MAX_IMAGES_PER_USER, len(available_ids))

    st.session_state.assigned_ids = random.sample(available_ids, sample_size)
    st.session_state.current_position = 0

# ==========================================
# 🔹 User completed all assigned images
# ==========================================
if (
    len(st.session_state.assigned_ids) == 0
    or st.session_state.current_position >= len(st.session_state.assigned_ids)
):

    st.balloons()
    st.success("🎉 انتهى التقييم، شكراً لمشاركتك!")
    st.stop()

# ==========================================
# 🔹 Current image
# ==========================================
current_image_id = st.session_state.assigned_ids[st.session_state.current_position]
current_row = items_df.loc[current_image_id]

# ==========================================
# 🔹 Skip if this image reached the max in the meantime
#    (lightweight query — only this one image, not the whole table)
# ==========================================
current_count_response = (
    supabase.table("evaluations")
    .select("image_id")
    .eq("image_id", current_image_id)
    .execute()
)
current_count = len(current_count_response.data or [])

if current_count >= MAX_EVALS_PER_IMAGE:

    st.session_state.current_position += 1
    st.rerun()

# ==========================================
# 🔹 Progress bar
# ==========================================
progress = (
    st.session_state.current_position + 1
) / len(st.session_state.assigned_ids)

st.progress(progress)

st.markdown(
    f"### 🧾 الخبر رقم "
    f"{st.session_state.current_position + 1}"
    f" / {len(st.session_state.assigned_ids)}"
)

# ==========================================
# 🔹 Display title
# ==========================================
st.subheader(current_row["title"])

# ==========================================
# 🔹 Display image
# ==========================================
img_path = current_row["generated_image_path"]

if pd.notna(img_path):
    img_path = str(img_path)
    if not os.path.isabs(img_path) or not os.path.exists(img_path):
        img_path = os.path.join(IMAGES_DIR, os.path.basename(img_path))

if pd.notna(img_path) and os.path.exists(img_path):
    st.image(img_path)
else:
    st.warning("⚠️ الصورة غير موجودة")

# ==========================================
# 🔹 Display caption
# ==========================================
if (
    "caption" in current_row
    and pd.notna(current_row["caption"])
):
    st.markdown("### 📝 الوصف")
    st.write(current_row["caption"])

# ==========================================
# 🔹 Rating
# ==========================================
st.markdown("### إلى أي مدى تبدو هذه الصورة واقعية؟")
st.caption("تذكير: هذا الخبر والصورة المرفقة مُولَّدان اصطناعياً وليسا حقيقيَّين.")

image_rating = st.slider(
    "تقييم الصورة (1 = تبدو مزيفة بشكل واضح، 5 = تبدو واقعية جداً):",
    min_value=1,
    max_value=5,
    value=3
)

st.markdown("### إلى أي مدى يبدو هذا العنوان واقعياً؟")

title_rating = st.slider(
    "تقييم العنوان (1 = يبدو مزيفاً بشكل واضح، 5 = يبدو واقعياً جداً):",
    min_value=1,
    max_value=5,
    value=3
)

# ==========================================
# 🔹 Submit
# ==========================================
if st.button("إرسال"):

    # Re-check the live count right before inserting (race-condition safety).
    # Bypass the 5s cache here since we need the true current count.
    fresh_response = (
        supabase.table("evaluations")
        .select("image_id")
        .eq("image_id", current_image_id)
        .execute()
    )
    fresh_count = len(fresh_response.data or [])

    if fresh_count >= MAX_EVALS_PER_IMAGE:

        st.warning("⚠️ تم تقييم هذه الصورة بالفعل من قِبل 3 مستخدمين آخرين، سيتم الانتقال للصورة التالية")
        st.session_state.current_position += 1
        st.cache_data.clear()
        st.rerun()

    try:
        supabase.table("evaluations").insert({
            "user_id": user_id,
            "image_id": current_image_id,
            "image_rating": image_rating,
            "title_rating": title_rating,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        st.success("✅ تم حفظ التقييم بنجاح")

    except Exception as e:
        # Most likely a duplicate (unique constraint on image_id+user_id)
        st.warning(f"⚠️ لم يتم حفظ هذا التقييم (ربما تم إرساله مسبقاً). سيتم الانتقال للصورة التالية.\n\n{e}")

    # Clear cached counts so the next page load reflects this submission
    st.cache_data.clear()

    st.session_state.current_position += 1
    st.rerun()