import streamlit as st
import sqlite3
from datetime import date, datetime
import calendar
import pandas as pd

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Money Tracker",
    page_icon="💰",
    layout="wide"
)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date TEXT NOT NULL,
    name TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    payment_method TEXT,
    notes TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS monthly_finances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    income REAL DEFAULT 0,
    budget REAL DEFAULT 0,
    UNIQUE(year, month)
)
""")

conn.commit()

# =========================================================
# OPTIONS
# =========================================================

categories = [
    "Rent",
    "EMI",
    "Groceries",
    "Shopping",
    "Dining",
    "Utilities",
    "Gas / Fuel",
    "Parking",
    "Trips / Travel",
    "Insurance",
    "Car",
    "Transport",
    "Subscriptions",
    "Medical",
    "Entertainment",
    "Personal Care",
    "Bills",
    "Other"
]

payment_methods = [
    "Credit Card",
    "Debit Card",
    "Bank Account",
    "Cash",
    "Other"
]

month_names = list(calendar.month_name)[1:]
month_short = list(calendar.month_abbr)[1:]

# =========================================================
# SESSION STATE
# =========================================================

if "selected_year" not in st.session_state:
    st.session_state.selected_year = date.today().year

if "selected_month" not in st.session_state:
    st.session_state.selected_month = date.today().month

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "reset_expense_form" not in st.session_state:
    st.session_state.reset_expense_form = False

year = st.session_state.selected_year
month = st.session_state.selected_month

# =========================================================
# FORM KEYS
# =========================================================

def expense_keys(y, m):
    return {
        "date": f"expense_date_{y}_{m}",
        "name": f"expense_name_{y}_{m}",
        "amount": f"expense_amount_{y}_{m}",
        "category": f"expense_category_{y}_{m}",
        "repeat": f"repeat_expense_{y}_{m}",
        "payment": f"expense_payment_{y}_{m}",
        "notes": f"expense_notes_{y}_{m}",
        "until_month": f"repeat_until_month_{y}_{m}",
        "until_year": f"repeat_until_year_{y}_{m}"
    }


def default_expense_date(y, m):
    if date.today().year == y and date.today().month == m:
        return date.today()
    return date(y, m, 1)


def reset_expense_widgets(y, m):
    keys = expense_keys(y, m)

    st.session_state[keys["date"]] = default_expense_date(y, m)
    st.session_state[keys["name"]] = ""
    st.session_state[keys["amount"]] = 0.0
    st.session_state[keys["category"]] = categories[0]
    st.session_state[keys["repeat"]] = False
    st.session_state[keys["payment"]] = payment_methods[0]
    st.session_state[keys["notes"]] = ""

    # Remove conditional widgets if they already exist.
    st.session_state.pop(keys["until_month"], None)
    st.session_state.pop(keys["until_year"], None)


# Reset BEFORE widgets are created.
if st.session_state.reset_expense_form:
    reset_expense_widgets(year, month)
    st.session_state.reset_expense_form = False

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.block-container {
    max-width: 1250px;
    padding-top: 4rem;
    padding-bottom: 3rem;
}

div[data-testid="stMetric"] {
    border: 1px solid #e5e7eb;
    padding: 16px;
    border-radius: 12px;
}

div[data-testid="stMetricValue"] {
    font-size: 26px;
    font-weight: 700;
}

div[data-testid="stForm"] {
    border-radius: 14px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# YEAR SELECTOR
# =========================================================

title_col, year_col = st.columns([4, 1])

with title_col:
    st.caption("Financial year")
    st.title(f"💰 {year} Money Tracker")

with year_col:
    year_options = list(range(2024, 2036))

    selected_year = st.selectbox(
        "Select Year",
        year_options,
        index=year_options.index(year)
        if year in year_options else 0
    )

if selected_year != year:
    st.session_state.selected_year = selected_year
    st.session_state.selected_month = 1
    st.session_state.edit_id = None
    st.rerun()

year = st.session_state.selected_year

# =========================================================
# MONTH BUTTONS
# =========================================================

month_columns = st.columns(12)

for i in range(12):
    month_number = i + 1

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE substr(expense_date, 1, 4) = ?
        AND substr(expense_date, 6, 2) = ?
    """, (
        str(year),
        f"{month_number:02d}"
    ))

    month_total = float(cursor.fetchone()[0])

    with month_columns[i]:
        if st.button(
            f"{month_short[i]} ${month_total:,.0f}",
            key=f"month_{year}_{month_number}",
            use_container_width=True,
            type="primary"
            if month == month_number
            else "secondary"
        ):
            st.session_state.selected_month = month_number
            st.session_state.edit_id = None
            st.rerun()

