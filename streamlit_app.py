import re
from datetime import date
from typing import get_args

import pandas as pd
import requests
import streamlit as st

from app.schemas import KNOWN_LOCATIONS, Category

API = "http://127.0.0.1:8000"
PLACES = sorted(KNOWN_LOCATIONS)
CATEGORY_PICKS = [c for c in get_args(Category) if c != "other"]
PAGES = ["🏠 Home", "📝 Report an item", "🔎 Browse", "🤝 Find matches"]
HOME, REPORT, BROWSE, MATCHES = PAGES
LABELS = {"CategoryScorer": "Category", "TextScorer": "Description",
          "LocationScorer": "Location", "DateScorer": "Date",
          "ColorBrandScorer": "Color / brand"}
STATUS_COLORS = {"open": "blue", "claimed": "gray", "expired": "orange"}

st.set_page_config(page_title="Campus Lost & Found", page_icon="🎒", layout="wide")


# ================= talking to the FastAPI backend =================
class ApiError(Exception):
    pass


def error_text(data, status):
    if isinstance(data, dict) and isinstance(data.get("detail"), str):
        return data["detail"]
    if isinstance(data, dict) and isinstance(data.get("detail"), list):
        parts = []
        for d in data["detail"]:
            where = " ".join(str(p) for p in d.get("loc", [])[1:])
            parts.append((where + ": " if where else "") + d.get("msg", ""))
        return " | ".join(parts)
    return f"Something went wrong ({status})"


def call(method, path, **kwargs):
    try:
        response = requests.request(method, API + path, timeout=10, **kwargs)
    except requests.RequestException:
        raise ApiError("Can't reach the API. Is 'uvicorn app.main:app' running?")
    try:
        data = response.json()
    except ValueError:
        data = None
    if not response.ok:
        raise ApiError(error_text(data, response.status_code))
    return data


# ================= small helpers =================
def nice(text):
    return text.replace("_", " ").title()


