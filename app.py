import base64
import io
from datetime import date, datetime, time, timedelta
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


def imagen_base64(nombre):
    try:
        with open(nombre, "rb") as archivo:
            return base64.b64encode(archivo.read()).decode()
    except FileNotFoundError:
        return ""


def aplicar_estilos():
    boton_cita = imagen_base64("agendar-cita-kroniq.jpg")
    boton_starter = imagen_base64("Conoce-starter-kroniq.jpg")
    boton_business = imagen_base64("Conoce-business-kroniq.jpg")
    boton_premium = imagen_base64("Conoce-premium-kroniq.jpg")
    boton_llamada = imagen_base64("llamada-accion-kroniq.jpg")

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {{
            --black: #111111;
            --field: #0b1015;
            --white: #f8fbff;
            --muted: #c2ced8;
            --aqua: #59e8df;
            --line: rgba(151,229,255,.34);
        }}

        .stApp {{
            background: var(--black) !important;
            color: var(--white);
            font-family: "DM Sans", sans-serif;
        }}

        #MainMenu, footer, header {{
            visibility: hidden;
        }}

        .block-container {{
            max-width: 900px;
            padding: 1rem 1rem 5rem;
        }}

        h2, h3 {{
            color: var(--white) !important;
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -.04em;
        }}

        h2 {{
            font-size: clamp(1.8rem, 5vw, 2.4rem) !important;
        }}

        h3 {{
            font-size: clamp(1.3rem, 4vw, 1.55rem) !important;
        }}

        p, label {{
            color: var(--muted) !important;
            font-size: 1.05rem !important;
        }}

        .hero {{
            overflow: hidden;
            margin: 0 0 3rem;
            border-radius: 24px;
            box-shadow: 0 20px 45px rgba(0,0,0,.45);
        }}

        .hero img {{
            display: block;
            width: 100%;
            height: auto;
        }}

        .section {{
            margin: 3rem 0 1rem;
        }}

        .eyebrow {{
            color: var(--aqua);
            font-size: .82rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
        }}

        .glass-card {{
            padding: clamp(1.25rem, 4vw, 2rem);
            margin: 1rem 0;
            border: 1px solid var(--line);
            border-radius: 24px;
            background: linear-gradient(
                135deg,
                rgba(255,255,255,.10),
                rgba(255,255,255,.02)
            ), rgba(16,25,33,.84);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.14),
                        0 15px 34px rgba(0,0,0,.34);
        }}

        .service {{
            margin: .65rem 0;
            padding: 1rem 1.1rem;
            border: 1px solid var(--line);
            border-radius: 17px;
            background: var(--field);
            color: var(--white);
            font-size: 1.08rem;
            font-weight: 600;
        }}

        .service span {{
            color: var(--aqua);
        }}

        div[data-testid="stForm"] {{
            padding: 1.3rem;
            border: 1px solid var(--line);
            border-radius: 24px;
            background: rgba(16,25,33,.84);
        }}

        .stSelectbox [data-baseweb="select"] > div,
        .stSelectbox [role="combobox"],
        .stDateInput [data-baseweb="input"] > div,
        .stDateInput input,
        .stTextInput [data-baseweb="input"] > div,
        .stTextInput input,
        .stTextArea textarea {{
            background: var(--field) !important;
            background-color: var(--field) !important;
            color: var(--white) !important;
            border: 1px solid var(--line) !important;
            border-radius: 15px !important;
            box-shadow: none !important;
        }}

        .stSelectbox [data-baseweb="select"] > div,
        .stDateInput input,
        .stTextInput input {{
            min-height: 56px !important;
        }}

        .stTextArea textarea {{
            min-height: 82px !important;
            max-height: 82px !important;
        }}

        .stSelectbox [data-baseweb="select"] *,
        .stDateInput input,
        .stTextInput input,
        .stTextArea textarea {{
            color: var(--white) !important;
            fill: var(--white) !important;
        }}

        div[data-testid="stWidgetLabel"] p {{
            color: var(--white) !important;
            font-size: 1.04rem !important;
            font-weight: 600 !important;
        }}

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus,
        .stSelectbox [role="combobox"]:focus-within {{
            border-color: var(--aqua) !important;
            box-shadow: 0 0 0 3px rgba(89,232,223,.14) !important;
        }}

        div[data-testid="stFormSubmitButton"] button {{
            min-height: 86px !important;
            border: 0 !important;
            border-radius: 18px !important;
            background: url("data:image/jpeg;base64,{boton_cita}") center / 100% 100% !important;
            color: transparent !important;
            font-size: 0 !important;
            box-shadow: none !important;
        }}

        .st-key-plan_starter button,
        .st-key-plan_business button,
        .st-key-plan_premium button {{
            width: 100% !important;
            min-height: 96px !important;
            border: 0 !important;
            border-radius: 15px !important;
            color: transparent !important;
            font-size: 0 !important;
            box-shadow: none !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-size: 100% 100% !important;
        }}

        .st-key-plan_starter button {{
            background-image: url("data:image/jpeg;base64,{boton_starter}") !important;
        }}

        .st-key-plan_business button {{
            background-image: url("data:image/jpeg;base64,{boton_business}") !important;
        }}

        .st-key-plan_premium button {{
            background-image: url("data:image/jpeg;base64,{boton_premium}") !important;
        }}

        .st-key-video_link a {{
            width: 100% !important;
            min-height: 105px !important;
            border: 0 !important;
            border-radius: 18px !important;
            background: url("data:image/jpeg;base64,{boton_llamada}") center / 100% 100% !important;
            color: transparent !important;
            font-size: 0 !important;
            box-shadow: none !important;
        }}

        .stAlert {{
            border-radius: 16px !important;
            background: rgba(10,48,50,.9) !important;
            color: var(--white) !important;
        }}

        @media(max-width:640px) {{
            .block-container {{
                padding: .8rem .8rem 4rem;
            }}

            .st-key-plan_starter button,
            .st-key-plan_business button,
            .st-key-plan_premium button {{
                min-height: 82px !important;
            }}
        }}
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


