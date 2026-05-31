import re
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from PIL import Image


APP_ICON_PATH = "app_icon.png"

st.set_page_config(
    page_title="KroniQ Booking",
    page_icon=APP_ICON_PATH,
    layout="centered",
    initial_sidebar_state="collapsed",
)

SHEET_ID = "1CiFPrWzvyeaTtdiMVYZ8a3DyxONSi4ZEpn2kNM0LSeU"

NEGOCIOS = {
    "Barberia": {
        "Corte caballero": 30,
        "Barba": 30,
        "Corte + barba": 60,
        "Tinte caballero": 90,
    },
    "Spa": {
        "Facial relajante": 60,
        "Masaje descontracturante": 90,
        "Depilacion": 45,
        "Paquete spa": 120,
    },
    "Medico": {
        "Consulta general": 30,
        "Primera valoracion": 45,
        "Consulta de seguimiento": 30,
        "Revision de estudios": 30,
    },
    "Dentista": {
        "Valoracion dental": 30,
        "Limpieza dental": 60,
        "Resina": 60,
        "Blanqueamiento": 90,
    },
}

BUSINESS_META = {
    "Barberia": {"icon": "B", "accent": "#f23b5f"},
    "Spa": {"icon": "S", "accent": "#2dd4bf"},
    "Medico": {"icon": "M", "accent": "#60a5fa"},
    "Dentista": {"icon": "D", "accent": "#fbbf24"},
}

PLANES = {
    "Starter - $799 setup + $299/mes": "Agenda digital, QR, bloqueo de empalmes y comentarios.",
    "Business - $1,499 setup + $499/mes": "Todo Starter + promociones, flyers y branding personalizado.",
    "Premium - $2,999 setup + $999/mes": "Todo Business + cancelaciones, reagendar y alertas por correo.",
}

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(18, 0)
COMIDA_INICIO = time(14, 0)
COMIDA_FIN = time(15, 0)

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = [
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
]


