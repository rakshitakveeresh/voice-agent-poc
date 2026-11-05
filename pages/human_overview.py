import os
from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env", override=True)


def is_placeholder(value):
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    lowered = text.lower()
    placeholder_markers = [
        "user",
        "password",
        "host",
        "dbname",
        "example.com",
        "postgresql://user:password@host:5432/dbname",
    ]
    return lowered == "user" or lowered == "password" or lowered == "host" or lowered == "dbname" or lowered in {m.lower() for m in placeholder_markers}


def get_db_connection():
    database_url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
    if database_url:
        if is_placeholder(database_url):
            return None
        try:
            return psycopg2.connect(database_url)
        except Exception:
            return None

    required = [
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]
    if all(os.getenv(key) for key in required):
        host = os.getenv("POSTGRES_HOST", "").strip()
        dbname = os.getenv("POSTGRES_DB", "").strip()
        user = os.getenv("POSTGRES_USER", "").strip()
        password = os.getenv("POSTGRES_PASSWORD", "").strip()
        if any(is_placeholder(v) for v in (host, dbname, user, password)):
            return None
        try:
            return psycopg2.connect(
                host=host,
                dbname=dbname,
                user=user,
                password=password,
                port=os.getenv("POSTGRES_PORT", "5432"),
            )
        except Exception:
            return None

    alt_required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    if all(os.getenv(key) for key in alt_required):
        host = os.getenv("DB_HOST", "").strip()
        dbname = os.getenv("DB_NAME", "").strip()
        user = os.getenv("DB_USER", "").strip()
        password = os.getenv("DB_PASSWORD", "").strip()
        if any(is_placeholder(v) for v in (host, dbname, user, password)):
            return None
        try:
            return psycopg2.connect(
                host=host,
                dbname=dbname,
                user=user,
                password=password,
                port=os.getenv("DB_PORT", "5432"),
            )
        except Exception:
            return None

    return None


@st.cache_data(ttl=60)
def load_customers():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame(), "missing"

    try:
        query = """
            SELECT
                customer_id,
                name,
                email,
                phone,
                preferred_language,
                customer_complaint,
                processed,
                created_at
            FROM customers
            ORDER BY created_at DESC;
        """
        df = pd.read_sql_query(query, conn)
        if "processed" in df.columns:
            df["processed"] = df["processed"].fillna(False).astype(bool)
        if "customer_complaint" not in df.columns:
            df["customer_complaint"] = None
        return df, "ok"
    except Exception as exc:
        return pd.DataFrame(), str(exc)
    finally:
        conn.close()


def ensure_customer_columns():
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='customers'")
            existing = {row[0] for row in cur.fetchall()}
            if "customer_complaint" not in existing:
                cur.execute("ALTER TABLE public.customers ADD COLUMN customer_complaint TEXT")
            if "processed" not in existing:
                cur.execute("ALTER TABLE public.customers ADD COLUMN processed BOOLEAN DEFAULT FALSE")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def mark_customer_processed(customer_id):
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE public.customers SET processed = TRUE WHERE customer_id = %s",
                (customer_id,),
            )
        conn.commit()
        st.cache_data.clear()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def render_human_overview():
    st.set_page_config(page_title="Human Overview", page_icon="👥")
    st.title("Human Overview")

    ensure_customer_columns()
    customers_df, status = load_customers()

    if status == "missing":
        st.warning(
            "No Postgres connection details were found in the environment. Add DATABASE_URL or POSTGRES_* / DB_* values in your .env file."
        )
        return

    if status != "ok":
        st.error(f"Database query failed: {status}")
        return

    if customers_df.empty:
        st.info("No customer records found in the customers table.")
        return

    st.subheader("Customer records")

    customers_df = customers_df.copy()
    customers_df["created_at"] = pd.to_datetime(customers_df["created_at"], errors="coerce")
    customers_df = customers_df.sort_values("created_at", ascending=False, na_position="last")

    display_cols = [
        "customer_id",
        "name",
        "email",
        "phone",
        "preferred_language",
        "customer_complaint",
        "processed",
        "created_at",
    ]
    for col in display_cols:
        if col not in customers_df.columns:
            if col == "processed":
                customers_df[col] = False
            else:
                customers_df[col] = None

    customers_df = customers_df[display_cols]
    customers_df["processed"] = customers_df["processed"].fillna(False).astype(bool)

    customers_df = customers_df.copy()
    customers_df["action"] = customers_df["customer_id"].apply(
        lambda cid: "Done" if customers_df.loc[customers_df["customer_id"] == cid, "processed"].iloc[0] else "Mark done"
    )

    def update_processed_status(cid):
        if mark_customer_processed(cid):
            st.session_state["processed_updated"] = True
            st.rerun()

    display_df = customers_df[[
        "customer_id",
        "name",
        "email",
        "phone",
        "preferred_language",
        "customer_complaint",
        "processed",
        "created_at",
    ]].copy()
    display_df["processed"] = display_df["processed"].map({True: "Done", False: "Pending"})
    display_df["customer_id"] = display_df["customer_id"].astype(str)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Quick actions")
    for _, row in customers_df.iterrows():
        customer_id = row["customer_id"]
        if not row["processed"]:
            if st.button(f"Set customer #{customer_id} as done", key=f"process_row_{customer_id}"):
                update_processed_status(customer_id)

    with st.expander("Quick summary"):
        total_customers = len(customers_df)
        processed_count = int(customers_df["processed"].sum())
        pending_count = total_customers - processed_count
        lang_counts = customers_df["preferred_language"].fillna("Unknown").value_counts()
        st.metric("Total customers", total_customers)
        st.metric("Processed", processed_count)
        st.metric("Pending", pending_count)
        st.bar_chart(lang_counts)


if __name__ == "__main__":
    render_human_overview()
