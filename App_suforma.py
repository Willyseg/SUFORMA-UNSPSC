import streamlit as st
import pandas as pd
import io

--- CONFIGURACIÓN DE LA PÁGINA ---

st.set_page_config(
page_title="Buscador de Experiencias",
page_icon="📂",
layout="wide"
)

--- ESTILOS CSS PERSONALIZADOS ---

st.markdown("""

<style>
.card {
background-color: #ffffff;
padding: 20px;
border-radius: 10px;
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
margin-bottom: 20px;
border: 1px solid #e2e8f0;
}
.card-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 12px;
border-bottom: 1px solid #f1f5f9;
padding-bottom: 12px;
}
.badge-id {
background-color: #f1f5f9;
color: #475569;
padding: 4px 8px;
border-radius: 4px;
font-size: 0.75em;
font-family: monospace;
font-weight: bold;
}
.badge-consecutivo {
background-color: #eff6ff;
color: #1d4ed8;
border: 1px solid #dbeafe;
padding: 4px 8px;
border-radius: 4px;
font-size: 0.75em;
font-family: monospace;
font-weight: bold;
margin-left: 8px;
}
.contratante {
font-weight: bold;
color: #1e40af;
text-transform: uppercase;
font-size: 0.9em;
}
.label-mini {
font-size: 0.65em;
color: #94a3b8;
text-transform: uppercase;
font-weight: bold;
letter-spacing: 0.05em;
display: block;
margin-bottom: 2px;
}
.objeto-text {
color: #1e293b;
font-size: 0.9em;
margin-bottom: 16px;
line-height: 1.5;
}
.value-grid {
display: grid;
grid-template-columns: 1fr 1fr;
gap: 16px;
background-color: #f8fafc;
padding: 12px;
border-radius: 8px;
border: 1px solid #f1f5f9;
margin-bottom: 16px;
}
.value-cop {
color: #475569;
font-weight: 600;
font-size: 0.9em;
}
.value-smmlv {
color: #047857;
font-weight: bold;
font-size: 1.1em;
}
.tag {
display: inline-block;
background-color: #f8fafc;
color: #64748b;
padding: 2px 8px;
border-radius: 12px;
font-size: 0.75em;
margin-right: 4px;
margin-bottom: 4px;
border: 1px solid #e2e8f0;
}
.tag.highlight {
background-color: #e0e7ff;
color: #4338ca;
border-color: #c7d2fe;
font-weight: bold;
}
</style>

""", unsafe_allow_html=True)

--- DATOS DE MUESTRA ---

SAMPLE_CSV = """ID_Experiencia;Consecutivo;Celebrado_Por;Contratista;Contratante;Objeto;Valor_SMMLV; Valor del contrato a COP en 2024 ;Porcentaje_Participacion;Codigos_UNSPSC
1;1;1 - EL PROPONENTE;SUFORMA S.A.S.;ALCALDIA MUNICIPAL DE CHIA;IMPRESOS;111,31; 144.703.000 ;1;11101500, 11101600, 11101700, 11101800, 11101900, 11111600, 14111500, 14111600, 14111700, 14111800, 14121500, 14121900, 24111500, 24112500, 31101700, 31121900, 31401700, 45101700, 55101500, 55111500, 55121700, 60141000, 60141100, 73151900, 82101500, 82101600, 82101700
"""

--- FUNCIONES ---

@st.cache_data
def load_data(file):
try:
if file is None:
df = pd.read_csv(io.StringIO(SAMPLE_CSV), sep=';')
else:
df = pd.read_csv(file, sep=';', encoding='latin-1')

    df.columns = [c.strip() for c in df.columns]
    
    col_map = {}
    for col in df.columns:
        lower_col = col.lower()
        if 'objeto' in lower_col: col_map['objeto'] = col
        elif 'codigos' in lower_col or 'unspsc' in lower_col: col_map['codigos'] = col
        elif 'contratante' in lower_col: col_map['contratante'] = col
        elif 'valor' in lower_col and 'cop' in lower_col: col_map['valor'] = col
        elif 'smmlv' in lower_col: col_map['smmlv'] = col
        elif 'consecutivo' in lower_col: col_map['consecutivo'] = col
        elif 'id' in lower_col: col_map['id'] = col

    def clean_smmlv(val):
        if pd.isna(val): return 0.0
        val_str = str(val).replace('.', '').replace(',', '.') 
        try: return float(val_str)
        except: return 0.0

    if 'smmlv' in col_map:
        df['smmlv_num'] = df[col_map['smmlv']].apply(clean_smmlv)
    else:
        df['smmlv_num'] = 0.0

    def clean_cop(val):
        if pd.isna(val): return 0
        val_str = str(val).replace('.', '').strip()
        try: return int(val_str)
        except: return 0
        
    if 'valor' in col_map:
        df['cop_num'] = df[col_map['valor']].apply(clean_cop)
    else:
        df['cop_num'] = 0

    st.session_state['col_map'] = col_map
    return df

