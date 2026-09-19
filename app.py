import io
from datetime import date, datetime, time, timedelta
from urllib.parse import quote

import gspread
import qrcode
import streamlit as st
from google.oauth2.service_account import Credentials
from PIL import Image

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
    "Starter": {
        "descripcion": "Lo esencial para comenzar a recibir citas con una imagen profesional.",
        "beneficios": [
            "Agenda personalizada con el logo de tu negocio",
            "Bloqueo automático de horarios empalmados",
            "Comentarios adicionales en cada reservación",
            "Confirmación de cita por WhatsApp",
        ],
    },
    "Business": {
        "descripcion": "Más herramientas para compartir tu agenda y atraer nuevos clientes.",
        "beneficios": [
            "Todo lo incluido en Starter",
            "Promociones por recomendación",
            "Código QR para compartir tu agenda",
            "Flyer promocional en el encabezado",
        ],
    },
    "Premium": {
        "descripcion": "Control avanzado para negocios que necesitan una operación más completa.",
        "beneficios": [
            "Todo lo incluido en Business",
            "Flyers promocionales nuevos cada mes",
            "Cancelación y reprogramación de citas",
            "Bloqueos por vacaciones o días inhábiles",
            "Administración avanzada de disponibilidad",
        ],
    },
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
            --carbon: #05080d;
            --carbon-soft: #09111b;
            --glass: rgba(20, 37, 54, 0.52);
            --glass-strong: rgba(23, 43, 62, 0.70);
            --glass-input: rgba(15, 29, 42, 0.78);
            --line: rgba(167, 218, 255, 0.20);
            --line-bright: rgba(178, 235, 255, 0.42);
            --white: #f7fbff;
            --muted: #b2c3d4;
            --aqua: #55e6df;
            --blue: #4c9eff;
            --radius: 22px;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 2%, rgba(65, 143, 214, .15), transparent 28rem),
                radial-gradient(circle at 98% 22%, rgba(61, 225, 217, .08), transparent 24rem),
                linear-gradient(145deg, #030609, var(--carbon) 45%, #06101a);
            color: var(--white);
            font-family: "DM Sans", sans-serif;
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            max-width: 920px;
            padding: 1.1rem 1rem 5rem;
        }

        h1, h2, h3 {
            color: var(--white) !important;
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -0.04em;
        }

        h1 {
            font-size: clamp(2.35rem, 8vw, 4.6rem) !important;
            line-height: 1.02 !important;
        }

        h2 {
            font-size: clamp(1.65rem, 5vw, 2.4rem) !important;
        }

        h3 {
            font-size: clamp(1.25rem, 4vw, 1.55rem) !important;
        }

        p, label, .stCaption, .stMarkdown {
            color: var(--muted);
            font-size: clamp(1rem, 2.5vw, 1.08rem);
        }

        .kb-glass {
            border: 1px solid var(--line);
            border-radius: var(--radius);
            background:
                linear-gradient(135deg, rgba(255,255,255,.10), rgba(255,255,255,.015)),
                var(--glass);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.09),
                0 18px 46px rgba(0,0,0,.25);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }

        .kb-logo-plaque {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 230px;
            padding: clamp(1rem, 4vw, 2.6rem);
            margin-bottom: 1.2rem;
            overflow: hidden;
        }

        .kb-logo-plaque img {
            width: min(100%, 700px);
            height: auto;
            object-fit: contain;
        }

        .kb-hero {
            padding: clamp(1.45rem, 5vw, 3rem);
            margin-bottom: 2rem;
        }

        .kb-eyebrow {
            color: var(--aqua);
            font-size: .78rem !important;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .kb-hero p {
            max-width: 650px;
            font-size: clamp(1.05rem, 3vw, 1.25rem);
            line-height: 1.6;
        }

        .kb-section {
            margin: 3.2rem 0 .9rem;
        }

        .kb-section-label {
            color: var(--aqua);
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .kb-section h2 {
            margin: .35rem 0 .5rem;
        }

        .kb-service {
            margin-bottom: .55rem;
            padding: .95rem 1rem;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: rgba(19, 36, 52, .42);
            color: var(--white);
            font-size: 1rem;
        }

        .kb-service span {
            color: var(--aqua);
            font-weight: 700;
        }

        .kb-plan-details {
            padding: 1.35rem;
            margin-top: .8rem;
        }

        .kb-plan-details p {
            font-size: 1.05rem;
            line-height: 1.55;
        }

        .kb-plan-details ul {
            margin: 1rem 0 0;
            padding-left: 1.15rem;
        }

        .kb-plan-details li {
            margin: .7rem 0;
            color: var(--white);
            font-size: 1rem;
        }

        .kb-video {
            padding: clamp(1.4rem, 4vw, 2.2rem);
            margin-top: 1rem;
            text-align: center;
        }

        .kb-video p {
            max-width: 560px;
            margin: .7rem auto 1.1rem;
            line-height: 1.55;
        }

        div[data-testid="stForm"] {
            margin-top: 1.2rem;
            padding: clamp(1rem, 4vw, 1.65rem);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            background:
                linear-gradient(135deg, rgba(255,255,255,.08), rgba(255,255,255,.01)),
                var(--glass-strong);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
            backdrop-filter: blur(20px);
        }

        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input {
            min-height: 54px !important;
            border: 1px solid var(--line-bright) !important;
            border-radius: 14px !important;
            background: var(--glass-input) !important;
            color: var(--white) !important;
            font-size: 1rem !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
        }

        .stTextArea textarea {
            min-height: 120px !important;
        }

        div[data-baseweb="select"] * {
            color: var(--white) !important;
        }

        label, div[data-testid="stWidgetLabel"] p {
            color: var(--white) !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
        }

        .stButton > button,
        .stLinkButton > a {
            width: 100%;
            min-height: 56px;
            margin-top: .35rem;
            border: 1px solid var(--line-bright) !important;
            border-radius: 16px !important;
            background:
                linear-gradient(135deg, rgba(114, 239, 232, .20), rgba(63, 136, 232, .16)),
                rgba(20, 43, 61, .72) !important;
            color: var(--white) !important;
            font-size: 1rem !important;
            font-weight: 800 !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.15),
                0 12px 28px rgba(0,0,0,.20);
            backdrop-filter: blur(18px);
            transition: transform .18s ease, border-color .18s ease, background .18s ease;
        }

        .stButton > button:hover,
        .stLinkButton > a:hover {
            border-color: var(--aqua) !important;
            background:
                linear-gradient(135deg, rgba(114, 239, 232, .30), rgba(63, 136, 232, .24)),
                rgba(20, 43, 61, .82) !important;
            transform: translateY(-1px);
        }

        .stButton > button:focus,
        .stLinkButton > a:focus,
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus {
            outline: 2px solid var(--aqua) !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 4px rgba(85, 230, 223, .14) !important;
        }

        .stAlert {
            border-radius: 16px !important;
            border: 1px solid var(--line) !important;
            background: rgba(17, 48, 53, .75) !important;
            color: var(--white) !important;
        }

        @media (max-width: 640px) {
            .block-container {
                padding: .8rem .8rem 4rem;
            }

            .kb-logo-plaque {
                min-height: 150px;
                border-radius: 18px;
            }

            .kb-hero, .kb-video {
                border-radius: 18px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes,
    )

    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1


def se_empalma(inicio1, fin1, inicio2, fin2):
    return inicio1 < fin2 and inicio2 < fin1


def formato_hora(dt):
    return dt.strftime("%I:%M %p")


def crear_qr(texto):
    qr = qrcode.QRCode(version=1, box_size=7, border=3)
    qr.add_data(texto)
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="#06101a", back_color="white")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def obtener_citas(fecha, giro):
    sheet = get_sheet()
    filas = sheet.get_all_values()
    citas = []

    for fila in filas[1:]:
        if len(fila) < 9:
            continue

        try:
            giro_cita = fila[1]
            duracion = int(fila[5])
            fecha_cita = fila[6]
            hora_cita = fila[7]

            if fecha_cita != str(fecha) or giro_cita != giro:
                continue

            inicio = datetime.strptime(
                f"{fecha_cita} {hora_cita}",
                "%Y-%m-%d %I:%M %p",
            )

            fin = inicio + timedelta(minutes=duracion)
            citas.append((inicio, fin))

        except (ValueError, IndexError):
            continue

    return citas


def horarios_disponibles(fecha, duracion, giro):
    disponibles = []
    citas = obtener_citas(fecha, giro)

    inicio_dia = datetime.combine(fecha, HORA_APERTURA)
    cierre_dia = datetime.combine(fecha, HORA_CIERRE)
    comida_inicio = datetime.combine(fecha, COMIDA_INICIO)
    comida_fin = datetime.combine(fecha, COMIDA_FIN)

    actual = inicio_dia

    while actual < cierre_dia:
        fin_servicio = actual + timedelta(minutes=duracion)

        if fin_servicio <= cierre_dia:
            choca_comida = se_empalma(
                actual,
                fin_servicio,
                comida_inicio,
                comida_fin,
            )

            choca_cita = any(
                se_empalma(actual, fin_servicio, cita_inicio, cita_fin)
                for cita_inicio, cita_fin in citas
            )

            if not choca_comida and not choca_cita:
                disponibles.append(formato_hora(actual))

        actual += timedelta(minutes=30)

    return disponibles


def mostrar_plan(nombre_plan):
    plan = PLANES[nombre_plan]

    beneficios_html = "".join(
        f"<li>✓ {beneficio}</li>"
        for beneficio in plan["beneficios"]
    )

    st.markdown(
        f"""
        <div class="kb-glass kb-plan-details">
            <div class="kb-eyebrow">{nombre_plan}</div>
            <h3>Esto es lo que puedes lograr</h3>
            <p>{plan["descripcion"]}</p>
            <ul>{beneficios_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if nombre_plan in ("Business", "Premium"):
        izquierda, derecha = st.columns([1, 1.4], vertical_alignment="center")

        with izquierda:
            st.image(
                crear_qr("https://kroniq-booking-demo.streamlit.app"),
                caption="Ejemplo de código QR para compartir la agenda",
                width=170,
            )

        with derecha:
            st.markdown(
                """
                <div class="kb-glass" style="padding:1.1rem">
                    <div class="kb-eyebrow">Comparte sin complicaciones</div>
                    <h3>Tu agenda llega a donde están tus clientes</h3>
                    <p style="margin-bottom:0">
                        Publica, imprime o envía tu código QR para que tus clientes
                        reserven desde cualquier dispositivo.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def mostrar_cta_video(plan_interes):
    mensaje = quote(
        "Hola, me interesa conocer KroniQ Booking. "
        f"Me llamó la atención la opción {plan_interes} y me gustaría "
        "agendar una videollamada."
    )

    st.markdown(
        """
        <div class="kb-glass kb-video">
            <div class="kb-eyebrow">El siguiente paso</div>
            <h2>¿Te imaginas esta agenda en tu negocio?</h2>
            <p>
                Vamos a conocernos y a diseñar una experiencia de reservación
                que se adapte a la manera en que trabajas.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.link_button(
        "Agendar una videollamada",
        f"https://wa.me/{WHATSAPP_VENTAS}?text={mensaje}",
        use_container_width=True,
    )


aplicar_estilos()

if "plan_interes" not in st.session_state:
    st.session_state.plan_interes = "KroniQ Booking"

st.markdown('<div class="kb-glass kb-logo-plaque">', unsafe_allow_html=True)

try:
    logo = Image.open("logo-kroniq-completo.png")
    st.image(logo, use_container_width=True)
except FileNotFoundError:
    st.markdown(
        """
        <div style="text-align:center">
            <div class="kb-eyebrow">KroniQ Booking</div>
            <h1 style="margin:.35rem 0">KroniQ Booking</h1>
            <p style="margin:0">Sincroniza tu tiempo, impulsa tu negocio.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <section class="kb-glass kb-hero">
        <div class="kb-eyebrow">Agenda inteligente para negocios</div>
        <h1>Simplemente agenda.<br>KroniQ se encarga del resto.</h1>
        <p>
            Descubre cómo una agenda digital puede hacer que tus clientes
            reserven con facilidad y que tu negocio se vea más profesional.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="kb-section">
        <div class="kb-section-label">Prueba la experiencia</div>
        <h2>Así se vería la agenda de tu negocio</h2>
        <p>Elige un giro, selecciona un servicio y agenda una cita de prueba.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

giro = st.selectbox("Tipo de negocio", list(NEGOCIOS.keys()))
servicios = NEGOCIOS[giro]

st.markdown("### Servicios disponibles")

for servicio_lista, duracion_lista in servicios.items():
    if duracion_lista < 60:
        texto_duracion = f"{duracion_lista} min"
    elif duracion_lista == 60:
        texto_duracion = "1 hora"
    else:
        texto_duracion = f"{duracion_lista // 60} horas"

    st.markdown(
        f"""
        <div class="kb-service">
            <span>{servicio_lista}</span> · {texto_duracion}
        </div>
        """,
        unsafe_allow_html=True,
    )

servicio = st.selectbox("Servicio", list(servicios.keys()))
duracion = servicios[servicio]
fecha = st.date_input("Fecha", min_value=date.today())
horas = horarios_disponibles(fecha, duracion, giro)

if not horas:
    st.warning("No hay horarios disponibles para este servicio en esta fecha.")

else:
    with st.form("formulario_demo", clear_on_submit=True):
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
        nombre = nombre.strip()
        whatsapp = whatsapp.strip()

        if not nombre:
            st.error("Escribe tu nombre.")

        elif len(whatsapp) != 10 or not whatsapp.isdigit():
            st.error("El WhatsApp debe tener exactamente 10 dígitos.")

        elif hora not in horarios_disponibles(fecha, duracion, giro):
            st.error("Ese horario acaba de ocuparse. Elige otro.")

        else:
            try:
                sheet = get_sheet()

                sheet.append_row(
                    [
                        datetime.now().strftime("%Y%m%d%H%M%S"),
                        giro,
                        nombre,
                        whatsapp,
                        servicio,
                        duracion,
                        str(fecha),
                        hora,
                        "Pendiente",
                        comentarios,
                        st.session_state.plan_interes,
                    ]
                )

                st.success(
                    f"Tu cita de prueba para {servicio} quedó guardada "
                    f"el {fecha.strftime('%d/%m/%Y')} a las {hora}."
                )

            except Exception:
                st.error(
                    "No fue posible guardar la cita. Intenta de nuevo más tarde."
                )

st.markdown(
    """
    <div class="kb-section">
        <div class="kb-section-label">Soluciones para crecer</div>
        <h2>Descubre lo que KroniQ puede hacer por tu negocio</h2>
        <p>
            Elige una opción para conocer las herramientas disponibles.
            La solución se adapta a lo que tu negocio necesita.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("Conoce Starter  +", use_container_width=True):
    st.session_state.plan_interes = "Starter"

if st.button("Conoce Business  +", use_container_width=True):
    st.session_state.plan_interes = "Business"

if st.button("Conoce Premium  +", use_container_width=True):
    st.session_state.plan_interes = "Premium"

if st.session_state.plan_interes in PLANES:
    mostrar_plan(st.session_state.plan_interes)

st.markdown("---")
mostrar_cta_video(st.session_state.plan_interes)

st.caption("KroniQ Booking · Sincroniza tu tiempo, impulsa tu negocio.")
