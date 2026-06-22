"""
Generate EDA.ipynb notebook for Phase 2.
Creates a comprehensive Exploratory Data Analysis notebook with pre-built cells.
"""
import json

def md_cell(source):
    """Create a markdown cell."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip().split("\n")]
    }

def code_cell(source, cell_id=None):
    """Create a code cell."""
    cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip().split("\n")]
    }
    return cell

cells = []

# ═══════════════════════════════════════════════════════════════
# SECTION 1: Setup
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""# 📊 Exploratory Data Analysis — 9study Career & University Recommendation System

**Objective**: Phân tích dữ liệu từ database 9study để hiểu rõ phân phối, chất lượng dữ liệu, và chuẩn bị cho việc xây dựng Recommendation System.

**Safety**: Tất cả queries đều READ-ONLY. Không có INSERT/UPDATE/DELETE/DROP.

---
## 1. Setup & Configuration"""))

cells.append(code_cell("""# Cell 1: Import Libraries & Load Environment
import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from collections import Counter

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_colwidth', 80)
pd.set_option('display.float_format', '{:.2f}'.format)

# Plot style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Load environment
load_dotenv(override=True)
print("✅ Libraries imported successfully.")"""))

cells.append(code_cell("""# Cell 2: Database Connection (Safe, READ-ONLY)
DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL, "❌ DATABASE_URL not found in .env"

engine = create_engine(DATABASE_URL, echo=False)

# Verify connection
with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    pg_version = result.scalar()
    print(f"✅ Connected to PostgreSQL")
    print(f"   Version: {pg_version[:60]}...")
    
    # Count tables
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
    ))
    n_tables = result.scalar()
    print(f"   Tables in 'public' schema: {n_tables}")"""))

# ═══════════════════════════════════════════════════════════════
# SECTION 2: Load Core Tables
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""---
## 2. Load Core Tables
Tải dữ liệu từ các bảng quan trọng nhất cho Recommendation System."""))

cells.append(code_cell("""# Cell 3: Load Universities
df_universities = pd.read_sql(
    "SELECT * FROM universities WHERE deleted_at IS NULL",
    engine
)
print(f"🏛️ Universities: {len(df_universities)} rows × {df_universities.shape[1]} cols")
df_universities.head(3)"""))

cells.append(code_cell("""# Cell 4: Load Programs (Ngành đào tạo)
df_programs = pd.read_sql(
    "SELECT * FROM programs WHERE deleted_at IS NULL",
    engine
)
print(f"📚 Programs: {len(df_programs)} rows × {df_programs.shape[1]} cols")
df_programs.head(3)"""))

cells.append(code_cell("""# Cell 5: Load Major Groups (Nhóm ngành)
df_major_groups = pd.read_sql(
    "SELECT * FROM major_groups",
    engine
)
print(f"🏷️ Major Groups: {len(df_major_groups)} rows")
df_major_groups"""))

cells.append(code_cell("""# Cell 6: Load Admission Scores (Điểm chuẩn)
df_admission_scores = pd.read_sql('''
    SELECT 
        a_s.id, a_s.program_admission_id, a_s.year, a_s.score, a_s.note,
        pa.program_id, pa.method, pa.exam_blocks,
        p.university_id, p.major_code, p.major_name, p.major_group_id,
        p.program_type, p.specialization, p.total_quota,
        p.tuition_min, p.tuition_max,
        u.university_code, u.name as university_name, u.province, u.type as university_type
    FROM admission_scores a_s
    JOIN program_admissions pa ON a_s.program_admission_id = pa.id
    JOIN programs p ON pa.program_id = p.id
    JOIN universities u ON p.university_id = u.id
    WHERE a_s.deleted_at IS NULL 
      AND pa.deleted_at IS NULL
      AND p.deleted_at IS NULL
      AND u.deleted_at IS NULL
''', engine)
print(f"📊 Admission Scores (enriched): {len(df_admission_scores)} rows × {df_admission_scores.shape[1]} cols")
df_admission_scores.head(3)"""))

cells.append(code_cell("""# Cell 7: Load Users
df_users = pd.read_sql(
    "SELECT id, created_at, name, email, role, status FROM users WHERE deleted_at IS NULL",
    engine
)
print(f"👤 Users: {len(df_users)} rows")
df_users.head()"""))

cells.append(code_cell("""# Cell 8: Load Exam Attempts (Lịch sử thi thử)
df_exam_attempts = pd.read_sql('''
    SELECT ea.*, e.title as exam_title, e.subject_id, s.name as subject_name
    FROM exam_attempts ea
    JOIN exams e ON ea.exam_id = e.id
    LEFT JOIN subjects s ON e.subject_id = s.id
    WHERE ea.deleted_at IS NULL
''', engine)
print(f"📝 Exam Attempts: {len(df_exam_attempts)} rows")
df_exam_attempts.head()"""))

cells.append(code_cell("""# Cell 9: Load Subjects
df_subjects = pd.read_sql(
    "SELECT * FROM subjects WHERE deleted_at IS NULL ORDER BY sort_order",
    engine
)
print(f"📖 Subjects: {len(df_subjects)} rows")
df_subjects[['id', 'name', 'short_name', 'sort_order']]"""))

cells.append(code_cell("""# Cell 10: Load Admission Methods
df_admission_methods = pd.read_sql('''
    SELECT am.*, u.name as university_name, u.university_code
    FROM admission_methods am
    JOIN universities u ON am.university_id = u.id
    WHERE am.deleted_at IS NULL AND u.deleted_at IS NULL
''', engine)
print(f"🔑 Admission Methods: {len(df_admission_methods)} rows")
df_admission_methods.head(3)"""))

# ═══════════════════════════════════════════════════════════════
# SECTION 3: Data Quality & Profiling
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""---
## 3. Data Quality Profiling
Kiểm tra missing values, data types, và tình trạng dữ liệu tổng thể."""))

