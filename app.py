import io
from datetime import date, datetime, time, timedelta
from pathlib import Path
from urllib.parse import quote

import gspread
import qrcode
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="KroniQ Booking",
    page_icon="🔷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).parent
SHEET_ID = "1CiFPrWzvyeaTtdiMVYZ8a3DyxONSi4ZEpn2kNM0LSeU"
WHATSAPP_VENTAS = "526563079754"

NEGOCIOS = {
    "Barbería": {
        "Corte caballero": 30,
        "Barba": 30,
        "Corte + barba": 60,
        "Tinte caballero": 90,
    },
    "Spa": {
        "Facial relajante": 60,
        "Masaje descontracturante": 90,
        "Depilación": 45,
        "Paquete spa": 120,
    },
    "Médico": {
        "Consulta general": 30,
        "Primera valoración": 45,
        "Consulta de seguimiento": 30,
        "Revisión de estudios": 30,
    },
    "Dentista": {
        "Valoración dental": 30,
        "Limpieza dental": 60,
        "Resina": 60,
        "Blanqueamiento": 90,
    },
}

PLANES = {
    "Starter": [
        "Agenda personalizada con logo e imagen del negocio",
        "Bloqueo automático de horarios empalmados",
        "Comentarios adicionales en cada reservación",
        "Confirmación de cita por WhatsApp",
    ],
    "Business": [
        "Todo lo incluido en Starter",
        "Promociones por recomendación",
        "Código QR para compartir tu agenda",
        "Flyer promocional en el encabezado",
    ],
    "Premium": [
        "Todo lo incluido en Business",
        "Flyers promocionales nuevos cada mes",
        "Cancelación y reprogramación de citas",
        "Bloqueos por vacaciones o días inhábiles",
        "Administración avanzada de disponibilidad",
    ],
}

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(18, 0)
COMIDA_INICIO = time(14, 0)
COMIDA_FIN = time(15, 0)


def aplicar_estilos():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {
            --bg: #101010;
            --surface: #17212a;
            --field: #091016;
            --text: #f5f8fc;
            --muted: #b7c4ce;
            --aqua: #59e8df;
            --line: rgba(135, 220, 255, .43);
        }

        .stApp,
        [data-testid="stAppViewContainer"],
        .main {
            background: var(--bg) !important;
            color: var(--text) !important;
            font-family: "DM Sans", sans-serif;
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            max-width: 920px;
            padding: 1rem 1rem 4rem !important;
        }

        h1, h2, h3 {
            color: var(--text) !important;
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -.035em;
        }

        h2 {
            font-size: clamp(1.8rem, 5vw, 2.45rem) !important;
        }

        p, li, .stCaption {
            color: var(--muted) !important;
        }

        .hero img {
            display: block;
            width: 100%;
            border-radius: 24px;
        }

        .section {
            margin: 2.45rem 0 1rem;
        }

        .eyebrow {
            color: var(--aqua);
            font-weight: 800;
            font-size: .74rem;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .glass-card,
        .selected-state {
            margin: 1rem 0;
            padding: 1.25rem;
            border: 1px solid var(--line);
            border-radius: 22px;
            background:
                linear-gradient(
                    135deg,
                    rgba(89, 232, 223, .09),
                    rgba(255, 255, 255, .025)
                ),
                var(--surface);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, .08),
                0 15px 32px rgba(0, 0, 0, .28);
        }

        .service {
            margin: .55rem 0;
            padding: .9rem 1rem;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: var(--field);
            color: var(--text);
            font-weight: 600;
        }

        .service span {
            color: var(--aqua);
        }

        /* Campos oscuros */
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        div[data-baseweb="input"] > div {
            background-color: var(--field) !important;
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
            border-radius: 13px !important;
            box-shadow: none !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        [data-testid="stTextInput"] input {
            min-height: 50px !important;
        }

        [data-testid="stTextArea"] textarea {
            min-height: 76px !important;
            max-height: 76px !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] *,
        [data-testid="stDateInput"] *,
        [data-testid="stTextInput"] *,
        [data-testid="stTextArea"] * {
            color: var(--text) !important;
            fill: var(--text) !important;
        }

        div[data-baseweb="popover"],
        ul[role="listbox"],
        [role="option"] {
            background: var(--field) !important;
            color: var(--text) !important;
        }

        [role="option"]:hover,
        [role="option"][aria-selected="true"] {
            background: #15232c !important;
        }

        div[data-testid="stWidgetLabel"] p {
            color: var(--muted) !important;
            font-weight: 600 !important;
        }

        /* Botones Liquid Glass */
        .stButton > button,
        .st-key-videollamada a {
            min-height: 58px !important;
            border: 1px solid #8edcff !important;
            border-radius: 999px !important;
            background:
                radial-gradient(
                    ellipse at 50% 0%,
                    rgba(184, 235, 255, .55),
                    transparent 45%
                ),
                linear-gradient(
                    180deg,
                    rgba(84, 112, 130, .78),
                    rgba(12, 18, 24, .91) 56%,
                    rgba(22, 54, 68, .72)
                ) !important;
            box-shadow:
                inset 0 1px 1px rgba(255, 255, 255, .82),
                inset 0 -1px 1px rgba(89, 232, 223, .45),
                0 0 17px rgba(65, 205, 255, .25),
                0 10px 20px rgba(0, 0, 0, .36) !important;
            color: var(--text) !important;
            font-family: "DM Sans", sans-serif !important;
            font-weight: 700 !important;
            text-shadow: 0 1px 8px rgba(0, 0, 0, .75) !important;
            transition: transform .18s ease, filter .18s ease !important;
        }

        .stButton > button:hover,
        .st-key-videollamada a:hover {
            transform: translateY(-2px);
            filter: brightness(1.14);
        }

        .st-key-videollamada a {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-decoration: none !important;
        }

        /* Los tres planes permanecen horizontales en móvil */
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"]:has(.st-key-plan_starter) {
                flex-wrap: nowrap !important;
                gap: .35rem !important;
            }

            [data-testid="stHorizontalBlock"]:has(.st-key-plan_starter)
            > [data-testid="stColumn"] {
                min-width: 0 !important;
                width: 33.333% !important;
                flex: 1 1 0 !important;
            }

            .st-key-plan_starter button,
            .st-key-plan_business button,
            .st-key-plan_premium button {
                min-height: 54px !important;
                padding: .25rem !important;
                font-size: .73rem !important;
                white-space: nowrap !important;
            }

            .block-container {
                padding-left: .78rem !important;
                padding-right: .78rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds).open_by_key(SHEET_ID).sheet1


