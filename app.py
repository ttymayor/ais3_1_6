import datetime
import os
import re
import sqlite3

import psutil
from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "monitoring-system-dev-key"

DB_PATH = "monitoring.db"

# 刻意設定為 True，把每次執行的 SQL 顯示在登入頁面上（教學用）
DEBUG_QUERY = True


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ip TEXT,
            success INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            photo_file TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            location TEXT NOT NULL,
            snapshot_time TEXT NOT NULL
        );
        """
    )
    # 種子使用者
    demo_users = [
        ("admin", "password123", "admin"),
        ("alice", "alice123", "user"),
        ("bob", "bob123", "user"),
    ]
    for u, p, r in demo_users:
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
            (u, p, r),
        )
    # 種子監控人物（身分證 -> 監控畫面）
    demo_persons = [
        (
            "A118153566",
            "威利",
            "A118153566.jpg",
            "CAM-01 ｜ 大門口",
            "一樓大廳入口",
            "20260919_15:30:52",
        ),
        (
            "B223456789",
            "陳小美",
            "B223456789.jpg",
            "CAM-02 ｜ 電梯口",
            "東側電梯前",
            "20260919_15:28:10",
        ),
        (
            "C123456789",
            "李大明",
            "C123456789.jpg",
            "CAM-03 ｜ 停車場",
            "地下停車場 B2",
            "20260919_15:25:44",
        ),
        (
            "D123456789",
            "王阿豪",
            "D123456789.jpg",
            "CAM-04 ｜ 走道",
            "三樓走道",
            "20260919_15:22:07",
        ),
    ]
    for p in demo_persons:
        conn.execute(
            "INSERT OR IGNORE INTO persons "
            "(id_number, name, photo_file, camera_id, location, snapshot_time) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            p,
        )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    executed_query = None

    if request.method == "POST":
        # 帳號欄位直接拼接 SQL，存在 SQL 注入漏洞！
        username = request.form["username"]
        password = request.form["password"]
        ip = request.remote_addr or "unknown"

        query = "SELECT * FROM users WHERE username = '{}' AND password = '{}'".format(
            username, password
        )
        executed_query = query

        try:
            cur = get_db().execute(query)
            row = cur.fetchone()

            if row is None:
                success = 0
                error = "帳號或密碼錯誤"
            else:
                success = 1
                session["user_id"] = row["id"]
                session["username"] = row["username"]
                session["role"] = row["role"]
                return redirect(url_for("dashboard"))
        except sqlite3.Error as e:
            success = 0
            error = "SQL 執行錯誤：" + str(e)

        log_attempt(username, ip, success)

    return render_template(
        "login.html", error=error, debug_query=executed_query, debug=DEBUG_QUERY
    )


def log_attempt(username, ip, success):
    conn = get_db()
    conn.execute(
        "INSERT INTO login_logs (username, ip, success, timestamp) VALUES (?, ?, ?, ?)",
        (username, ip, success, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    searched = None
    result = None
    search_term = (request.args.get("id") or "").strip()
    if search_term:
        searched = search_term
        row = (
            get_db()
            .execute("SELECT * FROM persons WHERE id_number = ?", (search_term,))
            .fetchone()
        )
        if row:
            result = dict(row)
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        metrics=get_system_metrics(),
        logs=get_recent_logs(),
        searched=searched,
        result=result,
    )


def get_system_metrics():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    return {
        "cpu": cpu,
        "mem_percent": mem.percent,
        "mem_used": mem.used / 1024**3,
        "mem_total": mem.total / 1024**3,
        "disk_percent": disk.percent,
        "disk_used": disk.used / 1024**3,
        "disk_total": disk.total / 1024**3,
        "net_sent": net.bytes_sent / 1024**2,
        "net_recv": net.bytes_recv / 1024**2,
        "processes": len(psutil.pids()),
        "uptime": psutil.boot_time(),
    }


def get_recent_logs(limit=30):
    conn = get_db()
    rows = conn.execute(
        "SELECT username, ip, success, timestamp FROM login_logs "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