cells.append(code_cell("""# Cell 11: Missing Values Analysis — All Core Tables
def missing_report(df, name):
    \"\"\"Generate a missing values report for a DataFrame.\"\"\"
    total = len(df)
    missing = df.isnull().sum()
    missing_pct = (missing / total * 100).round(2)
    
    report = pd.DataFrame({
        'Column': missing.index,
        'Missing': missing.values,
        'Missing %': missing_pct.values,
        'Dtype': df.dtypes.values
    })
    report = report[report['Missing'] > 0].sort_values('Missing %', ascending=False)
    
    if len(report) == 0:
        print(f"  ✅ {name}: No missing values!")
    else:
        print(f"  ⚠️ {name}: {len(report)} columns with missing values")
        print(report.to_string(index=False))
    print()
    return report

print("=" * 70)
print("📋 MISSING VALUES REPORT")
print("=" * 70)

datasets = {
    'Universities': df_universities,
    'Programs': df_programs,
    'Major Groups': df_major_groups,
    'Admission Scores (enriched)': df_admission_scores,
    'Users': df_users,
    'Exam Attempts': df_exam_attempts,
    'Subjects': df_subjects,
}

missing_reports = {}
for name, df in datasets.items():
    missing_reports[name] = missing_report(df, name)"""))

cells.append(code_cell("""# Cell 12: Missing Values Heatmap — Universities & Programs
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Universities
uni_cols = ['university_code', 'name', 'province', 'type', 'website', 
            'logo_url', 'featured_major', 'overview_text', 'facts', 'tuition_status']
uni_missing = df_universities[uni_cols].isnull()
sns.heatmap(uni_missing.T, cbar=True, yticklabels=True, ax=axes[0],
            cmap='YlOrRd', cbar_kws={'label': 'Missing'})
axes[0].set_title(f'Universities Missing Values (n={len(df_universities)})')
axes[0].set_xlabel('Row Index')

# Programs
prog_cols = ['major_code', 'major_name', 'program_type', 'specialization',
             'major_group_id', 'total_quota', 'tuition_min', 'tuition_max', 'is_featured']
prog_missing = df_programs[prog_cols].isnull()
sns.heatmap(prog_missing.T, cbar=True, yticklabels=True, ax=axes[1],
            cmap='YlOrRd', cbar_kws={'label': 'Missing'})
axes[1].set_title(f'Programs Missing Values (n={len(df_programs)})')
axes[1].set_xlabel('Row Index')

plt.tight_layout()
plt.savefig('plots/missing_values_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
print("💾 Saved: plots/missing_values_heatmap.png")"""))

# ═══════════════════════════════════════════════════════════════
# SECTION 4: Distributions
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""---
## 4. Data Distributions
Phân tích phân phối điểm chuẩn, ngành nghề, trường học."""))

cells.append(code_cell("""# Cell 13: Admission Score Distribution by Year
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Overall distribution
valid_scores = df_admission_scores[df_admission_scores['score'].notna() & (df_admission_scores['score'] > 0)]
sns.histplot(valid_scores['score'], bins=50, kde=True, ax=axes[0], color='#3498db')
axes[0].set_title('Overall Admission Score Distribution')
axes[0].set_xlabel('Score')
axes[0].set_ylabel('Count')
axes[0].axvline(valid_scores['score'].median(), color='red', linestyle='--', label=f"Median: {valid_scores['score'].median():.1f}")
axes[0].legend()