month = st.session_state.selected_month

# =========================================================
# MONTHLY FINANCES
# =========================================================

cursor.execute("""
SELECT income, budget
FROM monthly_finances
WHERE year = ? AND month = ?
""", (year, month))

finance = cursor.fetchone()

if finance:
    saved_income = float(finance[0])
    saved_budget = float(finance[1])
else:
    saved_income = 0.0
    saved_budget = 0.0

with st.container(border=True):

    st.subheader(
        f"💵 {month_names[month - 1]} Money Settings"
    )

    income_col, budget_col, save_col = st.columns([2, 2, 1])

    with income_col:
        monthly_income = st.number_input(
            "Monthly Income ($)",
            min_value=0.0,
            value=saved_income,
            step=100.0,
            key=f"income_{year}_{month}"
        )

    with budget_col:
        monthly_budget = st.number_input(
            "Spending Budget ($)",
            min_value=0.0,
            value=saved_budget,
            step=100.0,
            key=f"budget_{year}_{month}"
        )

    with save_col:
        st.write("")
        st.write("")

        if st.button(
            "💾 Save",
            use_container_width=True,
            key=f"save_finance_{year}_{month}"
        ):

            cursor.execute("""
                INSERT INTO monthly_finances
                    (year, month, income, budget)
                VALUES (?, ?, ?, ?)

                ON CONFLICT(year, month)
                DO UPDATE SET
                    income = excluded.income,
                    budget = excluded.budget
            """, (
                year,
                month,
                monthly_income,
                monthly_budget
            ))

            conn.commit()
            st.success("Income and budget saved!")
            st.rerun()

# =========================================================
# MONTH TOTAL
# =========================================================

cursor.execute("""
SELECT COALESCE(SUM(amount), 0)
FROM expenses
WHERE substr(expense_date, 1, 4) = ?
AND substr(expense_date, 6, 2) = ?
""", (
    str(year),
    f"{month:02d}"
))

month_spent = float(cursor.fetchone()[0])

actual_savings = monthly_income - month_spent
budget_left = monthly_budget - month_spent

# =========================================================
# YEAR TOTALS
# =========================================================

cursor.execute("""
SELECT COALESCE(SUM(income), 0)
FROM monthly_finances
WHERE year = ?
""", (year,))

year_income = float(cursor.fetchone()[0])

cursor.execute("""
SELECT COALESCE(SUM(amount), 0)
FROM expenses
WHERE substr(expense_date, 1, 4) = ?
""", (str(year),))

year_expenses = float(cursor.fetchone()[0])

year_savings = year_income - year_expenses

cursor.execute("""
SELECT category, SUM(amount)
FROM expenses
WHERE substr(expense_date, 1, 4) = ?
GROUP BY category
""", (str(year),))

year_category_data = dict(cursor.fetchall())

possible_savings = (
    year_category_data.get("Shopping", 0) * 0.20
    + year_category_data.get("Dining", 0) * 0.25
    + year_category_data.get("Groceries", 0) * 0.10
    + year_category_data.get("Subscriptions", 0) * 0.20
)

# =========================================================
# YEAR SUMMARY
# =========================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Year Income", f"${year_income:,.2f}")
c2.metric("Year Expenses", f"${year_expenses:,.2f}")
c3.metric("Year Savings", f"${year_savings:,.2f}")
c4.metric(
    "Possible Extra Savings",
    f"${possible_savings:,.2f}"
)

