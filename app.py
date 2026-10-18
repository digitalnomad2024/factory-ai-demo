import streamlit as st
from datetime import date, datetime, timedelta
from pathlib import Path
import json


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Factory AI - Factory Control",
    page_icon="🏭",
    layout="wide"
)


# =========================================================
# 7-DAY DEMO TRIAL
# =========================================================

TRIAL_FILE = Path(__file__).with_name("factory_trial.json")
TRIAL_DAYS = 7


def load_trial_start():
    if not TRIAL_FILE.exists():
        today = date.today().isoformat()
        TRIAL_FILE.write_text(
            json.dumps({"start_date": today}),
            encoding="utf-8"
        )
        return date.today()

    try:
        data = json.loads(TRIAL_FILE.read_text(encoding="utf-8"))
        return date.fromisoformat(data["start_date"])
    except Exception:
        return date.today()


trial_start = load_trial_start()
trial_end = trial_start + timedelta(days=TRIAL_DAYS)

if date.today() > trial_end:
    st.error("Your 7-day Factory AI demo has expired.")
    st.stop()


days_left = max(0, (trial_end - date.today()).days)


# =========================================================
# SESSION DATA
# =========================================================

DEFAULTS = {
    "orders": [],
    "raw_receipts": [],
    "material_consumption": [],
    "production_jobs": [],
    "dispatch_records": [],
    "store_verifications": [],
    "order_closures": [],
    "labour_entries": [],
    "factory_lines": [
        "Line 1",
        "Line 2",
        "Line 3",
        "Cutting Line",
        "Rolling Line",
        "Finishing Line",
    ],
    "factory_teams": [
        "Team A",
        "Team B",
        "Team C",
        "Shift 1",
        "Shift 2",
        "Shift 3",
    ],
    "factory_products": [
        "Flat Bar",
        "Round Bar",
        "Angle",
        "Channel",
        "Square Bar",
    ],
    "next_order": 1001,
}


for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, list) else value


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def product_key(product, size):
    return f"{product} | {size}"


def order_balance(order):
    dispatched = sum(
        float(x.get("quantity", 0))
        for x in st.session_state.dispatch_records
        if x.get("order_id") == order["id"]
    )

    return max(
        0,
        float(order["quantity"]) - dispatched
    )


def order_status(order):
    balance = order_balance(order)

    if balance <= 0:
        return "COMPLETED"

    job = get_job(order["id"])

    if not job:
        return "PENDING PRODUCTION"

    if job.get("status") == "READY FOR STORE VERIFICATION":
        return "STORE VERIFICATION"

    if job.get("status") == "IN PRODUCTION":
        return "IN PRODUCTION"

    return "PENDING"


def get_job(order_id):
    jobs = [
        j for j in st.session_state.production_jobs
        if j.get("order_id") == order_id
    ]

    if not jobs:
        return None

    return jobs[-1]


def raw_materials():
    materials = set()

    for item in st.session_state.raw_receipts:
        materials.add(item["material"])

    return sorted(materials)


def raw_received(material):
    return sum(
        float(x.get("quantity", 0))
        for x in st.session_state.raw_receipts
        if x.get("material") == material
    )


def raw_consumed(material):
    return sum(
        float(x.get("raw_input", 0))
        for x in st.session_state.material_consumption
        if x.get("material") == material
    )


def raw_available(material):
    return max(
        0,
        raw_received(material) - raw_consumed(material)
    )


def verified_finished_stock(product, size):
    key = product_key(product, size)

    return sum(
        float(x.get("quantity", 0))
        for x in st.session_state.store_verifications
        if x.get("product_key") == key
    )


def dispatched_for_product(product, size):
    key = product_key(product, size)

    return sum(
        float(x.get("quantity", 0))
        for x in st.session_state.dispatch_records
        if x.get("product_key") == key
    )


def available_finished_stock(product, size):
    return max(
        0,
        verified_finished_stock(product, size)
        - dispatched_for_product(product, size)
    )


def production_left(order):
    job = get_job(order["id"])

    if not job:
        return order_balance(order)

    return max(
        0,
        float(order["quantity"]) -
        float(job.get("finished", 0)) -
        sum(
            float(x.get("quantity", 0))
            for x in st.session_state.dispatch_records
            if x.get("order_id") == order["id"]
        )
    )


def total_labour_cost():
    return sum(
        float(x.get("cost", 0))
        for x in st.session_state.labour_entries
    )


