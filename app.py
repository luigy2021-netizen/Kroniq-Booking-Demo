import streamlit as st
from PIL import Image
import io
import gspread
import qrcode
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
    "Starter — $799 setup + $299/mes": (
        "Agenda personalizada con logo e imagen del negocio, bloqueo automático "
        "de empalmes, comentarios adicionales y confirmación automática por "
        "WhatsApp al crear una cita."
    ),
    "Business — $1,499 setup + $499/mes": (
        "Todo Starter + promociones por recomendación, código QR para compartir "
        "la agenda y 1 flyer promocional en el encabezado de la agenda."
    ),
    "Premium — $2,999 setup + $999/mes": (
        "Todo Business + 2 flyers promocionales nuevos por mes, gestión de "
        "cancelaciones y ajustes de disponibilidad por vacaciones o días inhábiles."
    )
}

PLANES_CORTOS = {
    "Starter": "Starter — $799 setup + $299/mes",
    "Business": "Business — $1,499 setup + $499/mes",
    "Premium": "Premium — $2,999 setup + $999/mes",
}

DETALLES_PLAN = {
    "Starter": {
        "precio": "$799 setup + $299/mes",
        "color": "#2563eb",
        "beneficios": [
            "Agenda personalizada con logo e imagen del negocio",
            "Bloqueo automático de empalmes",
            "Comentarios adicionales en cada reservación",
            "Confirmación automática por WhatsApp",
        ],
    },
    "Business": {
        "precio": "$1,499 setup + $499/mes",
        "color": "#7c3aed",
        "beneficios": [
            "Todo lo incluido en Starter",
            "Promociones por recomendación",
            "Código QR para compartir la agenda",
            "Un flyer promocional en el encabezado",
        ],
    },
    "Premium": {
        "precio": "$2,999 setup + $999/mes",
        "color": "#c2410c",
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

def crear_qr(texto):
    qr = qrcode.QRCode(version=1, box_size=7, border=3)
    qr.add_data(texto)
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="#111827", back_color="white")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

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

st.markdown("## Elige el plan que quieres probar")
plan_corto = st.radio(
    "La demostración cambia según el plan seleccionado",
    list(PLANES_CORTOS.keys()),
    horizontal=True,
)
plan_interes = PLANES_CORTOS[plan_corto]
detalle_plan = DETALLES_PLAN[plan_corto]
beneficios_html = "".join(
    f"<li style='margin:.42rem 0'>✓ {beneficio}</li>"
    for beneficio in detalle_plan["beneficios"]
)
st.markdown(
    f"""
    <section style="padding:1.35rem 1.5rem;border-radius:18px;
    border:2px solid {detalle_plan['color']};background:#ffffff;
    box-shadow:0 12px 32px rgba(15,23,42,.08);margin:.5rem 0 1.2rem">
        <div style="font-size:.78rem;font-weight:800;letter-spacing:.12em;
        text-transform:uppercase;color:{detalle_plan['color']}">
            DEMOSTRACIÓN ACTIVA
        </div>
        <h2 style="margin:.25rem 0;color:#111827">{plan_corto}</h2>
        <div style="font-size:1.12rem;font-weight:800;color:{detalle_plan['color']}">
            {detalle_plan['precio']}
        </div>
        <ul style="padding-left:1.1rem;margin:.9rem 0 0;color:#334155">
            {beneficios_html}
        </ul>
    </section>
    """,
    unsafe_allow_html=True,
)

if plan_corto == "Starter":
    st.caption(
        "Vista Starter: agenda esencial, clara y lista para recibir reservaciones."
    )

if plan_corto in ("Business", "Premium"):
    st.markdown(
        """
        <div style="padding:1.5rem;border-radius:16px;background:
        linear-gradient(135deg,#5b21b6,#0891b2);color:white;margin:1rem 0">
        <small style="font-weight:700;letter-spacing:.12em">PROMOCIÓN DEL MES</small>
        <h2 style="margin:.35rem 0;color:white">Agenda con un amigo y recibe un beneficio</h2>
        <p style="margin:0">Promoción de ejemplo visible en el encabezado de tu agenda.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if plan_corto == "Premium":
    st.markdown(
        """
        <div style="padding:1.2rem;border-radius:16px;background:#fff4db;
        border:1px solid #f2c66d;margin:0 0 1rem">
        <strong>✨ Segunda promoción Premium</strong><br>
        Reserva dos servicios este mes y recibe una atención especial.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Administración Premium")
    st.caption(
        "Estas herramientas adicionales no aparecen en Starter ni en Business."
    )
    accion_demo = st.selectbox(
        "Prueba una herramienta administrativa",
        ["Ver agenda activa", "Reprogramar una cita", "Cancelar una cita", "Bloquear vacaciones o día inhábil"],
    )
    if accion_demo == "Reprogramar una cita":
        st.success("La cita puede moverse a otro horario disponible sin crear empalmes.")
    elif accion_demo == "Cancelar una cita":
        st.warning("La cita se cancela y el horario vuelve a quedar disponible.")
    elif accion_demo == "Bloquear vacaciones o día inhábil":
        st.date_input("Fecha que se bloquearía", min_value=date.today(), key="fecha_bloqueo_demo")
        st.info("Durante una implementación real, esa fecha dejaría de aceptar reservaciones.")

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
            st.info(
                f"Confirmación automática de ejemplo: Hola, {nombre}. Tu cita de "
                f"{servicio} quedó agendada para el {fecha.strftime('%d/%m/%Y')} "
                f"a las {hora}."
            )
            if plan_corto in ("Business", "Premium"):
                st.success("También se generó una recomendación para compartir la agenda.")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.markdown("## Así se comparte la agenda")

if plan_corto in ("Business", "Premium"):
    izquierda, derecha = st.columns([1, 1.5], vertical_alignment="center")
    with izquierda:
        st.image(
            crear_qr("https://kroniq-booking-demo.streamlit.app"),
            caption="QR de demostración",
            width=190,
        )
    with derecha:
        st.markdown("### QR incluido")
        st.write("El negocio puede imprimirlo, publicarlo o enviarlo para que sus clientes abran la agenda.")
        st.code("Recomienda esta agenda y comparte el QR", language=None)
else:
    st.write("El código QR para compartir la agenda está disponible a partir del plan Business.")

with st.expander("Comparar los tres planes"):
    for plan, descripcion in PLANES.items():
        st.markdown(f"**{plan}**")
        st.write(descripcion)

st.markdown("---")
st.caption("KroniQ Booking — agenda digital para negocios modernos.")
