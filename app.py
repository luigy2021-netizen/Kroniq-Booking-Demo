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
    "Barbería": {"Corte caballero": 30, "Barba": 30, "Corte + barba": 60, "Tinte caballero": 90},
    "Spa": {"Facial relajante": 60, "Masaje descontracturante": 90, "Depilación": 45, "Paquete spa": 120},
    "Médico": {"Consulta general": 30, "Primera valoración": 45, "Consulta de seguimiento": 30, "Revisión de estudios": 30},
    "Dentista": {"Valoración dental": 30, "Limpieza dental": 60, "Resina": 60, "Blanqueamiento": 90},
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


def url_imagen(nombre):
    imagen = imagen_base64(nombre)
    return f"data:image/png;base64,{imagen}" if imagen else ""


def aplicar_estilos():
    imagenes = {
        "plan_starter": url_imagen("Conoce-starter-kroniq.png"),
        "plan_business": url_imagen("Conoce-business-kroniq.png"),
        "plan_premium": url_imagen("Conoce-premium-kroniq.png"),
        "cita": url_imagen("agendar-cita-kroniq.png"),
        "videollamada": url_imagen("llamada-accion-kroniq.png"),
    }

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {{
            --black: #101010; --surface: #101820; --field: #091016;
            --white: #f5f8fc; --muted: #b9c5cf; --aqua: #59e8df;
            --line: rgba(151, 229, 255, .38);
        }}
        .stApp, .stAppViewContainer, [data-testid="stAppViewContainer"] {{
            background: var(--black) !important; color: var(--white) !important;
            font-family: "DM Sans", sans-serif;
        }}
        #MainMenu, footer, header {{ visibility: hidden; }}
        .block-container {{ max-width: 920px; padding: 1rem 1rem 4rem; }}
        h2, h3 {{ color: var(--white) !important; font-family: "Space Grotesk", sans-serif !important; letter-spacing: -.035em; }}
        h2 {{ font-size: clamp(1.8rem, 5vw, 2.45rem) !important; }}
        h3 {{ font-size: 1.4rem !important; }}
        p, li {{ color: var(--muted) !important; }}

        .hero {{ margin: 0 0 2.4rem; overflow: hidden; border-radius: 24px; background: #090909; }}
        .hero img {{ width: 100%; display: block; }}
        .eyebrow {{ color: var(--aqua); font-size: .74rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }}
        .section {{ margin: 2.6rem 0 1rem; }}
        .glass-card {{
            margin: 1rem 0; padding: 1.35rem; border: 1px solid var(--line); border-radius: 22px;
            background: linear-gradient(135deg, rgba(89,232,223,.09), rgba(255,255,255,.025)), var(--surface);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 16px 32px rgba(0,0,0,.28);
        }}
        .service {{ margin: .6rem 0; padding: .9rem 1rem; border: 1px solid var(--line); border-radius: 16px; background: var(--field); color: var(--white); font-weight: 600; }}
        .service span {{ color: var(--aqua); }}

        /* Ningún control de Streamlit queda blanco */
        div[data-testid="stForm"] {{ padding: 1.25rem; border: 1px solid var(--line); border-radius: 22px; background: var(--surface); }}
        .stSelectbox div[data-baseweb="select"] > div,
        .stDateInput div[data-baseweb="input"] > div,
        .stTextInput div[data-baseweb="input"] > div,
        .stTextInput input, .stDateInput input, .stTextArea textarea {{
            background: var(--field) !important; color: var(--white) !important;
            border: 1px solid var(--line) !important; border-radius: 13px !important;
            box-shadow: none !important;
        }}
        .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stTextInput input {{ min-height: 50px !important; }}
        .stTextArea textarea {{ min-height: 76px !important; max-height: 76px !important; }}
        [data-baseweb="select"] *, [data-baseweb="input"] *, .stTextArea textarea {{ color: var(--white) !important; fill: var(--white) !important; }}
        div[data-baseweb="popover"], ul[role="listbox"], [role="option"] {{ background: var(--field) !important; color: var(--white) !important; }}
        [role="option"]:hover {{ background: #15222a !important; }}
        div[data-testid="stWidgetLabel"] p {{ color: var(--muted) !important; font-weight: 600; }}

        /* Cada plan es UN botón: no hay enlace ni botón blanco adicional. */
        .st-key-plan_starter button, .st-key-plan_business button, .st-key-plan_premium button {{
            min-height: 0 !important; height: auto !important; aspect-ratio: 2.74 / 1 !important;
            padding: 0 !important; border: 0 !important; border-radius: 17px !important;
            background-color: #000 !important; background-position: center !important;
            background-size: 100% 100% !important; background-repeat: no-repeat !important;
            color: transparent !important; font-size: 0 !important; box-shadow: none !important;
            transition: transform .18s ease, filter .18s ease;
        }}
        .st-key-plan_starter button {{ background-image: url('{imagenes['plan_starter']}') !important; }}
        .st-key-plan_business button {{ background-image: url('{imagenes['plan_business']}') !important; }}
        .st-key-plan_premium button {{ background-image: url('{imagenes['plan_premium']}') !important; }}
        .st-key-plan_starter button:hover, .st-key-plan_business button:hover, .st-key-plan_premium button:hover {{ transform: translateY(-3px); filter: brightness(1.12); }}

        /* Botón de reserva: una sola imagen, sin texto nativo encima. */
        div[data-testid="stFormSubmitButton"] button {{
            height: 86px !important; padding: 0 !important; border: 0 !important; border-radius: 16px !important;
            background: #000 url('{imagenes['cita']}') center / 100% 100% no-repeat !important;
            color: transparent !important; font-size: 0 !important; box-shadow: none !important;
        }}
        .st-key-videollamada a {{
            display: block !important; height: 112px !important; padding: 0 !important; border: 0 !important; border-radius: 18px !important;
            background: #000 url('{imagenes['videollamada']}') center / 100% 100% no-repeat !important;
            color: transparent !important; font-size: 0 !important; box-shadow: none !important;
        }}
        .stAlert {{ background: #12272a !important; color: var(--white) !important; border-color: var(--line) !important; }}
        @media (max-width: 640px) {{
            .block-container {{ padding-left: .8rem; padding-right: .8rem; }}
            .st-key-videollamada a {{ height: 86px !important; }}
            div[data-testid="stFormSubmitButton"] button {{ height: 72px !important; }}
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
            if len(fila) >= 9 and fila[1] == giro and fila[6] == str(fecha):
                inicio = datetime.strptime(f"{fila[6]} {fila[7]}", "%Y-%m-%d %I:%M %p")
                citas.append((inicio, inicio + timedelta(minutes=int(fila[5]))))
    except Exception:
        pass

    disponibles, actual = [], datetime.combine(fecha, HORA_APERTURA)
    cierre = datetime.combine(fecha, HORA_CIERRE)
    comida_inicio, comida_fin = datetime.combine(fecha, COMIDA_INICIO), datetime.combine(fecha, COMIDA_FIN)
    while actual < cierre:
        fin = actual + timedelta(minutes=duracion)
        ocupado = any(se_empalma(actual, fin, inicio, termino) for inicio, termino in citas)
        if fin <= cierre and not ocupado and not se_empalma(actual, fin, comida_inicio, comida_fin):
            disponibles.append(actual.strftime("%I:%M %p"))
        actual += timedelta(minutes=30)
    return disponibles


def crear_qr():
    qr = qrcode.QRCode(version=1, box_size=7, border=3)
    qr.add_data("https://kroniq-booking-demo.streamlit.app")
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="#f5f8fc", back_color="#091016")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def duracion_legible(minutos):
    if minutos < 60:
        return f"{minutos} min"
    return "1 hora" if minutos == 60 else f"{minutos // 60} horas"


aplicar_estilos()
st.session_state.setdefault("plan", None)

hero = imagen_base64("hero-logo-kroniq.jpg")
if hero:
    st.markdown(f'<div class="hero"><img src="data:image/jpeg;base64,{hero}" alt="KroniQ Booking"></div>', unsafe_allow_html=True)

st.markdown('<section class="section"><div class="eyebrow">Prueba la experiencia</div><h2>Así se vería la agenda de tu negocio</h2><p>Elige un giro, selecciona un servicio y agenda una cita de prueba.</p></section>', unsafe_allow_html=True)
giro = st.selectbox("Tipo de negocio", list(NEGOCIOS))
servicios = NEGOCIOS[giro]
st.markdown("### Servicios disponibles")
for nombre, minutos in servicios.items():
    st.markdown(f'<div class="service"><span>{nombre}</span> · {duracion_legible(minutos)}</div>', unsafe_allow_html=True)

servicio = st.selectbox("Servicio", list(servicios))
duracion = servicios[servicio]
fecha = st.date_input("Fecha", min_value=date.today())
horas = horarios_disponibles(fecha, duracion, giro)

if horas:
    with st.form("cita", clear_on_submit=True):
        st.markdown("### Crea una cita de prueba")
        nombre = st.text_input("Nombre completo")
        whatsapp = st.text_input("WhatsApp (10 dígitos)", max_chars=10)
        hora = st.selectbox("Hora disponible", horas)
        comentarios = st.text_area("Comentarios adicionales")
        enviar = st.form_submit_button("Agendar cita de prueba", use_container_width=True)
    if enviar:
        if not nombre.strip():
            st.error("Escribe tu nombre.")
        elif len(whatsapp.strip()) != 10 or not whatsapp.strip().isdigit():
            st.error("El WhatsApp debe tener exactamente 10 dígitos.")
        elif hora not in horarios_disponibles(fecha, duracion, giro):
            st.error("Ese horario acaba de ocuparse. Elige otro.")
        else:
            try:
                get_sheet().append_row([datetime.now().strftime("%Y%m%d%H%M%S"), giro, nombre.strip(), whatsapp.strip(), servicio, duracion, str(fecha), hora, "Pendiente", comentarios, st.session_state.plan or "Sin seleccionar"])
                st.success("Cita demo guardada correctamente.")
            except Exception:
                st.error("No fue posible guardar la cita. Intenta de nuevo más tarde.")
else:
    st.warning("No hay horarios disponibles para este servicio en esta fecha.")

st.markdown('<section class="section"><div class="eyebrow">Soluciones para crecer</div><h2>Descubre lo que KroniQ puede hacer por tu negocio</h2></section>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="small")
with col1:
    if st.button("Conoce Starter", key="plan_starter", use_container_width=True):
        st.session_state.plan = "Starter"
with col2:
    if st.button("Conoce Business", key="plan_business", use_container_width=True):
        st.session_state.plan = "Business"
with col3:
    if st.button("Conoce Premium", key="plan_premium", use_container_width=True):
        st.session_state.plan = "Premium"

if st.session_state.plan:
    plan = st.session_state.plan
    beneficios = "".join(f"<li>✓ {beneficio}</li>" for beneficio in PLANES[plan])
    st.markdown(f'<section class="glass-card"><div class="eyebrow">{plan}</div><h3>Esto es lo que puedes lograr</h3><ul>{beneficios}</ul></section>', unsafe_allow_html=True)
    if plan in ("Business", "Premium"):
        izquierda, derecha = st.columns([1, 1.4], vertical_alignment="center")
        with izquierda:
            st.image(crear_qr(), caption="Ejemplo de código QR", width=150)
        with derecha:
            st.markdown('<section class="glass-card"><div class="eyebrow">Comparte tu agenda</div><h3>Imprime o publica tu código QR</h3><p>Haz que tus clientes abran tu agenda y reserven con facilidad.</p></section>', unsafe_allow_html=True)

st.markdown('<section class="section"><h2>¿Te imaginas esta agenda en tu negocio?</h2><p>Vamos a conocernos y a diseñar una agenda para tu negocio.</p></section>', unsafe_allow_html=True)
mensaje = quote("Hola, me interesa conocer KroniQ Booking y me gustaría agendar una videollamada.")
st.link_button("Vamos a conocernos por videollamada", f"https://wa.me/{WHATSAPP_VENTAS}?text={mensaje}", key="videollamada", use_container_width=True)
st.caption("KroniQ Booking · Sincroniza tu tiempo, impulsa tu negocio.")
