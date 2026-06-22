"""
Database Introspection Script
=============================
Career & University Recommendation System - Phase 1

This script connects to the PostgreSQL database, introspects the full schema,
and produces a Data Dictionary + ER Map summary.

SAFETY: All operations are READ-ONLY. No INSERT/UPDATE/DELETE/DROP.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from tabulate import tabulate
import json

# ──────────────────────────────────────────────
# 1. Load environment variables
# ──────────────────────────────────────────────
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file.")
    print("   Please update .env with your PostgreSQL connection string.")
    print("   Format: postgresql://user:password@host:port/dbname")
    sys.exit(1)

# ──────────────────────────────────────────────
# 2. Connect to Database (READ-ONLY intent)
# ──────────────────────────────────────────────
print("🔌 Connecting to database...")
try:
    engine = create_engine(DATABASE_URL, echo=False)
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        result.fetchone()
    print("✅ Database connection successful!\n")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

inspector = inspect(engine)

# ──────────────────────────────────────────────
# 3. Pull Schema Information
# ──────────────────────────────────────────────
schemas = inspector.get_schema_names()
print(f"📂 Available schemas: {schemas}\n")

# We'll focus on 'public' schema by default, but scan all non-system schemas
target_schemas = [s for s in schemas if s not in ('information_schema', 'pg_catalog', 'pg_toast')]

data_dictionary = {}
er_relationships = []

for schema in target_schemas:
    table_names = inspector.get_table_names(schema=schema)
    if not table_names:
        continue
    
    print(f"{'='*70}")
    print(f"📋 SCHEMA: {schema} ({len(table_names)} tables)")
    print(f"{'='*70}\n")
    
    for table_name in sorted(table_names):
        full_table_name = f"{schema}.{table_name}" if schema != "public" else table_name
        
        # Get columns
        columns = inspector.get_columns(table_name, schema=schema)
        
        # Get primary keys
        pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
        pk_columns = pk_constraint.get("constrained_columns", []) if pk_constraint else []
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
        fk_columns = {fk["constrained_columns"][0]: fk for fk in foreign_keys if fk.get("constrained_columns")}
        
        # Get row count (READ-ONLY)
        try:
            with engine.connect() as conn:
                count_result = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
                )
                row_count = count_result.scalar()
        except Exception:
            row_count = "N/A"
        
        # Build table info
        table_info = {
            "schema": schema,
            "row_count": row_count,
            "columns": [],
            "primary_keys": pk_columns,
            "foreign_keys": foreign_keys,
        }
        
        # Prepare display table
        col_rows = []
        for col in columns:
            col_name = col["name"]
            col_type = str(col["type"])
            nullable = "✓" if col.get("nullable", True) else "✗"
            is_pk = "🔑 PK" if col_name in pk_columns else ""
            is_fk = ""
            
            if col_name in fk_columns:
                fk = fk_columns[col_name]
                ref_table = fk.get("referred_table", "?")
                ref_schema = fk.get("referred_schema", schema)
                ref_cols = fk.get("referred_columns", ["?"])
                is_fk = f"🔗 FK → {ref_schema}.{ref_table}({', '.join(ref_cols)})"
                
                er_relationships.append({
                    "from_table": f"{schema}.{table_name}",
                    "from_column": col_name,
                    "to_table": f"{ref_schema}.{ref_table}",
                    "to_column": ", ".join(ref_cols),
                })
            
            col_rows.append([col_name, col_type, nullable, is_pk, is_fk])
            table_info["columns"].append({
                "name": col_name,
                "type": col_type,
                "nullable": col.get("nullable", True),
                "is_pk": col_name in pk_columns,
                "is_fk": col_name in fk_columns,
            })
        
        data_dictionary[full_table_name] = table_info
        
        # Print table summary
        print(f"┌─ 📊 TABLE: {full_table_name}  (Rows: {row_count:,} )" if isinstance(row_count, int) else f"┌─ 📊 TABLE: {full_table_name}  (Rows: {row_count})")
        print(f"│")
        print(tabulate(
            col_rows,
            headers=["Column", "Type", "Nullable", "Key", "Reference"],
            tablefmt="pipe",
            stralign="left",
        ))
        print(f"│")
        print(f"└─────────────────────────────────────────\n")


# ──────────────────────────────────────────────
# 4. Entity-Relationship Map
# ──────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"🔗 ENTITY-RELATIONSHIP MAP")
print(f"{'='*70}\n")

if er_relationships:
    er_rows = []
    for rel in er_relationships:
        er_rows.append([
            rel["from_table"],
            rel["from_column"],
            "──→",
            rel["to_table"],
            rel["to_column"],
        ])
    print(tabulate(
        er_rows,
        headers=["From Table", "FK Column", "", "To Table", "Referenced Column"],
        tablefmt="pipe",
        stralign="left",
    ))
else:
    print("⚠️  No foreign key relationships detected.")
    print("   Tables may use implicit relationships (matching column names).")

# ──────────────────────────────────────────────
# 5. Feature Readiness Assessment
# ──────────────────────────────────────────────
print(f"\n\n{'='*70}")
print(f"📝 FEATURE READINESS ASSESSMENT FOR RECOMMENDATION SYSTEM")
print(f"{'='*70}\n")

# Define what we look for
desired_features = {
    "Điểm thi / Exam Scores": ["diem", "score", "grade", "mark", "point", "exam", "thi", "ket_qua"],
    "Khối thi / Exam Groups": ["khoi", "block", "group", "to_hop", "combination"],
    "MBTI Personality": ["mbti", "personality", "tinh_cach", "trait"],
    "Holland Code": ["holland", "riasec", "interest", "so_thich"],
    "Ngành học / Major": ["nganh", "major", "field", "chuyen_nganh", "specialization", "career"],
    "Trường ĐH / University": ["truong", "university", "school", "institution", "dai_hoc"],
    "Điểm chuẩn / Admission Score": ["diem_chuan", "admission", "cutoff", "benchmark"],
    "User Profile / Demographics": ["user", "student", "hoc_sinh", "profile", "sinh_vien"],
    "Lịch sử tương tác / Interaction": ["history", "interaction", "click", "view", "rating", "feedback"],
}

all_columns_lower = []
all_table_names_lower = []
for tbl_name, tbl_info in data_dictionary.items():
    all_table_names_lower.append(tbl_name.lower())
    for col in tbl_info["columns"]:
        all_columns_lower.append(col["name"].lower())

print(f"{'Feature Category':<45} {'Status':<10} {'Evidence'}")
print(f"{'-'*45} {'-'*10} {'-'*40}")

for feature, keywords in desired_features.items():
    found_evidence = []
    for kw in keywords:
        for col in all_columns_lower:
            if kw in col:
                found_evidence.append(f"col:{col}")
        for tbl in all_table_names_lower:
            if kw in tbl:
                found_evidence.append(f"tbl:{tbl}")
    
    # Deduplicate
    found_evidence = list(set(found_evidence))
    
    if found_evidence:
        status = "✅ Found"
        evidence_str = ", ".join(found_evidence[:5])
        if len(found_evidence) > 5:
            evidence_str += f" (+{len(found_evidence)-5} more)"
    else:
        status = "❌ Missing"
        evidence_str = "—"
    
    print(f"{feature:<45} {status:<10} {evidence_str}")

print(f"\n{'='*70}")
print(f"📊 SUMMARY")
print(f"{'='*70}")
print(f"Total schemas scanned : {len(target_schemas)}")
print(f"Total tables found    : {len(data_dictionary)}")
print(f"Total relationships   : {len(er_relationships)}")
print(f"{'='*70}\n")

# ──────────────────────────────────────────────
# 6. Export schema to JSON for later phases
# ──────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(__file__), "schema_snapshot.json")
export_data = {
    "schemas": target_schemas,
    "tables": {},
    "relationships": er_relationships,
}
for tbl_name, tbl_info in data_dictionary.items():
    export_data["tables"][tbl_name] = {
        "schema": tbl_info["schema"],
        "row_count": tbl_info["row_count"] if isinstance(tbl_info["row_count"], int) else 0,
        "columns": tbl_info["columns"],
        "primary_keys": tbl_info["primary_keys"],
    }

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

print(f"💾 Schema snapshot exported to: {output_path}")
print(f"\n🏁 Phase 1 introspection complete. Review the output above.")
print(f"   When ready, proceed to Phase 2 (EDA.ipynb generation).")
