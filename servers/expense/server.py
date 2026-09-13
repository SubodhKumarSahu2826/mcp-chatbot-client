from fastmcp import FastMCP
import os
import sqlite3


# ---------------- PATHS ----------------

BASE_DIR = os.path.dirname(__file__)

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "expenses.db")

CATEGORIES_PATH = os.path.join(
    BASE_DIR,
    "categories.json"
)


# ---------------- MCP SERVER ----------------

mcp = FastMCP("ExpenseTracker")


# ---------------- DATABASE ----------------

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                description TEXT DEFAULT '',
                note TEXT DEFAULT '',
                type TEXT DEFAULT 'expense'
            )
        """)


init_db()


# ---------------- ADD EXPENSE ----------------

@mcp.tool()
def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    description: str = "",
    note: str = ""
):
    """Add a new expense entry to the database."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            INSERT INTO expenses(
                date,
                amount,
                category,
                subcategory,
                description,
                note,
                type
            )
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                date,
                amount,
                category,
                subcategory,
                description,
                note,
                "expense"
            )
        )

        return {
            "status": "ok",
            "message": "Expense added successfully",
            "id": cur.lastrowid
        }


# ---------------- LIST EXPENSES ----------------

@mcp.tool()
def list_expenses(
    start_date: str,
    end_date: str
):
    """List all expense entries within an inclusive date range."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                description,
                note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            AND type = 'expense'
            ORDER BY date DESC
            """,
            (start_date, end_date)
        )

        columns = [column[0] for column in cur.description]

        return [
            dict(zip(columns, row))
            for row in cur.fetchall()
        ]


# ---------------- SUMMARIZE ----------------

@mcp.tool()
def summarize():
    """Return total expenses and expenses grouped by category."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            SELECT SUM(amount)
            FROM expenses
            WHERE type = 'expense'
            """
        )

        total = cur.fetchone()[0] or 0

        cur = c.execute(
            """
            SELECT
                category,
                SUM(amount)
            FROM expenses
            WHERE type = 'expense'
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """
        )

        by_category = {
            category: amount
            for category, amount in cur.fetchall()
        }

        return {
            "total_expenses": total,
            "by_category": by_category
        }


# ---------------- EDIT EXPENSE ----------------

@mcp.tool()
def edit_expense(
    expense_id: int,
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    description: str = "",
    note: str = ""
):
    """Edit an existing expense using its ID."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            UPDATE expenses
            SET
                date = ?,
                amount = ?,
                category = ?,
                subcategory = ?,
                description = ?,
                note = ?
            WHERE
                id = ?
                AND type = 'expense'
            """,
            (
                date,
                amount,
                category,
                subcategory,
                description,
                note,
                expense_id
            )
        )

        if cur.rowcount == 0:
            return {
                "status": "error",
                "message": f"No expense found with ID {expense_id}"
            }

        return {
            "status": "ok",
            "message": "Expense updated successfully",
            "id": expense_id
        }


# ---------------- DELETE EXPENSE ----------------

@mcp.tool()
def delete_expense(expense_id: int):
    """Delete an expense using its ID."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            DELETE FROM expenses
            WHERE
                id = ?
                AND type = 'expense'
            """,
            (expense_id,)
        )

        if cur.rowcount == 0:
            return {
                "status": "error",
                "message": f"No expense found with ID {expense_id}"
            }

        return {
            "status": "ok",
            "message": "Expense deleted successfully",
            "id": expense_id
        }


# ---------------- ADD CREDIT ----------------

@mcp.tool()
def add_credit(
    date: str,
    amount: float,
    category: str,
    description: str = "",
    note: str = ""
):
    """Add money received as a credit or income."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            INSERT INTO expenses(
                date,
                amount,
                category,
                description,
                note,
                type
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                date,
                amount,
                category,
                description,
                note,
                "credit"
            )
        )

        return {
            "status": "ok",
            "message": "Credit added successfully",
            "id": cur.lastrowid
        }


# ---------------- CATEGORIES RESOURCE ----------------

@mcp.resource(
    "expense://categories",
    mime_type="application/json"
)
def categories():
    """Return available expense categories."""

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------- START SERVER ----------------

if __name__ == "__main__":
    mcp.run()