def inject_css():
    st.markdown(
        """
        <style>
            #MainMenu, footer, header,
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"],
            [data-testid="stHeader"],
            .stDeployButton {
                display: none !important;
            }

            :root {
                --bg: #090b10;
                --panel: #10141d;
                --panel-2: #171c27;
                --line: rgba(255,255,255,.1);
                --text-soft: rgba(255,255,255,.68);
                --brand: #f23b5f;
                --brand-2: #2dd4bf;
            }

            html, body, [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at top left, rgba(242,59,95,.16), transparent 28rem),
                    radial-gradient(circle at bottom right, rgba(45,212,191,.12), transparent 28rem),
                    var(--bg);
                color: #f8fafc;
            }

            [data-testid="stAppViewBlockContainer"] {
                max-width: 760px;
                padding: 1.2rem 1rem 5rem;
            }

            h1, h2, h3, p, label, span {
                letter-spacing: 0;
            }

            h1 {
                font-size: 2.3rem !important;
                line-height: 1.02 !important;
                margin-bottom: .35rem !important;
            }

            h2 {
                font-size: 1.35rem !important;
                margin-top: 1.4rem !important;
            }

            h3 {
                font-size: 1rem !important;
            }

            .kq-hero {
                border: 1px solid var(--line);
                border-radius: 20px;
                padding: 1.1rem;
                background: linear-gradient(145deg, rgba(16,20,29,.96), rgba(13,16,23,.92));
                box-shadow: 0 22px 70px rgba(0,0,0,.38);
                margin-bottom: 1.1rem;
            }

            .kq-logo img {
                border-radius: 16px;
                margin-bottom: .75rem;
            }

            .kq-eyebrow {
                color: var(--brand-2);
                font-size: .76rem;
                font-weight: 800;
                letter-spacing: .12em;
                text-transform: uppercase;
                margin-bottom: .55rem;
            }

            .kq-copy {
                color: var(--text-soft);
                font-size: 1rem;
                line-height: 1.55;
                margin: .2rem 0 0;
            }

            .kq-progress {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: .45rem;
                margin: 1rem 0 .2rem;
            }

            .kq-step {
                border: 1px solid rgba(45,212,191,.22);
                border-radius: 999px;
                color: rgba(255,255,255,.82);
                font-size: .72rem;
                font-weight: 700;
                padding: .48rem .55rem;
                text-align: center;
                background: linear-gradient(135deg, rgba(45,212,191,.1), rgba(242,59,95,.08));
                white-space: nowrap;
            }

            .kq-step.is-active {
                background: linear-gradient(135deg, var(--brand), #ff7a59);
                color: white;
                border-color: transparent;
            }

            .kq-section {
                border: 1px solid var(--line);
                border-radius: 18px;
                padding: 1rem;
                background: rgba(16,20,29,.72);
                margin: 1rem 0;
            }

            .kq-card-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: .75rem;
                margin-top: .7rem;
            }

            .kq-service-card, .kq-plan-card {
                border: 1px solid var(--line);
                border-radius: 14px;
                background: linear-gradient(145deg, rgba(255,255,255,.065), rgba(255,255,255,.025));
                padding: .85rem;
                min-height: 96px;
            }

            .kq-service-name, .kq-plan-name {
                color: #f8fafc;
                font-weight: 800;
                margin-bottom: .4rem;
            }

            .kq-duration, .kq-plan-copy {
                color: var(--text-soft);
                font-size: .86rem;
                line-height: 1.4;
            }

            .kq-pill {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 2rem;
                height: 2rem;
                border-radius: 999px;
                color: #0b0f16;
                font-weight: 900;
                background: var(--brand-2);
                margin-bottom: .65rem;
            }

            .kq-summary {
                border-radius: 16px;
                padding: 1rem;
                border: 1px solid rgba(45,212,191,.35);
                background: rgba(45,212,191,.1);
                color: #dffcf7;
                margin: .9rem 0;
            }

            .kq-success {
                border-radius: 18px;
                padding: 1.1rem;
                border: 1px solid rgba(34,197,94,.35);
                background: linear-gradient(145deg, rgba(34,197,94,.18), rgba(22,163,74,.08));
                color: #dcfce7;
                margin-top: 1rem;
            }

            .kq-success strong {
                display: block;
                font-size: 1.1rem;
                color: #f0fdf4;
                margin-bottom: .35rem;
            }

            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stDateInput input {
                border-radius: 14px !important;
                border: 1px solid rgba(148,163,184,.22) !important;
                background-color: #151b27 !important;
                color: #f8fafc !important;
                min-height: 3rem;
                box-shadow: none !important;
            }

            .stTextInput input:focus,
            .stTextArea textarea:focus,
            .stDateInput input:focus {
                border-color: rgba(45,212,191,.35) !important;
                box-shadow: 0 0 0 1px rgba(45,212,191,.06) !important;
                outline: none !important;
            }

            .stTextInput input::placeholder,
            .stTextArea textarea::placeholder {
                color: rgba(255,255,255,.5) !important;
                opacity: 1 !important;
            }

            .stTextInput label,
            .stTextArea label,
            .stSelectbox label,
            .stDateInput label {
                color: rgba(255,255,255,.82) !important;
                font-weight: 700 !important;
            }

            .stTextInput label p,
            .stTextArea label p,
            .stSelectbox label p,
            .stDateInput label p {
                color: rgba(255,255,255,.82) !important;
            }

            .stDateInput input {
                height: 3rem !important;
                padding: .7rem .9rem !important;
            }

            .stTextInput [data-baseweb="input"],
            .stDateInput [data-baseweb="input"],
            .stTextArea [data-baseweb="textarea"] {
                border-radius: 14px !important;
                border: 1px solid rgba(148,163,184,.22) !important;
                box-shadow: none !important;
                background-color: #151b27 !important;
            }

            .stTextInput [data-baseweb="base-input"],
            .stTextArea [data-baseweb="base-input"],
            .stDateInput [data-baseweb="base-input"] {
                border-color: transparent !important;
                box-shadow: none !important;
                outline: none !important;
                background-color: #151b27 !important;
            }

            .stTextInput [data-baseweb="input"]:focus-within,
            .stDateInput [data-baseweb="input"]:focus-within,
            .stTextArea [data-baseweb="textarea"]:focus-within {
                border-color: rgba(45,212,191,.35) !important;
                box-shadow: none !important;
            }

            .stTextInput [data-baseweb="input"]:focus-within input,
            .stDateInput [data-baseweb="input"]:focus-within input,
            .stTextArea [data-baseweb="textarea"]:focus-within textarea {
                border-color: transparent !important;
            }

            input:-webkit-autofill,
            textarea:-webkit-autofill {
                -webkit-text-fill-color: #f8fafc !important;
                box-shadow: 0 0 0 1000px #151b27 inset !important;
                transition: background-color 9999s ease-in-out 0s !important;
            }

            [data-testid="InputInstructions"] {
                display: none !important;
            }

            div[data-testid="stForm"] {
                border: 1px solid var(--line);
                border-radius: 18px;
                padding: 1rem;
                background: rgba(16,20,29,.72);
            }

            .stButton button,
            .stFormSubmitButton button {
                border-radius: 14px !important;
                min-height: 3.15rem;
                font-weight: 800 !important;
                border: 1px solid rgba(255,255,255,.12) !important;
            }

            .stFormSubmitButton button {
                width: 100%;
                background: linear-gradient(135deg, var(--brand), #ff7a59) !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 14px 34px rgba(242,59,95,.25);
            }

            @media (max-width: 560px) {
                [data-testid="stAppViewBlockContainer"] {
                    padding-left: .85rem;
                    padding-right: .85rem;
                }

                h1 {
                    font-size: 1.85rem !important;
                }

                .kq-card-grid {
                    grid-template-columns: 1fr;
                }

                .kq-step {
                    font-size: .64rem;
                    padding: .42rem .34rem;
                }
            }
        </style>
        <link rel="apple-touch-icon" href="app_icon.png">
        <link rel="icon" type="image/png" href="app_icon.png">
        <meta name="apple-mobile-web-app-title" content="KroniQ Booking">
        <meta name="application-name" content="KroniQ Booking">
        <meta name="theme-color" content="#090b10">
        """,
        unsafe_allow_html=True,
    )


