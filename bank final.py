import tkinter as tk
from tkinter import messagebox
import mysql.connector
import hashlib


conn = mysql.connector.connect(host="localhost",user="root", password="seshaa3",database="new_bank_management")
cursor = conn.cursor()


def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def validate_registration(mobile, pincode, pin):
    if len(mobile) != 10 or not mobile.isdigit():
        messagebox.showerror("Error", "Invalid mobile number.")
        return False
    if len(pincode) != 6 or not pincode.isdigit():
        messagebox.showerror("Error", "Invalid pincode.")
        return False
    if len(pin) != 4 or not pin.isdigit():
        messagebox.showerror("Error", "PIN must be a 4-digit number.")
        return False
    return True


def register_user():
    def submit_registration():
        name = name_entry.get()
        mobile = mobile_entry.get()
        address = address_entry.get()
        pincode = pincode_entry.get()
        account_number = account_number_entry.get()
        pin = pin_entry.get()

        if not validate_registration(mobile, pincode, pin):
            return

        cursor.execute("INSERT INTO Users (name, mobile, address, pincode) VALUES (%s, %s, %s, %s)",
                       (name, mobile, address, pincode))
        conn.commit()

        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()[0]

        hashed_pin = hash_pin(pin)
        cursor.execute("INSERT INTO Accounts (user_id, account_number, password) VALUES (%s, %s, %s)",
                       (user_id, account_number, hashed_pin))
        conn.commit()

        messagebox.showinfo("Success", "Registration successful. You can now log in.")
        register_window.destroy()
        login_window.deiconify()

    register_window = tk.Toplevel()
    register_window.title("Register")
    register_window.geometry("400x500")

    name_entry = create_label_entry(register_window, "Full Name:", 0)
    mobile_entry = create_label_entry(register_window, "Mobile Number:", 1)
    address_entry = create_label_entry(register_window, "Address:", 2)
    pincode_entry = create_label_entry(register_window, "Pincode:", 3)
    account_number_entry = create_label_entry(register_window, "Account Number (for login):", 4)
    pin_entry = create_label_entry(register_window, "PIN (4 digits):", 5, show="*")

    submit_button = tk.Button(register_window, text="Submit", font=("Helvetica", 12), command=submit_registration)
    submit_button.grid(row=6, column=1, pady=10)

def create_label_entry(window, text, row, show=None):
    tk.Label(window, text=text, font=("Helvetica", 12)).grid(row=row, column=0, pady=10, padx=10, sticky="e")
    entry = tk.Entry(window, font=("Helvetica", 12), show=show)
    entry.grid(row=row, column=1, pady=10, padx=10)
    return entry


def login_user():
    username = account_number_entry.get()
    pin = pin_entry.get()
    hashed_pin = hash_pin(pin)

    cursor.execute("SELECT account_id, user_id FROM Accounts WHERE account_number = %s AND password = %s", (username, hashed_pin))
    user = cursor.fetchone()

    if user:
        messagebox.showinfo("Success", "Login successful!")
        global current_user_id
        current_user_id = user[1]
        account_id = user[0]

        cursor.execute("SELECT name FROM Users WHERE user_id = %s", (current_user_id,))
        user_name = cursor.fetchone()[0]

        login_window.withdraw()
        open_main_window(user_name, account_id)
    else:
        messagebox.showerror("Error", "Invalid account number or PIN.")


def open_main_window(user_name, account_id):
    main_window = tk.Tk()
    main_window.title("Banking Services")
    main_window.geometry("600x400")
    main_window.config(bg="#f0f0f0")

    tk.Label(main_window, text=f"Welcome {user_name}!", font=("Helvetica", 16, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=20)

    global amount_entry
    amount_entry = create_label_entry(main_window, "Amount:", 1)

    tk.Button(main_window, text="Deposit Money", font=("Helvetica", 12), bg="#2196F3", fg="white", command=lambda: deposit_money(account_id)).grid(row=2, column=0, pady=20)
    tk.Button(main_window, text="Withdraw Money", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=lambda: withdraw_money(account_id)).grid(row=2, column=1, pady=20)

    tk.Button(main_window, text="View Transaction History", font=("Helvetica", 12), command=lambda: view_history(account_id)).grid(row=3, column=0, pady=10, padx=20)
    tk.Button(main_window, text="Get Bill (Balance)", font=("Helvetica", 12), command=lambda: view_bill(account_id)).grid(row=3, column=1, pady=10, padx=20)

    tk.Button(main_window, text="Admin Portal", font=("Helvetica", 12), bg="#FF5722", fg="white", command=open_admin_login).grid(row=4, column=0, columnspan=2, pady=20)

    main_window.mainloop()

def deposit_money(account_id):
    amount = float(amount_entry.get())
    cursor.execute("SELECT balance FROM Accounts WHERE account_id = %s", (account_id,))
    current_balance = float(cursor.fetchone()[0])
    new_balance = current_balance + amount

    cursor.execute("UPDATE Accounts SET balance = %s WHERE account_id = %s", (new_balance, account_id))
    cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount) VALUES (%s, %s, %s)", (account_id, "Deposit", amount))
    conn.commit()

    messagebox.showinfo("Success", f"Deposited ₹{amount}. New balance: ₹{new_balance}")

