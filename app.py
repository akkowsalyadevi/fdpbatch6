"""
Streamlit SQLite CRUD App

This app demonstrates full CRUD operations (Create, Read, Update, Delete)
using an SQLite database. The database file is created/connected on startup.

Run with: streamlit run app.py

Fields: name, email, age, notes
"""
import os
import sqlite3
from typing import List, Tuple, Optional
import streamlit as st
import pandas as pd


# --------- Database helpers ---------
DB_FILENAME = os.path.join(os.path.dirname(__file__), "data.db")


def get_connection(db_path: str = DB_FILENAME) -> sqlite3.Connection:
	"""Return a new SQLite connection with foreign keys enabled."""
	conn = sqlite3.connect(db_path, check_same_thread=False)
	conn.row_factory = sqlite3.Row
	# Ensure foreign key constraint is enabled
	conn.execute("PRAGMA foreign_keys = ON;")
	return conn


def init_db() -> None:
	"""Create the table if it does not exist."""
	with get_connection() as conn:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS entries (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				email TEXT NOT NULL,
				age INTEGER,
				notes TEXT
			)
			"""
		)


def insert_entry(name: str, email: str, age: Optional[int], notes: str) -> int:
	"""Insert a new entry and return its new id."""
	with get_connection() as conn:
		cur = conn.execute(
			"INSERT INTO entries (name, email, age, notes) VALUES (?, ?, ?, ?)",
			(name, email, age, notes),
		)
		return cur.lastrowid


def view_all() -> List[sqlite3.Row]:
	"""Return all records from entries."""
	with get_connection() as conn:
		cur = conn.execute("SELECT * FROM entries ORDER BY id DESC")
		return cur.fetchall()


def get_entry(row_id: int) -> Optional[sqlite3.Row]:
	"""Return a single entry by id, or None if not found."""
	with get_connection() as conn:
		cur = conn.execute("SELECT * FROM entries WHERE id = ?", (row_id,))
		return cur.fetchone()


def update_entry(row_id: int, name: str, email: str, age: Optional[int], notes: str) -> bool:
	"""Update an existing entry; return True if updated."""
	with get_connection() as conn:
		cur = conn.execute(
			"UPDATE entries SET name = ?, email = ?, age = ?, notes = ? WHERE id = ?",
			(name, email, age, notes, row_id),
		)
		return cur.rowcount > 0


def delete_entry(row_id: int) -> bool:
	"""Delete an entry by id; return True if deleted."""
	with get_connection() as conn:
		cur = conn.execute("DELETE FROM entries WHERE id = ?", (row_id,))
		return cur.rowcount > 0


# --------- Streamlit UI ---------


def main():
	st.set_page_config(page_title="SQLite CRUD with Streamlit", layout="centered")
	st.title("📚 Student Records - Streamlit + SQLite")

	# Initialize/create DB
	init_db()

	with st.expander("ℹ️ About"):
		st.markdown(
			"""
			This simple app uses an SQLite database (data.db) and provides full CRUD
			operations. Use the forms below to Create, Read, Update and Delete records.
			"""
		)

	# --- Create: Add new entry ---
	st.subheader("➕ Add New Entry")
	with st.form("add_form", clear_on_submit=True):
		name = st.text_input("Name")
		email = st.text_input("Email")
		age = st.number_input("Age", min_value=0, max_value=150, value=18)
		notes = st.text_area("Notes", value="")
		submitted = st.form_submit_button("Add Entry")
		if submitted:
			if not name or not email:
				st.error("Name and Email are required.")
			else:
				new_id = insert_entry(name.strip(), email.strip(), int(age), notes.strip())
				st.success(f"Entry added with id {new_id}")

	st.markdown("---")

	# --- Read: Display all records ---
	st.subheader("📋 Records")
	rows = view_all()
	if rows:
		df = pd.DataFrame(rows)
		# Convert sqlite Row objects to dicts for display
		df = df.astype(object)
		st.dataframe(df, use_container_width=True)
	else:
		st.info("No records found. Add some via the form above.")

	st.markdown("---")

	# Prepare options for update/delete selection
	rows_for_select = [(r["id"], r["name"], r["email"]) for r in rows]
	selection_map = {f"{r[0]} - {r[1]} ({r[2]})": r[0] for r in rows_for_select}

	# --- Update: Select and edit a record ---
	st.subheader("✏️ Update a Record")
	if rows:
		selected_label = st.selectbox("Select record to edit", options=list(selection_map.keys()))
		selected_id = selection_map[selected_label]

		record = get_entry(selected_id)
		if record:
			with st.form("update_form"):
				new_name = st.text_input("Name", value=record["name"])
				new_email = st.text_input("Email", value=record["email"])
				new_age = st.number_input("Age", min_value=0, max_value=150, value=record["age"] if record["age"] is not None else 18)
				new_notes = st.text_area("Notes", value=record["notes"] if record["notes"] else "")
				updated = st.form_submit_button("Save changes")
				if updated:
					ok = update_entry(selected_id, new_name.strip(), new_email.strip(), int(new_age), new_notes.strip())
					if ok:
						st.success("Record updated successfully.")
					else:
						st.error("Failed to update record. It may have been removed.")
		else:
			st.warning("Selected record not found.")
	else:
		st.info("No records to update.")

	st.markdown("---")

	# --- Delete: Pick and delete a record ---
	st.subheader("🗑️ Delete a Record")
	if rows:
		del_label = st.selectbox("Select record to delete", options=list(selection_map.keys()), key="del_select")
		del_id = selection_map[del_label]
		# require the user to check the confirmation box before allowing deletion
		confirm_delete = st.checkbox("Confirm delete (check box to enable delete)", key="del_confirm")
		if st.button("Delete Record"):
			if not confirm_delete:
				st.warning("Please check 'Confirm delete' before pressing Delete.")
			else:
				if delete_entry(del_id):
					st.success("Record deleted successfully")
				else:
					st.error("Failed to delete. It might already be removed.")
	else:
		st.info("No records to delete.")

	st.markdown("---")

	# Footer
	st.caption("Streamlit + SQLite CRUD demo - data.db stored alongside app file.")


if __name__ == "__main__":
	main()

