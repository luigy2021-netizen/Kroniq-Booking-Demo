import base64
import io
from datetime import date, datetime, time, timedelta
from urllib.parse import quote

import gspread
import qrcode
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config("KroniQ Booking", "🔷", layout="centered")

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
        "Agenda personalizada con la imagen de tu negocio",
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
    fondo = imagen_base64("fondo-kroniq.jpg")

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {{
            --white:#f8fbff;
            --muted:#c6d3df;
            --aqua:#5be8df;
            --line:rgba(202,239,255,.30);
            --glass:rgba(12,24,37,.54);
            --glass-deep:rgba(7,15,24,.72);
        }}

        .stApp {{
            background:
                linear-gradient(rgba(2,5,9,.60), rgba(2,5,9,.76)),
                url("data:image/jpeg;base64,{fondo}") center top / cover fixed;
            color:var(--white);
            font-family:"DM Sans",sans-serif;
        }}

        #MainMenu, footer, header {{ visibility:hidden; }}
        .block-container {{ max-width:880px; padding:1rem 1rem 5rem; }}

        h1,h2,h3 {{
            color:var(--white)!important;
            font-family:"Space Grotesk",sans-serif!important;
            letter-spacing:-.04em;
        }}

        h1 {{ font-size:clamp(2.25rem,8vw,4.2rem)!important; line-height:1.04!important; }}
        h2 {{ font-size:clamp(1.7rem,5vw,2.4rem)!important; }}
        h3 {{ font-size:clamp(1.25rem,4vw,1.55rem)!important; }}
        p,label {{ color:var(--muted)!important; font-size:1.05rem!important; }}

        .glass {{
            border:1px solid var(--line);
            border-radius:24px;
            background:
                linear-gradient(135deg,rgba(255,255,255,.16),rgba(255,255,255,.025)),
                var(--glass);
            box-shadow:inset 0 1px 0 rgba(255,255,255,.18),0 18px 40px rgba(0,0,0,.30);
            backdrop-filter:blur(24px) saturate(135%);
            -webkit-backdrop-filter:blur(24px) saturate(135%);
        }}

        .hero {{
            overflow:hidden;
            margin:0 0 2.5rem;
            border-radius:26px;
            border:1px solid rgba(206,241,255,.27);
            box-shadow:0 22px 48px rgba(0,0,0,.42);
        }}

        .hero img {{ display:block; width:100%; height:auto; }}

        .intro,.form-card,.plan-card,.video-card {{
            padding:clamp(1.3rem,4vw,2.4rem);
            margin:1rem 0;
        }}

        .eyebrow {{
            color:var(--aqua);
            font-size:.80rem;
            font-weight:800;
            letter-spacing:.13em;
            text-transform:uppercase;
        }}

        .section {{ margin:3.3rem 0 1rem; }}
        .section p {{ line-height:1.6; }}

        .service {{
            margin:.65rem 0;
            padding:1rem 1.1rem;
            border:1px solid var(--line);
            border-radius:17px;
            background:rgba(9,21,32,.48);
            color:var(--white);
            font-size:1.08rem;
            font-weight:600;
            backdrop-filter:blur(18px);
        }}

        .service span {{ color:var(--aqua); }}

        div[data-testid="stForm"] {{
            padding:1.25rem;
            border:1px solid var(--line);
            border-radius:24px;
            background:linear-gradient(135deg,rgba(255,255,255,.12),rgba(255,255,255,.02)),var(--glass);
            backdrop-filter:blur(24px);
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input {{
            min-height:56px!important;
            border:1px solid rgba(210,242,255,.38)!important;
            border-radius:15px!important;
            background:rgba(5,14,23,.72)!important;
            color:var(--white)!important;
            font-size:1.05rem!important;
        }}

        .stTextArea textarea {{ min-height:118px!important; }}
        div[data-baseweb="select"] * {{ color:var(--white)!important; }}
        div[data-testid="stWidgetLabel"] p {{ color:var(--white)!important; font-size:1.03rem!important; font-weight:600!important; }}

        .stButton > button,.stLinkButton > a {{
            min-height:58px;
            border:1px solid rgba(191,244,255,.48)!important;
            border-radius:17px!important;
            background:linear-gradient(135deg,rgba(112,239,232,.30),rgba(66,139,235,.24)),rgba(8,26,41,.68)!important;
            color:var(--white)!important;
            font-size:1.08rem!important;
            font-weight:800!important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.22),0 12px 26px rgba(0,0,0,.24);
            backdrop-filter:blur(22px);
        }}

        .stButton > button:hover,.stLinkButton > a:hover {{
            border-color:var(--aqua)!important;
            transform:translateY(-1px);
        }}

        .stAlert {{
            border-radius:16px!important;
            background:rgba(12,48,54,.82)!important;
            color:var(--white)!important;
        }}

        @media(max-width:640px) {{
            .block-container {{ padding:.75rem .8rem 4rem; }}
            .hero {{ border-radius:18px; }}
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
            inicio = datetime.strptime(f"{fila[6]} {fila[7]}", "%Y-%m-%d %I:%M %p")
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
        ocupado = any(se_empalma(actual, fin, inicio, termino) for inicio, termino in citas)

        if fin <= cierre and not ocupado and not se_empalma(actual, fin, comida_inicio, comida_fin):
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
        f'<div class="hero"><img src="data:image/jpeg;base64,{hero}" alt="KroniQ Booking"></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <section class="glass intro">
        <div class="eyebrow">Agenda inteligente para negocios</div>
        <h1>Simplemente agenda.<br>KroniQ se encarga del resto.</h1>
        <p>Descubre una experiencia de reservación clara, moderna y profesional para tus clientes.</p>
    </section>
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

giro = st.selectbox("Tipo de negocio", list(NEGOCIOS))
servicios = NEGOCIOS[giro]

st.markdown("### Servicios disponibles")

for nombre, minutos in servicios.items():
    duracion_texto = "1 hora" if minutos == 60 else f"{minutos} min" if minutos < 60 else f"{minutos // 60} horas"
    st.markdown(f'<div class="service"><span>{nombre}</span> · {duracion_texto}</div>', unsafe_allow_html=True)

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
                get_sheet().append_row([
                    datetime.now().strftime("%Y%m%d%H%M%S"), giro, nombre.strip(),
                    whatsapp.strip(), servicio, duracion, str(fecha), hora,
                    "Pendiente", comentarios, st.session_state.plan or "Sin seleccionar",
                ])
                st.success(f"Tu cita de prueba para {servicio} quedó guardada para el {fecha.strftime('%d/%m/%Y')} a las {hora}.")
            except Exception:
                st.error("No fue posible guardar la cita. Intenta de nuevo más tarde.")
else:
    st.warning("No hay horarios disponibles para este servicio en esta fecha.")

st.markdown(
    """
    <section class="section">
        <div class="eyebrow">Soluciones para crecer</div>
        <h2>Descubre lo que KroniQ puede hacer por tu negocio</h2>
        <p>Conoce las herramientas disponibles para cada etapa de tu negocio.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

for nombre_plan in PLANES:
    if st.button(f"Conoce {nombre_plan}  +", use_container_width=True, key=nombre_plan):
        st.session_state.plan = nombre_plan

if st.session_state.plan:
    beneficios = "".join(f"<li>✓ {beneficio}</li>" for beneficio in PLANES[st.session_state.plan])
    st.markdown(
        f"""
        <section class="glass plan-card">
            <div class="eyebrow">{st.session_state.plan}</div>
            <h3>Esto es lo que puedes lograr</h3>
            <ul style="line-height:1.7;color:#f8fbff;font-size:1.05rem">{beneficios}</ul>
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
                <section class="glass plan-card">
                    <div class="eyebrow">Comparte tu agenda</div>
                    <h3>Imprime o publica tu código QR</h3>
                    <p>Haz que tus clientes abran tu agenda y reserven con facilidad.</p>
                </section>
                """,
                unsafe_allow_html=True,
            )

mensaje = quote(
    "Hola, me interesa conocer KroniQ Booking. "
    f"Me llamó la atención {st.session_state.plan or 'la demo'} y me gustaría agendar una videollamada."
)

st.markdown(
    """
    <section class="glass video-card">
        <div class="eyebrow">El siguiente paso</div>
        <h2>¿Te imaginas esta agenda en tu negocio?</h2>
        <p>Vamos a conocernos y a diseñar una experiencia de reservación para tu negocio.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.link_button(
    "Agendar una videollamada",
    f"https://wa.me/{WHATSAPP_VENTAS}?text={mensaje}",
    use_container_width=True,
)

st.caption("KroniQ Booking · Sincroniza tu tiempo, impulsa tu negocio.")