def se_empalma(inicio_a, fin_a, inicio_b, fin_b):
    return inicio_a < fin_b and inicio_b < fin_a


def horarios_disponibles(fecha, duracion, giro):
    citas = []

    try:
        for fila in get_sheet().get_all_values()[1:]:
            if len(fila) >= 9 and fila[1] == giro and fila[6] == str(fecha):
                inicio = datetime.strptime(
                    f"{fila[6]} {fila[7]}",
                    "%Y-%m-%d %I:%M %p",
                )
                citas.append(
                    (inicio, inicio + timedelta(minutes=int(fila[5])))
                )
    except Exception:
        pass

    disponibles = []
    actual = datetime.combine(fecha, HORA_APERTURA)
    cierre = datetime.combine(fecha, HORA_CIERRE)
    comida_inicio = datetime.combine(fecha, COMIDA_INICIO)
    comida_fin = datetime.combine(fecha, COMIDA_FIN)

    while actual < cierre:
        fin = actual + timedelta(minutes=duracion)
        ocupado = any(
            se_empalma(actual, fin, inicio, termino)
            for inicio, termino in citas
        )

        if (
            fin <= cierre
            and not ocupado
            and not se_empalma(actual, fin, comida_inicio, comida_fin)
        ):
            disponibles.append(actual.strftime("%I:%M %p"))

        actual += timedelta(minutes=30)

    return disponibles


def duracion_legible(minutos):
    if minutos < 60:
        return f"{minutos} min"

    return "1 hora" if minutos == 60 else f"{minutos // 60} horas"