def total_material_cost():
    return sum(
        float(x.get("material_cost", 0))
        for x in st.session_state.material_consumption
    )


def total_wastage():
    return sum(
        float(x.get("wastage", 0))
        for x in st.session_state.material_consumption
    )


def total_damage():
    return sum(
        float(x.get("damage", 0))
        for x in st.session_state.material_consumption
    )


def production_jobs_waiting_store():
    return [
        j for j in st.session_state.production_jobs
        if j.get("status") == "READY FOR STORE VERIFICATION"
    ]


def dispatch_queue():
    result = []

    for order in st.session_state.orders:
        ready = available_finished_stock(
            order["product"],
            order["size"]
        )

        balance = order_balance(order)

        if ready > 0 and balance > 0:
            result.append({
                "order": order,
                "ready": min(ready, balance)
            })

    return result


def clear_all_demo_data():
    st.session_state.orders = []
    st.session_state.raw_receipts = []
    st.session_state.material_consumption = []
    st.session_state.production_jobs = []
    st.session_state.dispatch_records = []
    st.session_state.store_verifications = []
    st.session_state.order_closures = []
    st.session_state.labour_entries = []
    st.session_state.next_order = 1001


# =========================================================
# HEADER
# =========================================================

st.title("🏭 Factory AI")
st.caption(
    "Factory Control System • Orders • Production • Material • Labour • Dispatch • AI Report"
)

st.info(
    f"Demo Mode | {days_left} day(s) remaining | "
    "No sample factory data is loaded."
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🏭 Factory AI")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Owner Dashboard",
        "Factory Setup",
        "New Customer Order",
        "Material Receiving",
        "Raw Material Stock",
        "Production Planning",
        "Production Line",
        "Store Verification",
        "Loading & Dispatch",
        "Order Balance & Closure",
        "Daily Factory Report",
        "Bills & Documents",
    ]
)

st.sidebar.divider()

if st.sidebar.button("🗑️ Reset Demo Data"):
    clear_all_demo_data()
    st.success("All factory demo data has been cleared.")
    st.rerun()


# =========================================================
# OWNER DASHBOARD
# =========================================================

if menu == "Owner Dashboard":

    st.header("📊 Owner Dashboard")

    active_jobs = [
        j for j in st.session_state.production_jobs
        if j.get("status") == "IN PRODUCTION"
    ]

    produced = sum(
        float(j.get("finished", 0))
        for j in st.session_state.production_jobs
    )

    total_balance = sum(
        order_balance(o)
        for o in st.session_state.orders
    )

    raw_stock = sum(
        raw_available(m)
        for m in raw_materials()
    )

    store_pending = len(production_jobs_waiting_store())

    loading_ready = sum(
        x["ready"]
        for x in dispatch_queue()
    )

    dispatched = sum(
        float(x.get("quantity", 0))
        for x in st.session_state.dispatch_records
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Customer Orders",
        len(st.session_state.orders)
    )

    c2.metric(
        "Production Lines Active",
        len(active_jobs)
    )

    c3.metric(
        "Produced KG",
        f"{produced:,.2f}"
    )

    c4.metric(
        "Order Balance KG",
        f"{total_balance:,.2f}"
    )

    c5, c6, c7, c8 = st.columns(4)

    c5.metric(
        "Raw Material Stock",
        f"{raw_stock:,.2f} KG"
    )

    c6.metric(
        "Store Pending",
        len(production_jobs_waiting_store())
    )

    c7.metric(
        "Loading Ready",
        f"{loading_ready:,.2f} KG"
    )

    c8.metric(
        "Dispatched",
        f"{dispatched:,.2f} KG"
    )

    st.divider()

    st.subheader("📋 Current Orders")

    if not st.session_state.orders:
        st.info(
            "No customer orders yet. Go to 'New Customer Order' to create the first order."
        )
    else:

        rows = []

        for order in st.session_state.orders:

            job = get_job(order["id"])

            rows.append({
                "Order": order["id"],
                "Customer": order["customer"],
                "Product": order["product"],
                "Size": order["size"],
                "Order KG": order["quantity"],
                "Balance KG": order_balance(order),
                "Production Line": job.get("line", "-") if job else "-",
                "Team": job.get("team", "-") if job else "-",
                "Status": order_status(order),
                "Priority": order.get("priority", "Normal"),
            })

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True
        )

    if active_jobs:
        st.warning(
            f"⚙️ {len(active_jobs)} production job(s) are currently active."
        )

    if store_pending:
        st.warning(
            f"📦 {store_pending} production job(s) waiting for store verification."
        )

    if loading_ready > 0:
        st.success(
            f"🚚 {loading_ready:,.2f} KG is ready for loading."
        )


