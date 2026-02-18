import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(
    page_title="Buscador de Experiencias SuForma",
    page_icon="🔍",
    layout="wide"
)

# CSS Personalizado para ocultar elementos default y mejorar estética
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
    """
    Convierte string formato '144.703.000' a int 144703000
    Elimina puntos.
    """
    if pd.isna(val): return 0
    val_str = str(val).replace('.', '').strip()
    try:
        return int(val_str)
    except ValueError:
        return 0

def clean_smmlv(val):
    """
    Convierte string formato '1.000,00' o '111,31' a float.
    Elimina puntos de miles y reemplaza coma decimal por punto.
    """
    if pd.isna(val): return 0.0
    # Eliminar puntos de miles (ej: 1.000,50 -> 1000,50)
    val_str = str(val).replace('.', '')
    # Reemplazar coma decimal por punto (ej: 1000,50 -> 1000.50)
    val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def identify_columns(df):
    """
    Identifica dinámicamente las columnas clave basándose en palabras clave.
    Retorna un diccionario con el mapeo.
    """
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
    """Carga y limpia los datos desde el archivo subido o el ejemplo."""
    try:
        if uploaded_file is not None:
            # Intentamos detectar separador, pero por defecto el prompt pide coma.
            # Sin embargo, el ejemplo del prompt usa punto y coma. 
            # Usaremos engine='python' y sep=None para autodetectar si es posible,
            # o fallback a los comunes.
            try:
                df = pd.read_csv(uploaded_file, sep=',', engine='python')
                if len(df.columns) < 2: # Si falló la coma
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=';', engine='python')
            except:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=';', engine='python')
        else:
            df = pd.read_csv(io.StringIO(SAMPLE_CSV), sep=';')

        # Mapeo de columnas
        col_map = identify_columns(df)
        
        # Validar que existan las columnas críticas
        missing = [k for k, v in col_map.items() if v is None]
        if missing:
            st.error(f"No se pudieron identificar las siguientes columnas en el archivo: {', '.join(missing)}")
            return None, None

        # Limpieza de datos
        df['clean_smmlv'] = df[col_map['valor_smmlv']].apply(clean_smmlv)
        df['clean_cop'] = df[col_map['valor_cop']].apply(clean_currency_cop)
        
        # Asegurar que UNSPSC sea string para búsquedas
        df[col_map['unspsc']] = df[col_map['unspsc']].astype(str)

        return df, col_map

    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None, None

# -----------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# -----------------------------------------------------------------------------

st.title("💼 Buscador de Experiencias SuForma")
st.markdown("Carga tu base de datos de contratación y encuentra experiencias por códigos UNSPSC o descripción.")

# Sidebar de Carga
with st.sidebar:
    st.header("📂 Cargar Datos")
    uploaded_file = st.file_uploader("Subir archivo CSV", type=['csv'])
    
    st.info("💡 Si no subes archivo, se usarán datos de prueba.")
    st.markdown("---")
    st.markdown("**Instrucciones:**")
    st.markdown("1. El archivo debe ser CSV.")
    st.markdown("2. Formato moneda: 1.000,00 (Europa/Latam).")

# Cargar DataFrame
df, col_map = load_data(uploaded_file)