# =========================================================
# MONTH CATEGORY TOTALS
# =========================================================

cursor.execute("""
SELECT category, SUM(amount)
FROM expenses
WHERE substr(expense_date, 1, 4) = ?
AND substr(expense_date, 6, 2) = ?
GROUP BY category
ORDER BY SUM(amount) DESC
""", (
    str(year),
    f"{month:02d}"
))

category_data = cursor.fetchall()
category_totals = dict(category_data)

# =========================================================
# ADD EXPENSE + SUMMARY COLUMNS
# =========================================================

left, right = st.columns(
    [1, 1.1],
    gap="large"
)

# =========================================================
# ADD EXPENSE
# =========================================================

with left:

    with st.container(border=True):

        st.subheader(
            f"➕ Add Expense to {month_names[month - 1]}"
        )

        keys = expense_keys(year, month)

        with st.form(
            f"add_expense_form_{year}_{month}",
            clear_on_submit=False
        ):

            expense_date = st.date_input(
                "Date money was spent/deducted",
                value=default_expense_date(year, month),
                key=keys["date"]
            )

            expense_name = st.text_input(
                "Expense Name",
                placeholder="Example: Costco groceries",
                key=keys["name"]
            )

            amount_col, category_col = st.columns(2)

            with amount_col:
                amount = st.number_input(
                    "Amount ($)",
                    min_value=0.0,
                    step=1.0,
                    key=keys["amount"]
                )

            with category_col:
                category = st.selectbox(
                    "Category",
                    categories,
                    key=keys["category"]
                )

            repeat_monthly = st.checkbox(
                "🔁 Repeat this expense every month",
                key=keys["repeat"]
            )

            repeat_until_month = None
            repeat_until_year = None

            if repeat_monthly:

                st.caption(
                    "This expense will be added to each month "
                    "through the month and year you choose."
                )

                repeat_col1, repeat_col2 = st.columns(2)

                with repeat_col1:
                    repeat_until_month = st.selectbox(
                        "Repeat Until Month",
                        month_names,
                        index=11,
                        key=keys["until_month"]
                    )

                with repeat_col2:
                    repeat_year_options = list(
                        range(year, year + 11)
                    )

                    repeat_until_year = st.selectbox(
                        "Repeat Until Year",
                        repeat_year_options,
                        index=0,
                        key=keys["until_year"]
                    )

            payment = st.selectbox(
                "Payment Method",
                payment_methods,
                key=keys["payment"]
            )

            notes = st.text_area(
                "Notes (optional)",
                placeholder="Example: Monthly car insurance",
                key=keys["notes"]
            )

            save_expense = st.form_submit_button(
                "Add Expense",
                use_container_width=True
            )

            # =================================================
            # VALIDATION
            # =================================================

            if save_expense:

                error_message = None

                if not expense_name.strip():

                    error_message = (
                        "Please enter an expense name."
                    )

                elif amount <= 0:

                    error_message = (
                        "Amount must be greater than $0."
                    )

                elif (
                    expense_date.year != year
                    or expense_date.month != month
                ):

                    error_message = (
                        f"Please select a date in "
                        f"{month_names[month - 1]} {year}."
                    )

                # ---------------------------------------------
                # SHOW ERROR - DO NOT CLEAR FORM
                # ---------------------------------------------

                if error_message:

                    st.error(error_message)

                # ---------------------------------------------
                # SAVE
                # ---------------------------------------------

                else:

                    # ONE-TIME EXPENSE
                    if not repeat_monthly:

                        cursor.execute("""
                            INSERT INTO expenses (
                                expense_date,
                                name,
                                amount,
                                category,
                                payment_method,
                                notes
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            str(expense_date),
                            expense_name.strip(),
                            amount,
                            category,
                            payment,
                            notes
                        ))

                        conn.commit()

                        # Tell next run to clear form
                        st.session_state.reset_expense_form = True

                        st.rerun()

                    # RECURRING EXPENSE
                    else:

                        end_month_number = (
                            month_names.index(
                                repeat_until_month
                            ) + 1
                        )

                        start_value = year * 12 + month

                        end_value = (
                            repeat_until_year * 12
                            + end_month_number
                        )

                        if end_value < start_value:

                            st.error(
                                "Repeat-until date cannot be "
                                "before the expense month."
                            )

                        else:

                            current_year = year
                            current_month = month
                            number_added = 0

                            while (
                                current_year < repeat_until_year
                                or (
                                    current_year
                                    == repeat_until_year
                                    and current_month
                                    <= end_month_number
                                )
                            ):

                                requested_day = expense_date.day

                                last_day = calendar.monthrange(
                                    current_year,
                                    current_month
                                )[1]

                                safe_day = min(
                                    requested_day,
                                    last_day
                                )

                                repeated_date = date(
                                    current_year,
                                    current_month,
                                    safe_day
                                )

                                cursor.execute("""
                                    INSERT INTO expenses (
                                        expense_date,
                                        name,
                                        amount,
                                        category,
                                        payment_method,
                                        notes
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    str(repeated_date),
                                    expense_name.strip(),
                                    amount,
                                    category,
                                    payment,
                                    notes
                                ))

                                number_added += 1

                                if current_month == 12:
                                    current_month = 1
                                    current_year += 1
                                else:
                                    current_month += 1

                            conn.commit()

                            st.session_state.reset_expense_form = True

                            st.rerun()