def get_service_account_info():
    try:
        return dict(st.secrets["gcp_service_account"])
    except Exception:
        pass

    for json_path in Path(".").glob("*.json"):
        with json_path.open("r", encoding="utf-8") as file:
            service_account = json.load(file)

        if "client_email" in service_account and "private_key" in service_account:
            return service_account

    raise RuntimeError(
        "No encontre credenciales de Google Sheets. Agrega secrets.toml o un JSON "
        "de cuenta de servicio en la carpeta del proyecto."
    )


def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(get_service_account_info(), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1


def se_empalma(inicio1, fin1, inicio2, fin2):
    return inicio1 < fin2 and inicio2 < fin1


def formato_hora(dt):
    hora = dt.hour % 12 or 12
    periodo = "manana" if dt.hour < 12 else "tarde"
    return f"{hora}:{dt.minute:02d} de la {periodo}"


def normalizar_hora(hora):
    valor = hora.replace(".", "").strip().lower()
    valor = valor.replace(" de la manana", "am").replace(" de la tarde", "pm")
    valor = valor.replace(" manana", "am").replace(" tarde", "pm")
    valor = valor.replace(" ", "")

    if valor.endswith("am"):
        return f"{valor[:-2]} AM"
    if valor.endswith("pm"):
        return f"{valor[:-2]} PM"

    return hora.upper()


def formato_duracion(minutos):
    if minutos < 60:
        return f"{minutos} min"
    if minutos == 60:
        return "1 hr"
    horas = minutos // 60
    resto = minutos % 60
    return f"{horas} hr {resto} min" if resto else f"{horas} hrs"


def limpiar_telefono(valor):
    return re.sub(r"\D", "", valor or "")


def opciones_fecha(dias=21):
    opciones = {}
    hoy = date.today()

    for offset in range(dias):
        fecha = hoy + timedelta(days=offset)
        if offset == 0:
            etiqueta = "Hoy"
        elif offset == 1:
            etiqueta = "Manana"
        else:
            etiqueta = f"{DIAS[fecha.weekday()]} {fecha.day} {MESES[fecha.month - 1]}"

        opciones[etiqueta] = fecha

    return opciones


def obtener_citas(fecha, giro):
    sheet = get_sheet()
    filas = sheet.get_all_values()
    citas = []

    for fila in filas[1:]:
        try:
            if len(fila) < 9:
                continue

            giro_cita = fila[1]
            duracion = int(fila[5])
            fecha_cita = fila[6]
            hora_cita = fila[7]

            if fecha_cita != str(fecha) or giro_cita != giro:
                continue

            inicio = datetime.strptime(
                f"{fecha_cita} {normalizar_hora(hora_cita)}",
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
            choca_comida = comida_inicio <= actual < comida_fin
            choca_cita = any(
                se_empalma(actual, fin_servicio, cita_inicio, cita_fin)
                for cita_inicio, cita_fin in citas
            )

            if not choca_comida and not choca_cita:
                disponibles.append(formato_hora(actual))

        actual += timedelta(minutes=30)

    return disponibles


def horarios_base():
    disponibles = []
    actual = datetime.combine(date.today(), HORA_APERTURA)
    cierre_dia = datetime.combine(date.today(), HORA_CIERRE)
    comida_inicio = datetime.combine(date.today(), COMIDA_INICIO)
    comida_fin = datetime.combine(date.today(), COMIDA_FIN)

    while actual < cierre_dia:
        if not comida_inicio <= actual < comida_fin:
            disponibles.append(formato_hora(actual))
        actual += timedelta(minutes=30)

    return disponibles


def render_hero():
    st.markdown('<div class="kq-hero">', unsafe_allow_html=True)
    try:
        logo = Image.open("logo.png")
        st.markdown('<div class="kq-logo">', unsafe_allow_html=True)
        st.image(logo, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.markdown('<div class="kq-eyebrow">KroniQ Booking</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="kq-eyebrow">Agenda inteligente para negocios por cita</div>
        <h1>Reserva una cita demo en menos de un minuto.</h1>
        <p class="kq-copy">
            Elige el giro, selecciona un servicio disponible y deja tus datos.
            Asi se veria una agenda personalizada para tus clientes.
        </p>
        <div class="kq-progress">
            <div class="kq-step is-active">Giro</div>
            <div class="kq-step">Servicio</div>
            <div class="kq-step">Horario</div>
            <div class="kq-step">Confirmar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_service_cards(servicios):
    cards = ['<div class="kq-card-grid">']
    for servicio, duracion in servicios.items():
        cards.append(
            f'<div class="kq-service-card">'
            f'<div class="kq-service-name">{servicio}</div>'
            f'<div class="kq-duration">{formato_duracion(duracion)}</div>'
            f"</div>"
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def render_plan_cards():
    cards = ['<div class="kq-card-grid">']
    for plan, descripcion in PLANES.items():
        cards.append(
            f'<div class="kq-plan-card">'
            f'<div class="kq-plan-name">{plan}</div>'
            f'<div class="kq-plan-copy">{descripcion}</div>'
            f"</div>"
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


inject_css()
render_hero()

st.markdown('<div class="kq-section">', unsafe_allow_html=True)
st.markdown("## 1. Elige tu negocio")
giro = st.selectbox("Tipo de negocio", list(NEGOCIOS.keys()), label_visibility="collapsed")
meta = BUSINESS_META[giro]
st.markdown(
    f"""
    <div class="kq-summary" style="border-color: {meta['accent']}55; background: {meta['accent']}16;">
        <span class="kq-pill" style="background:{meta['accent']}">{meta['icon']}</span>
        <strong>{giro}</strong><br>
        Servicios de ejemplo para mostrar disponibilidad real por duracion.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("### Servicios disponibles")
servicios = NEGOCIOS[giro]
render_service_cards(servicios)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="kq-section">', unsafe_allow_html=True)
st.markdown("## 2. Selecciona servicio y fecha")
servicio = st.selectbox("Servicio", list(servicios.keys()))
duracion = servicios[servicio]
fechas = opciones_fecha()
fecha_label = st.selectbox("Fecha", list(fechas.keys()))
fecha = fechas[fecha_label]

horas = horarios_disponibles(fecha, duracion, giro)
horas_para_mostrar = horarios_base()
horas_ocupadas = [hora for hora in horas_para_mostrar if hora not in horas]

if not horas:
    st.warning("No hay horarios disponibles para este servicio en esta fecha.")
    st.stop()

st.markdown(
    f"""
    <div class="kq-summary">
        <strong>{servicio}</strong>
        Duracion estimada: {formato_duracion(duracion)}. Horarios disponibles:
        {len(horas)}.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("## 3. Confirma tus datos")

with st.form("formulario_demo", clear_on_submit=True):
    hora = st.selectbox("Hora disponible", horas_para_mostrar)
    nombre = st.text_input(
        "Nombre completo",
        placeholder="",
        autocomplete="new-password",
        key="kq_demo_full_name_no_autofill",
    )
    whatsapp = st.text_input(
        "WhatsApp (10 digitos)",
        max_chars=14,
        placeholder="",
        autocomplete="one-time-code",
        key="kq_demo_phone_one_time_code",
    )
    comentarios = st.text_area(
        "Comentarios adicionales",
        placeholder="",
        key="kq_demo_notes",
    )
    plan_interes = st.selectbox("Plan que te interesa conocer", list(PLANES.keys()))
    enviar = st.form_submit_button("Confirmar cita demo")

if enviar:
    nombre = nombre.strip()
    whatsapp = limpiar_telefono(whatsapp)

    if not nombre:
        st.error("Escribe tu nombre.")
    elif len(whatsapp) != 10:
        st.error("El WhatsApp debe tener exactamente 10 digitos.")
    elif hora in horas_ocupadas:
        st.error("Ese horario ya tiene una cita registrada. Elige otro.")
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
            st.markdown(
                f"""
                <div class="kq-success">
                    <strong>Cita demo guardada correctamente.</strong>
                    {servicio} el {fecha.strftime('%d/%m/%Y')} a las {hora}.<br>
                    Te mostramos como se veria una agenda personalizada para tu negocio.
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown('<div class="kq-section">', unsafe_allow_html=True)
st.markdown("## Planes KroniQ Booking")
render_plan_cards()
st.markdown("</div>", unsafe_allow_html=True)

st.caption("KroniQ Booking - agenda digital para negocios modernos.")