if df is not None:
    # -------------------------------------------------------------------------
    # FILTROS
    # -------------------------------------------------------------------------
    st.subheader("🔍 Filtros de Búsqueda")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        search_unspsc = st.text_input("Códigos UNSPSC (separados por coma)", placeholder="Ej: 14111500, 11101500")
    
    with c2:
        search_object = st.text_input("Palabra clave en Objeto", placeholder="Ej: Papelería, Mantenimiento...")

    # Lógica de Filtrado
    filtered_df = df.copy()

    # 1. Filtro por Objeto
    if search_object:
        filtered_df = filtered_df[filtered_df[col_map['objeto']].astype(str).str.contains(search_object, case=False, na=False)]

    # 2. Filtro por UNSPSC (Lógica ESTRICTA AND)
    if search_unspsc:
        # Convertir input a lista de códigos limpios
        input_codes = [code.strip() for code in search_unspsc.split(',') if code.strip()]
        
        def has_all_codes(row_codes_str, target_codes):
            if pd.isna(row_codes_str): return False
            # Asumimos que la celda tiene codigos separados por coma u otro
            # Normalizamos la celda
            row_clean = str(row_codes_str).replace(';', ',') 
            row_code_list = [c.strip() for c in row_clean.split(',')]
            
            # Verificar que TODOS los target_codes estén en row_code_list
            return all(target in row_code_list for target in target_codes)

        if input_codes:
            filtered_df = filtered_df[filtered_df[col_map['unspsc']].apply(lambda x: has_all_codes(x, input_codes))]

    # Ordenamiento (Mayor a Menor SMMLV)
    filtered_df = filtered_df.sort_values(by='clean_smmlv', ascending=False)

    # -------------------------------------------------------------------------
    # DASHBOARD DE MÉTRICAS
    # -------------------------------------------------------------------------
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    
    total_count = len(filtered_df)
    total_smmlv = filtered_df['clean_smmlv'].sum()
    total_cop = filtered_df['clean_cop'].sum()

    m1.metric("Experiencias Encontradas", f"{total_count}")
    m2.metric("Valor Total SMMLV", f"{total_smmlv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    m3.metric("Presupuesto Total (COP)", f"$ {total_cop:,.0f}".replace(",", "."))
    
    st.markdown("---")

    # -------------------------------------------------------------------------
    # RESULTADOS (TARJETAS HTML)
    # -------------------------------------------------------------------------
    
    if total_count == 0:
        st.warning("No se encontraron resultados con los filtros aplicados.")
    else:
        for index, row in filtered_df.iterrows():
            # Extracción de datos seguros
            r_id = row[col_map['id']]
            r_consecutivo = row[col_map['consecutivo']]
            r_contratante = row[col_map['contratante']]
            r_objeto = row[col_map['objeto']]
            r_unspsc_str = row[col_map['unspsc']]
            
            # Formateo de números para visualización
            val_cop_fmt = f"$ {row['clean_cop']:,.0f}".replace(",", ".")
            val_smmlv_fmt = f"{row['clean_smmlv']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # Generación de badges para UNSPSC
            codes_list = [c.strip() for c in str(r_unspsc_str).replace(';', ',').split(',')]
            tags_html = ""
            for code in codes_list:
                if code: # evitar vacíos
                    tags_html += f"<span style='background-color: #e2e8f0; color: #475569; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-right: 4px; display: inline-block; margin-bottom: 2px;'>{code}</span>"

            # Renderizado HTML de la Tarjeta
            # NOTA: HTML pegado a la izquierda para evitar problemas de indentación
            card_html = f"""
<div style="background-color: white; border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; margin-bottom: 10px; color: #888; font-size: 0.85rem;">
<span>ID: {r_id}</span>
<span>Consecutivo: {r_consecutivo}</span>
</div>
<div style="font-size: 1.1rem; font-weight: bold; color: #1e293b; margin-bottom: 5px;">
{r_contratante}
</div>
<div style="font-size: 0.95rem; color: #475569; margin-bottom: 15px; line-height: 1.5;">
{r_objeto}
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background-color: #f8fafc; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
<div>
<div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Valor COP</div>
<div style="font-size: 1rem; font-weight: 600; color: #334155;">{val_cop_fmt}</div>
</div>
<div>
<div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Valor SMMLV</div>
<div style="font-size: 1rem; font-weight: bold; color: #16a34a;">{val_smmlv_fmt}</div>
</div>
</div>
<div>
<div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 5px;">Códigos UNSPSC:</div>
<div>{tags_html}</div>
</div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