def withdraw_money(account_id):
    amount = float(amount_entry.get())
    cursor.execute("SELECT balance FROM Accounts WHERE account_id = %s", (account_id,))
    current_balance = float(cursor.fetchone()[0])

    if current_balance >= amount:
        new_balance = current_balance - amount
        cursor.execute("UPDATE Accounts SET balance = %s WHERE account_id = %s", (new_balance, account_id))
        cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount) VALUES (%s, %s, %s)", (account_id, "Withdraw", amount))
        conn.commit()
        messagebox.showinfo("Success", f"Withdrew ₹{amount}. New balance: ₹{new_balance}")
    else:
        messagebox.showerror("Error", "Insufficient funds!")

def view_history(account_id):
    cursor.execute("SELECT * FROM Transactions WHERE account_id = %s", (account_id,))
    transactions = cursor.fetchall()
    transaction_history = "\n".join([f"Type: {t[2]}, Amount: ₹{t[3]}, Date: {t[4]}" for t in transactions])
    messagebox.showinfo("Transaction History", transaction_history)

def view_bill(account_id):
    cursor.execute("SELECT balance FROM Accounts WHERE account_id = %s", (account_id,))
    balance = cursor.fetchone()[0]
    messagebox.showinfo("Account Balance", f"Your current balance is ₹{balance}")


def open_admin_login():
    admin_login_window = tk.Toplevel()
    admin_login_window.title("Admin Login")
    admin_login_window.geometry("400x300")

    tk.Label(admin_login_window, text="Admin Username:", font=("Helvetica", 12)).pack(pady=10)
    admin_username_entry = tk.Entry(admin_login_window, font=("Helvetica", 12))
    admin_username_entry.pack(pady=10)

    tk.Label(admin_login_window, text="Admin Password:", font=("Helvetica", 12)).pack(pady=10)
    admin_password_entry = tk.Entry(admin_login_window, font=("Helvetica", 12), show="*")
    admin_password_entry.pack(pady=10)

    def admin_login():
        username = admin_username_entry.get()
        password = admin_password_entry.get()

        # Replace with your admin credentials
        if username == "admin" and password == "admin123":
            messagebox.showinfo("Success", "Admin login successful!")
            admin_login_window.destroy()
            open_admin_portal()
        else:
            messagebox.showerror("Error", "Invalid admin username or password.")

    login_button = tk.Button(admin_login_window, text="Login", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=admin_login)
    login_button.pack(pady=20)

