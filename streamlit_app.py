import google_auth_httplib2
import httplib2
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
import requests

SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SPREADSHEET_ID = "1QlPTiVvfRM82snGN6LELpNkOwVI1_Mp9J9xeJe-QoaA"
SHEET_NAME = "Database"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"


def getWsforUser(email):
    try:
        urlApi = "https://lpul7iylefbdlepxbtbovin4zy.appsync-api.us-west-2.amazonaws.com/graphql"
        header = {"x-api-key": "da2-al2jiagsazhcfaxqtaswe2pi2i"}

        query = (
            """
            query MyQuery {
                get_workspace_info(WSID: 5) {
                    season {
                    name
                    farms {
                        name
                        fields {
                        name
                        }
                    }
                    }
                    name
                }
                }

             """
        )
        request = requests.post(urlApi, json={"query": query}, headers=header)
        result = request.json()
        return result["data"]["get_workspace_info"]

    except:
        return None

st.set_page_config(page_title="Bug report", page_icon="🐞", layout="centered")

st.title("Pedidos de Procesamiento")
st.sidebar.image("https://as.geoagro.com/wp-content/uploads/2022/08/geoagro-1.png",use_column_width=True)

st.sidebar.write(
    f"Esta App ayuda a recibir los pedidos de procesamiento para Geoagro"
)


st.sidebar.write(
    f"[Leer más](https://support.geoagro.com/es/) acerca de esto."
)

form = st.form(key="annotation")


with form:
    cols = st.columns((1, 1))


    userWSs = getWsforUser('acuello@geoagro.com')
    
    optionsWS = userWSs['name']
   
    print (type(optionsWS))

    season= userWSs['season'][0]['name']
        
    
    
    ##Fields
    list_fields=list()
    for item in userWSs["season"][0]['farms'][0]['fields']:
        list_fields.append(item['name'])
    
    ##Farms
    list_farms=list()
    for item in userWSs["season"][0]['farms']:
        list_farms.append(item['name'])

    pedido = cols[0].selectbox("Pedido:", ["Mapa de Productividad", "Procesamiento de Rindes", "Procesamiento de Aplicaciones", ], index=2    )
    dominio = cols[0].selectbox("Dominio:", ["Domain 1", "Domain 2"] )
    workspace = cols[0].selectbox("Workspace:", [optionsWS,] )
    campaña = cols[0].selectbox("Campaña:", [season,] )
    establecimiento = cols[0].selectbox("Establecimiento:", list_farms)
    uploaded_files = st.file_uploader("Monitores", accept_multiple_files=True)
    for uploaded_file in uploaded_files:
        bytes_data = uploaded_file.read()
        st.write("filename:", uploaded_file.name)
        st.write(bytes_data)
    lotes = cols[0].selectbox("Lotes:", list_fields)
    comentarios = st.text_area("Comentarios:")
    date = cols[0].date_input("Fecha")
    bug_severity = cols[1].slider("Urgencia de procesamiento (sólo como ejemplo):", 1, 5, 2)
    submitted = st.form_submit_button(label="Enviar")

if submitted:
    st.success("Gracias! Su pedido fue enviado.",icon="✅")