# =========================================================
# FACTORY SETUP
# =========================================================

elif menu == "Factory Setup":

    st.header("⚙️ Factory Setup")

    st.write(
        "Configure your actual factory production lines, teams and products."
    )

    st.subheader("Production Lines")

    lines_text = st.text_area(
        "Production Lines",
        value="\n".join(st.session_state.factory_lines),
        height=150
    )

    st.subheader("Production Teams")

    teams_text = st.text_area(
        "Production Teams",
        value="\n".join(st.session_state.factory_teams),
        height=150
    )

    st.subheader("Products")

    products_text = st.text_area(
        "Products",
        value="\n".join(st.session_state.factory_products),
        height=150
    )

    if st.button("💾 Save Factory Setup"):

        st.session_state.factory_lines = [
            x.strip()
            for x in lines_text.splitlines()
            if x.strip()
        ]

        st.session_state.factory_teams = [
            x.strip()
            for x in teams_text.splitlines()
            if x.strip()
        ]

        st.session_state.factory_products = [
            x.strip()
            for x in products_text.splitlines()
            if x.strip()
        ]

        st.success("Factory setup saved.")


# =========================================================
# NEW CUSTOMER ORDER
# =========================================================

elif menu == "New Customer Order":

    st.header("📝 New Customer Order")

    with st.form("new_order"):

        c1, c2 = st.columns(2)

        customer = c1.text_input(
            "Customer / Company Name"
        )

        contact = c2.text_input(
            "Customer Contact"
        )

        c3, c4 = st.columns(2)

        product = c3.selectbox(
            "Product",
            st.session_state.factory_products
        )

        size = c4.text_input(
            "Size / Specification",
            placeholder="Example: 40 x 5 mm"
        )

        c5, c6, c7 = st.columns(3)

        quantity = c5.number_input(
            "Order Quantity KG",
            min_value=0.0,
            step=100.0
        )

        rate = c6.number_input(
            "Selling Rate ₹ / KG",
            min_value=0.0,
            step=1.0
        )

        priority = c7.selectbox(
            "Priority",
            ["Normal", "High", "Urgent"]
        )

        pickup_date = st.date_input(
            "Required / Pickup Date",
            value=date.today()
        )

        remarks = st.text_area(
            "Order Remarks"
        )

        submitted = st.form_submit_button(
            "➕ Create Customer Order"
        )

    if submitted:

        if not customer.strip():
            st.error("Customer name is required.")

        elif not size.strip():
            st.error("Product size/specification is required.")

        elif quantity <= 0:
            st.error("Order quantity must be greater than zero.")

        else:

            order_number = f"ORD-{st.session_state.next_order}"

            order = {
                "id": order_number,
                "customer": customer.strip(),
                "contact": contact.strip(),
                "product": product,
                "size": size.strip(),
                "quantity": quantity,
                "rate": rate,
                "priority": priority,
                "pickup_date": str(pickup_date),
                "remarks": remarks.strip(),
                "created_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            st.session_state.orders.append(order)
            st.session_state.next_order += 1

            st.success(
                f"Customer order {order_number} created successfully."
            )


# =========================================================
# MATERIAL RECEIVING
# =========================================================

elif menu == "Material Receiving":

    st.header("📥 Raw Material Receiving")

    with st.form("material_receiving"):

        c1, c2 = st.columns(2)

        supplier = c1.text_input("Supplier")
        material = c2.text_input(
            "Raw Material / Grade",
            placeholder="Example: MS Billet"
        )

        c3, c4 = st.columns(2)

        grn = c3.text_input("GRN / Receipt Number")
        vehicle = c4.text_input("Vehicle Number")

        c5, c6, c7 = st.columns(3)

        quantity = c5.number_input(
            "Received Quantity KG",
            min_value=0.0,
            step=100.0
        )

        rate = c6.number_input(
            "Purchase Rate ₹ / KG",
            min_value=0.0,
            step=1.0
        )

        receiving_date = c7.date_input(
            "Receiving Date",
            value=date.today()
        )

        received_by = st.text_input(
            "Received By"
        )

        location = st.text_input(
            "Storage Location"
        )

        remarks = st.text_area(
            "Remarks"
        )

        submitted = st.form_submit_button(
            "📥 Receive Material"
        )

    if submitted:

        if not material.strip():
            st.error("Enter raw material / grade.")

        elif quantity <= 0:
            st.error("Quantity must be greater than zero.")

        else:

            st.session_state.raw_receipts.append({
                "supplier": supplier.strip(),
                "material": material.strip(),
                "grn": grn.strip(),
                "vehicle": vehicle.strip(),
                "quantity": quantity,
                "rate": rate,
                "value": quantity * rate,
                "date": str(receiving_date),
                "received_by": received_by.strip(),
                "location": location.strip(),
                "remarks": remarks.strip(),
                "created_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            })

            st.success(
                f"{quantity:,.2f} KG received successfully."
            )


# =========================================================
# RAW MATERIAL STOCK
# =========================================================

elif menu == "Raw Material Stock":

    st.header("📦 Raw Material Stock")

    materials = raw_materials()

    if not materials:
        st.info(
            "No raw material has been received yet."
        )
    else:

        rows = []

        for material in materials:

            received = raw_received(material)
            consumed = raw_consumed(material)
            available = raw_available(material)

            rows.append({
                "Material / Grade": material,
                "Received KG": received,
                "Consumed KG": consumed,
                "Available KG": available,
            })

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Material Receiving History")

        st.dataframe(
            st.session_state.raw_receipts,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# PRODUCTION PLANNING
# =========================================================

elif menu == "Production Planning":

    st.header("📋 Production Planning")

    if not st.session_state.orders:
        st.info(
            "Create a customer order first."
        )
    else:

        for order in st.session_state.orders:

            balance = order_balance(order)

            available_stock = available_finished_stock(
                order["product"],
                order["size"]
            )

            production_required = max(
                0,
                balance - available_stock
            )

            with st.expander(
                f"{order['id']} | {order['customer']} | "
                f"{order['product']} | Balance {balance:,.2f} KG"
            ):

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Order Quantity",
                    f"{order['quantity']:,.2f} KG"
                )

                c2.metric(
                    "Ready Stock",
                    f"{available_stock:,.2f} KG"
                )

                c3.metric(
                    "Order Balance",
                    f"{balance:,.2f} KG"
                )

                c4.metric(
                    "Production Required",
                    f"{production_required:,.2f} KG"
                )

                job = get_job(order["id"])

                if job:
                    st.info(
                        f"Production job already exists | "
                        f"{job.get('line', '-')} | "
                        f"{job.get('team', '-')} | "
                        f"{job.get('status', '-')}"
                    )

                elif production_required > 0:

                    if st.button(
                        f"⚙️ Create Production Job - {order['id']}",
                        key=f"create_job_{order['id']}"
                    ):

                        st.session_state.production_jobs.append({
                            "order_id": order["id"],
                            "product": order["product"],
                            "size": order["size"],
                            "required": production_required,
                            "finished": 0.0,
                            "wastage": 0.0,
                            "damage": 0.0,
                            "scrap": 0.0,
                            "line": "",
                            "team": "",
                            "status": "PLANNED",
                            "created_at": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        })

                        st.success(
                            "Production job created."
                        )

                else:
                    st.success(
                        "No new production required. Existing verified stock can cover the order."
                    )


# =========================================================
# PRODUCTION LINE
# =========================================================

elif menu == "Production Line":

    st.header("🏭 Production Line Control")

    jobs = st.session_state.production_jobs

    if not jobs:
        st.info(
            "No production jobs yet. Create one from Production Planning."
        )
    else:

        for index, job in enumerate(jobs):

            order = next(
                (
                    x for x in st.session_state.orders
                    if x["id"] == job["order_id"]
                ),
                None
            )

            if not order:
                continue

            with st.expander(
                f"{job['order_id']} | "
                f"{order['customer']} | "
                f"{job['product']} | "
                f"{job['status']}"
            ):

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Required",
                    f"{job['required']:,.2f} KG"
                )

                c2.metric(
                    "Produced",
                    f"{job['finished']:,.2f} KG"
                )

                c3.metric(
                    "Wastage",
                    f"{job['wastage']:,.2f} KG"
                )

                c4.metric(
                    "Damage",
                    f"{job['damage']:,.2f} KG"
                )

                line = st.selectbox(
                    "Production Line",
                    st.session_state.factory_lines,
                    key=f"line_{index}"
                )

                team = st.selectbox(
                    "Production Team",
                    st.session_state.factory_teams,
                    key=f"team_{index}"
                )

                material_list = raw_materials()

                if not material_list:
                    st.warning(
                        "No raw material available. Receive raw material first."
                    )
                    continue

                material = st.selectbox(
                    "Raw Material",
                    material_list,
                    key=f"material_{index}"
                )

                available_raw = raw_available(material)

                st.caption(
                    f"Available raw material: {available_raw:,.2f} KG"
                )

                c5, c6 = st.columns(2)

                raw_input = c5.number_input(
                    "Raw Material Input KG",
                    min_value=0.0,
                    max_value=max(available_raw, 0.0),
                    step=100.0,
                    key=f"raw_{index}"
                )

                finished = c6.number_input(
                    "Finished Output KG",
                    min_value=0.0,
                    step=100.0,
                    key=f"finished_{index}"
                )

                c7, c8, c9 = st.columns(3)

                wastage = c7.number_input(
                    "Wastage KG",
                    min_value=0.0,
                    step=1.0,
                    key=f"waste_{index}"
                )

                damage = c8.number_input(
                    "Damage KG",
                    min_value=0.0,
                    step=1.0,
                    key=f"damage_{index}"
                )

                scrap = c9.number_input(
                    "Reusable Scrap KG",
                    min_value=0.0,
                    step=1.0,
                    key=f"scrap_{index}"
                )

                material_rate = st.number_input(
                    "Material Cost ₹ / KG",
                    min_value=0.0,
                    step=1.0,
                    key=f"rate_{index}"
                )

                if st.button(
                    "▶️ Record Production",
                    key=f"produce_{index}"
                ):

                    if finished <= 0:
                        st.error(
                            "Finished output must be greater than zero."
                        )

                    elif raw_input <= 0:
                        st.error(
                            "Raw material input must be greater than zero."
                        )

                    elif raw_input > available_raw:
                        st.error(
                            "Insufficient raw material stock."
                        )

                    elif (
                        finished + wastage + damage + scrap
                        > raw_input + 0.0001
                    ):
                        st.error(
                            "Finished + wastage + damage + scrap "
                            "cannot exceed raw input."
                        )

                    else:

                        remaining_required = max(
                            0,
                            job["required"] - job["finished"]
                        )

                        if finished > remaining_required:
                            st.error(
                                f"Finished output cannot exceed remaining "
                                f"requirement of {remaining_required:,.2f} KG."
                            )
                        else:

                            job["line"] = line
                            job["team"] = team
                            job["finished"] += finished
                            job["wastage"] += wastage
                            job["damage"] += damage
                            job["scrap"] += scrap

                            if job["finished"] >= job["required"]:
                                job["status"] = (
                                    "READY FOR STORE VERIFICATION"
                                )
                            else:
                                job["status"] = "IN PRODUCTION"

                            st.session_state.material_consumption.append({
                                "order_id": job["order_id"],
                                "product": job["product"],
                                "size": job["size"],
                                "material": material,
                                "raw_input": raw_input,
                                "finished": finished,
                                "wastage": wastage,
                                "damage": damage,
                                "scrap": scrap,
                                "material_rate": material_rate,
                                "material_cost": raw_input * material_rate,
                                "line": line,
                                "team": team,
                                "date": str(date.today()),
                                "created_at": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                            })

                            st.success(
                                f"{finished:,.2f} KG production recorded."
                            )

                            st.rerun()

                st.divider()

                st.subheader("👷 Labour Entry")

                c10, c11, c12 = st.columns(3)

                worker = c10.text_input(
                    "Worker / Operator",
                    key=f"worker_{index}"
                )

                hours = c11.number_input(
                    "Hours",
                    min_value=0.0,
                    step=1.0,
                    key=f"hours_{index}"
                )

                hourly_rate = c12.number_input(
                    "Rate ₹ / Hour",
                    min_value=0.0,
                    step=10.0,
                    key=f"hourly_{index}"
                )

                if st.button(
                    "👷 Add Labour Cost",
                    key=f"labour_{index}"
                ):

                    if worker.strip() and hours > 0:

                        st.session_state.labour_entries.append({
                            "order_id": job["order_id"],
                            "worker": worker.strip(),
                            "hours": hours,
                            "rate": hourly_rate,
                            "cost": hours * hourly_rate,
                            "date": str(date.today()),
                        })

                        st.success(
                            "Labour cost added."
                        )

                    else:
                        st.error(
                            "Enter worker name and hours."
                        )


# =========================================================
# STORE VERIFICATION
# =========================================================

elif menu == "Store Verification":

    st.header("📦 Store Verification")

    jobs = production_jobs_waiting_store()

    if not jobs:
        st.info(
            "No completed production is waiting for store verification."
        )
    else:

        for index, job in enumerate(jobs):

            with st.expander(
                f"{job['order_id']} | {job['product']} | "
                f"{job['finished']:,.2f} KG"
            ):

                quantity = st.number_input(
                    "Physical Verified Quantity KG",
                    min_value=0.0,
                    max_value=float(job["finished"]),
                    value=float(job["finished"]),
                    key=f"verify_qty_{index}"
                )

                location = st.text_input(
                    "Finished Goods Location",
                    key=f"verify_location_{index}"
                )

                verifier = st.text_input(
                    "Verified By",
                    key=f"verifier_{index}"
                )

                notes = st.text_area(
                    "Verification Notes",
                    key=f"verify_notes_{index}"
                )

                if st.button(
                    "✅ Verify & Move to Finished Stock",
                    key=f"verify_{index}"
                ):

                    if quantity <= 0:
                        st.error(
                            "Verified quantity must be greater than zero."
                        )

                    else:

                        st.session_state.store_verifications.append({
                            "order_id": job["order_id"],
                            "product": job["product"],
                            "size": job["size"],
                            "product_key": product_key(
                                job["product"],
                                job["size"]
                            ),
                            "quantity": quantity,
                            "location": location.strip(),
                            "verifier": verifier.strip(),
                            "notes": notes.strip(),
                            "date": str(date.today()),
                            "created_at": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        })

                        if quantity >= job["finished"]:
                            job["status"] = "VERIFIED"
                        else:
                            job["status"] = "PARTIALLY VERIFIED"

                        st.success(
                            f"{quantity:,.2f} KG moved to finished goods stock."
                        )

                        st.rerun()


# =========================================================
# LOADING & DISPATCH
# =========================================================

elif menu == "Loading & Dispatch":

    st.header("🚚 Loading & Dispatch")

    queue = dispatch_queue()

    if not queue:
        st.info(
            "No finished goods are currently ready for dispatch."
        )
    else:

        for index, item in enumerate(queue):

            order = item["order"]
            ready = item["ready"]
            job = get_job(order["id"])

            with st.expander(
                f"{order['id']} | {order['customer']} | "
                f"{order['product']} | Ready {ready:,.2f} KG"
            ):

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Order Balance",
                    f"{order_balance(order):,.2f} KG"
                )

                c2.metric(
                    "Ready Stock",
                    f"{ready:,.2f} KG"
                )

                c3.metric(
                    "Rate",
                    f"₹{order['rate']:,.2f}/KG"
                )

                c4.metric(
                    "Priority",
                    order.get("priority", "Normal")
                )

                if job:
                    st.caption(
                        f"Production: {job.get('line', '-')} / "
                        f"{job.get('team', '-')}"
                    )

                c5, c6 = st.columns(2)

                truck = c5.text_input(
                    "Truck Number",
                    key=f"truck_{index}"
                )

                driver = c6.text_input(
                    "Driver",
                    key=f"driver_{index}"
                )

                loading_weight = st.number_input(
                    "Loading Quantity KG",
                    min_value=0.0,
                    max_value=float(ready),
                    value=float(ready),
                    step=100.0,
                    key=f"dispatch_qty_{index}"
                )

                dispatch_rate = st.number_input(
                    "Dispatch Rate ₹ / KG",
                    min_value=0.0,
                    value=float(order["rate"]),
                    step=1.0,
                    key=f"dispatch_rate_{index}"
                )

                remarks = st.text_area(
                    "Dispatch Remarks",
                    key=f"dispatch_remarks_{index}"
                )

                if st.button(
                    "🚚 Confirm Loading & Dispatch",
                    key=f"dispatch_{index}"
                ):

                    if loading_weight <= 0:
                        st.error(
                            "Loading quantity must be greater than zero."
                        )

                    else:

                        st.session_state.dispatch_records.append({
                            "order_id": order["id"],
                            "customer": order["customer"],
                            "product": order["product"],
                            "size": order["size"],
                            "product_key": product_key(
                                order["product"],
                                order["size"]
                            ),
                            "quantity": loading_weight,
                            "rate": dispatch_rate,
                            "value": loading_weight * dispatch_rate,
                            "truck": truck.strip(),
                            "driver": driver.strip(),
                            "remarks": remarks.strip(),
                            "date": str(date.today()),
                            "created_at": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        })

                        st.success(
                            f"{loading_weight:,.2f} KG dispatched."
                        )

                        st.rerun()


# =========================================================
# ORDER BALANCE & CLOSURE
# =========================================================

elif menu == "Order Balance & Closure":

    st.header("📌 Order Balance & Closure")

    if not st.session_state.orders:
        st.info("No customer orders.")
    else:

        for index, order in enumerate(
            st.session_state.orders
        ):

            balance = order_balance(order)

            with st.expander(
                f"{order['id']} | {order['customer']} | "
                f"Balance {balance:,.2f} KG"
            ):

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Order Quantity",
                    f"{order['quantity']:,.2f} KG"
                )

                c2.metric(
                    "Dispatched",
                    f"{order['quantity'] - balance:,.2f} KG"
                )

                c3.metric(
                    "Balance",
                    f"{balance:,.2f} KG"
                )

                st.write(
                    f"**Current Status:** {order_status(order)}"
                )

                closure_note = st.text_area(
                    "Closure Note",
                    key=f"closure_note_{index}"
                )

                if st.button(
                    "🔒 Close Order",
                    key=f"close_{index}"
                ):

                    st.session_state.order_closures.append({
                        "order_id": order["id"],
                        "date": str(date.today()),
                        "balance_at_closure": balance,
                        "note": closure_note.strip(),
                    })

                    st.success(
                        f"{order['id']} marked for closure."
                    )