# By year (boxplot)
years = sorted(valid_scores['year'].unique())
sns.boxplot(data=valid_scores, x='year', y='score', ax=axes[1], palette='viridis')
axes[1].set_title('Admission Score by Year')
axes[1].set_xlabel('Year')
axes[1].set_ylabel('Score')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('plots/score_distribution.png', dpi=150, bbox_inches='tight')
plt.show()

# Stats
print("📊 Score Statistics:")
print(valid_scores.groupby('year')['score'].describe().round(2))"""))

cells.append(code_cell("""# Cell 14: Score Distribution by Admission Method
fig, ax = plt.subplots(figsize=(14, 7))

top_methods = valid_scores['method'].value_counts().head(10).index.tolist()
filtered = valid_scores[valid_scores['method'].isin(top_methods)]

sns.violinplot(data=filtered, x='method', y='score', ax=ax, palette='Set2', inner='box')
ax.set_title('Score Distribution by Admission Method (Top 10)')
ax.set_xlabel('Admission Method')
ax.set_ylabel('Score')
ax.tick_params(axis='x', rotation=45, labelsize=9)

plt.tight_layout()
plt.savefig('plots/score_by_method.png', dpi=150, bbox_inches='tight')
plt.show()

print("\\n📊 Records per method:")
print(valid_scores['method'].value_counts().head(10))"""))

cells.append(code_cell("""# Cell 15: University Distribution by Province & Type
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# By Province (Top 15)
province_counts = df_universities['province'].value_counts().head(15)
province_counts.plot(kind='barh', ax=axes[0], color=sns.color_palette('husl', 15))
axes[0].set_title('Top 15 Provinces by Number of Universities')
axes[0].set_xlabel('Number of Universities')
axes[0].invert_yaxis()
for i, v in enumerate(province_counts.values):
    axes[0].text(v + 0.3, i, str(v), va='center', fontweight='bold')

# By Type
if 'type' in df_universities.columns:
    type_counts = df_universities['type'].value_counts()
    colors = sns.color_palette('pastel', len(type_counts))
    wedges, texts, autotexts = axes[1].pie(
        type_counts.values, labels=type_counts.index, autopct='%1.1f%%',
        colors=colors, startangle=90
    )
    axes[1].set_title('Universities by Type')

plt.tight_layout()
plt.savefig('plots/university_distribution.png', dpi=150, bbox_inches='tight')
plt.show()"""))

cells.append(code_cell("""# Cell 16: Programs per Major Group (Nhóm ngành)
# Merge to get group names
df_programs_with_group = df_programs.merge(
    df_major_groups[['id', 'name']].rename(columns={'id': 'group_id', 'name': 'group_name'}), 
    left_on='major_group_id', 
    right_on='group_id', 
    how='left'
)

fig, ax = plt.subplots(figsize=(14, 10))
group_counts = df_programs_with_group['group_name'].value_counts()

colors = sns.color_palette('husl', len(group_counts))
group_counts.plot(kind='barh', ax=ax, color=colors)
ax.set_title('Number of Programs per Major Group (Nhóm ngành)')
ax.set_xlabel('Number of Programs')
ax.set_ylabel('Major Group')
ax.invert_yaxis()

for i, v in enumerate(group_counts.values):
    ax.text(v + 5, i, str(v), va='center', fontweight='bold', fontsize=9)

