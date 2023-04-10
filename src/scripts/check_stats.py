import sqlite3, os, sys, json

ADMIN_DB_PATH = os.environ.get("ADMIN_DB_PATH")
DATA_DB_PATH = os.environ.get("DATA_DB_PATH")

if not ADMIN_DB_PATH or not DATA_DB_PATH:
    print("You need to specify ADMIN_DB_PATH and DATA_DB_PATH environment variables")
    sys.exit(1)

if __name__ == "__main__":
    admindb = sqlite3.connect(ADMIN_DB_PATH)
    for row in admindb.execute("SELECT COUNT(*) FROM users"):
        user_count = row[0]

    datadb = sqlite3.connect(DATA_DB_PATH)
    num_items = datadb.execute("SELECT COUNT(*) FROM source").fetchone()[0]
    num_edits = datadb.execute("SELECT COUNT(id) FROM history").fetchone()[0]
    num_edited_objects = datadb.execute(
        "SELECT COUNT(distinct id) FROM history"
    ).fetchone()[0]
    num_can_you_help = datadb.execute(
        "SELECT count(id) FROM source WHERE canyouhelp IS NOT NULL"
    ).fetchone()[0]
    num_comments = datadb.execute("SELECT count(uid) FROM annotation").fetchone()[0]

    buf = {
        "num_items": num_items,
        "num_edits": num_edits,
        "num_edited_objects": num_edited_objects,
        "num_can_you_help": num_can_you_help,
        "num_comments": num_comments,
    }

    last_stats = datadb.execute(
        "SELECT obj from stats ORDER BY TIMESTAMP DESC"
    ).fetchone()[0]
    last_stats = json.loads(last_stats)
    if last_stats != buf:
        datadb.execute(
            "insert into stats values( strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), ?)",
            (json.dumps(buf),),
        )
        datadb.commit()