# =========================================================
# DAILY FACTORY REPORT
# =========================================================

elif menu == "Daily Factory Report":

    st.header("🤖 Daily Factory AI Report")

    report_date = st.date_input(
        "Report Date",
        value=date.today()
    )

    report_date_str = str(report_date)

    raw_received_today = sum(
        float(x.get("quantity", 0))
        for x in st.session_state.raw_receipts
        if x.get("date") == report_date_str
    )

    raw_consumed_today = sum(
        float(x.get("raw_input", 0))
        for x in st.session_state.material_consumption
        if x.get("date") == report_date_str
    )

    material_cost_today = sum(
        float(x.get("material_cost", 0))
        for x in st.session_state.material_consumption
        if x.get("date") == report_date_str
    )

    finished_today = sum(
        float(x.get("finished", 0))
        for x in st.session_state.material_consumption
        if x.get("date") == report_date_str
    )

    wastage_today = sum(
        float(x.get("wastage", 0))
        for x in st.session_state.material_consumption
        if x.get("date") == report_date_str
    )

    damage_today = sum(
        float(x.get("damage", 0))
        for x in st.session_state.material_consumption
        if x.get("date") == report_date_str
    )

    scrap_today = sum(
        float(x.get("scrap", 0))
        for x in st.session_state.material_consumption
        if x.get("date") == report_date_str
    )

    labour_today = sum(
        float(x.get("cost", 0))
        for x in st.session_state.labour_entries
        if x.get("date") == report_date_str
    )

    verified_today = sum(
        float(x.get("quantity", 0))
        for x in st.session_state.store_verifications
        if x.get("date") == report_date_str
    )

    dispatched_today = sum(
        float(x.get("quantity", 0))
        for x in st.session_state.dispatch_records
        if x.get("date") == report_date_str
    )

    dispatch_value_today = sum(
        float(x.get("value", 0))
        for x in st.session_state.dispatch_records
        if x.get("date") == report_date_str
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Raw Received",
        f"{raw_received_today:,.2f} KG"
    )

    c2.metric(
        "Raw Consumed",
        f"{raw_consumed_today:,.2f} KG"
    )

    c3.metric(
        "Finished Production",
        f"{finished_today:,.2f} KG"
    )

    c4.metric(
        "Dispatched",
        f"{dispatched_today:,.2f} KG"
    )

    c5, c6, c7, c8 = st.columns(4)

    c5.metric(
        "Wastage",
        f"{wastage_today:,.2f} KG"
    )

    c6.metric(
        "Damage",
        f"{damage_today:,.2f} KG"
    )

    c7.metric(
        "Labour Cost",
        f"₹{labour_today:,.2f}"
    )

    c8.metric(
        "Dispatch Value",
        f"₹{dispatch_value_today:,.2f}"
    )

    st.divider()

    st.subheader("📊 Factory AI Management Summary")

    active_jobs = len([
        j for j in st.session_state.production_jobs
        if j.get("status") == "IN PRODUCTION"
    ])

    store_pending = len(
        production_jobs_waiting_store()
    )

    loading_ready = sum(
        x["ready"]
        for x in dispatch_queue()
    )

    messages = []

    if raw_received_today == 0:
        messages.append(
            "• No raw material was received today."
        )

    if finished_today > 0:
        messages.append(
            f"• Factory produced {finished_today:,.2f} KG today."
        )
    else:
        messages.append(
            "• No production was recorded today."
        )

    if wastage_today > 0:
        messages.append(
            f"• Wastage recorded: {wastage_today:,.2f} KG."
        )

    if damage_today > 0:
        messages.append(
            f"• Damaged material: {damage_today:,.2f} KG."
        )

    if labour_today > 0:
        messages.append(
            f"• Labour cost recorded: ₹{labour_today:,.2f}."
        )

    if dispatched_today > 0:
        messages.append(
            f"• {dispatched_today:,.2f} KG dispatched."
        )

    if active_jobs > 0:
        messages.append(
            f"• {active_jobs} production job(s) remain active."
        )

    if store_pending > 0:
        messages.append(
            f"• {store_pending} production job(s) need store verification."
        )

    if loading_ready > 0:
        messages.append(
            f"• {loading_ready:,.2f} KG is ready for loading."
        )

    for message in messages:
        st.write(message)

    st.divider()

    st.subheader("📱 WhatsApp-Ready Daily Report")

    whatsapp_report = f"""
🏭 FACTORY AI — DAILY REPORT

Date: {report_date_str}

PRODUCTION
Finished Production: {finished_today:,.2f} KG

MATERIAL
Raw Material Received: {raw_received_today:,.2f} KG
Raw Material Consumed: {raw_consumed_today:,.2f} KG
Wastage: {wastage_today:,.2f} KG
Damage: {damage_today:,.2f} KG
Reusable Scrap: {scrap_today:,.2f} KG

COST
Material Cost: ₹{material_cost_today:,.2f}
Labour Cost: ₹{labour_today:,.2f}

STORE
Verified Finished Goods: {verified_today:,.2f} KG

DISPATCH
Dispatched: {dispatched_today:,.2f} KG
Dispatch Value: ₹{dispatch_value_today:,.2f}

FACTORY STATUS
Active Production Jobs: {active_jobs}
Store Verification Pending: {store_pending}
Loading Ready: {loading_ready:,.2f} KG

MANAGEMENT NOTE
Production, material, wastage, labour and dispatch
figures should be reviewed before closing the day.
"""

    st.code(
        whatsapp_report,
        language="text"
    )

    st.download_button(
        "📥 Download Daily Report",
        data=whatsapp_report,
        file_name=f"factory_report_{report_date_str}.txt",
        mime="text/plain"
    )