def plain(text):
    """Show user-typed text as plain text (no markdown tricks)."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>~$:<])", r"\\\1", str(text))


def kind_badge(kind):
    return ":red-badge[LOST]" if kind == "lost" else ":green-badge[FOUND]"


def status_badge(status):
    return f":{STATUS_COLORS.get(status, 'gray')}-badge[{status}]"


def ago(date_text):
    try:
        days = (date.today() - date.fromisoformat(date_text)).days
    except ValueError:
        return ""
    if days <= 0:
        return " · today"
    if days == 1:
        return " · yesterday"
    return f" · {days} days ago"


def details_line(r):
    extra = " · ".join(x for x in (r["color"], r["brand"]) if x)
    return f"📍 {r['location'] or '…'} · 📅 {r['event_date']}" + (f" · {extra}" if extra else "")


def flash(kind, message):
    st.session_state.flash = (kind, message)


def show_flash():
    item = st.session_state.pop("flash", None)
    if item:
        getattr(st, item[0])(item[1])


def show_item(r, key_prefix, button=True):
    with st.container(border=True):
        st.markdown(f"{kind_badge(r['kind'])} {status_badge(r['status'])}")
        title = nice(r["category"]) if r["category"] else "Item"
        st.markdown(f"**{plain(title)}**" + (f" · #{r['id']}" if r["id"] != "new" else ""))
        st.markdown(plain(r["description"]) if r["description"] else "_Your description will appear here_")
        st.caption(details_line(r) + ago(r["event_date"]))
        if button and r["status"] == "open":
            st.button("Find matches", key=f"{key_prefix}_{r['id']}",
                      on_click=go_matches, args=(r["id"],))


# ================= button callbacks (they run before the page redraws) =================
def go_matches(report_id):
    st.session_state.page = MATCHES
    st.session_state.match_input = int(report_id)
    st.session_state.active_id = int(report_id)


def start_report(kind):
    st.session_state.page = REPORT
    st.session_state.rep_kind = kind


def pick(pill_key, text_key):
    """A quick-pick chip fills the matching text box, then clears itself."""
    choice = st.session_state.get(pill_key)
    if choice:
        st.session_state[text_key] = choice.replace("_", " ")
    st.session_state[pill_key] = None


def show_more():
    st.session_state.browse_limit = st.session_state.get("browse_limit", 9) + 9


def submit_report():
    s = st.session_state
    kind = s.get("rep_kind", "lost")
    body = {"kind": kind,
            "category": s.get("rep_cat", ""),
            "description": s.get("rep_desc", ""),
            "location": s.get("rep_loc", ""),
            "event_date": s.get("rep_date", date.today()).isoformat(),
            "contact": s.get("rep_contact", ""),
            "color": s.get("rep_color", ""),
            "brand": s.get("rep_brand", "")}
    if kind == "found":
        body["verification_question"] = s.get("rep_q", "")
        body["verification_answer"] = s.get("rep_a", "")
    try:
        report = call("POST", "/reports", json=body)
    except ApiError as err:
        flash("error", str(err))          # keep what the user typed
        return
    for key in ("rep_cat", "rep_loc", "rep_desc", "rep_color", "rep_brand",
            "rep_q", "rep_a", "rep_contact"):
        s[key] = ""
    s.saved = {"id": report["id"], "kind": kind}


# ================= page: home =================
def page_home(stats):
    st.title("🎒 Campus Lost & Found")
    st.subheader("Lost something? Found something? We match them up.")
    b1, b2, _ = st.columns([1, 1, 2])
    b1.button("😢 I lost something", on_click=start_report, args=("lost",), type="primary")
    b2.button("🙌 I found something", on_click=start_report, args=("found",))

    if stats:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Reports", stats["total"])
        m2.metric("Lost", stats["lost"])
        m3.metric("Found", stats["found"])
        m4.metric("Items recovered", stats["items_recovered"])

    st.divider()
    st.subheader("How it works")
    s1, s2, s3 = st.columns(3)
    s1.markdown("### 1️⃣ Report\nTell us what you lost or found, where, and when.")
    s2.markdown("### 2️⃣ Match\nWe score every pair and show the best matches first.")
    s3.markdown("### 3️⃣ Claim\nAnswer the finder's secret question to get their contact.")

    st.divider()
    st.subheader("Recently reported")
    latest = call("GET", "/reports", params={"status": "open"})[::-1][:3]
    if not latest:
        st.info("No open reports yet. Be the first to add one!")
    for col, r in zip(st.columns(3), latest):
        with col:
            show_item(r, "home")


# ================= page: report an item =================
def page_report():
    st.header("📝 Report an item")

    saved = st.session_state.pop("saved", None)
    if saved:
        st.success(f"Report saved! Your report ID is #{saved['id']}. Keep it: you need it "
                   "to check matches" + (" and claim your item." if saved["kind"] == "lost" else "."))
        st.button("See matches for my report", on_click=go_matches,
                  args=(saved["id"],), type="primary")

    left, right = st.columns([3, 2], gap="large")
    with left:
        kind = st.radio("What happened?", ["lost", "found"], horizontal=True, key="rep_kind",
                        format_func=lambda k: "😢 I lost something" if k == "lost"
                        else "🙌 I found something")
        category = st.text_input("What is it?", key="rep_cat",
                                 placeholder="e.g. earphones, wallet, ID card")
        st.pills("Quick pick", CATEGORY_PICKS, key="pick_cat", format_func=nice,
                 label_visibility="collapsed", on_change=pick, args=("pick_cat", "rep_cat"))
        location = st.text_input("Where?", key="rep_loc",
                                 placeholder="e.g. library, canteen, main block")
        st.pills("Common places", PLACES, key="pick_loc", format_func=str.title,
                 label_visibility="collapsed", on_change=pick, args=("pick_loc", "rep_loc"))
        description = st.text_area("Describe it", key="rep_desc", max_chars=300, height=110,
                                   placeholder="e.g. Black boAt earphones with a charging case")
        c1, c2 = st.columns(2)
        color = c1.text_input("Color (optional)", key="rep_color")
        brand = c2.text_input("Brand (optional)", key="rep_brand")
        event_date = c1.date_input("Date", value=date.today(), max_value=date.today(),
                                   key="rep_date")
        c2.text_input("Your phone number", key="rep_contact",
                      help="Kept private. Only a found item's number is shown, and only "
                           "to the verified owner.")
        if kind == "found":
            st.info("Set a secret question that only the real owner can answer "
                    "(a sticker, a scratch, what is inside). Never share the answer.")
            st.text_input("Secret question", key="rep_q",
                          placeholder="e.g. What sticker is on the case?")
            st.text_input("Secret answer", key="rep_a")
        st.button("Submit report", type="primary", on_click=submit_report)

    with right:
        st.subheader("Live preview")
        preview = {"id": "new", "kind": kind, "status": "open",
                   "category": category.strip(), "description": description.strip(),
                   "location": location.strip(), "event_date": event_date.isoformat(),
                   "color": color.strip(), "brand": brand.strip()}
        show_item(preview, "preview", button=False)
        st.caption("This is how your report will look to others. The preview updates "
                   "when you click out of a field.")


# ================= page: browse =================
def page_browse():
    st.header("🔎 Browse reports")
    f1, f2, f3, f4 = st.columns([3, 1.2, 1.2, 1.4])
    query = f1.text_input("Search", placeholder="🔍 Search: wallet, black, library…",
                          label_visibility="collapsed")
    kind = f2.selectbox("Type", ["all", "lost", "found"], label_visibility="collapsed",
                        format_func={"all": "Lost + found", "lost": "Lost only",
                                     "found": "Found only"}.get)
    status = f3.selectbox("Status", ["open", "claimed", "expired", "any"],
                          label_visibility="collapsed", format_func=str.title)
    view = f4.radio("View", ["Cards", "Table"], horizontal=True, label_visibility="collapsed")

    params = {}
    if kind != "all":
        params["kind"] = kind
    if status != "any":
        params["status"] = status
    items = call("GET", "/reports", params=params)[::-1]          # newest first

    words = query.lower().split()
    if words:
        def haystack(r):
            text = " ".join(str(r.get(k, "")) for k in
                            ("description", "category", "location", "color", "brand"))
            return text.lower().replace("_", " ")
        items = [r for r in items if all(w in haystack(r) for w in words)]

    st.caption(f"{len(items)} result{'s' if len(items) != 1 else ''}")
    if not items:
        st.info("Nothing found. Try fewer words or another filter.")
        return

    if view == "Table":
        st.dataframe([{"ID": r["id"], "Type": r["kind"], "Item": nice(r["category"]),
                       "Description": r["description"], "Where": r["location"],
                       "Date": r["event_date"], "Status": r["status"]} for r in items],
                     hide_index=True)
        return

    limit = st.session_state.get("browse_limit", 9)
    shown = items[:limit]
    for i in range(0, len(shown), 3):
        for col, r in zip(st.columns(3), shown[i:i + 3]):
            with col:
                show_item(r, "browse")
    if len(items) > limit:
        st.button(f"Show more ({len(items) - limit} left)", on_click=show_more)


# ================= page: matches and claims =================
@st.dialog("Verify it's yours")
def claim_dialog(report, found):
    st.write("Answer the finder's secret question to get their contact details.")
    st.markdown(f"**{plain(found.get('verification_question') or 'No question was set')}**")
    typed = st.text_input("Your answer", key=f"ans_{found['id']}")
    if st.button("Claim item", type="primary"):
        if not typed.strip():
            st.warning("Type your answer first.")
            return
        try:
            result = call("POST", "/claim", json={"lost_id": report["id"],
                                                  "found_id": found["id"], "answer": typed})
        except ApiError as err:
            st.error(str(err))
            return
        st.session_state.claim_result = {"lost_id": report["id"],
                                         "contact": result["finder_contact"]}
        st.session_state.celebrate = True
        st.rerun()


def page_matches(stats):
    min_score = stats["claim_min_score"] if stats else 80
    st.header("🤝 Find matches")
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    c1.number_input("Your report ID", min_value=1, step=1, key="match_input")
    if c2.button("Find matches", type="primary"):
        st.session_state.active_id = int(st.session_state.match_input)

    active = st.session_state.get("active_id")
    if not active:
        st.info("Enter the ID you got when you reported your item, or press "
                "'Find matches' on any report in Browse.")
        return

    with st.spinner("Looking for matches…"):
        report = call("GET", f"/reports/{active}")
        matches = call("GET", f"/reports/{active}/matches")
        others = [call("GET", "/reports/{}".format(
                  m["found_id"] if report["kind"] == "lost" else m["lost_id"]))
                  for m in matches]

    result = st.session_state.get("claim_result")
    claimed_now = bool(result and result["lost_id"] == active)
    if claimed_now:
        st.success(f"🎉 Verified! Contact the finder on **{result['contact']}** "
                   "to collect your item.")
        if st.session_state.pop("celebrate", False):
            st.balloons()

    st.markdown("#### Your report")
    show_item(report, "mine", button=False)

    if not matches:
        if not claimed_now:
            st.info("No matches yet. Matches are re-checked every time you search, "
                    "so come back soon.")
        return

    st.markdown(f"#### {len(matches)} possible match{'es' if len(matches) != 1 else ''}")
    for m, other in zip(matches, others):
        with st.container(border=True):
            left, right = st.columns([1, 3])
            with left:
                st.metric("Match", f"{m['score']}%")
                st.progress(min(m["score"], 100) / 100)
            with right:
                st.markdown(f"{kind_badge(other['kind'])} **{plain(nice(other['category']))}**"
                            f" · #{other['id']}")
                st.markdown(plain(other["description"]))
                st.caption(details_line(other) + ago(other["event_date"]))
                with st.expander("Why this match?"):
                    chart = pd.DataFrame({"Points": list(m["why"].values())},
                                         index=[LABELS.get(k, k) for k in m["why"]])
                    st.bar_chart(chart, horizontal=True, height=200)
                if report["kind"] == "lost" and report["status"] == "open":
                    if m["score"] >= min_score:
                        st.markdown(":green-badge[Strong match]")
                        if st.button("✋ This is mine", key=f"claim_{other['id']}",
                                     type="primary"):
                            claim_dialog(report, other)
                    else:
                        st.caption(f"🔒 Claiming needs at least a {min_score}% match, "
                                   "so the finder's contact stays private.")
                elif report["kind"] == "found":
                    st.caption("Owners claim items from their own lost report.")


# ================= the app shell =================
try:
    stats = call("GET", "/stats")
except ApiError:
    stats = None

with st.sidebar:
    st.markdown("## 🎒 Lost & Found")
    page = st.radio("Menu", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    if stats:
        st.metric("Open reports", stats["open"])
        st.metric("Items recovered", stats["items_recovered"])
    with st.expander("How matching works"):
        st.markdown("Every lost and found pair gets a score out of 100:\n\n"
                    "- Category: 30\n- Description: 30\n- Location: 20\n"
                    "- Date: 15\n- Color / brand: 5\n\nScores of 60 or more are shown.")

show_flash()

try:
    if page == HOME:
        page_home(stats)
    elif page == REPORT:
        page_report()
    elif page == BROWSE:
        page_browse()
    else:
        page_matches(stats)
except ApiError as err:
    st.error(str(err))