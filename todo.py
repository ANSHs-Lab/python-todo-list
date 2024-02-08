import tkinter as tk
from tkinter import ttk
from datetime import datetime
import sqlite3
import os

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List App")

        # Initialize SQLite database
        self.create_database()

        # Task entry variables
        self.task_description_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="Low")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.time_var = tk.StringVar(value="12:00")

        self.create_widgets()
        self.load_tasks_from_database()

    def create_widgets(self):
        entry_frame = ttk.Frame(self.root, padding="10")
        entry_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(entry_frame, text="Task Description:").grid(column=0, row=0, sticky=tk.W)
        task_entry = ttk.Entry(entry_frame, textvariable=self.task_description_var)
        task_entry.grid(column=1, row=0, sticky=(tk.W, tk.E))

        ttk.Label(entry_frame, text="Priority:").grid(column=0, row=1, sticky=tk.W)
        priority_combobox = ttk.Combobox(entry_frame, values=["Low", "Medium", "High"], textvariable=self.priority_var)
        priority_combobox.grid(column=1, row=1, sticky=(tk.W, tk.E))

        ttk.Label(entry_frame, text="Date:").grid(column=0, row=2, sticky=tk.W)
        date_entry = ttk.Entry(entry_frame, textvariable=self.date_var)
        date_entry.grid(column=1, row=2, sticky=(tk.W, tk.E))

        # Time entry
        ttk.Label(entry_frame, text="Time:").grid(column=0, row=3, sticky=tk.W)
        time_entry = ttk.Entry(entry_frame, textvariable=self.time_var)
        time_entry.grid(column=1, row=3, sticky=(tk.W, tk.E))

        add_button = ttk.Button(entry_frame, text="Add Task", command=self.add_task)
        add_button.grid(column=0, row=4, columnspan=2, pady=(10, 0))

        remove_button = ttk.Button(entry_frame, text="Remove Task", command=self.remove_task)
        remove_button.grid(column=0, row=5, columnspan=2, pady=(10, 0))

        mark_done_button = ttk.Button(entry_frame, text="Mark as Done", command=self.mark_task_as_done)
        mark_done_button.grid(column=0, row=6, columnspan=2, pady=(10, 0))

        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        columns = ("#", "Description", "Priority", "Date", "Time", "Status")
        self.treeview = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, anchor="center")

        self.treeview.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.treeview.yview)
        scrollbar.grid(column=1, row=0, sticky=(tk.N, tk.S))
        self.treeview.configure(yscrollcommand=scrollbar.set)

    def create_database(self):
        # Remove the existing 'todo.db' file
        if os.path.exists("todo.db"):
            os.remove("todo.db")

        # Create a SQLite database and a 'tasks' table
        with sqlite3.connect("todo.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    priority TEXT,
                    date TEXT,
                    time TEXT,
                    status TEXT DEFAULT 'Pending'
                )
            ''')

    def add_task(self):
        description = self.task_description_var.get()
        priority = self.priority_var.get()
        date_str = self.date_var.get()
        time_str = self.time_var.get()

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            date = ""

        try:
            time = datetime.strptime(time_str, "%H:%M").strftime("%H:%M")
        except ValueError:
            time = ""

        self.save_task_to_database(description, priority, date, time)
        self.load_tasks_from_database()

    def remove_task(self):
        selected_item = self.treeview.selection()
        if selected_item:
            task_id = int(self.treeview.item(selected_item)['values'][0])
            self.delete_task_from_database(task_id)
            self.load_tasks_from_database()

    def mark_task_as_done(self):
        selected_item = self.treeview.selection()
        if selected_item:
            task_id = int(self.treeview.item(selected_item)['values'][0])
            self.update_task_status(task_id, 'Done')
            self.load_tasks_from_database()

    def save_task_to_database(self, description, priority, date, time):
        # Save the task to the 'tasks' table in the SQLite database
        with sqlite3.connect("todo.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (description, priority, date, time)
                VALUES (?, ?, ?, ?)
            ''', (description, priority, date, time))
            conn.commit()

    def delete_task_from_database(self, task_id):
        # Delete the task with the specified ID from the 'tasks' table
        with sqlite3.connect("todo.db") as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()

    def update_task_status(self, task_id, status):
        # Update the task status in the 'tasks' table
        with sqlite3.connect("todo.db") as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
            conn.commit()

    def load_tasks_from_database(self):
        # Load tasks from the 'tasks' table and update the table
        with sqlite3.connect("todo.db") as conn:
            cursor = conn.cursor()

            # Check if the 'status' column exists in the 'tasks' table
            cursor.execute('PRAGMA table_info(tasks)')
            columns = cursor.fetchall()
            status_column_exists = any(column[1] == 'status' for column in columns)

            # If 'status' column does not exist, add it
            if not status_column_exists:
                cursor.execute('ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT "Pending"')
                conn.commit()

            cursor.execute(
                'SELECT id, description, priority, date, time, status FROM tasks ORDER BY priority DESC, date ASC, time ASC')
            tasks = cursor.fetchall()

            # Print tasks to the terminal
            print("\nTasks in the Database:")
            print("======================")
            for task in tasks:
                print(
                    f"ID: {task[0]}, Description: {task[1]}, Priority: {task[2]}, Date: {task[3]}, Time: {task[4]}, Status: {task[5]}")

            self.tasks = tasks
            self.update_task_list()

    def update_task_list(self):
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        for task in self.tasks:
            self.treeview.insert("", "end", values=task)

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()