# =========================================================
# BILLS & DOCUMENTS
# =========================================================

elif menu == "Bills & Documents":

    st.header("📄 Bills & Documents")

    if not st.session_state.dispatch_records:
        st.info(
            "No dispatch records available."
        )
    else:

        st.subheader("Dispatch History")

        st.dataframe(
            st.session_state.dispatch_records,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("🧾 Dispatch Bill Preview")

        selected_order = st.selectbox(
            "Select Order",
            [
                x["order_id"]
                for x in st.session_state.dispatch_records
            ]
        )

        records = [
            x for x in st.session_state.dispatch_records
            if x["order_id"] == selected_order
        ]

        if records:

            latest = records[-1]

            st.markdown(
                f"""
### FACTORY DISPATCH DOCUMENT

**Order:** {latest['order_id']}  
**Customer:** {latest['customer']}  
**Product:** {latest['product']}  
**Size:** {latest['size']}  
**Quantity:** {latest['quantity']:,.2f} KG  
**Rate:** ₹{latest['rate']:,.2f} / KG  
**Value:** ₹{latest['value']:,.2f}  
**Truck:** {latest['truck']}  
**Driver:** {latest['driver']}  
**Date:** {latest['date']}  

**Remarks:** {latest['remarks']}
"""
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Factory AI • Clean Offline Demo • No Fake Factory Data • "
    "Designed for manufacturing / steel factory operations"
)