plt.tight_layout()
plt.savefig('plots/programs_per_major_group.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\\n📊 Total major groups: {len(group_counts)}")
print(f"   Programs without group: {df_programs_with_group['group_name'].isna().sum()}")"""))

cells.append(code_cell("""# Cell 17: Programs per University (Top 20)
fig, ax = plt.subplots(figsize=(14, 8))

programs_per_uni = df_programs.merge(
    df_universities[['id', 'name', 'university_code']], 
    left_on='university_id', right_on='id', suffixes=('', '_uni')
)
uni_program_counts = programs_per_uni.groupby('university_code').size().sort_values(ascending=False)

top20 = uni_program_counts.head(20)
top20.plot(kind='bar', ax=ax, color=sns.color_palette('coolwarm', 20))
ax.set_title('Top 20 Universities by Number of Programs')
ax.set_xlabel('University Code')
ax.set_ylabel('Number of Programs')
ax.tick_params(axis='x', rotation=45)

for i, v in enumerate(top20.values):
    ax.text(i, v + 1, str(v), ha='center', fontweight='bold', fontsize=8)

plt.tight_layout()
plt.savefig('plots/programs_per_university.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\\n📊 University program stats:")
print(f"   Total universities with programs: {len(uni_program_counts)}")
print(f"   Mean programs/university: {uni_program_counts.mean():.1f}")
print(f"   Median: {uni_program_counts.median():.0f}")
print(f"   Max: {uni_program_counts.max()} ({uni_program_counts.idxmax()})")"""))

# ═══════════════════════════════════════════════════════════════
# SECTION 5: Outlier Detection
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""---
## 5. Outlier Detection
Phát hiện giá trị bất thường trong điểm chuẩn, học phí, chỉ tiêu."""))

cells.append(code_cell("""# Cell 18: Outlier Detection — Admission Scores
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Score outliers
q1 = valid_scores['score'].quantile(0.25)
q3 = valid_scores['score'].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
outliers = valid_scores[(valid_scores['score'] < lower) | (valid_scores['score'] > upper)]

sns.boxplot(y=valid_scores['score'], ax=axes[0], color='#3498db')
axes[0].set_title(f'Score Outliers (n={len(outliers)}, {len(outliers)/len(valid_scores)*100:.1f}%)')
axes[0].axhline(lower, color='red', linestyle='--', alpha=0.5, label=f'Lower: {lower:.1f}')
axes[0].axhline(upper, color='red', linestyle='--', alpha=0.5, label=f'Upper: {upper:.1f}')
axes[0].legend(fontsize=9)

# Tuition outliers (programs)
tuition_data = df_programs[df_programs['tuition_min'].notna() & (df_programs['tuition_min'] > 0)]
if len(tuition_data) > 0:
    sns.boxplot(y=tuition_data['tuition_min'] / 1e6, ax=axes[1], color='#2ecc71')
    axes[1].set_title(f'Tuition Min (million VND)')
    axes[1].set_ylabel('Million VND')

# Quota outliers
quota_data = df_programs[df_programs['total_quota'].notna() & (df_programs['total_quota'] > 0)]
if len(quota_data) > 0:
    sns.boxplot(y=quota_data['total_quota'], ax=axes[2], color='#e74c3c')
    axes[2].set_title(f'Program Quota Distribution')
    axes[2].set_ylabel('Total Quota')

plt.tight_layout()
plt.savefig('plots/outlier_detection.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\\n📊 Outlier Summary:")
print(f"   Scores: {len(outliers)} outliers out of {len(valid_scores)} ({len(outliers)/len(valid_scores)*100:.1f}%)")
print(f"   Score range: [{valid_scores['score'].min():.1f}, {valid_scores['score'].max():.1f}]")
print(f"   IQR bounds: [{lower:.1f}, {upper:.1f}]")

if len(outliers) > 0:
    print(f"\\n   Top outlier scores:")
    print(outliers.nlargest(5, 'score')[['university_name', 'major_name', 'score', 'year', 'method']].to_string(index=False))"""))

# ═══════════════════════════════════════════════════════════════
# SECTION 6: Class Imbalance
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""---
## 6. Class Imbalance Analysis
Trường/Ngành nào đang bị over-represented hoặc under-represented?"""))

cells.append(code_cell("""# Cell 19: Class Imbalance — Major Groups
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Major group representation in programs
group_dist = df_programs_with_group['group_name'].value_counts()
group_pct = (group_dist / group_dist.sum() * 100).round(2)

# Pareto chart
ax1 = axes[0]
cumulative = group_pct.cumsum()
ax1.bar(range(len(group_pct)), group_pct.values, color=sns.color_palette('husl', len(group_pct)), alpha=0.7)
ax1_twin = ax1.twinx()
ax1_twin.plot(range(len(cumulative)), cumulative.values, 'r-o', markersize=4, label='Cumulative %')
ax1_twin.set_ylabel('Cumulative %')
ax1_twin.axhline(80, color='gray', linestyle='--', alpha=0.5, label='80% threshold')
ax1_twin.legend(loc='center right')
ax1.set_title('Major Group Distribution (Pareto)')
ax1.set_xlabel('Major Group (ranked)')
ax1.set_ylabel('% of Programs')