except Exception as e:
    st.error(f"Error al procesar el archivo: {e}")
    return pd.DataFrame()


--- INTERFAZ ---

st.title("📂 Buscador de Experiencias")

with st.sidebar:
st.header("Configuración")
uploaded_file = st.file_uploader("Cargar CSV (Delimitado por ;)", type=['csv'])
if st.button("Borrar Caché y Recargar"):
st.cache_data.clear()
st.rerun()

df = load_data(uploaded_file)
col_map = st.session_state.get('col_map', {})

if df.empty:
st.warning("No hay datos para mostrar.")
st.stop()

--- FILTROS ---

st.subheader("Filtros de Búsqueda")
c1, c2 = st.columns(2)
with c1:
search_codes = st.text_input("Códigos UNSPSC", placeholder="Ej: 11121600, 14111500")
st.caption("Muestra experiencias que contengan TODOS los códigos.")
with c2:
search_object = st.text_input("Objeto del Contrato", placeholder="Buscar...")
st.caption("Busca texto dentro de la descripción.")

--- LÓGICA ---

filtered_df = df.copy()

if search_object and 'objeto' in col_map:
filtered_df = filtered_df[filtered_df[col_map['objeto']].astype(str).str.contains(search_object, case=False, na=False)]

input_codes_list = []
if search_codes and 'codigos' in col_map:
input_codes_list = [c.strip() for c in search_codes.split(',') if c.strip()]
if input_codes_list:
def check_codes(row_codes):
if pd.isna(row_codes): return False
row_codes_str = str(row_codes)
return all(code in row_codes_str for code in input_codes_list)
filtered_df = filtered_df[filtered_df[col_map['codigos']].apply(check_codes)]

filtered_df = filtered_df.sort_values(by='smmlv_num', ascending=False)

--- DASHBOARD ---

st.divider()
total_count = len(filtered_df)
total_smmlv = filtered_df['smmlv_num'].sum()
total_cop = filtered_df['cop_num'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("Experiencias Encontradas", total_count)
m2.metric("Total SMMLV", f"{total_smmlv:,.2f}")
m3.metric("Presupuesto Total (COP)", f"${total_cop:,.0f}".replace(",", "."))
st.divider()

--- RESULTADOS ---

st.subheader(f"Resultados ({total_count})")

if filtered_df.empty:
st.info("No se encontraron resultados.")
else:
for index, row in filtered_df.iterrows():
r_id = row[col_map.get('id', '')] if 'id' in col_map else index
r_consecutivo = row[col_map.get('consecutivo', '')] if 'consecutivo' in col_map else '-'
r_contratante = row[col_map.get('contratante', '')] if 'contratante' in col_map else 'Desconocido'
r_objeto = row[col_map.get('objeto', '')] if 'objeto' in col_map else ''
r_valor_raw = row[col_map.get('valor', '')] if 'valor' in col_map else '0'
r_smmlv_raw = row[col_map.get('smmlv', '')] if 'smmlv' in col_map else '0'
r_codigos = str(row[col_map.get('codigos', '')]) if 'codigos' in col_map else ''

    codes_html = ""
    if r_codigos and r_codigos.lower() != 'nan':
        code_list = [c.strip() for c in r_codigos.split(',')]
        for code in code_list:
            is_match = code in input_codes_list
            css_class = "tag highlight" if is_match else "tag"
            codes_html += f'<span class="{css_class}">{code}</span>'
    else:
        codes_html = '<span class="tag">Sin códigos</span>'

    # TARJETA HTML: SIN SANGRÍA PARA EVITAR ERROR
    card_html = f"""


<div class="card">
<div class="card-header">
<div><span class="badge-id">ID: {r_id}</span><span class="badge-consecutivo">#{r_consecutivo}</span></div>
<div class="contratante">{r_contratante}</div>
</div>
<div><span class="label-mini">Objeto del Contrato</span><div class="objeto-text">{r_objeto}</div></div>
<div class="value-grid">
<div style="border-right: 1px solid #e2e8f0;"><span class="label-mini">Valor (2024 COP)</span><div class="value-cop">{r_valor_raw}</div></div>
<div style="padding-left: 10px;"><span class="label-mini" style="color: #059669;">Valor (SMMLV)</span><div class="value-smmlv">{r_smmlv_raw}</div></div>
</div>
<div><span class="label-mini">Códigos UNSPSC</span><div>{codes_html}</div></div>
</div>
"""
st.markdown(card_html, unsafe_allow_html=True)
