import logging
import streamlit as st
import pandas as pd
import folium
import requests
from streamlit_folium import folium_static
import json


urlApi="https://f2lzsiec4jdvfj3skzyuvxkil4.appsync-api.us-east-1.amazonaws.com/graphql"
header = {"x-api-key": "da2-pzzdaq5habgdpbhpaxwlngah7e"}


def getData(kobo_token):
        try:
            query=(
                """
                query MyQuery {
                listProjects (filter: {kobo_token: {eq: "%s"}})  {
                    items {
                    id
                    name
                    kobo_token
                    forms_definition {
                        items {
                        id
                        definition
                        submits {
                            items {
                            data
                            geolocation
                            attachments
                            submitted_by
                            submission_time
                            }
                        }
                        }
                    }
                    }
                }
                }

                """
                % (kobo_token)
            )
            
            request = requests.post(urlApi, json={"query": query}, headers=header, timeout=60)
            if request.status_code == 200:
                return request.json()
            else:
                raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        except Exception as exception:
            logging.error(exception)


def syncDataKoboTokenServer(kobo_token):
    try:
        mutation=(
            """
            mutation MyMutation {
            syncDataKoboTokenServer(token: "%s", server: "https://kf.kobotoolbox.org/api/v2") {
                message
                success
            }
            }
            """
            % (kobo_token)
        )
        
        request = requests.post(urlApi, json={"query": mutation}, headers=header, timeout=60)
        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, mutation))
    except Exception as exception:
        logging.error(exception)


# Define a Streamlit function to display the map
def display_map():
    tooltip_width = '400px'
    m.get_root().html.add_child(folium.Element(f'.leaflet-tooltip{{max-width: {tooltip_width};}}'))
    folium_static(m, 1200,800)
    


# Define a Streamlit function to display a tooltip for a selected data point
def display_tooltip():
    # Get the index of the selected data point
    index = st.session_state.selected_index
    if index is not None:
        # Display the tooltip for the selected data point
        st.write(data.loc[index, "Name"])
        st.write("Latitude:", data.loc[index, "Latitude"])
        st.write("Longitude:", data.loc[index, "Longitude"])

st.set_page_config(page_title="Recorridas",layout="wide")
st.title("Recorridas")

# Define the Streamlit form
with st.form("my_form"):
    
    # Add a text input field to the form
    token_input_text = st.text_input("1- Ingrese el Kobo Token", value='71fc459f827710c4ab918771a017b45e0373d6e3')

    st.write("2- Sincronizar los datos de Kobo.")

    sync_button=st.form_submit_button("Sincronizar")
    if sync_button:
        with st.spinner('Espere por favor...'):
            result_sync=syncDataKoboTokenServer(token_input_text)
            if result_sync['data']['syncDataKoboTokenServer']['success']:
                st.info("Sincronización existosa.")
            else:
                st.error(result_sync['data']['syncDataKoboTokenServer']['message'])
            

    # Add a submit button to the form
    
    st.write("3- Verificar los datos sincronizados.")

    submit_button = st.form_submit_button("Consultar")

    # Define behavior for when the form is submitted
    if submit_button and token_input_text is not None:
        # Load sample data

        with st.spinner('Espere por favor...'):
            data = getData(token_input_text)

        if data['data']['listProjects']['items']!=[]:
            
            m = folium.Map(location=[-34.603722, -58.381592], zoom_start=5)

            # iterate over the items in the listProjects object
            table_data = []

            for project in data['data']['listProjects']['items']:
                # iterate over the forms in each project
                for definition in project['forms_definition']['items']:
                    # iterate over the submissions in each form
                    for submit in definition['submits']['items']:
                        # print the submission data and submission time

                        row = {'Project Name (Form)': project['name'], 'Definition (id version)':definition['id'] , 'Submits (data)':submit ['data']}
                        table_data.append(row)

                        try: 

                            keys_standard_form={'_attachments','_geolocation','meta/rootUuid','meta/deprecatedID'}
                            sub=json.loads(submit['data'])

                            submit2={ k:v for k,v in sub.items() if k not in keys_standard_form }
                            
                            url_attachment=json.loads(submit['attachments'])[0]['url']

                            tooltip=folium.Tooltip(
                                '<div style="text-align:center"><img src="'+url_attachment+'"style="max-width:200px;"><br>'+project['name']+'<br>'+"Fecha Muestra: "+submit['submission_time']+'<br>'+"Ubicación: "+str(submit['geolocation'])+'<br>'+"Datos: "+'<pre>{}</pre>'.format(json.dumps(submit2, indent=2))+'<br></div>',
                                sticky=True,
                                direction='top'
                            )
                            folium.Marker([submit['geolocation'][0],submit['geolocation'][1]],
                                tooltip=tooltip).add_to(m)
                            
                            
                        except Exception as exs:
                            print (exs)
                            continue
            
            df = pd.DataFrame(table_data)
            st.table(df)

            # Display the map and allow the user to select a data point
            with st.container():
                try:
                    st.write("## Map")
                    display_map()
                    selected_point = folium.ClickForMarker(popup="Selected Point")
                    folium_static(selected_point)
                except:
                    pass

            # Display the tooltip for the selected data point
            with st.container():
                try:
                    display_tooltip()
                except:
                    pass
        else:
            st.error("No se encontró información asociada a ese token.")