# Score records per university (Top vs Bottom)
score_per_uni = df_admission_scores.groupby('university_name').size()
ax2 = axes[1]
ax2.hist(score_per_uni.values, bins=30, color='#3498db', alpha=0.7, edgecolor='white')
ax2.set_title(f'Score Records per University (mean={score_per_uni.mean():.0f})')
ax2.set_xlabel('Number of Score Records')
ax2.set_ylabel('Number of Universities')
ax2.axvline(score_per_uni.median(), color='red', linestyle='--', label=f'Median: {score_per_uni.median():.0f}')
ax2.legend()

plt.tight_layout()
plt.savefig('plots/class_imbalance.png', dpi=150, bbox_inches='tight')
plt.show()

# Identify over/under-represented
print("\\n📊 IMBALANCE ANALYSIS")
print("=" * 60)
print(f"\\n🔝 Top 5 Over-represented Major Groups:")
for i, (name, pct) in enumerate(group_pct.head(5).items()):
    print(f"   {i+1}. {name}: {pct:.1f}% ({group_dist[name]} programs)")

print(f"\\n🔻 Bottom 5 Under-represented Major Groups:")
for i, (name, pct) in enumerate(group_pct.tail(5).items()):
    print(f"   {i+1}. {name}: {pct:.1f}% ({group_dist[name]} programs)")"""))

cells.append(code_cell("""# Cell 20: Province Imbalance — Geographic distribution
fig, ax = plt.subplots(figsize=(16, 6))

province_programs = programs_per_uni.groupby('province' if 'province' in programs_per_uni.columns 
                                              else df_universities.set_index('id').loc[
                                                  programs_per_uni['university_id']
                                              ]['province'].values).size()

# Recalculate with proper merge
uni_province = df_programs.merge(
    df_universities[['id', 'province']], 
    left_on='university_id', right_on='id', suffixes=('', '_uni')
)
province_prog_counts = uni_province.groupby('province').size().sort_values(ascending=False)

province_prog_counts.head(20).plot(kind='bar', ax=ax, color=sns.color_palette('Spectral', 20))
ax.set_title('Programs by Province (Top 20)')
ax.set_xlabel('Province')
ax.set_ylabel('Number of Programs')
ax.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('plots/province_imbalance.png', dpi=150, bbox_inches='tight')
plt.show()

total = province_prog_counts.sum()
top3 = province_prog_counts.head(3)
print(f"\\n📊 Geographic Concentration:")
print(f"   Top 3 provinces hold {top3.sum()/total*100:.1f}% of all programs:")
for prov, cnt in top3.items():
    print(f"   - {prov}: {cnt} programs ({cnt/total*100:.1f}%)")"""))

# ═══════════════════════════════════════════════════════════════
# SECTION 7: Correlation & Feature Analysis
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""---
## 7. Feature Correlation & Relationship Analysis
Phân tích mối quan hệ giữa các features quan trọng."""))

cells.append(code_cell("""# Cell 21: Score vs Tuition Correlation
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Merge scores with tuition
score_tuition = df_admission_scores.merge(
    df_programs[['id', 'tuition_min', 'tuition_max', 'total_quota']],
    left_on='program_id', right_on='id', suffixes=('', '_prog')
)
score_tuition = score_tuition[
    score_tuition['score'].notna() & 
    score_tuition['tuition_min'].notna() & 
    (score_tuition['score'] > 0) &
    (score_tuition['tuition_min'] > 0)
]

if len(score_tuition) > 0:
    # Score vs Tuition
    ax = axes[0]
    ax.scatter(score_tuition['tuition_min'] / 1e6, score_tuition['score'], 
               alpha=0.1, s=5, color='#3498db')
    ax.set_title('Admission Score vs Tuition')
    ax.set_xlabel('Tuition Min (million VND)')
    ax.set_ylabel('Admission Score')
    
    corr = score_tuition[['score', 'tuition_min']].corr().iloc[0, 1]
    ax.text(0.05, 0.95, f'r = {corr:.3f}', transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Score vs Quota
score_quota = score_tuition[score_tuition['total_quota'].notna() & (score_tuition['total_quota'] > 0)]
if len(score_quota) > 0:
    ax = axes[1]
    ax.scatter(score_quota['total_quota'], score_quota['score'],
               alpha=0.1, s=5, color='#2ecc71')
    ax.set_title('Admission Score vs Quota')
    ax.set_xlabel('Total Quota')
    ax.set_ylabel('Admission Score')
    
    corr = score_quota[['score', 'total_quota']].corr().iloc[0, 1]
    ax.text(0.05, 0.95, f'r = {corr:.3f}', transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('plots/score_correlations.png', dpi=150, bbox_inches='tight')
plt.show()"""))

