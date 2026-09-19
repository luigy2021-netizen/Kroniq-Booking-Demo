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
    "Starter — $799 setup + $299/mes": (
        "Agenda personalizada con logo e imagen del negocio, bloqueo automático "
        "de empalmes, comentarios adicionales y confirmación automática por "
        "WhatsApp al crear una cita."
    ),
    "Business — $1,499 setup + $499/mes": (
        "Todo Starter + promociones por recomendación, código QR para compartir "
        "la agenda y un flyer promocional en el encabezado de la agenda."
    ),
    "Premium — $2,999 setup + $999/mes": (
        "Todo Business + dos flyers promocionales nuevos por mes, gestión de "
        "cancelaciones y ajustes de disponibilidad."
    ),
}

PLANES_CORTOS = {
    "Starter": "Starter — $799 setup + $299/mes",
    "Business": "Business — $1,499 setup + $499/mes",
    "Premium": "Premium — $2,999 setup + $999/mes",
}

DETALLES_PLAN = {
    "Starter": {
        "precio": "$799 setup + $299/mes",
        "color": "#2da9ff",
        "beneficios": [
            "Agenda personalizada con logo e imagen del negocio",
            "Bloqueo automático de empalmes",
            "Comentarios adicionales en cada reservación",
            "Confirmación automática por WhatsApp",
        ],
    },
    "Business": {
        "precio": "$1,499 setup + $499/mes",
        "color": "#53e0dc",
        "beneficios": [
            "Todo lo incluido en Starter",
            "Promociones por recomendación",
            "Código QR para compartir la agenda",
            "Un flyer promocional en el encabezado",
        ],
    },
    "Premium": {
        "precio": "$2,999 setup + $999/mes",
        "color": "#ff9a4d",
        "beneficios": [
            "Todo lo incluido en Business",
            "Dos flyers promocionales nuevos cada mes",
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
            --kb-bg: #07111f;
            --kb-bg-deep: #040a13;
            --kb-surface: rgba(13, 30, 51, .72);
            --kb-surface-soft: rgba(19, 43, 70, .58);
            --kb-border: rgba(160, 210, 255, .15);
            --kb-text: #f5f9ff;
            --kb-muted: #9db1c8;
            --kb-blue: #2da9ff;
            --kb-aqua: #53e0dc;
            --kb-orange: #ff8a3d;
            --kb-radius: 22px;
            --kb-shadow: 0 18px 48px rgba(0, 0, 0, .23);
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 4%, rgba(45, 169, 255, .16), transparent 27rem),
                radial-gradient(circle at 92% 18%, rgba(83, 224, 220, .10), transparent 25rem),
                linear-gradient(160deg, var(--kb-bg-deep), var(--kb-bg) 55%, #0a1b30);
            color: var(--kb-text);
            font-family: "DM Sans", sans-serif;
        }

        #MainMenu, footer, header { visibility: hidden; }
        .block-container {
            max-width: 1050px;
            padding: 1.2rem 1rem 4.5rem;
        }

        h1, h2, h3 {
            color: var(--kb-text) !important;
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -.035em;
        }

        h1 { font-size: clamp(2rem, 7vw, 4rem) !important; }
        h2 { font-size: clamp(1.4rem, 4vw, 2rem) !important; }
        h3 { font-size: 1.1rem !important; }

        p, label, .stCaption, .stMarkdown {
            color: var(--kb-muted);
        }

        .kb-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding: .75rem 1rem;
            border: 1px solid var(--kb-border);
            border-radius: 18px;
            background: rgba(11, 28, 48, .56);
            backdrop-filter: blur(16px);
        }

        .kb-brand {
            color: var(--kb-text);
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
        }

        .kb-brand span { color: var(--kb-aqua); }
        .kb-nav-copy { color: var(--kb-muted); font-size: .82rem; }

        .kb-hero {
            padding: clamp(1.5rem, 5vw, 3.25rem);
            margin: 1rem 0 1.25rem;
            border: 1px solid var(--kb-border);
            border-radius: 28px;
            background:
                linear-gradient(125deg, rgba(30, 90, 142, .30), rgba(10, 30, 51, .62)),
                var(--kb-surface);
            box-shadow: var(--kb-shadow);
            overflow: hidden;
        }

        .kb-eyebrow {
            color: var(--kb-aqua);
            font-size: .73rem;
            font-weight: 700;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .kb-hero p {
            max-width: 620px;
            font-size: 1.08rem;
            line-height: 1.6;
        }

        .kb-card {
            height: 100%;
            min-height: 126px;
            padding: 1.2rem;
            border: 1px solid var(--kb-border);
            border-radius: var(--kb-radius);
            background: var(--kb-surface-soft);
            box-shadow: 0 12px 32px rgba(0, 0, 0, .15);
            backdrop-filter: blur(15px);
            transition: transform .2s ease, border-color .2s ease;
        }

        .kb-card:hover {
            border-color: rgba(83, 224, 220, .35);
            transform: translateY(-2px);
        }

        .kb-metric-label {
            color: var(--kb-muted);
            font-size: .8rem;
            font-weight: 600;
        }

        .kb-metric {
            margin-top: .2rem;
            color: var(--kb-text);
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            font-weight: 700;
        }

        .kb-status {
            display: inline-block;
            margin-top: .55rem;
            padding: .25rem .55rem;
            border-radius: 999px;
            color: var(--kb-aqua);
            background: rgba(83, 224, 220, .12);
            font-size: .72rem;
            font-weight: 700;
        }

        .kb-plan {
            padding: 1.35rem 1.4rem;
            border: 1px solid var(--plan-color);
            border-radius: var(--kb-radius);
            background: linear-gradient(135deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
            box-shadow: var(--kb-shadow);
        }

        .kb-plan-tag {
            color: var(--plan-color);
            font-size: .73rem;
            font-weight: 700;
            letter-spacing: .12em;
        }

        .kb-plan-price {
            color: var(--plan-color);
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
        }

        .kb-plan ul {
            margin: .9rem 0 0;
            padding-left: 1.2rem;
            color: var(--kb-muted);
        }

        .kb-plan li { margin: .45rem 0; }

        .kb-section-label {
            margin: 2rem 0 .65rem;
            color: var(--kb-aqua);
            font-size: .74rem;
            font-weight: 700;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .kb-cta {
            padding: 1.35rem;
            border: 1px solid rgba(255, 138, 61, .42);
            border-radius: var(--kb-radius);
            background: linear-gradient(135deg, rgba(255, 138, 61, .15), rgba(45, 169, 255, .08));
        }

        .stButton > button, .stLinkButton > a {
            min-height: 46px;
            border: 0 !important;
            border-radius: 14px !important;
            background: linear-gradient(135deg, var(--kb-orange), #ffac50) !important;
            color: #17100a !important;
            font-weight: 800 !important;
            box-shadow: 0 8px 22px rgba(255, 138, 61, .22);
            transition: transform .16s ease, filter .16s ease;
        }

        .stButton > button:hover, .stLinkButton > a:hover {
            filter: brightness(1.06);
            transform: translateY(-1px);
        }

        .stButton > button:focus, .stLinkButton > a:focus,
        input:focus, textarea:focus {
            outline: 3px solid rgba(83, 224, 220, .7) !important;
            outline-offset: 2px;
        }

        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input {
            border-radius: 12px !important;
            border-color: var(--kb-border) !important;
            background: rgba(5, 16, 29, .7) !important;
            color: var(--kb-text) !important;
        }

        div[data-testid="stForm"] {
            padding: 1.1rem;
            border: 1px solid var(--kb-border);
            border-radius: var(--kb-radius);
            background: var(--kb-surface-soft);
        }

        div[role="radiogroup"] {
            gap: .45rem;
            padding: .3rem;
            border-radius: 14px;
            background: rgba(5, 16, 29, .4);
        }

        .stAlert {
            border-radius: 14px !important;
        }

        @media (max-width: 640px) {
            .block-container { padding: .85rem .8rem 5rem; }
            .kb-nav-copy { display: none; }
            .kb-hero { border-radius: 22px; }
            .kb-card { min-height: 110px; margin-bottom: .35rem; }
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
    imagen = qr.make_image(fill_color="#0b1523", back_color="white")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def obtener_filas():
    try:
        return get_sheet().get_all_values()
    except Exception:
        return []


def obtener_citas(fecha, giro):
    filas = obtener_filas()
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
            citas.append((inicio, inicio + timedelta(minutes=duracion)))
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


def obtener_resumen():
    filas = obtener_filas()
    hoy = str(date.today())
    citas_hoy = []
    pendientes = 0
    confirmadas = 0

    for fila in filas[1:]:
        if len(fila) < 9:
            continue

        if fila[6] == hoy:
            citas_hoy.append(fila)

            if fila[8].strip().lower() == "pendiente":
                pendientes += 1
            elif fila[8].strip().lower() == "confirmada":
                confirmadas += 1

    proxima = "Sin citas próximas"
    if citas_hoy:
        try:
            proxima_fila = sorted(
                citas_hoy,
                key=lambda fila: datetime.strptime(fila[7], "%I:%M %p"),
            )[0]
            proxima = f"{proxima_fila[4]} · {proxima_fila[7]}"
        except (ValueError, IndexError):
            pass

    return {
        "hoy": len(citas_hoy),
        "pendientes": pendientes,
        "confirmadas": confirmadas,
        "proxima": proxima,
    }


def mostrar_cta_video(plan_corto, ubicacion):
    mensaje = quote(
        f"Hola, me interesa KroniQ Booking. Estuve viendo el plan "
        f"{plan_corto} y me gustaría agendar una videollamada para "
        f"conocer los detalles."
    )

    st.markdown(
        """
        <div class="kb-cta">
            <div class="kb-eyebrow">Conversemos</div>
            <h3>¿Te gustó lo que viste? ¡Vamos a conocernos!</h3>
            <p>
                Agenda una videollamada breve y descubre cómo KroniQ Booking
                puede ayudar a impulsar tu negocio.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.link_button(
        "💻 Quiero agendar una videollamada",
        f"https://wa.me/{WHATSAPP_VENTAS}?text={mensaje}",
        use_container_width=True,
        key=f"video_{ubicacion}",
    )


aplicar_estilos()

st.markdown(
    """
    <div class="kb-nav">
        <div class="kb-brand">Kroni<span>Q</span> Booking</div>
        <div class="kb-nav-copy">Sincroniza tu tiempo, impulsa tu negocio.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    logo = Image.open("logo.png")
    st.image(logo, use_container_width=True)
except FileNotFoundError:
    pass

st.markdown(
    """
    <section class="kb-hero">
        <div class="kb-eyebrow">Agenda inteligente para negocios</div>
        <h1>Simplemente agenda.<br>KroniQ se encarga del resto.</h1>
        <p>
            Una experiencia de reservación clara, moderna y profesional para
            negocios que valoran su tiempo y el de sus clientes.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

resumen = obtener_resumen()

st.markdown('<div class="kb-section-label">Vista rápida de la agenda</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div class="kb-card">
            <div class="kb-metric-label">Citas de hoy</div>
            <div class="kb-metric">{resumen["hoy"]}</div>
            <span class="kb-status">Agenda activa</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="kb-card">
            <div class="kb-metric-label">Próxima cita</div>
            <div style="margin-top:.6rem;color:#f5f9ff;font-weight:700">
                {resumen["proxima"]}
            </div>
            <span class="kb-status">Hoy</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

col3, col4 = st.columns(2)

with col3:
    st.markdown(
        f"""
        <div class="kb-card">
            <div class="kb-metric-label">Confirmadas hoy</div>
            <div class="kb-metric">{resumen["confirmadas"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="kb-card">
            <div class="kb-metric-label">Pendientes hoy</div>
            <div class="kb-metric">{resumen["pendientes"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="kb-section-label">Explora los planes</div>', unsafe_allow_html=True)

plan_corto = st.radio(
    "Selecciona el plan que quieres conocer",
    list(PLANES_CORTOS.keys()),
    horizontal=True,
)

plan_interes = PLANES_CORTOS[plan_corto]
detalle_plan = DETALLES_PLAN[plan_corto]

beneficios_html = "".join(
    f"<li>✓ {beneficio}</li>"
    for beneficio in detalle_plan["beneficios"]
)

st.markdown(
    f"""
    <section class="kb-plan" style="--plan-color:{detalle_plan["color"]}">
        <div class="kb-plan-tag">DEMO ACTIVA</div>
        <h2 style="margin:.35rem 0">{plan_corto}</h2>
        <div class="kb-plan-price">{detalle_plan["precio"]}</div>
        <ul>{beneficios_html}</ul>
    </section>
    """,
    unsafe_allow_html=True,
)

mostrar_cta_video(plan_corto, "superior")

if plan_corto == "Starter":
    st.caption("Agenda esencial, clara y lista para recibir reservaciones.")

if plan_corto in ("Business", "Premium"):
    st.markdown(
        """
        <div class="kb-card" style="margin-top:1rem">
            <div class="kb-eyebrow">Promoción del mes</div>
            <h3>Agenda con un amigo y recibe un beneficio</h3>
            <p style="margin-bottom:0">
                Ejemplo de promoción visible en el encabezado de la agenda.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if plan_corto == "Premium":
    st.markdown('<div class="kb-section-label">Administración Premium</div>', unsafe_allow_html=True)

    accion_demo = st.selectbox(
        "Prueba una herramienta administrativa",
        [
            "Ver agenda activa",
            "Reprogramar una cita",
            "Cancelar una cita",
            "Bloquear vacaciones o día inhábil",
        ],
    )

    if accion_demo == "Reprogramar una cita":
        st.success("La cita puede moverse a otro horario disponible sin empalmes.")
    elif accion_demo == "Cancelar una cita":
        st.warning("La cita se cancela y el horario vuelve a quedar disponible.")
    elif accion_demo == "Bloquear vacaciones o día inhábil":
        st.date_input(
            "Fecha que se bloquearía",
            min_value=date.today(),
            key="fecha_bloqueo_demo",
        )
        st.info("En una implementación real, esa fecha dejaría de aceptar reservaciones.")

st.markdown('<div class="kb-section-label">Crea una cita de prueba</div>', unsafe_allow_html=True)

giro = st.selectbox("Tipo de negocio", list(NEGOCIOS.keys()))
servicios = NEGOCIOS[giro]

st.markdown("### Servicios disponibles")

for servicio_lista, duracion_lista in servicios.items():
    if duracion_lista < 60:
        texto_duracion = f"{duracion_lista} min"
    elif duracion_lista == 60:
        texto_duracion = "1 hr"
    else:
        texto_duracion = f"{duracion_lista // 60} hrs"

    st.caption(f"• {servicio_lista} · {texto_duracion}")

servicio = st.selectbox("Servicio", list(servicios.keys()))
duracion = servicios[servicio]
fecha = st.date_input("Fecha", min_value=date.today())
horas = horarios_disponibles(fecha, duracion, giro)

if not horas:
    st.warning("No hay horarios disponibles para este servicio en esta fecha.")
else:
    with st.form("formulario_demo", clear_on_submit=True):
        st.markdown("### Nueva cita")
        nombre = st.text_input("Nombre completo")
        whatsapp = st.text_input("WhatsApp (10 dígitos)", max_chars=10)
        hora = st.selectbox("Hora disponible", horas)
        comentarios = st.text_area("Comentarios adicionales")
        enviar = st.form_submit_button("Agendar cita demo", use_container_width=True)

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
                        plan_interes,
                    ]
                )

                st.success("✅ Cita demo guardada correctamente.")
                st.info(
                    f"Hola, {nombre}. Tu cita de {servicio} quedó agendada para "
                    f"el {fecha.strftime('%d/%m/%Y')} a las {hora}."
                )

                if plan_corto in ("Business", "Premium"):
                    st.success("También se generó una recomendación para compartir la agenda.")

            except Exception:
                st.error("No fue posible guardar la cita. Intenta de nuevo más tarde.")

st.markdown('<div class="kb-section-label">Comparte tu agenda</div>', unsafe_allow_html=True)

if plan_corto in ("Business", "Premium"):
    izquierda, derecha = st.columns([1, 1.45], vertical_alignment="center")

    with izquierda:
        st.image(
            crear_qr("https://kroniq-booking-demo.streamlit.app"),
            caption="QR de demostración",
            width=190,
        )

    with derecha:
        st.markdown(
            """
            <div class="kb-card">
                <div class="kb-eyebrow">Business y Premium</div>
                <h3>Tu agenda, lista para compartir</h3>
                <p style="margin-bottom:0">
                    Imprímela, publícala o envíala directamente a tus clientes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("El código QR para compartir la agenda está disponible a partir del plan Business.")

with st.expander("Comparar los tres planes"):
    for plan, descripcion in PLANES.items():
        st.markdown(f"**{plan}**")
        st.write(descripcion)

st.markdown("---")
mostrar_cta_video(plan_corto, "inferior")

st.caption("KroniQ Booking · Sincroniza tu tiempo, impulsa tu negocio.")
