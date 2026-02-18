import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Buscador de Experiencias", layout="wide")

# --- LÓGICA DE DETECCIÓN DE COLUMNAS ---
def find_column(df, possible_names):
    """Busca una columna que contenga alguna de las palabras clave"""
    for col in df.columns:
        for name in possible_names:
            if name.lower() in col.lower():
                return col
    return None

# Estilo visual
st.markdown("""
    <style>
    .result-card { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .contratante-header { color: #1e40af; font-weight: bold; text-transform: uppercase; font-size: 0.9rem; }
    .badge { background-color: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-right: 5px; border: 1px solid #e2e8f0; }
    .badge-match { background-color: #e0e7ff; color: #4338ca; font-weight: bold; border: 1px solid #c7d2fe; }
    </style>
""", unsafe_allow_html=True)

# Datos de muestra
SAMPLE_DATA = """ID_Experiencia;Consecutivo;Contratante;Objeto;Valor_SMMLV;Valor_COP;Codigos_UNSPSC
1;1;ALCALDIA DE CHIA;IMPRESOS;111.31;144703000;11101500, 14111500"""

st.sidebar.title("⚙️ Configuración")
uploaded_file = st.sidebar.file_uploader("Cargar archivo CSV (Separado por ;)", type=["csv"])

if uploaded_file is not None:
    # Intentamos leer con diferentes encodings por si acaso
    try:
        df = pd.read_csv(uploaded_file, sep=";", encoding="latin1")
    except:
        df = pd.read_csv(uploaded_file, sep=";", encoding="utf-8")
    st.sidebar.success("¡Archivo cargado!")
else:
    df = pd.read_csv(io.StringIO(SAMPLE_DATA), sep=";")
    st.sidebar.info("Usando datos de muestra")

# --- ASIGNACIÓN INTELIGENTE DE COLUMNAS ---
# Buscamos los nombres reales de las columnas en tu archivo
col_objeto = find_column(df, ['objeto']) or df.columns[min(5, len(df.columns)-1)]
col_cop = find_column(df, ['valor del contrato', 'valor_cop', 'cop']) or df.columns[min(7, len(df.columns)-1)]
col_smmlv = find_column(df, ['smmlv']) or df.columns[min(6, len(df.columns)-1)]
col_codes = find_column(df, ['codigos', 'unspsc']) or df.columns[-1]
col_contratante = find_column(df, ['contratante']) or df.columns[min(4, len(df.columns)-1)]
col_consecutivo = find_column(df, ['consecutivo']) or df.columns[min(1, len(df.columns)-1)]

# Limpieza de números
for c in [col_smmlv, col_cop]:
    if df[c].dtype == object:
        df[c] = df[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

# --- PANEL DE BÚSQUEDA ---
st.title("🔍 Buscador de Experiencias")

c1, c2 = st.columns(2)
with c1:
    search_codes = st.text_input("🏷️ Códigos UNSPSC", placeholder="Ej: 11101500")
with c2:
    search_obj = st.text_input("📄 Objeto del Contrato", placeholder="Buscar...")

# --- FILTRADO ---
mask_obj = df[col_objeto].str.contains(search_obj, case=False, na=False) if search_obj else True
mask_codes = True
if search_codes:
    search_list = [c.strip() for c in search_codes.split(',') if c.strip()]
    mask_codes = df[col_codes].apply(lambda x: all(str(s) in str(x) for s in search_list) if pd.notna(x) else False)

filtered_df = df[mask_obj & mask_codes].sort_values(by=col_smmlv, ascending=False)

# --- DASHBOARD ---
m1, m2, m3 = st.columns(3)
m1.metric("Experiencias", len(filtered_df))
m2.metric("Total SMMLV", f"{filtered_df[col_smmlv].sum():,.2f}")
m3.metric("Total COP", f"$ {filtered_df[col_cop].sum():,.0f}".replace(",", "."))

st.divider()

# --- RESULTADOS ---
if filtered_df.empty:
    st.warning("No hay resultados.")
else:
    for _, item in filtered_df.iterrows():
        # Lógica de badges
        current_codes = str(item[col_codes]).split(',')
        search_terms = [c.strip() for c in search_codes.split(',')] if search_codes else []
        badges = "".join([f'<span class="badge {"badge-match" if c.strip() in search_terms else ""}">{c.strip()}</span>' for c in current_codes])

        st.markdown(f"""
            <div class="result-card">
                <div class="contratante-header">#{item[col_consecutivo]} | {item[col_contratante]}</div>
                <div style="margin: 10px 0;">{item[col_objeto]}</div>
                <div style="display: flex; gap: 20px; background: #f8fafc; padding: 10px; border-radius: 8px;">
                    <div><small>COP</small><br><strong>$ {item[col_cop]:,.0f}</strong></div>
                    <div style="border-left: 2px solid #ddd; padding-left: 20px;">
                        <small style="color: green;">SMMLV</small><br><strong style="color: green; font-size: 1.2rem;">{item[col_smmlv]:,.2f}</strong>
                    </div>
                </div>
                <div style="margin-top: 10px;">{badges}</div>
            </div>
        """, unsafe_allow_html=True)