# =========================================================
# MONTH SUMMARY
# =========================================================

with right:

    with st.container(border=True):

        st.subheader(
            f"📊 {month_names[month - 1]} Summary"
        )

        s1, s2, s3 = st.columns(3)

        s1.metric(
            "Income",
            f"${monthly_income:,.2f}"
        )

        s2.metric(
            "Spent",
            f"${month_spent:,.2f}"
        )

        s3.metric(
            "Actual Savings",
            f"${actual_savings:,.2f}"
        )

        b1, b2 = st.columns(2)

        b1.metric(
            "Spending Budget",
            f"${monthly_budget:,.2f}"
        )

        b2.metric(
            "Budget Left",
            f"${budget_left:,.2f}"
        )

        if monthly_budget > 0:

            percentage = month_spent / monthly_budget

            st.write(
                f"Budget used: "
                f"**{percentage * 100:.1f}%**"
            )

            st.progress(
                min(max(percentage, 0.0), 1.0)
            )

        st.write("")

        if category_data:

            st.markdown(
                "**Spending by category**"
            )

            max_category = max(
                value
                for _, value in category_data
            )

            for category_name, category_amount in category_data:

                x1, x2 = st.columns([3, 1])

                x1.write(category_name)

                x2.markdown(
                    f"**${category_amount:,.2f}**"
                )

                if max_category > 0:
                    st.progress(
                        category_amount / max_category
                    )

        else:

            st.info(
                "No expenses entered for this month."
            )

# =========================================================
# TRANSACTIONS
# =========================================================

st.write("")