def crear_qr():
    qr = qrcode.QRCode(version=1, box_size=7, border=3)
    qr.add_data("https://kroniq-booking-demo.streamlit.app")
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="#59e8df", back_color="#091016")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def mostrar_experiencia():
    st.markdown(
        """
        <section class="section">
            <div class="eyebrow">Prueba la experiencia</div>
            <h2>Así se vería la agenda de tu negocio</h2>
            <p>Selecciona cada paso para probar el recorrido.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    giro = st.selectbox(
        "Tipo de negocio",
        list(NEGOCIOS),
        index=None,
        placeholder="Selecciona un tipo de negocio",
    )

    if not giro:
        st.info("Selecciona un tipo de negocio para continuar.")
        return

    servicios = NEGOCIOS[giro]

    st.markdown(
        f"""
        <div class="selected-state">
            Elegiste <b>{giro}</b>. Ahora selecciona el servicio.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Servicios disponibles")

    for nombre, minutos in servicios.items():
        st.markdown(
            f"""
            <div class="service">
                <span>{nombre}</span> · {duracion_legible(minutos)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    servicio = st.selectbox(
        "Servicio",
        list(servicios),
        index=None,
        placeholder="Selecciona un servicio",
    )

    if not servicio:
        st.info("Selecciona un servicio para ver horarios.")
        return

    duracion = servicios[servicio]

    fecha = st.date_input(
        "Fecha",
        min_value=date.today(),
        format="DD/MM/YYYY",
    )

    horas = horarios_disponibles(fecha, duracion, giro)

    if not horas:
        st.info("No hay horarios disponibles para este servicio en esta fecha.")
        return

    hora = st.selectbox(
        "Horario disponible",
        horas,
        index=None,
        placeholder="Selecciona una hora",
    )

    if not hora:
        st.info("Selecciona un horario para completar tus datos.")
        return

    st.markdown("### Crea una cita de prueba")

    nombre = st.text_input("Nombre completo")
    whatsapp = st.text_input("WhatsApp (10 dígitos)", max_chars=10)
    comentarios = st.text_area("Comentarios adicionales")

    datos_validos = bool(nombre.strip()) and whatsapp.isdigit() and len(whatsapp) == 10

    enviar = st.button(
        "Agendar cita de prueba",
        key="agendar_cita",
        use_container_width=True,
        disabled=not datos_validos,
    )

    if whatsapp and not (whatsapp.isdigit() and len(whatsapp) == 10):
        st.caption("El WhatsApp debe contener exactamente 10 números.")

    if enviar:
        if hora not in horarios_disponibles(fecha, duracion, giro):
            st.error("Ese horario acaba de ocuparse. Elige otro.")
            return

        try:
            get_sheet().append_row(
                [
                    datetime.now().strftime("%Y%m%d%H%M%S"),
                    giro,
                    nombre.strip(),
                    whatsapp.strip(),
                    servicio,
                    duracion,
                    str(fecha),
                    hora,
                    "Pendiente",
                    comentarios,
                    st.session_state.get("plan") or "Sin seleccionar",
                ]
            )
            st.success("Cita demo guardada correctamente.")
        except Exception:
            st.error("No fue posible guardar la cita. Intenta de nuevo más tarde.")


def mostrar_planes():
    st.markdown(
        """
        <section class="section">
            <div class="eyebrow">Soluciones para crecer</div>
            <h2>Descubre lo que KroniQ puede hacer por tu negocio</h2>
            <p>Conoce qué incluye cada nivel.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3, gap="small")

    with col1:
        if st.button(
            "Conoce Starter",
            key="plan_starter",
            use_container_width=True,
        ):
            st.session_state.plan = "Starter"

    with col2:
        if st.button(
            "Conoce Business",
            key="plan_business",
            use_container_width=True,
        ):
            st.session_state.plan = "Business"

    with col3:
        if st.button(
            "Conoce Premium",
            key="plan_premium",
            use_container_width=True,
        ):
            st.session_state.plan = "Premium"

    plan = st.session_state.get("plan")

    if not plan:
        st.info("Elige un plan para conocer sus beneficios.")
        return

    beneficios = "".join(
        f"<li>✓ {beneficio}</li>"
        for beneficio in PLANES[plan]
    )

    st.markdown(
        f"""
        <section class="glass-card">
            <div class="eyebrow">{plan}</div>
            <h3>Esto es lo que puedes lograr</h3>
            <ul>{beneficios}</ul>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if plan in ("Business", "Premium"):
        izquierda, derecha = st.columns(
            [1, 1.35],
            vertical_alignment="center",
        )

        with izquierda:
            st.image(
                crear_qr(),
                caption="Ejemplo de código QR",
                width=150,
            )

        with derecha:
            st.markdown(
                """
                <section class="glass-card">
                    <div class="eyebrow">Comparte tu agenda</div>
                    <h3>Imprime o publica tu código QR</h3>
                    <p>
                        Haz que tus clientes abran tu agenda y reserven
                        con facilidad.
                    </p>
                </section>
                """,
                unsafe_allow_html=True,
            )


def main():
    aplicar_estilos()
    st.session_state.setdefault("plan", None)

    hero = BASE_DIR / "hero-logo-kroniq.jpg"

    if hero.exists():
        st.markdown('<div class="hero">', unsafe_allow_html=True)
        st.image(str(hero), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    mostrar_experiencia()
    mostrar_planes()

    st.markdown(
        """
        <section class="section">
            <h2>¿Te imaginas esta agenda en tu negocio?</h2>
            <p>
                Vamos a conocernos y a diseñar una agenda para tu negocio.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    mensaje = quote(
        "Hola, me interesa conocer KroniQ Booking y me gustaría "
        "agendar una videollamada."
    )

    st.link_button(
        "Vamos a conocernos por videollamada",
        f"https://wa.me/{WHATSAPP_VENTAS}?text={mensaje}",
        key="videollamada",
        use_container_width=True,
    )

    st.caption("KroniQ Booking · Sincroniza tu tiempo, impulsa tu negocio.")


if __name__ == "__main__":
    main()
