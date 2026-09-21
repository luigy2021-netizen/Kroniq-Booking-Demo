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
            --bg: #070b0f;
            --surface: rgba(18, 27, 35, .72);
            --surface-2: rgba(24, 35, 44, .86);
            --field: #0d141a;
            --text: #f4f8fb;
            --muted: #91a2ae;
            --aqua: #5de8df;
            --aqua-soft: rgba(93, 232, 223, .12);
            --line: rgba(255, 255, 255, .09);
            --line-active: rgba(93, 232, 223, .55);
        }

        .stApp,
        [data-testid="stAppViewContainer"],
        .main {
            background:
                radial-gradient(circle at 50% -10%, rgba(35, 116, 122, .16), transparent 34rem),
                var(--bg) !important;
            color: var(--text) !important;
            font-family: "DM Sans", sans-serif;
        }

        #MainMenu, footer, header { visibility: hidden; }

        .block-container {
            max-width: 760px;
            padding: .8rem 1rem 5rem !important;
        }

        h1, h2, h3 {
            color: var(--text) !important;
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -.035em;
        }

        h2 {
            font-size: clamp(1.75rem, 5vw, 2.35rem) !important;
            line-height: 1.08 !important;
            margin-bottom: .55rem !important;
        }

        h3 { margin-bottom: .4rem !important; }

        p, li, .stCaption { color: var(--muted) !important; }

        .hero img {
            display: block;
            width: 100%;
            border-radius: 26px;
            border: 1px solid var(--line);
            box-shadow: 0 24px 70px rgba(0,0,0,.34);
        }

        .section { margin: 2.7rem 0 1rem; }

        .eyebrow {
            color: var(--aqua);
            font-weight: 700;
            font-size: .72rem;
            letter-spacing: .13em;
            text-transform: uppercase;
            margin-bottom: .5rem;
        }

        .glass-card,
        .selected-state,
        .booking-summary {
            margin: .9rem 0;
            padding: 1.15rem 1.2rem;
            border: 1px solid var(--line);
            border-radius: 22px;
            background:
                linear-gradient(145deg, rgba(255,255,255,.055), rgba(255,255,255,.018)),
                var(--surface);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow: 0 18px 50px rgba(0,0,0,.20);
        }

        .selected-state {
            padding: .8rem 1rem;
            color: var(--muted);
            font-size: .92rem;
        }

        .selected-state b { color: var(--text); }

        .booking-summary strong { color: var(--text); }
        .booking-summary .accent { color: var(--aqua); }

        div[data-testid="stWidgetLabel"] p {
            color: var(--muted) !important;
            font-weight: 600 !important;
            font-size: .88rem !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        div[data-baseweb="input"] > div {
            background-color: var(--field) !important;
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
            border-radius: 15px !important;
            box-shadow: none !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        [data-testid="stTextInput"] input {
            min-height: 52px !important;
        }

        [data-testid="stTextArea"] textarea {
            min-height: 84px !important;
            max-height: 110px !important;
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
            background: #0d141a !important;
            color: var(--text) !important;
        }

        [role="option"]:hover,
        [role="option"][aria-selected="true"] {
            background: #162229 !important;
        }

        /* Botones: vidrio sobrio, sin glow excesivo */
        .stButton > button,
        .st-key-videollamada a {
            min-height: 54px !important;
            border: 1px solid var(--line) !important;
            border-radius: 16px !important;
            background:
                linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.025)),
                var(--surface-2) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.07),
                0 8px 24px rgba(0,0,0,.18) !important;
            color: var(--text) !important;
            font-family: "DM Sans", sans-serif !important;
            font-weight: 650 !important;
            transition: transform .16s ease, border-color .16s ease, background .16s ease !important;
        }

        .stButton > button:hover,
        .st-key-videollamada a:hover {
            transform: translateY(-1px);
            border-color: rgba(93,232,223,.35) !important;
            background:
                linear-gradient(180deg, rgba(93,232,223,.10), rgba(255,255,255,.025)),
                var(--surface-2) !important;
        }

        .stButton > button[kind="primary"] {
            border-color: var(--line-active) !important;
            background:
                linear-gradient(180deg, rgba(93,232,223,.22), rgba(93,232,223,.09)),
                #102328 !important;
            color: #ecfffd !important;
        }

        .st-key-videollamada a {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-decoration: none !important;
            border-radius: 999px !important;
        }

        /* Botones de servicio */
        [class*="st-key-servicio_"] button {
            min-height: 72px !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: .8rem 1rem !important;
        }

        /* Chips de horario */
        [class*="st-key-hora_"] button {
            min-height: 44px !important;
            border-radius: 999px !important;
            padding: .35rem .5rem !important;
            font-size: .86rem !important;
        }

        /* Avisos menos invasivos */
        [data-testid="stAlert"] {
            border-radius: 16px !important;
            border: 1px solid var(--line) !important;
            background: rgba(255,255,255,.035) !important;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-left: .78rem !important;
                padding-right: .78rem !important;
                padding-top: .45rem !important;
            }

            .hero img { border-radius: 20px; }
            .section { margin-top: 2.25rem; }

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
                min-height: 50px !important;
                padding: .25rem !important;
                font-size: .72rem !important;
                white-space: nowrap !important;
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
            <div class="eyebrow">Reserva en segundos</div>
            <h2>Así se sentiría reservar en tu negocio</h2>
            <p>Elige una opción y KroniQ te muestra únicamente el siguiente paso.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    giro = st.selectbox(
        "¿Qué tipo de negocio quieres probar?",
        list(NEGOCIOS),
        index=None,
        placeholder="Selecciona tu negocio",
        key="giro_demo",
    )

    if not giro:
        return

    # Si cambia el giro, limpiamos selecciones dependientes.
    if st.session_state.get("_ultimo_giro") != giro:
        st.session_state["_ultimo_giro"] = giro
        st.session_state["servicio_demo"] = None
        st.session_state["hora_demo"] = None

    servicios = NEGOCIOS[giro]

    st.markdown(
        f"""
        <div class="selected-state">
            <span class="accent">01</span> &nbsp; <b>{giro}</b> · Elige el servicio
        </div>
        """,
        unsafe_allow_html=True,
    )

    nombres = list(servicios.keys())
    for i in range(0, len(nombres), 2):
        cols = st.columns(2, gap="small")
        for j, nombre_servicio in enumerate(nombres[i:i + 2]):
            minutos = servicios[nombre_servicio]
            seleccionado = st.session_state.get("servicio_demo") == nombre_servicio
            etiqueta = f"{'✓  ' if seleccionado else ''}{nombre_servicio}\n{duracion_legible(minutos)}"
            with cols[j]:
                if st.button(
                    etiqueta,
                    key=f"servicio_{i+j}",
                    use_container_width=True,
                    type="primary" if seleccionado else "secondary",
                ):
                    st.session_state["servicio_demo"] = nombre_servicio
                    st.session_state["hora_demo"] = None
                    st.rerun()

    servicio = st.session_state.get("servicio_demo")
    if not servicio:
        return

    duracion = servicios[servicio]

    st.markdown(
        f"""
        <div class="selected-state">
            <span class="accent">02</span> &nbsp;
            <b>{servicio}</b> · {duracion_legible(duracion)} · Ahora elige el día
        </div>
        """,
        unsafe_allow_html=True,
    )

    fecha = st.date_input(
        "Fecha de la cita",
        min_value=date.today(),
        format="DD/MM/YYYY",
        key="fecha_demo",
    )

    fecha_key = str(fecha)
    if st.session_state.get("_ultima_fecha") != fecha_key:
        st.session_state["_ultima_fecha"] = fecha_key
        st.session_state["hora_demo"] = None

    horas = horarios_disponibles(fecha, duracion, giro)

    if not horas:
        st.warning("Ese día ya no tiene espacios disponibles. Prueba otra fecha.")
        return

    st.markdown(
        """
        <div class="selected-state">
            <span class="accent">03</span> &nbsp; Elige un horario disponible
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Horarios como chips: 3 por fila para que funcionen bien en móvil.
    for i in range(0, len(horas), 3):
        cols = st.columns(3, gap="small")
        for j, hora_opcion in enumerate(horas[i:i + 3]):
            seleccionado = st.session_state.get("hora_demo") == hora_opcion
            with cols[j]:
                if st.button(
                    f"{'✓ ' if seleccionado else ''}{hora_opcion}",
                    key=f"hora_{i+j}",
                    use_container_width=True,
                    type="primary" if seleccionado else "secondary",
                ):
                    st.session_state["hora_demo"] = hora_opcion
                    st.rerun()

    hora = st.session_state.get("hora_demo")
    if not hora:
        return

    fecha_legible = fecha.strftime("%d/%m/%Y")
    st.markdown(
        f"""
        <div class="booking-summary">
            <div class="eyebrow">Tu cita</div>
            <strong>{servicio}</strong><br>
            <span>{fecha_legible} · <span class="accent">{hora}</span> · {duracion_legible(duracion)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Solo faltan tus datos")

    nombre = st.text_input(
        "Nombre completo",
        placeholder="Tu nombre",
        key="nombre_demo",
    )
    whatsapp = st.text_input(
        "WhatsApp",
        max_chars=10,
        placeholder="10 dígitos",
        key="whatsapp_demo",
    )
    comentarios = st.text_area(
        "Comentarios (opcional)",
        placeholder="¿Hay algo que el negocio deba saber?",
        key="comentarios_demo",
    )

    datos_validos = bool(nombre.strip()) and whatsapp.isdigit() and len(whatsapp) == 10

    if whatsapp and not (whatsapp.isdigit() and len(whatsapp) == 10):
        st.caption("Ingresa los 10 números de tu WhatsApp.")

    enviar = st.button(
        "Confirmar mi cita",
        key="agendar_cita",
        use_container_width=True,
        disabled=not datos_validos,
        type="primary",
    )

    if enviar:
        # Validación final para evitar doble reserva.
        if hora not in horarios_disponibles(fecha, duracion, giro):
            st.error("Ese horario acaba de ocuparse. Elige otro disponible.")
            st.session_state["hora_demo"] = None
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

            st.success("¡Listo! Tu cita de prueba quedó confirmada.")
            st.markdown(
                f"""
                <div class="booking-summary">
                    <div class="eyebrow">Reserva confirmada</div>
                    <strong>{nombre.strip()}</strong><br>
                    <span>{servicio}</span><br>
                    <span>{fecha_legible} · <span class="accent">{hora}</span></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            st.error("No fue posible guardar la cita. Intenta nuevamente.")


def mostrar_planes():
    st.markdown(
        """
        <section class="section">
            <div class="eyebrow">Elige cómo crecer</div>
            <h2>Una agenda que crece con tu negocio</h2>
            <p>Empieza simple y activa más herramientas cuando las necesites.</p>
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
            <h2>Tu negocio. Tu marca. Tu agenda.</h2>
            <p>
                Convirtamos esta experiencia en la agenda digital de tu negocio.
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