def se_empalma(inicio1, fin1, inicio2, fin2):
    return inicio1 < fin2 and inicio2 < fin1


def horarios_disponibles(fecha, duracion, giro):
    citas = []

    try:
        for fila in get_sheet().get_all_values()[1:]:
            if len(fila) < 9 or fila[1] != giro or fila[6] != str(fecha):
                continue

            inicio = datetime.strptime(
                f"{fila[6]} {fila[7]}",
                "%Y-%m-%d %I:%M %p",
            )

            citas.append((inicio, inicio + timedelta(minutes=int(fila[5]))))
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


def crear_qr():
    qr = qrcode.QRCode(version=1, box_size=7, border=3)
    qr.add_data("https://kroniq-booking-demo.streamlit.app")
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="#07111c", back_color="white")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


aplicar_estilos()

if "plan" not in st.session_state:
    st.session_state.plan = None

hero = imagen_base64("hero-logo-kroniq.jpg")

if hero:
    st.markdown(
        f"""
        <div class="hero">
            <img src="data:image/jpeg;base64,{hero}" alt="KroniQ Booking">
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <section class="section">
        <div class="eyebrow">Prueba la experiencia</div>
        <h2>Así se vería la agenda de tu negocio</h2>
        <p>Elige un giro, selecciona un servicio y agenda una cita de prueba.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

giro = st.selectbox("Tipo de negocio", list(NEGOCIOS.keys()))
servicios = NEGOCIOS[giro]

st.markdown("### Servicios disponibles")

for nombre, minutos in servicios.items():
    if minutos < 60:
        texto_duracion = f"{minutos} min"
    elif minutos == 60:
        texto_duracion = "1 hora"
    else:
        texto_duracion = f"{minutos // 60} horas"

    st.markdown(
        f'<div class="service"><span>{nombre}</span> · {texto_duracion}</div>',
        unsafe_allow_html=True,
    )

servicio = st.selectbox("Servicio", list(servicios.keys()))
duracion = servicios[servicio]
fecha = st.date_input("Fecha", min_value=date.today())
horas = horarios_disponibles(fecha, duracion, giro)

if not horas:
    st.warning("No hay horarios disponibles para este servicio en esta fecha.")

else:
    with st.form("cita", clear_on_submit=True):
        st.markdown("### Crea una cita de prueba")

        nombre = st.text_input("Nombre completo")
        whatsapp = st.text_input("WhatsApp (10 dígitos)", max_chars=10)
        hora = st.selectbox("Hora disponible", horas)
        comentarios = st.text_area("Comentarios adicionales")

        enviar = st.form_submit_button(
            "Agendar cita de prueba",
            use_container_width=True,
        )

    if enviar:
        if not nombre.strip():
            st.error("Escribe tu nombre.")

        elif len(whatsapp.strip()) != 10 or not whatsapp.strip().isdigit():
            st.error("El WhatsApp debe tener exactamente 10 dígitos.")

        elif hora not in horarios_disponibles(fecha, duracion, giro):
            st.error("Ese horario acaba de ocuparse. Elige otro.")

        else:
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
                        st.session_state.plan or "Sin seleccionar",
                    ]
                )

                st.success("Cita demo guardada correctamente.")

            except Exception:
                st.error(
                    "No fue posible guardar la cita. Intenta de nuevo más tarde."
                )

st.markdown(
    """
    <section class="section">
        <div class="eyebrow">Soluciones para crecer</div>
        <h2>Descubre lo que KroniQ puede hacer por tu negocio</h2>
    </section>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("", key="plan_starter", use_container_width=True):
        st.session_state.plan = "Starter"

with col2:
    if st.button("", key="plan_business", use_container_width=True):
        st.session_state.plan = "Business"

with col3:
    if st.button("", key="plan_premium", use_container_width=True):
        st.session_state.plan = "Premium"

if st.session_state.plan:
    beneficios = "".join(
        f"<li>✓ {beneficio}</li>"
        for beneficio in PLANES[st.session_state.plan]
    )

    st.markdown(
        f"""
        <section class="glass-card">
            <div class="eyebrow">{st.session_state.plan}</div>
            <h3>Esto es lo que puedes lograr</h3>
            <ul style="line-height:1.8;color:#f8fbff;font-size:1.08rem">
                {beneficios}
            </ul>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.plan in ("Business", "Premium"):
        izquierda, derecha = st.columns([1, 1.3], vertical_alignment="center")

        with izquierda:
            st.image(crear_qr(), caption="Ejemplo de código QR", width=170)

        with derecha:
            st.markdown(
                """
                <section class="glass-card">
                    <div class="eyebrow">Comparte tu agenda</div>
                    <h3>Imprime o publica tu código QR</h3>
                    <p>Haz que tus clientes abran tu agenda y reserven con facilidad.</p>
                </section>
                """,
                unsafe_allow_html=True,
            )

mensaje = quote(
    "Hola, me interesa conocer KroniQ Booking y me gustaría agendar una videollamada."
)

st.link_button(
    "",
    f"https://wa.me/{WHATSAPP_VENTAS}?text={mensaje}",
    use_container_width=True,
    key="video_link",
)

st.caption("KroniQ Booking · Sincroniza tu tiempo, impulsa tu negocio.")
