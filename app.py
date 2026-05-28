import streamlit as st
from PIL import Image
import gspread
from datetime import datetime, date, time, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="KroniQ Booking Demo", page_icon="🔷", layout="centered")

SHEET_ID = "1CiFPrWzvyeaTtdiMVYZ8a3DyxONSi4ZEpn2kNM0LSeU"

NEGOCIOS = {
    "Barbería": {
        "Corte caballero": 30,
        "Barba": 30,
        "Corte + barba": 60,
        "Tinte caballero": 90
    },
    "Spa": {
        "Facial relajante": 60,
        "Masaje descontracturante": 90,
        "Depilación": 45,
        "Paquete spa": 120
    },
    "Médico": {
        "Consulta general": 30,
        "Primera valoración": 45,
        "Consulta de seguimiento": 30,
        "Revisión de estudios": 30
    },
    "Dentista": {
        "Valoración dental": 30,
        "Limpieza dental": 60,
        "Resina": 60,
        "Blanqueamiento": 90
    }
}

PLANES = {
    "Starter — $799 setup + $299/mes": "Agenda digital, QR, bloqueo de empalmes y comentarios.",
    "Business — $1,499 setup + $499/mes": "Todo Starter + promociones, flyers y branding personalizado.",
    "Premium — $2,999 setup + $999/mes": "Todo Business + cancelaciones, reagendar y alertas por correo."
}

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(18, 0)
COMIDA_INICIO = time(14, 0)
COMIDA_FIN = time(15, 0)

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def se_empalma(inicio1, fin1, inicio2, fin2):
    return inicio1 < fin2 and inicio2 < fin1

def formato_hora(dt):
    return dt.strftime("%I:%M %p")

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

            inicio = datetime.strptime(f"{fecha_cita} {hora_cita}", "%Y-%m-%d %I:%M %p")
            fin = inicio + timedelta(minutes=duracion)
            citas.append((inicio, fin))
        except:
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
            choca_comida = se_empalma(actual, fin_servicio, comida_inicio, comida_fin)
            choca_cita = any(
                se_empalma(actual, fin_servicio, cita_inicio, cita_fin)
                for cita_inicio, cita_fin in citas
            )

            if not choca_comida and not choca_cita:
                disponibles.append(formato_hora(actual))

        actual += timedelta(minutes=30)

    return disponibles

logo = Image.open("logo.png")
st.image(logo, use_container_width=True)

st.write("Demo de agenda digital para negocios que trabajan por cita.")

st.markdown("---")

st.markdown("## Elige el tipo de negocio")
giro = st.selectbox("Tipo de negocio", list(NEGOCIOS.keys()))

servicios = NEGOCIOS[giro]

st.markdown("### Servicios de ejemplo")
for servicio, duracion in servicios.items():
    if duracion < 60:
        texto = f"{duracion} min"
    elif duracion == 60:
        texto = "1 hr"
    else:
        texto = f"{duracion // 60} hrs"
    st.write(f"• {servicio}: {texto}")

st.markdown("---")

servicio = st.selectbox("Servicio", list(servicios.keys()))
duracion = servicios[servicio]
fecha = st.date_input("Fecha", min_value=date.today())

horas = horarios_disponibles(fecha, duracion, giro)

if not horas:
    st.warning("No hay horarios disponibles para este servicio en esta fecha.")
    st.stop()

with st.form("formulario_demo", clear_on_submit=True):
    nombre = st.text_input("Nombre completo")
    whatsapp = st.text_input("WhatsApp (10 dígitos)", max_chars=10)
    hora = st.selectbox("Hora disponible", horas)
    comentarios = st.text_area("Comentarios adicionales")
    plan_interes = st.selectbox("Plan que te interesa conocer", list(PLANES.keys()))
    enviar = st.form_submit_button("Agendar cita demo")

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
            sheet.append_row([
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
                plan_interes
            ])
            st.success("✅ Cita demo guardada correctamente.")
            st.info("Así funcionaría una agenda personalizada para tu negocio.")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.markdown("## Planes KroniQ Booking")

for plan, descripcion in PLANES.items():
    st.markdown(f"### {plan}")
    st.write(descripcion)

st.markdown("---")
st.caption("KroniQ Booking — agenda digital para negocios modernos.")
