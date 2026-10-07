"""
Run: streamlit run human_validation.py
"""
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
from datetime import datetime

DB_PATH = "PJDB.db"
RANDOM_SEED = 7

FACTORS_14 = [
    "company_policy_administration", "supervision", "interpersonal_relations",
    "working_conditions", "salary", "personal_life", "job_security",
    "achievement", "recognition", "work_itself", "responsibility",
    "advancement", "possibility_of_growth", "status",
]
LABELS = {
    "company_policy_administration": "Company Policy",
    "supervision":                   "Supervision",
    "interpersonal_relations":       "Interpersonal Relations",
    "working_conditions":            "Working Conditions",
    "salary":                        "Salary",
    "personal_life":                 "Work-Life Balance",
    "job_security":                  "Job Security",
    "achievement":                   "Achievement",
    "recognition":                   "Recognition",
    "work_itself":                   "Work Itself",
    "responsibility":                "Responsibility",
    "advancement":                   "Advancement",
    "possibility_of_growth":         "Growth",
    "status":                        "Status",
}
DEFINITIONS = {
    "company_policy_administration": "Company-wide organisation, HR processes, bureaucracy, communication structures, delegation.",
    "supervision":                   "Competence, fairness or behaviour of the direct supervisor only.",
    "interpersonal_relations":       "Social quality of relationships with colleagues — atmosphere, collegiality.",
    "working_conditions":            "Physical environment (space, equipment, tools, noise) and workload volume.",
    "salary":                        "Base pay, bonuses, benefits, raises — all forms of compensation.",
    "personal_life":                 "Work's impact on life outside work: work-life balance, remote work, family-friendliness.",
    "job_security":                  "Job stability, contract type, fear of layoffs, company financial health.",
    "achievement":                   "The employee's own sense of accomplishing something — internal feeling of success.",
    "recognition":                   "External acknowledgement by others — praise, awards, feeling valued or ignored.",
    "work_itself":                   "Intrinsic interest, variety, meaningfulness or creativity of the actual tasks.",
    "responsibility":                "Autonomy, decision-making freedom, ownership of one's own work area.",
    "advancement":                   "Actual or potential promotions, title changes, career progression.",
    "possibility_of_growth":         "Opportunities to learn — training, new skills, personal development programmes.",
    "status":                        "External prestige — company brand recognition, impressive job title, rank symbols.",
}
HYGIENE = {
    "company_policy_administration", "supervision", "interpersonal_relations",
    "working_conditions", "salary", "personal_life", "job_security", "status",
}


def get_conn():
    return sqlite3.connect(DB_PATH, timeout=10)