# Admin Portal
def open_admin_portal():
    admin_window = tk.Toplevel()
    admin_window.title("Admin Portal")
    admin_window.geometry("600x400")
    admin_window.config(bg="#f0f0f0")

    tk.Label(admin_window, text="Admin Portal", font=("Helvetica", 16, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=20)

    tk.Button(admin_window, text="View Accounts", font=("Helvetica", 12), command=view_accounts).grid(row=1, column=0, pady=10, padx=20)
    tk.Button(admin_window, text="Add Account", font=("Helvetica", 12), command=add_account).grid(row=1, column=1, pady=10, padx=20)
    tk.Button(admin_window, text="Remove Account", font=("Helvetica", 12), command=remove_account).grid(row=2, column=0, pady=10, padx=20)
    tk.Button(admin_window, text="View Transaction History", font=("Helvetica", 12), command=view_all_history).grid(row=2, column=1, pady=10, padx=20)

def view_accounts():
    cursor.execute("SELECT Users.name, Accounts.account_number, Accounts.balance FROM Users JOIN Accounts ON Users.user_id = Accounts.user_id")
    accounts = cursor.fetchall()
    accounts_info = "\n".join([f"Name: {a[0]}, Account Number: {a[1]}, Balance: ₹{a[2]}" for a in accounts])
    messagebox.showinfo("Accounts Information", accounts_info)

def add_account():
    add_account_window = tk.Toplevel()
    add_account_window.title("Add Account")
    add_account_window.geometry("400x400")

    name_entry = create_label_entry(add_account_window, "Full Name:", 0)
    mobile_entry = create_label_entry(add_account_window, "Mobile Number:", 1)
    address_entry = create_label_entry(add_account_window, "Address:", 2)
    pincode_entry = create_label_entry(add_account_window, "Pincode:", 3)
    account_number_entry = create_label_entry(add_account_window, "Account Number (for login):", 4)
    pin_entry = create_label_entry(add_account_window, "PIN (4 digits):", 5, show="*")

    def submit_add_account():
        name = name_entry.get()
        mobile = mobile_entry.get()
        address = address_entry.get()
        pincode = pincode_entry.get()
        account_number = account_number_entry.get()
        pin = pin_entry.get()

        if not validate_registration(mobile, pincode, pin):
            return

        cursor.execute("INSERT INTO Users (name, mobile, address, pincode) VALUES (%s, %s, %s, %s)",
                       (name, mobile, address, pincode))
        conn.commit()

        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()[0]

        hashed_pin = hash_pin(pin)
        cursor.execute("INSERT INTO Accounts (user_id, account_number, password) VALUES (%s, %s, %s)",
                       (user_id, account_number, hashed_pin))
        conn.commit()

        messagebox.showinfo("Success", "Account added successfully.")
        add_account_window.destroy()

    submit_button = tk.Button(add_account_window, text="Submit", font=("Helvetica", 12), command=submit_add_account)
    submit_button.grid(row=6, column=1, pady=10)

def remove_account():
    remove_account_window = tk.Toplevel()
    remove_account_window.title("Remove Account")
    remove_account_window.geometry("400x200")

    account_number_entry = create_label_entry(remove_account_window, "Account Number:", 0)

    def submit_remove_account():
        account_number = account_number_entry.get()

        cursor.execute("SELECT account_id FROM Accounts WHERE account_number = %s", (account_number,))
        account = cursor.fetchone()

        if account:
            account_id = account[0]
            cursor.execute("DELETE FROM Transactions WHERE account_id = %s", (account_id,))
            cursor.execute("DELETE FROM Accounts WHERE account_id = %s", (account_id,))
            cursor.execute("DELETE FROM Users WHERE user_id = (SELECT user_id FROM Accounts WHERE account_id = %s)", (account_id,))
            conn.commit()
            messagebox.showinfo("Success", "Account removed successfully.")
            remove_account_window.destroy()
        else:
            messagebox.showerror("Error", "Account not found.")

    submit_button = tk.Button(remove_account_window, text="Submit", font=("Helvetica", 12), command=submit_remove_account)
    submit_button.grid(row=1, column=1, pady=10)

def view_all_history():
    cursor.execute("SELECT * FROM Transactions")
    transactions = cursor.fetchall()
    transaction_history = "\n".join([f"Account ID: {t[1]}, Type: {t[2]}, Amount: ₹{t[3]}, Date: {t[4]}" for t in transactions])
    messagebox.showinfo("All Transaction History", transaction_history)

# Login Window
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("400x400")

tk.Label(login_window, text="Account Number:", font=("Helvetica", 12)).pack(pady=10)
account_number_entry = tk.Entry(login_window, font=("Helvetica", 12))
account_number_entry.pack(pady=10)

tk.Label(login_window, text="PIN:", font=("Helvetica", 12)).pack(pady=10)
pin_entry = tk.Entry(login_window, font=("Helvetica", 12), show="*")
pin_entry.pack(pady=10)

login_button = tk.Button(login_window, text="Login", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=login_user)
login_button.pack(pady=20)

register_button = tk.Button(login_window, text="Register", font=("Helvetica", 12), bg="#2196F3", fg="white", command=register_user)
register_button.pack(pady=10)

admin_button = tk.Button(login_window, text="Admin Login", font=("Helvetica", 12), bg="#FF5722", fg="white", command=open_admin_login)
admin_button.pack(pady=10)

login_window.mainloop()