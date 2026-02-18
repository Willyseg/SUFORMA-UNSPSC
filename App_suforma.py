import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(
    page_title="Buscador de Experiencias SuForma",
    page_icon="🔍",
    layout="wide"
)

# CSS Personalizado para mejorar estética
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
        color: #0f54c9;
    }
    .stTextInput > label {
        font-weight: bold;
        color: #333;
    }
    .stDownloadButton > button {
        width: 100%;
        background-color: #16a34a !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATOS DE PRUEBA (Dummy Data)
# -----------------------------------------------------------------------------
SAMPLE_CSV = """ID_Experiencia;Consecutivo;Celebrado_Por;Contratista;Contratante;Objeto;Valor_SMMLV;Valor COP;Porcentaje_Participacion;Codigos_UNSPSC
1;001;EL PROPONENTE;SUFORMA;ALCALDIA EJEMPLO;SUMINISTRO DE PAPELERIA E IMPRESOS;111,31;144.703.000;1;11101500, 14111500
2;002;CONSORCIO;SUFORMA;GOBERNACION DEL VALLE;DOTACION DE MOBILIARIO ESCOLAR;50,5;65.000.000;0.5;56121000, 56101700
3;003;UNION TEMPORAL;SUFORMA;HOSPITAL SAN JORGE;MANTENIMIENTO DE EQUIPOS DE COMPUTO;200,00;260.000.000;1;81111800, 81112300
4;004;EL PROPONENTE;SUFORMA;ALCALDIA DE PEREIRA;SUMINISTRO DE ELEMENTOS DE ASEO Y CAFETERIA;10,00;13.000.000;1;47131800, 14111700
5;005;EL PROPONENTE;SUFORMA;SENA REGIONAL;ADQUISICION DE MATERIAL DE FORMACION;80,20;104.260.000;1;14111500, 44121700"""

# -----------------------------------------------------------------------------
# FUNCIONES DE LIMPIEZA Y CARGA
# -----------------------------------------------------------------------------

def clean_currency_cop(val):
    if pd.isna(val): return 0
    val_str = str(val).replace('.', '').strip()
    try:
        return int(val_str)
    except ValueError:
        return 0

def clean_smmlv(val):
    if pd.isna(val): return 0.0
    val_str = str(val).replace('.', '')
    val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def identify_columns(df):
    cols = df.columns
    cols_lower = [c.lower() for c in cols]
    
    mapping = {
        'id': None,
        'consecutivo': None,
        'contratante': None,
        'objeto': None,
        'valor_cop': None,
        'valor_smmlv': None,
        'unspsc': None
    }

    for actual_col, lower_col in zip(cols, cols_lower):
        if 'id' in lower_col and mapping['id'] is None: mapping['id'] = actual_col
        elif 'consecutivo' in lower_col: mapping['consecutivo'] = actual_col
        elif 'contratante' in lower_col: mapping['contratante'] = actual_col
        elif 'objeto' in lower_col: mapping['objeto'] = actual_col
        elif ('valor' in lower_col or 'presupuesto' in lower_col) and 'cop' in lower_col: mapping['valor_cop'] = actual_col
        elif 'smmlv' in lower_col: mapping['valor_smmlv'] = actual_col
        elif 'unspsc' in lower_col or 'codigos' in lower_col: mapping['unspsc'] = actual_col

    return mapping

def load_data(uploaded_file):
    try:
        if uploaded_file is not None:
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
            df = None
            for encoding in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=';', encoding=encoding)
                    if len(df.columns) < 2:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep=',', encoding=encoding)
                    if len(df.columns) >= 2:
                        break
                except Exception:
                    continue
            if df is None:
                st.error("No se pudo leer el archivo. Asegúrate de que sea un CSV válido.")
                return None, None
        else:
            df = pd.read_csv(io.StringIO(SAMPLE_CSV), sep=';')

        col_map = identify_columns(df)
        missing = [k for k, v in col_map.items() if v is None]
        if missing:
            st.error(f"No se pudieron identificar las siguientes columnas en el archivo: {', '.join(missing)}")
            return None, None

        df['clean_smmlv'] = df[col_map['valor_smmlv']].apply(clean_smmlv)
        df['clean_cop'] = df[col_map['valor_cop']].apply(clean_currency_cop)
        df[col_map['unspsc']] = df[col_map['unspsc']].astype(str)

        return df, col_map
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None, None

def convert_df_to_excel(df):
    """Convierte el DataFrame filtrado a un archivo Excel en memoria."""
    output = io.BytesIO()
    # Usamos el motor 'openpyxl' (asegúrate de incluirlo en requirements.txt)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados_Busqueda')
    return output.getvalue()

# -----------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# -----------------------------------------------------------------------------

st.title("💼 Buscador de Experiencias SuForma")
st.markdown("Carga tu base de datos de contratación y encuentra experiencias por códigos UNSPSC o descripción.")

