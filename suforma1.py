import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Buscador de Experiencias", layout="wide")

# Estilo personalizado para las tarjetas (Simulando el diseño de React)
st.markdown("""
    <style>
    .result-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .contratante-header {
        color: #1e40af;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    .badge {
        background-color: #f1f5f9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-right: 5px;
    }
    .badge-match {
        background-color: #e0e7ff;
        color: #4338ca;
        font-weight: bold;
        border: 1px solid #c7d2fe;
    }
    </style>
""", unsafe_allow_html=True)

# Datos de muestra iniciales
SAMPLE_DATA = """ID_Experiencia;Consecutivo;Celebrado_Por;Contratista;Contratante;Objeto;Valor_SMMLV;Valor_COP;Porcentaje_Participacion;Codigos_UNSPSC
1;1;1 - EL PROPONENTE;SUFORMA S.A.S.;ALCALDIA MUNICIPAL DE CHIA;IMPRESOS;111.31;144703000;1;11101500, 11101600, 11101700, 11101800, 11101900, 11111600, 14111500"""

def format_currency(val):
    return f"$ {val:,.0f}".replace(",", ".")

# --- LÓGICA DE CARGA DE DATOS ---
st.sidebar.title("⚙️ Configuración")
uploaded_file = st.sidebar.file_uploader("Cargar archivo CSV (Punto y coma)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=";", encoding="latin1")
    st.sidebar.success("¡Archivo cargado!")
else:
    df = pd.read_csv(io.StringIO(SAMPLE_DATA), sep=";")
    st.sidebar.info("Usando datos de muestra")

# Limpieza básica de datos numéricos
for col in ['Valor_SMMLV', 'Valor_COP']:
    if col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.replace('.', '').str.replace(',', '.').astype(float)

# --- PANEL DE BÚSQUEDA ---
st.title("🔍 Buscador de Experiencias")

col1, col2 = st.columns(2)
with col1:
    search_codes = st.text_input("🏷️ Códigos UNSPSC (separa por comas)", placeholder="Ej: 11101500, 14111500")
with col2:
    search_object = st.text_input("📄 Objeto del Contrato", placeholder="Buscar descripción...")

# --- FILTRADO ---
filtered_df = df.copy()

if search_object:
    filtered_df = filtered_df[filtered_df['Objeto'].str.contains(search_object, case=False, na=False)]

if search_codes:
    codes_to_find = [c.strip() for c in search_codes.split(',') if c.strip()]
    def match_codes(row_codes):
        if pd.isna(row_codes): return False
        return all(str(c) in str(row_codes) for c in codes_to_find)
    filtered_df = filtered_df[filtered_df['Codigos_UNSPSC'].apply(match_codes)]

# Ordenar por SMMLV
filtered_df = filtered_df.sort_values(by='Valor_SMMLV', ascending=False)

# --- DASHBOARD ---
m1, m2, m3 = st.columns(3)
m1.metric("Experiencias", len(filtered_df))
m2.metric("Total SMMLV", f"{filtered_df['Valor_SMMLV'].sum():,.2f}")
m3.metric("Presupuesto Total", format_currency(filtered_df['Valor_COP'].sum()))

st.divider()

# --- LISTA DE RESULTADOS ---
if filtered_df.empty:
    st.warning("No se encontraron resultados con esos filtros.")
else:
    for _, item in filtered_df.iterrows():
        # Crear la tarjeta visual con HTML
        codes_list = str(item['Codigos_UNSPSC']).split(',')
        search_list = [c.strip() for c in search_codes.split(',')] if search_codes else []
        
        badges_html = ""
        for c in codes_list:
            cls = "badge-match" if c.strip() in search_list else ""
            badges_html += f'<span class="badge {cls}">{c.strip()}</span>'

        st.markdown(f"""
            <div class="result-card">
                <div class="contratante-header">#{item['Consecutivo']} | {item['Contratante']}</div>
                <div style="margin: 10px 0; font-size: 1rem; color: #1e293b;">{item['Objeto']}</div>
                <div style="display: flex; gap: 20px; background: #f8fafc; padding: 10px; border-radius: 8px;">
                    <div>
                        <small style="color: #64748b; display: block;">VALOR (COP)</small>
                        <strong>{format_currency(item['Valor_COP'])}</strong>
                    </div>
                    <div style="border-left: 2px solid #e2e8f0; padding-left: 20px;">
                        <small style="color: #059669; display: block;">VALOR (SMMLV)</small>
                        <strong style="color: #059669; font-size: 1.2rem;">{item['Valor_SMMLV']:,.2f}</strong>
                    </div>
                </div>
                <div style="margin-top: 10px;">
                    <small style="color: #94a3b8; display: block; margin-bottom: 5px;">CÓDIGOS UNSPSC</small>
                    {badges_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
