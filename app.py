import io
import hmac
from html import escape
from datetime import date, datetime, time, timedelta
from pathlib import Path
from urllib.parse import quote

import gspread
import qrcode
import streamlit as st
from google.oauth2.service_account import Credentials


# =====================================================
# CONFIGURACION GENERAL
# =====================================================

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

COLUMNAS_CITAS = [
    "id",
    "giro",
    "nombre",
    "whatsapp",
    "servicio",
    "duracion",
    "fecha",
    "hora",
    "estado",
    "comentarios",
    "plan",
]


# =====================================================
# ESTILOS
# =====================================================

def aplicar_estilos():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --bg: #070b0f;
        --surface: rgba(18,27,35,.85);
        --surface-2: rgba(24,35,44,.95);
        --field: #0d141a;
        --text: #f4f8fb;
        --muted: #91a2ae;
        --aqua: #5de8df;
        --line: rgba(255,255,255,.09);
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    .main {
        background:
            radial-gradient(
                circle at 50% -10%,
                rgba(35,116,122,.16),
                transparent 34rem
            ),
            var(--bg) !important;
        color: var(--text) !important;
        font-family: "DM Sans", sans-serif;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

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
        font-size: clamp(1.75rem,5vw,2.35rem) !important;
        line-height: 1.08 !important;
    }

    p, li, .stCaption {
        color: var(--muted) !important;
    }

    .hero img {
        display: block;
        width: 100%;
        border-radius: 26px;
        border: 1px solid var(--line);
        box-shadow: 0 24px 70px rgba(0,0,0,.34);
    }

    .section {
        margin: 2.7rem 0 1rem;
    }

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
        background: var(--surface);
        box-shadow: 0 18px 50px rgba(0,0,0,.20);
    }

    .selected-state {
        padding: .8rem 1rem;
        color: var(--muted);
        font-size: .92rem;
    }

    .selected-state b,
    .booking-summary strong {
        color: var(--text);
    }

    .accent {
        color: var(--aqua);
    }

    div[data-testid="stWidgetLabel"] p {
        color: var(--muted) !important;
        font-weight: 600 !important;
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

    .stButton > button {
        min-height: 54px !important;
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
        background: var(--surface-2) !important;
        color: var(--text) !important;
        font-family: "DM Sans", sans-serif !important;
        font-weight: 650 !important;
    }

    .stButton > button:hover {
        border-color: rgba(93,232,223,.35) !important;
    }

    .stButton > button[kind="primary"] {
        border-color: rgba(93,232,223,.55) !important;
        background: #102328 !important;
        color: #ecfffd !important;
    }

    [class*="st-key-servicio_"] button {
        min-height: 72px !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    [class*="st-key-hora_"] button {
        min-height: 44px !important;
        border-radius: 999px !important;
        font-size: .86rem !important;
    }

    [data-testid="stAlert"] {
        border-radius: 16px !important;
        border: 1px solid var(--line) !important;
        background: rgba(255,255,255,.035) !important;
    }

    .owner-header {
        padding: 1rem 0 .35rem;
    }

    .owner-header h1 {
        margin: 0 !important;
        font-size: clamp(2rem,8vw,3rem) !important;
    }

    .metric-card {
        min-height: 112px;
        padding: 1rem;
        border: 1px solid var(--line);
        border-radius: 20px;
        background: var(--surface);
    }

    .metric-card .value {
        color: var(--text);
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.9rem;
        font-weight: 700;
    }

    .metric-card .label {
        color: var(--muted);
        font-size: .8rem;
    }

    .appointment-card {
        margin: .65rem 0;
        padding: .9rem 1rem;
        border-left: 3px solid var(--aqua);
        border-radius: 0 16px 16px 0;
        background: rgba(255,255,255,.035);
    }

    .appointment-card strong {
        color: var(--text);
    }

    .appointment-card .meta {
        color: var(--muted);
        font-size: .84rem;
    }

    @media (max-width: 640px) {
        .block-container {
            padding-left: .78rem !important;
            padding-right: .78rem !important;
        }

        .hero img {
            border-radius: 20px;
        }

        [class*="st-key-plan_"] button {
            min-height: 50px !important;
            padding: .25rem !important;
            font-size: .72rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


# =====================================================
# GOOGLE SHEETS
# =====================================================

@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds).open_by_key(SHEET_ID).sheet1


def texto_seguro(valor):
    return escape(str(valor or "").strip())


def obtener_citas():
    filas = get_sheet().get_all_values()[1:]
    citas = []

    for fila in filas:
        if not any(str(v).strip() for v in fila):
            continue

        valores = list(fila[:len(COLUMNAS_CITAS)])
        valores.extend([""] * (len(COLUMNAS_CITAS) - len(valores)))
        cita = dict(zip(COLUMNAS_CITAS, valores))

        try:
            cita["inicio"] = datetime.strptime(
                f"{cita['fecha']} {cita['hora']}",
                "%Y-%m-%d %I:%M %p",
            )
        except (TypeError, ValueError):
            cita["inicio"] = None

        try:
            cita["duracion_min"] = int(cita["duracion"])
        except (TypeError, ValueError):
            cita["duracion_min"] = 0

        citas.append(cita)

    return citas


def se_empalma(inicio_a, fin_a, inicio_b, fin_b):
    return inicio_a < fin_b and inicio_b < fin_a


def horarios_disponibles(fecha, duracion, giro):
    citas = []
    filas = get_sheet().get_all_values()[1:]

    for fila in filas:
        if (
            len(fila) >= 9
            and fila[1] == giro
            and fila[6] == str(fecha)
            and fila[8].strip().lower() != "cancelada"
        ):
            try:
                inicio = datetime.strptime(
                    f"{fila[6]} {fila[7]}",
                    "%Y-%m-%d %I:%M %p",
                )
                citas.append(
                    (inicio, inicio + timedelta(minutes=int(fila[5])))
                )
            except (ValueError, TypeError):
                continue

    disponibles = []
    actual = datetime.combine(fecha, HORA_APERTURA)
    cierre = datetime.combine(fecha, HORA_CIERRE)
    comida_inicio = datetime.combine(fecha, COMIDA_INICIO)
    comida_fin = datetime.combine(fecha, COMIDA_FIN)
    ahora = datetime.now()

    while actual < cierre:
        fin = actual + timedelta(minutes=duracion)

        ocupado = any(
            se_empalma(actual, fin, inicio, termino)
            for inicio, termino in citas
        )

        if (
            fin <= cierre
            and actual > ahora
            and not ocupado
            and not se_empalma(
                actual, fin, comida_inicio, comida_fin
            )
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

    imagen = qr.make_image(
        fill_color="#59e8df",
        back_color="#091016",
    )
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# =====================================================
# AGENDA PUBLICA
# =====================================================

def mostrar_experiencia():
    st.markdown("""
        <section class="section">
            <div class="eyebrow">Reserva en segundos</div>
            <h2>Así se sentiría reservar en tu negocio</h2>
            <p>Elige una opción y KroniQ te muestra únicamente el siguiente paso.</p>
        </section>
    """, unsafe_allow_html=True)

    giro = st.selectbox(
        "¿Qué tipo de negocio quieres probar?",
        list(NEGOCIOS),
        index=None,
        placeholder="Selecciona tu negocio",
        key="giro_demo",
    )

    if not giro:
        return

    if st.session_state.get("_ultimo_giro") != giro:
        st.session_state["_ultimo_giro"] = giro
        st.session_state["servicio_demo"] = None
        st.session_state["hora_demo"] = None

    servicios = NEGOCIOS[giro]

    st.markdown(
        f'<div class="selected-state">'
        f'<span class="accent">01</span> &nbsp; '
        f'<b>{texto_seguro(giro)}</b> · Elige el servicio'
        f'</div>',
        unsafe_allow_html=True,
    )

    nombres = list(servicios.keys())

    for i in range(0, len(nombres), 2):
        cols = st.columns(2, gap="small")

        for j, nombre_servicio in enumerate(nombres[i:i + 2]):
            minutos = servicios[nombre_servicio]
            seleccionado = (
                st.session_state.get("servicio_demo")
                == nombre_servicio
            )

            etiqueta = (
                f"{'✓  ' if seleccionado else ''}"
                f"{nombre_servicio}\n"
                f"{duracion_legible(minutos)}"
            )

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
        f'<div class="selected-state">'
        f'<span class="accent">02</span> &nbsp; '
        f'<b>{texto_seguro(servicio)}</b> · '
        f'{duracion_legible(duracion)} · Ahora elige el día'
        f'</div>',
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

    try:
        horas = horarios_disponibles(fecha, duracion, giro)
    except Exception:
        st.error("No fue posible consultar los horarios disponibles.")
        return

    if not horas:
        st.warning(
            "Ese día ya no tiene espacios disponibles. "
            "Prueba otra fecha."
        )
        return

    st.markdown("""
        <div class="selected-state">
            <span class="accent">03</span>
            &nbsp; Elige un horario disponible
        </div>
    """, unsafe_allow_html=True)

    for i in range(0, len(horas), 3):
        cols = st.columns(3, gap="small")

        for j, hora_opcion in enumerate(horas[i:i + 3]):
            seleccionado = (
                st.session_state.get("hora_demo")
                == hora_opcion
            )

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
        f'<div class="booking-summary">'
        f'<div class="eyebrow">Tu cita</div>'
        f'<strong>{texto_seguro(servicio)}</strong><br>'
        f'<span>{fecha_legible} · '
        f'<span class="accent">{texto_seguro(hora)}</span> · '
        f'{duracion_legible(duracion)}</span>'
        f'</div>',
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

    datos_validos = (
        bool(nombre.strip())
        and whatsapp.isdigit()
        and len(whatsapp) == 10
    )

    if whatsapp and not (
        whatsapp.isdigit() and len(whatsapp) == 10
    ):
        st.caption("Ingresa los 10 números de tu WhatsApp.")

    enviar = st.button(
        "Confirmar mi cita",
        key="agendar_cita",
        use_container_width=True,
        disabled=not datos_validos,
        type="primary",
    )

    if enviar:
        try:
            if hora not in horarios_disponibles(
                fecha, duracion, giro
            ):
                st.error(
                    "Ese horario acaba de ocuparse. "
                    "Elige otro disponible."
                )
                st.session_state["hora_demo"] = None
                return

            get_sheet().append_row([
                datetime.now().strftime("%Y%m%d%H%M%S%f"),
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
            ])

            st.success(
                "¡Listo! Tu cita de prueba quedó confirmada."
            )

            st.markdown(
                f'<div class="booking-summary">'
                f'<div class="eyebrow">Reserva confirmada</div>'
                f'<strong>{texto_seguro(nombre)}</strong><br>'
                f'<span>{texto_seguro(servicio)}</span><br>'
                f'<span>{fecha_legible} · '
                f'<span class="accent">{texto_seguro(hora)}</span>'
                f'</span></div>',
                unsafe_allow_html=True,
            )

        except Exception:
            st.error(
                "No fue posible guardar la cita. "
                "Intenta nuevamente."
            )


def mostrar_planes():
    st.markdown("""
        <section class="section">
            <div class="eyebrow">Elige cómo crecer</div>
            <h2>Una agenda que crece con tu negocio</h2>
            <p>Empieza simple y activa más herramientas cuando las necesites.</p>
        </section>
    """, unsafe_allow_html=True)

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
        f"<li>✓ {texto_seguro(beneficio)}</li>"
        for beneficio in PLANES[plan]
    )

    st.markdown(
        f'<section class="glass-card">'
        f'<div class="eyebrow">{texto_seguro(plan)}</div>'
        f'<h3>Esto es lo que puedes lograr</h3>'
        f'<ul>{beneficios}</ul>'
        f'</section>',
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
            st.markdown("""
                <section class="glass-card">
                    <div class="eyebrow">Comparte tu agenda</div>
                    <h3>Imprime o publica tu código QR</h3>
                    <p>
                        Haz que tus clientes abran tu agenda
                        y reserven con facilidad.
                    </p>
                </section>
            """, unsafe_allow_html=True)


def mostrar_agenda_publica():
    hero = BASE_DIR / "hero-logo-kroniq.jpg"

    if hero.exists():
        st.markdown(
            '<div class="hero">',
            unsafe_allow_html=True,
        )
        st.image(str(hero), use_container_width=True)
        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    mostrar_experiencia()
    mostrar_planes()

    st.markdown("""
        <section class="section">
            <h2>Tu negocio. Tu marca. Tu agenda.</h2>
            <p>
                Convirtamos esta experiencia
                en la agenda digital de tu negocio.
            </p>
        </section>
    """, unsafe_allow_html=True)

    mensaje = quote(
        "Hola, me interesa conocer KroniQ Booking "
        "y me gustaría agendar una videollamada."
    )

    st.link_button(
        "Vamos a conocernos por videollamada",
        f"https://wa.me/{WHATSAPP_VENTAS}?text={mensaje}",
        key="videollamada",
        use_container_width=True,
    )

    st.caption(
        "KroniQ Booking · Sincroniza tu tiempo, "
        "impulsa tu negocio."
    )


# =====================================================
# CRM DEL DUEÑO
# =====================================================

def tarjeta_metrica(valor, etiqueta):
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="value">{texto_seguro(valor)}</div>'
        f'<div class="label">{texto_seguro(etiqueta)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def tarjeta_cita(cita, mostrar_fecha=True):
    inicio = cita.get("inicio")
    fecha_hora = "Fecha sin reconocer"

    if inicio:
        fecha_hora = (
            inicio.strftime("%d/%m/%Y · %I:%M %p")
            if mostrar_fecha
            else inicio.strftime("%I:%M %p")
        )

    estado = cita.get("estado") or "Sin estado"

    st.markdown(
        f'<div class="appointment-card">'
        f'<strong>{texto_seguro(fecha_hora)} · '
        f'{texto_seguro(cita["nombre"])}</strong><br>'
        f'<span>{texto_seguro(cita["servicio"])}</span><br>'
        f'<span class="meta">'
        f'{texto_seguro(cita["giro"])} · '
        f'{texto_seguro(estado)} · '
        f'{texto_seguro(cita["whatsapp"])}'
        f'</span></div>',
        unsafe_allow_html=True,
    )


def mostrar_inicio_dueno(citas):
    ahora = datetime.now()
    hoy = ahora.date()

    validas = [
        cita for cita in citas
        if cita.get("inicio")
    ]

    citas_hoy = [
        cita for cita in validas
        if cita["inicio"].date() == hoy
    ]

    proximas = sorted(
        (
            cita for cita in validas
            if cita["inicio"] >= ahora
        ),
        key=lambda cita: cita["inicio"],
    )

    clientes = {
        (
            cita["whatsapp"].strip()
            or cita["nombre"].strip().lower()
        )
        for cita in citas
        if cita["whatsapp"].strip()
        or cita["nombre"].strip()
    }

    izquierda, derecha = st.columns(2, gap="small")

    with izquierda:
        tarjeta_metrica(len(citas_hoy), "Citas hoy")

    with derecha:
        tarjeta_metrica(len(clientes), "Clientes")

    st.markdown("### Próximas citas")

    if not proximas:
        st.info("No hay próximas citas registradas.")
        return

    for cita in proximas[:8]:
        tarjeta_cita(cita)


def mostrar_agenda_dueno(citas):
    st.markdown("### Agenda")

    fecha_filtro = st.date_input(
        "Ver día",
        value=date.today(),
        format="DD/MM/YYYY",
        key="fecha_agenda_dueno",
    )

    del_dia = sorted(
        (
            cita for cita in citas
            if cita.get("inicio")
            and cita["inicio"].date() == fecha_filtro
        ),
        key=lambda cita: cita["inicio"],
    )

    if not del_dia:
        st.info("No hay citas para este día.")
        return

    for cita in del_dia:
        tarjeta_cita(cita, mostrar_fecha=False)


def mostrar_clientes_dueno(citas):
    st.markdown("### Clientes")
    clientes = {}

    for cita in citas:
        clave = (
            cita["whatsapp"].strip()
            or cita["nombre"].strip().lower()
        )

        if not clave:
            continue

        cliente = clientes.setdefault(
            clave,
            {
                "nombre": cita["nombre"],
                "whatsapp": cita["whatsapp"],
                "citas": 0,
                "ultima": None,
            },
        )

        cliente["citas"] += 1

        if cita.get("inicio") and (
            cliente["ultima"] is None
            or cita["inicio"] > cliente["ultima"]
        ):
            cliente["ultima"] = cita["inicio"]

    if not clientes:
        st.info("Aún no hay clientes registrados.")
        return

    busqueda = st.text_input(
        "Buscar cliente",
        placeholder="Nombre o WhatsApp",
        key="buscar_cliente_dueno",
    ).strip().lower()

    lista = sorted(
        clientes.values(),
        key=lambda cliente: cliente["nombre"].lower(),
    )

    if busqueda:
        lista = [
            cliente for cliente in lista
            if busqueda in cliente["nombre"].lower()
            or busqueda in cliente["whatsapp"].lower()
        ]

    if not lista:
        st.info("No encontramos clientes con esa búsqueda.")
        return

    for cliente in lista:
        ultima = (
            cliente["ultima"].strftime("%d/%m/%Y")
            if cliente["ultima"]
            else "Sin fecha válida"
        )

        st.markdown(
            f'<div class="appointment-card">'
            f'<strong>{texto_seguro(cliente["nombre"])}</strong><br>'
            f'<span>{texto_seguro(cliente["whatsapp"])}</span><br>'
            f'<span class="meta">'
            f'{cliente["citas"]} cita(s) · '
            f'Última: {texto_seguro(ultima)}'
            f'</span></div>',
            unsafe_allow_html=True,
        )


def mostrar_ventas_dueno(citas):
    st.markdown("### Ventas")

    st.info(
        "KroniQ todavía no guarda precios. "
        "Por eso esta sección muestra actividad "
        "de reservaciones, sin inventar ingresos."
    )

    hoy = date.today()
    mes_actual = (hoy.year, hoy.month)

    citas_mes = [
        cita for cita in citas
        if cita.get("inicio")
        and (
            cita["inicio"].year,
            cita["inicio"].month,
        ) == mes_actual
    ]

    completadas = [
        cita for cita in citas_mes
        if cita["estado"].strip().lower()
        in {"completada", "completado", "atendida"}
    ]

    izquierda, derecha = st.columns(2, gap="small")

    with izquierda:
        tarjeta_metrica(
            len(citas_mes),
            "Reservas este mes",
        )

    with derecha:
        tarjeta_metrica(
            len(completadas),
            "Completadas",
        )

    conteo_servicios = {}

    for cita in citas_mes:
        servicio = cita["servicio"].strip() or "Sin servicio"
        conteo_servicios[servicio] = (
            conteo_servicios.get(servicio, 0) + 1
        )

    st.markdown("### Servicios reservados")

    if not conteo_servicios:
        st.caption("Aún no hay reservaciones este mes.")
        return

    for servicio, cantidad in sorted(
        conteo_servicios.items(),
        key=lambda elemento: (-elemento[1], elemento[0]),
    ):
        st.markdown(
            f"- **{texto_seguro(servicio)}:** {cantidad}"
        )


# =====================================================
# ACCESO PRIVADO DEL PROPIETARIO
# =====================================================

def credenciales_configuradas():
    celular = str(
        st.secrets.get("owner_phone", "")
    ).strip()

    contrasena = str(
        st.secrets.get("owner_password", "")
    )

    return bool(celular and contrasena)


def normalizar_celular(celular):
    return "".join(
        caracter for caracter in str(celular)
        if caracter.isdigit()
    )


def validar_credenciales(celular, contrasena):
    if not credenciales_configuradas():
        return False

    celular_correcto = normalizar_celular(
        st.secrets["owner_phone"]
    )

    contrasena_correcta = str(
        st.secrets["owner_password"]
    )

    celular_valido = hmac.compare_digest(
        normalizar_celular(celular).encode("utf-8"),
        celular_correcto.encode("utf-8"),
    )

    contrasena_valida = hmac.compare_digest(
        contrasena.encode("utf-8"),
        contrasena_correcta.encode("utf-8"),
    )

    return celular_valido and contrasena_valida


def mostrar_login_dueno():
    st.markdown("""
        <section class="owner-header">
            <div class="eyebrow">Área privada</div>
            <h1>KroniQ Booking</h1>
            <p>Acceso exclusivo para propietarios.</p>
        </section>
    """, unsafe_allow_html=True)

    st.markdown("### Iniciar sesión")

    with st.form("form_login_dueno"):
        celular = st.text_input(
            "Número de celular",
            placeholder="Incluye lada o código de país",
        )

        contrasena = st.text_input(
            "Contraseña",
            type="password",
            placeholder="Ingresa tu contraseña",
        )

        ingresar = st.form_submit_button(
            "Iniciar sesión",
            use_container_width=True,
            type="primary",
        )

    if ingresar:
        if not credenciales_configuradas():
            st.error(
                "El acceso del propietario aún no está "
                "configurado en Streamlit Secrets."
            )
        elif validar_credenciales(celular, contrasena):
            st.session_state["dueno_autorizado"] = True
            st.session_state["vista_app"] = "dueno"
            st.rerun()
        else:
            st.error("Celular o contraseña incorrectos.")

    st.caption(
        "Acceso privado de KroniQ Booking."
    )


def cerrar_sesion_dueno():
    st.session_state["dueno_autorizado"] = False
    st.session_state["vista_app"] = "publica"
    st.session_state.pop("seccion_dueno", None)
    st.rerun()


def mostrar_panel_dueno():
    if not st.session_state.get("dueno_autorizado", False):
        mostrar_login_dueno()
        return

    if not credenciales_configuradas():
        cerrar_sesion_dueno()
        return

    st.markdown("""
        <section class="owner-header">
            <div class="eyebrow">Panel del negocio</div>
            <h1>KroniQ Dueño</h1>
            <p>Las reservaciones de tu agenda, en un solo lugar.</p>
        </section>
    """, unsafe_allow_html=True)

    izquierda, derecha = st.columns(2, gap="small")

    with izquierda:
        if st.button(
            "Actualizar datos",
            use_container_width=True,
            key="actualizar_dueno",
        ):
            st.rerun()

    with derecha:
        if st.button(
            "Cerrar sesión",
            use_container_width=True,
            key="cerrar_sesion_dueno",
        ):
            cerrar_sesion_dueno()

    try:
        citas = obtener_citas()
    except Exception:
        st.error(
            "No fue posible leer las citas de Google Sheets. "
            "Intenta nuevamente."
        )
        return

    seccion = st.radio(
        "Sección del panel",
        ["Inicio", "Agenda", "Clientes", "Ventas"],
        horizontal=True,
        label_visibility="collapsed",
        key="seccion_dueno",
    )

    if seccion == "Inicio":
        mostrar_inicio_dueno(citas)
    elif seccion == "Agenda":
        mostrar_agenda_dueno(citas)
    elif seccion == "Clientes":
        mostrar_clientes_dueno(citas)
    elif seccion == "Ventas":
        mostrar_ventas_dueno(citas)


# =====================================================
# NAVEGACION PRINCIPAL
# =====================================================

def main():
    aplicar_estilos()

    st.session_state.setdefault("plan", None)
    st.session_state.setdefault("dueno_autorizado", False)
    st.session_state.setdefault("vista_app", "publica")

    vista = st.session_state["vista_app"]

    if vista == "publica":
        izquierda, derecha = st.columns([2.2, 1.4])

        with derecha:
            if st.button(
                "Acceso propietarios",
                key="acceso_propietarios",
                use_container_width=True,
            ):
                st.session_state["vista_app"] = "login"
                st.rerun()

        mostrar_agenda_publica()

    elif vista == "login":
        if st.button(
            "← Volver a la agenda",
            key="volver_agenda",
        ):
            st.session_state["vista_app"] = "publica"
            st.rerun()

        mostrar_login_dueno()

    elif vista == "dueno":
        if st.session_state.get("dueno_autorizado", False):
            mostrar_panel_dueno()
        else:
            st.session_state["vista_app"] = "login"
            mostrar_login_dueno()

    else:
        st.session_state["vista_app"] = "publica"
        st.rerun()


if __name__ == "__main__":
    main()