with st.sidebar:
    st.header("📂 Cargar Datos")
    uploaded_file = st.file_uploader("Subir archivo CSV", type=['csv'])
    st.info("💡 Si no subes archivo, se usarán datos de prueba.")
    st.markdown("---")
    st.markdown("**Instrucciones:**")
    st.markdown("1. El archivo debe ser CSV.")
    st.markdown("2. Formato moneda: 1.000,00 (Europa/Latam).")

df, col_map = load_data(uploaded_file)

if df is not None:
    st.subheader("🔍 Filtros de Búsqueda")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        search_unspsc = st.text_input("Códigos UNSPSC (separados por coma)", placeholder="Ej: 14111500, 11101500")
    
    with c2:
        search_object = st.text_input("Palabra clave en Objeto", placeholder="Ej: Papelería, Mantenimiento...")

    filtered_df = df.copy()
    input_codes = []

    if search_object:
        filtered_df = filtered_df[filtered_df[col_map['objeto']].astype(str).str.contains(search_object, case=False, na=False)]

    if search_unspsc:
        input_codes = [code.strip() for code in search_unspsc.split(',') if code.strip()]
        
        def has_all_codes(row_codes_str, target_codes):
            if pd.isna(row_codes_str): return False
            row_clean = str(row_codes_str).replace(';', ',') 
            row_code_list = [c.strip() for c in row_clean.split(',')]
            return all(target in row_code_list for target in target_codes)

        if input_codes:
            filtered_df = filtered_df[filtered_df[col_map['unspsc']].apply(lambda x: has_all_codes(x, input_codes))]

    filtered_df = filtered_df.sort_values(by='clean_smmlv', ascending=False)

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    total_count = len(filtered_df)
    total_smmlv = filtered_df['clean_smmlv'].sum()
    total_cop = filtered_df['clean_cop'].sum()

    m1.metric("Experiencias Encontradas", f"{total_count}")
    m2.metric("Valor Total SMMLV", f"{total_smmlv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    m3.metric("Presupuesto Total (COP)", f"$ {total_cop:,.0f}".replace(",", "."))
    
    # -------------------------------------------------------------------------
    # BOTÓN DE DESCARGA
    # -------------------------------------------------------------------------
    if total_count > 0:
        excel_data = convert_df_to_excel(filtered_df)
        st.download_button(
            label="📊 Descargar resultados en Excel",
            data=excel_data,
            file_name="experiencias_suforma_filtrado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("---")

    if total_count == 0:
        st.warning("No se encontraron resultados con los filtros aplicados.")
    else:
        for index, row in filtered_df.iterrows():
            r_id = row[col_map['id']]
            r_consecutivo = row[col_map['consecutivo']]
            r_contratante = row[col_map['contratante']]
            r_objeto = row[col_map['objeto']]
            r_unspsc_str = row[col_map['unspsc']]
            
            val_cop_fmt = f"$ {row['clean_cop']:,.0f}".replace(",", ".")
            val_smmlv_fmt = f"{row['clean_smmlv']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # Lógica para badges con resaltado
            codes_list = [c.strip() for c in str(r_unspsc_str).replace(';', ',').split(',')]
            tags_html = ""
            for code in codes_list:
                if not code: continue
                # Si el código actual está en la lista de búsqueda, aplicar estilo resaltado
                is_searched = code in input_codes
                bg_color = "#3b82f6" if is_searched else "#e2e8f0"
                text_color = "white" if is_searched else "#475569"
                border = "2px solid #2563eb" if is_searched else "none"
                weight = "bold" if is_searched else "normal"
                
                tags_html += f"<span style='background-color: {bg_color}; color: {text_color}; border: {border}; font-weight: {weight}; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; margin-right: 6px; display: inline-block; margin-bottom: 5px;'>{code}</span>"

            card_html = f"""
<div style="background-color: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; margin-bottom: 10px; color: #888; font-size: 0.85rem;">
<span>ID: {r_id}</span>
<span>Consecutivo: {r_consecutivo}</span>
</div>
<div style="font-size: 1.2rem; font-weight: bold; color: #1e293b; margin-bottom: 8px;">
{r_contratante}
</div>
<div style="font-size: 1rem; color: #475569; margin-bottom: 18px; line-height: 1.5; border-left: 3px solid #cbd5e1; padding-left: 12px;">
{r_objeto}
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; background-color: #f8fafc; padding: 12px; border-radius: 10px; margin-bottom: 18px;">
<div>
<div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Valor COP</div>
<div style="font-size: 1.1rem; font-weight: 600; color: #334155;">{val_cop_fmt}</div>
</div>
<div>
<div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Valor SMMLV</div>
<div style="font-size: 1.1rem; font-weight: bold; color: #16a34a;">{val_smmlv_fmt}</div>
</div>
</div>
<div>
<div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px; font-weight: 600;">CÓDIGOS UNSPSC:</div>
<div>{tags_html}</div>
</div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