with st.container(border=True):

    st.subheader(
        f"🧾 {month_names[month - 1]} "
        f"{year} Transactions"
    )

    cursor.execute("""
    SELECT
        id,
        expense_date,
        name,
        amount,
        category,
        payment_method,
        notes
    FROM expenses
    WHERE substr(expense_date, 1, 4) = ?
    AND substr(expense_date, 6, 2) = ?
    ORDER BY expense_date DESC, id DESC
    """, (
        str(year),
        f"{month:02d}"
    ))

    transactions = cursor.fetchall()

    if not transactions:

        st.info(
            "No transactions for this month."
        )

    for transaction in transactions:

        (
            expense_id,
            saved_date,
            saved_name,
            saved_amount,
            saved_category,
            saved_payment,
            saved_notes
        ) = transaction

        saved_notes = saved_notes or ""

        # =================================================
        # EDIT MODE
        # =================================================

        if st.session_state.edit_id == expense_id:

            with st.form(
                f"edit_{expense_id}"
            ):

                st.markdown("### ✏️ Edit Expense")

                old_date = datetime.strptime(
                    saved_date,
                    "%Y-%m-%d"
                ).date()

                new_date = st.date_input(
                    "Date",
                    old_date,
                    key=f"edit_date_{expense_id}"
                )

                new_name = st.text_input(
                    "Expense Name",
                    saved_name,
                    key=f"edit_name_{expense_id}"
                )

                e1, e2 = st.columns(2)

                with e1:

                    new_amount = st.number_input(
                        "Amount ($)",
                        min_value=0.01,
                        value=float(saved_amount),
                        key=f"edit_amount_{expense_id}"
                    )

                with e2:

                    cat_index = (
                        categories.index(saved_category)
                        if saved_category in categories
                        else 0
                    )

                    new_category = st.selectbox(
                        "Category",
                        categories,
                        index=cat_index,
                        key=f"edit_category_{expense_id}"
                    )

                pay_index = (
                    payment_methods.index(saved_payment)
                    if saved_payment in payment_methods
                    else 0
                )

                new_payment = st.selectbox(
                    "Payment Method",
                    payment_methods,
                    index=pay_index,
                    key=f"edit_payment_{expense_id}"
                )

                new_notes = st.text_area(
                    "Notes",
                    saved_notes,
                    key=f"edit_notes_{expense_id}"
                )

                save_col, cancel_col = st.columns(2)

                save_changes = save_col.form_submit_button(
                    "💾 Save Changes",
                    use_container_width=True
                )

                cancel = cancel_col.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )

                if save_changes:

                    if not new_name.strip():

                        st.error(
                            "Expense name cannot be empty."
                        )

                    elif new_amount <= 0:

                        st.error(
                            "Amount must be greater than $0."
                        )

                    else:

                        cursor.execute("""
                        UPDATE expenses
                        SET
                            expense_date = ?,
                            name = ?,
                            amount = ?,
                            category = ?,
                            payment_method = ?,
                            notes = ?
                        WHERE id = ?
                        """, (
                            str(new_date),
                            new_name.strip(),
                            new_amount,
                            new_category,
                            new_payment,
                            new_notes,
                            expense_id
                        ))

                        conn.commit()

                        st.session_state.edit_id = None

                        st.rerun()

                if cancel:

                    st.session_state.edit_id = None

                    st.rerun()

        # =================================================
        # NORMAL TRANSACTION
        # =================================================

        else:

            r1, r2, r3, r4 = st.columns(
                [4, 1.3, 1, 1.2]
            )

            with r1:

                st.markdown(
                    f"**{saved_name}**"
                )

                pretty_date = datetime.strptime(
                    saved_date,
                    "%Y-%m-%d"
                ).strftime("%b %d, %Y")

                st.caption(
                    f"{saved_category} • "
                    f"{pretty_date} • "
                    f"{saved_payment}"
                )

                if saved_notes:
                    st.caption(
                        f"📝 {saved_notes}"
                    )

            with r2:

                st.markdown(
                    f"### ${saved_amount:,.2f}"
                )

            with r3:

                if st.button(
                    "Edit",
                    key=f"edit_button_{expense_id}",
                    use_container_width=True
                ):

                    st.session_state.edit_id = expense_id

                    st.rerun()

            with r4:

                if st.button(
                    "Remove",
                    key=f"remove_button_{expense_id}",
                    use_container_width=True
                ):

                    cursor.execute("""
                    DELETE FROM expenses
                    WHERE id = ?
                    """, (expense_id,))

                    conn.commit()

                    st.rerun()

            st.divider()

# =========================================================
# SAVINGS COACH
# =========================================================

