"""一次性迁移脚本：为旧表添加 content 列，删除废弃列"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "experiments.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cols = [row[1] for row in cur.execute("PRAGMA table_info(experiments)")]
print(f"当前列: {cols}")

if "content" not in cols:
    cur.execute('ALTER TABLE experiments ADD COLUMN content TEXT DEFAULT ""')
    print("已添加 content 列")

for old_col in ["description", "parameters", "results"]:
    if old_col in cols:
        try:
            cur.execute(f"ALTER TABLE experiments DROP COLUMN {old_col}")
            print(f"已删除 {old_col} 列")
        except Exception as e:
            print(f"删除 {old_col} 列失败（SQLite 版本可能不支持 DROP COLUMN）: {e}")

conn.commit()

cols_after = [row[1] for row in cur.execute("PRAGMA table_info(experiments)")]
print(f"迁移后列: {cols_after}")

conn.close()
print("迁移完成！")