def ensure_table():
    cols = ", ".join(
        [f"p_{f} INTEGER DEFAULT 0, c_{f} INTEGER DEFAULT 0" for f in FACTORS_14]
    )
    with get_conn() as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS human_validation (
                review_id TEXT PRIMARY KEY,
                {cols},
                coded_at TEXT
            )
        """)


@st.cache_data
def load_sample():
    with get_conn() as conn:
        df = pd.read_sql("""
            SELECT r.id AS review_id, r.company, r.pros, r.cons
            FROM REVIEWS_GER r
            WHERE (r.pros IS NOT NULL AND r.pros != '')
               OR (r.cons  IS NOT NULL AND r.cons  != '')
        """, conn)
    return df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)


def load_coded_ids():
    try:
        with get_conn() as conn:
            rows = conn.execute("SELECT review_id FROM human_validation").fetchall()
        return {str(r[0]) for r in rows}
    except Exception:
        return set()


def save_annotation(review_id, pro_vals: dict, con_vals: dict):
    cols = (
        ["review_id"]
        + [f"p_{f}" for f in FACTORS_14]
        + [f"c_{f}" for f in FACTORS_14]
        + ["coded_at"]
    )
    vals = (
        [str(review_id)]
        + [int(pro_vals.get(f, 0)) for f in FACTORS_14]
        + [int(con_vals.get(f, 0)) for f in FACTORS_14]
        + [datetime.now().isoformat()]
    )
    ph = ", ".join(["?"] * len(cols))
    col_str = ", ".join(cols)
    upd = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "review_id")
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO human_validation ({col_str}) VALUES ({ph}) "
            f"ON CONFLICT(review_id) DO UPDATE SET {upd}",
            vals,
        )


def load_results():
    with get_conn() as conn:
        human = pd.read_sql("SELECT * FROM human_validation", conn)
        llm   = pd.read_sql("SELECT * FROM llm_proscons_kununu", conn)
    llm["review_id"]   = llm["review_id"].astype(str)
    human["review_id"] = human["review_id"].astype(str)
    return human.merge(llm, on="review_id", suffixes=("_h", "_l"))


#  App 

st.set_page_config(page_title="Herzberg Coding", layout="wide")
ensure_table()

sample    = load_sample()
coded_ids = load_coded_ids()
n_coded   = sum(str(r) in coded_ids for r in sample["review_id"])

with st.sidebar:
    st.markdown("**Factor Definitions**")
    for f in FACTORS_14:
        tag = "Hygiene" if f in HYGIENE else "Motivator"
        with st.expander(f"{LABELS[f]} ({tag})"):
            st.write(DEFINITIONS[f])
    st.divider()
    st.caption("Code only factors that are clearly and directly mentioned.")

tab_code, tab_results = st.tabs(["Coding", "Results"])

#  Tab 1: Coding 
with tab_code:
    q_total = len(sample)
    prog    = n_coded / q_total if q_total else 1.0
    st.progress(prog, text=f"{n_coded} / {q_total} coded")

    if n_coded >= q_total:
        st.success("All reviews coded.")
        st.stop()

    if "idx" not in st.session_state:
        st.session_state["idx"] = 0

    while (
        st.session_state["idx"] < q_total
        and str(sample.iloc[st.session_state["idx"]]["review_id"]) in coded_ids
    ):
        st.session_state["idx"] += 1

    if st.session_state["idx"] >= q_total:
        st.success("Done.")
        st.stop()

    row = sample.iloc[st.session_state["idx"]]
    rid = str(row["review_id"])

    st.subheader(f"Review {st.session_state['idx'] + 1} / {q_total} — {row['company']}")
    st.caption(f"ID: {rid}")

    col_pro, col_con = st.columns(2)
    with col_pro:
        st.markdown("**Pros**")
        st.info(row["pros"] if pd.notna(row["pros"]) and row["pros"] else "—")
    with col_con:
        st.markdown("**Cons**")
        st.warning(row["cons"] if pd.notna(row["cons"]) and row["cons"] else "—")

    st.divider()
    st.markdown("Select all factors that are clearly mentioned.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Pros**")
        pro_vals = {}
        for f in FACTORS_14:
            pro_vals[f] = st.checkbox(LABELS[f], key=f"pro_{rid}_{f}", help=DEFINITIONS[f])
    with col2:
        st.markdown("**Cons**")
        con_vals = {}
        for f in FACTORS_14:
            con_vals[f] = st.checkbox(LABELS[f], key=f"con_{rid}_{f}", help=DEFINITIONS[f])

    st.divider()
    nav1, nav2, _ = st.columns([1, 1, 4])
    with nav1:
        if st.button("Skip"):
            st.session_state["idx"] += 1
            st.rerun()
    with nav2:
        if st.button("Save & Next", type="primary"):
            save_annotation(rid, pro_vals, con_vals)
            coded_ids.add(rid)
            st.session_state["idx"] += 1
            st.rerun()

#  Tab 2: Results 
with tab_results:
    st.subheader(f"Cohen's Kappa: Human vs. LLM ({n_coded} reviews coded)")

    if n_coded < 10:
        st.info("At least 10 coded reviews required.")
        st.stop()

    merged = load_results()
    kappa_rows = []
    for f in FACTORS_14:
        for prefix, label in [("p", "Pros"), ("c", "Cons")]:
            col_h = f"{prefix}_{f}_h"
            col_l = f"{prefix}_{f}_l"
            if col_h not in merged.columns or col_l not in merged.columns:
                continue
            y_h = merged[col_h].fillna(0).astype(int)
            y_l = merged[col_l].fillna(0).astype(int)
            if y_h.nunique() < 2 and y_l.nunique() < 2:
                kappa = np.nan
            else:
                try:
                    kappa = cohen_kappa_score(y_h, y_l)
                except Exception:
                    kappa = np.nan
            kappa_rows.append({
                "Factor":    LABELS[f],
                "Type":      "Hygiene" if f in HYGIENE else "Motivator",
                "Field":     label,
                "kappa":     kappa,
                "Agreement": (y_h == y_l).mean(),
                "Human +":   int(y_h.sum()),
                "LLM +":     int(y_l.sum()),
            })

    kdf     = pd.DataFrame(kappa_rows)
    avg_k   = kdf["kappa"].dropna().mean()

    col_a, col_b, _ = st.columns([1, 1, 4])
    col_a.metric("Mean kappa", f"{avg_k:.3f}")
    col_b.metric("Reviews coded", n_coded)

    st.divider()
    st.dataframe(
        kdf.style.format({"kappa": "{:.3f}", "Agreement": "{:.1%}"}, na_rep="n/a"),
        use_container_width=True,
        height=600,
    )
  

 