with st.container(border=True):

    st.subheader("💡 Savings Coach")

    suggestions = []

    shopping = category_totals.get("Shopping", 0)
    dining = category_totals.get("Dining", 0)
    groceries = category_totals.get("Groceries", 0)
    parking = category_totals.get("Parking", 0)
    travel = category_totals.get("Trips / Travel", 0)
    subscriptions = category_totals.get(
        "Subscriptions",
        0
    )

    if shopping >= 100:

        suggestions.append(
            (
                "🛍️ Shopping",
                f"You spent ${shopping:,.2f}. "
                f"Reducing shopping by 20% could save "
                f"about ${shopping * 0.20:,.2f}."
            )
        )

    if dining >= 80:

        suggestions.append(
            (
                "🍽️ Dining",
                f"You spent ${dining:,.2f}. "
                f"Reducing dining by 25% could save "
                f"about ${dining * 0.25:,.2f}."
            )
        )

    if groceries >= 200:

        suggestions.append(
            (
                "🛒 Groceries",
                f"You spent ${groceries:,.2f}. "
                f"A 10% reduction could save about "
                f"${groceries * 0.10:,.2f}."
            )
        )

    if parking >= 75:

        suggestions.append(
            (
                "🅿️ Parking",
                f"You spent ${parking:,.2f} on parking. "
                "Look for cheaper parking options."
            )
        )

    if travel >= 250:

        suggestions.append(
            (
                "✈️ Trips / Travel",
                f"You spent ${travel:,.2f}. "
                "Consider setting a separate travel limit."
            )
        )

    if subscriptions >= 50:

        suggestions.append(
            (
                "📺 Subscriptions",
                f"You spent ${subscriptions:,.2f}. "
                "Review subscriptions you rarely use."
            )
        )

    if monthly_budget > 0 and budget_left < 0:

        suggestions.insert(
            0,
            (
                "⚠️ Over Budget",
                f"You are ${abs(budget_left):,.2f} "
                "over your monthly spending budget."
            )
        )

    if suggestions:

        coach_columns = st.columns(
            min(3, len(suggestions))
        )

        for index, (title, message) in enumerate(suggestions):

            with coach_columns[
                index % len(coach_columns)
            ]:

                with st.container(border=True):

                    st.markdown(
                        f"**{title}**"
                    )

                    st.write(message)

    else:

        st.success(
            "Your spending currently looks controlled. "
            "Add more expenses and the coach will "
            "identify possible savings."
        )

# =========================================================
# YEAR MONTH-BY-MONTH
# =========================================================

st.write("")

st.subheader(
    f"📅 {year} Month-by-Month"
)

monthly_summary = []

for m in range(1, 13):

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE substr(expense_date, 1, 4) = ?
        AND substr(expense_date, 6, 2) = ?
    """, (
        str(year),
        f"{m:02d}"
    ))

    spent = float(cursor.fetchone()[0])

    cursor.execute("""
        SELECT income, budget
        FROM monthly_finances
        WHERE year = ? AND month = ?
    """, (
        year,
        m
    ))

    monthly_finance = cursor.fetchone()

    if monthly_finance:
        income = float(monthly_finance[0])
        budget = float(monthly_finance[1])
    else:
        income = 0.0
        budget = 0.0

    saved = income - spent

    monthly_summary.append({
        "Month": month_names[m - 1],
        "Income": income,
        "Budget": budget,
        "Spent": spent,
        "Saved": saved
    })

summary_df = pd.DataFrame(
    monthly_summary
)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Income": st.column_config.NumberColumn(
            "Income",
            format="$%.2f"
        ),
        "Budget": st.column_config.NumberColumn(
            "Budget",
            format="$%.2f"
        ),
        "Spent": st.column_config.NumberColumn(
            "Spent",
            format="$%.2f"
        ),
        "Saved": st.column_config.NumberColumn(
            "Saved",
            format="$%.2f"
        )
    }
)

# =========================================================
# YEAR CHART
# =========================================================

st.subheader(
    f"📈 {year} Spending by Month"
)

chart_df = summary_df[
    ["Month", "Spent"]
].copy()

chart_df["Month"] = pd.Categorical(
    chart_df["Month"],
    categories=month_names,
    ordered=True
)

chart_df = (
    chart_df
    .sort_values("Month")
    .set_index("Month")
)

st.bar_chart(chart_df)

conn.commit()