cells.append(code_cell("""# Cell 22: Score Trends Over Years by Top Major Groups
fig, ax = plt.subplots(figsize=(14, 7))

# Enrich scores with major group names
score_with_group = df_admission_scores.merge(
    df_programs[['id', 'major_group_id']], 
    left_on='program_id', right_on='id', suffixes=('', '_prog')
).merge(
    df_major_groups[['id', 'name']].rename(columns={'id': 'mg_id', 'name': 'group_name'}), 
    left_on='major_group_id', right_on='mg_id'
)

# Top 8 major groups by volume
top_groups = score_with_group['group_name'].value_counts().head(8).index
filtered = score_with_group[
    score_with_group['group_name'].isin(top_groups) & 
    score_with_group['score'].notna() &
    (score_with_group['score'] > 0)
]

trend = filtered.groupby(['year', 'group_name'])['score'].median().reset_index()
for grp in top_groups:
    grp_data = trend[trend['group_name'] == grp]
    ax.plot(grp_data['year'], grp_data['score'], marker='o', linewidth=2, label=grp)

ax.set_title('Median Admission Score Trend by Major Group (Top 8)')
ax.set_xlabel('Year')
ax.set_ylabel('Median Score')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plots/score_trend_by_group.png', dpi=150, bbox_inches='tight')
plt.show()"""))

# ═══════════════════════════════════════════════════════════════
# SECTION 8: Summary
# ═══════════════════════════════════════════════════════════════

cells.append(md_cell("""---
## 8. EDA Summary & Key Findings"""))

cells.append(code_cell("""# Cell 23: Summary Statistics
print("=" * 70)
print("📊 EDA SUMMARY REPORT")
print("=" * 70)

print(f\"\"\"
┌─────────────────────────────────────────────────────────────────┐
│ DATASET OVERVIEW                                                │
├─────────────────────────────────────────────────────────────────┤
│ Universities        : {len(df_universities):>6,}                                    │
│ Programs (ngành)    : {len(df_programs):>6,}                                    │
│ Major Groups        : {len(df_major_groups):>6,}                                    │
│ Admission Scores    : {len(df_admission_scores):>6,}                                    │
│ Users               : {len(df_users):>6,}                                    │
│ Exam Attempts       : {len(df_exam_attempts):>6,}                                    │
│ Subjects            : {len(df_subjects):>6,}                                    │
├─────────────────────────────────────────────────────────────────┤
│ SCORE STATISTICS                                                │
├─────────────────────────────────────────────────────────────────┤
│ Valid scores        : {len(valid_scores):>6,}                                    │
│ Mean score          : {valid_scores['score'].mean():>8.2f}                                  │
│ Median score        : {valid_scores['score'].median():>8.2f}                                  │
│ Std dev             : {valid_scores['score'].std():>8.2f}                                  │
│ Years covered       : {sorted(valid_scores['year'].unique())}  │
├─────────────────────────────────────────────────────────────────┤
│ DATA QUALITY                                                    │
├─────────────────────────────────────────────────────────────────┤
│ User data           : ⚠️ SPARSE (only {len(df_users)} users)                      │
│ Interaction data    : ❌ MISSING (0 answer records)                │
│ MBTI/Holland        : ❌ NOT AVAILABLE                              │
│ Item metadata       : ✅ RICH                                       │
│ Score history       : ✅ COMPREHENSIVE                              │
└─────────────────────────────────────────────────────────────────┘
\"\"\")

print("\\n🏁 EDA Complete. Ready for Phase 3: Recommendation System Architecture.")"""))

# ═══════════════════════════════════════════════════════════════
# Build Notebook
# ═══════════════════════════════════════════════════════════════

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.12.0",
            "mimetype": "text/x-python",
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py"
        }
    },
    "cells": cells
}

# Fix: remove trailing newline from last line of each cell
for cell in notebook["cells"]:
    if cell["source"]:
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

output_path = "EDA.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"✅ Created {output_path}")
print(f"   Total cells: {len(cells)}")
print(f"   Code cells: {sum(1 for c in cells if c['cell_type'] == 'code')}")
print(f"   Markdown cells: {sum(1 for c in cells if c['cell_type'] == 'markdown')}")
