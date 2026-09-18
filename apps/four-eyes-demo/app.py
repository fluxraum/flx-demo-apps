"""Four-eyes-principle (Vier-Augen-Prinzip) demo.

One person creates a request (the "maker"); a *different* person has to
approve it (the "checker") before it takes effect -- the maker can never
approve their own request. The point of this demo is that the checker
constraint is enforced against a *real* identity, not a dropdown: the
current user comes from the X-Auth-Request-Email header the platform's
oauth2-proxy sets after a real Entra ID login (see
infra/addons.py's deploy_oauth2_proxy/deploy_monitoring for the same
mechanism already used to give Grafana single sign-on) and that nginx
forwards here via this chart's auth-response-headers annotation (see
templates/streamlit/templates/ingress.yaml).

State is a plain in-memory list, deliberately: this is a demo, not a
product, and a restart clearing it is a fine trade for not needing a
database. It also means this only makes sense with a single replica --
see templates/streamlit/values.yaml's autoscaling override for this app.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock

import streamlit as st

st.set_page_config(page_title="Vier-Augen-Demo", page_icon="\U0001f440")


@dataclass
class Request:
    id: str
    title: str
    description: str
    amount: float
    created_by: str
    created_at: datetime
    status: str = "pending"  # pending | approved | rejected
    decided_by: str | None = None
    decided_at: datetime | None = None


@st.cache_resource
def _store() -> tuple[list[Request], Lock]:
    # A single instance of this (list, lock) pair is shared by every
    # session that hits this process -- st.cache_resource, unlike
    # st.session_state, is not per-browser-session.
    return [], Lock()


def current_user() -> str:
    header_email = st.context.headers.get("X-Auth-Request-Email")
    if header_email:
        return header_email
    # Not running behind oauth2-proxy (e.g. `streamlit run app.py` on a
    # laptop) -- let the user pick who they're "logged in" as instead of
    # just crashing, so the demo is still usable outside the cluster.
    st.sidebar.warning("Kein X-Auth-Request-Email-Header gefunden -- lokaler Testmodus.")
    return st.sidebar.text_input("Angemeldet als (Test)", value="alice@example.com")


def main() -> None:
    requests, lock = _store()
    me = current_user()

    st.title("\U0001f440 Vier-Augen-Prinzip -- Demo")
    st.caption(
        "Wer einen Antrag stellt, kann ihn nicht selbst genehmigen -- das wird hier "
        "gegen die echte, per SSO angemeldete Identität durchgesetzt, nicht nur "
        "gegen eine Auswahlliste."
    )
    st.info(f"Angemeldet als **{me}**", icon="\U0001f464")

    with st.form("new_request", clear_on_submit=True):
        st.subheader("Neuer Antrag")
        title = st.text_input("Titel")
        description = st.text_area("Beschreibung")
        amount = st.number_input("Betrag (EUR)", min_value=0.0, step=100.0)
        if st.form_submit_button("Antrag einreichen") and title:
            with lock:
                requests.append(
                    Request(
                        id=str(uuid.uuid4())[:8],
                        title=title,
                        description=description,
                        amount=amount,
                        created_by=me,
                        created_at=datetime.now(timezone.utc),
                    )
                )
            st.success("Antrag eingereicht -- wartet auf Genehmigung durch eine andere Person.")
            st.rerun()

    st.subheader("Offene Anträge")
    pending = [r for r in requests if r.status == "pending"]
    if not pending:
        st.caption("Keine offenen Anträge.")
    for r in pending:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{r.title}** -- {r.amount:,.2f} EUR")
                st.caption(f"von {r.created_by} am {r.created_at:%Y-%m-%d %H:%M} UTC")
                if r.description:
                    st.write(r.description)
            with col2:
                if r.created_by == me:
                    st.caption("Wartet auf eine andere Person -- du hast diesen Antrag gestellt.")
                else:
                    approve, reject = st.columns(2)
                    if approve.button("Genehmigen", key=f"approve-{r.id}", type="primary"):
                        with lock:
                            r.status = "approved"
                            r.decided_by = me
                            r.decided_at = datetime.now(timezone.utc)
                        st.rerun()
                    if reject.button("Ablehnen", key=f"reject-{r.id}"):
                        with lock:
                            r.status = "rejected"
                            r.decided_by = me
                            r.decided_at = datetime.now(timezone.utc)
                        st.rerun()

    decided = [r for r in requests if r.status != "pending"]
    if decided:
        st.subheader("Historie")
        st.dataframe(
            [
                {
                    "Titel": r.title,
                    "Betrag": r.amount,
                    "Antragsteller": r.created_by,
                    "Status": r.status,
                    "Entschieden von": r.decided_by,
                    "Entschieden am": r.decided_at,
                }
                for r in reversed(decided)
            ],
            hide_index=True,
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
