import logging
import time
import webbrowser
import streamlit as st
import streamlit_google_oauth as oauth
import datasource as ds
import pandas as pd
from datetime import datetime
from secretManager import AWSSecret
from jira import create_issue_jira
from helper import is_not_empty, re, validateParticipants, upload_file_to_bucket, createGrid, get_limit_date, decrypt_token, traslate
from streamlit_elements import elements, mui, html, sync
from streamlit_tags import st_tags
from PIL import Image
import extra_streamlit_components as stx
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from dateutil.relativedelta import relativedelta
import os.path


client_id = "420866573912-f2hoi3eslaqauot1i4e888u969lv2dk8.apps.googleusercontent.com"
client_secret = "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"
#redirect_uri=" http://localhost:8501"
redirect_uri="https://datarequest.geoagro.com/"



def clear_fields_data():
    #Info Fields Procesamiento de Aplicaciones
    try:
        st.session_state['unidad_input']=""
    except:
        pass
    try:
        st.session_state['insumo_input']=""
    except:
        pass
    try:
        st.session_state['prescripcion_input']=""
    except:
        pass
    #Info Fields Mapas Interpolados
    try:
        st.session_state['formato_input']=[]
    except:
        pass
    try:
        st.session_state['especificaciones_input']=""
    except:
        pass
    try:
        st.session_state['variable_interpolar_input']=[]
    except:
        pass
    #Info Fields Mapas de Productividad
    try:
        st.session_state['consideraciones_input']=""
    except:
        pass
    try:#Info Fields Procesamiento de Rindes
        st.session_state['rinde_prom_input']=""
    except:
        pass

def clear_data():
    try:
        ####### DELETE ALL FIELDS WHEN REQUEST IS CHANGED ######
        try:
            del st.session_state['request']
            del st.session_state['domain']['id']
            del st.session_state['domain']['name']
            try:
                del st.session_state['area']['id']
                del st.session_state['area']['name']
            except:
                pass
            try:
                del st.session_state['workspace']['id']
            except:
                pass
            try:
                del st.session_state['workspace']['name']
            except:
                pass
            try:
                del st.session_state['season']['id']
            except:
                pass
            try:
                del st.session_state['season']['name']
            except:
                pass
            try:
                del st.session_state['farm']['id']
            except:
                pass
            try:    
                del st.session_state['farm']['name']
            except:
                pass
            try:
                del st.session_state['date_start_harvest']
            except:
                pass
            try:
                del st.session_state['date_end_harvest']
            except:
                pass
            try:
                del st.session_state['date_limit']
            except:
                pass
            try:
                del st.session_state['data']
            except:
                pass
            
            clear_fields_data()

            #Info Adicional
            st.session_state['reason_input']=""
            st.session_state['comments_input']=""
            st.session_state['participants_input']=[]

    
            del st.session_state['uploaded_files']
        except Exception as exception:
            logging.error (exception)
    except:
        pass


def main_app(user_info):

    ##################### GENERAL CONFIG  #####################

    st.set_page_config(page_title="Data Request - Geoagro", initial_sidebar_state="expanded",page_icon="https://site.geoagro.com/wp-content/uploads/2022/09/favicon-geoagro-nuevo-13.svg")

    ##################### USER INFO #####################
    
    language=user_info['language']
    email=user_info['email']
    env=user_info['env']
    st.session_state['env']=env

    ##################### LANGUAGE  #####################

    c_1,c_2,c_3=st.columns([1,5,1], gap="small")
    with c_3:   
        try:
            langs = ['es','en','pt']
            if language is not None:
                lang=st.selectbox(traslate("language",language),label_visibility="hidden",options=langs, index=langs.index(language))
            else: ## from public link
                lang=st.selectbox(traslate("es",language),label_visibility="hidden", options=langs)
            st.session_state['lang']=lang
        except Exception as exception:
            lang="es"
            st.session_state['lang']=lang
            pass

    ##################### SIDEBAR  #####################
    with st.sidebar:
        selected3 = option_menu(traslate("menu",lang), [traslate("select_type_of_service",lang), traslate("select_farm",lang), traslate("select_field_and_params",lang),traslate("select_files",lang), traslate("additional_info",lang)], 
        icons=['None', 'None', 'None', 'None', 'None'], 
        menu_icon="None", 
        default_index=0, 
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#ffffff"},
            "nav-link": {"color":"rgba(0, 0, 0, 0.87)","font-size": "1rem", "font-family":"Roboto","font-weight":400,"text-align": "left", "margin":"0px", "--hover-color": "rgb(236, 236, 238)"},
            "nav-link-selected": {"background-color": "rgb(236, 236, 238)","color":"rgba(0, 0, 0, 0.87)", "font-size": "1rem", "font-family":"Roboto","font-weight":400},
        }
        )
        st.markdown(
            """
            <style>
                div [data-testid=stImage]{
                    position: fixed;
                    bottom:0;
                    display: flex;
                    margin-bottom:10px;
                }
            </style>
            """, unsafe_allow_html=True
            )
            
        
        cI1,cI2,cI3=st.columns([1,4,1], gap="small")
        with cI1:
            pass
        with cI2:
            image = Image.open('./assets/bygeoagro.png')
            new_image = image.resize((220, 35))
            st.image(new_image)
        with cI3:
            pass
        


     
    ##################### HEADER  #####################
    st.subheader(traslate("title",lang))

    st.markdown(f'{traslate("requested_by",lang)}<a style="color:blue;font-size:18px;">{" "+email+""}</a> | <a style="color:blue;font-size:16px;" target="_self" href="/"> {traslate("logout",lang)}</a>', unsafe_allow_html=True)
    
    ##################### STYLES #####################
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


    ##################### SCROLLING SECTIONS #####################
    
    #option_selected = stx.stepper_bar(steps=["Nuevo Pedido", "Fecha Límite", "Lotes a procesar", "Monitores y Archivos a Procesar", "Consideraciones"])

    if selected3==traslate("select_type_of_service",lang):
        components.html(f"""<script>window.parent.document.querySelector('section.main').scrollTo(0, 50);</script>""",height=0)
       
    if selected3==traslate("select_farm",lang):
        components.html(f"""<script>window.parent.document.querySelector('section.main').scrollTo(0, 400);</script>""",height=0)
           
    if selected3==traslate("select_field_and_params",lang):
        components.html(f"""<script>window.parent.document.querySelector('section.main').scrollTo(0, 750);</script>""",height=0)
    
    if selected3==traslate("select_files",lang):
       components.html(f"""<script>window.parent.document.querySelector('section.main').scrollTo(0, 1800);</script>""",height=0)
    
    if selected3==traslate("additional_info",lang):
        components.html(f"""<script>window.parent.document.querySelector('section.main').scrollTo(0, 2400);</script>""",height=0)
    
       
    ##################### EMAIL #####################
        
    st.session_state['email']=email
    
    st.markdown('----')
    
    ##################### REQUEST #####################
    st.subheade=traslate("select_type_of_service",lang)

    request=None

    options_request=[traslate("app_processing",lang),traslate("interpolated_maps",lang),traslate("productivity_maps",lang), traslate("yields_processing",lang)]
    try:
        st.subheader(traslate("select_type_of_service",lang))
        request= st.selectbox('as',label_visibility="hidden", key="selected_request", options=options_request,help=traslate("help_type_of_service",lang))
        
        try:
            if request!=st.session_state['request']:
                clear_data()
        except:
            pass

        st.session_state['request']=request
    except Exception as exception:
        logging.error (exception)
        st.warning(traslate("error_type_of_request",lang), icon="⚠️") 
   
    st.markdown('----')

    ##################### DOMAIN #####################
    
    colu1, colu2= st.columns([4,3], gap="small")
    with colu1:
        st.subheader(traslate("select_farm",lang))
    with colu2:
        with st.spinner(""):
            userDomains = ds.Obteniendo_DominiosyAreas(email, env)
            if userDomains is None:
                st.session_state['denied']=True
                st.error(traslate("error_accessing",lang))
                st.stop()
            else:
                st.session_state['denied']=False

    c1, c2, c3, c4 = st.columns([3,3,4,3], gap="small")

    with c1:
        try:
            ds_ids=list()
            ds_names=list()
            for domain in userDomains:
                ds_names.append(domain['name'])
                ds_ids.append(domain['id'])
                
            df_ds = pd.DataFrame({"id": ds_ids, "name": ds_names})
            df_ds.sort_values(by=['name'], inplace=True, key=lambda x: x.str.lower())

            records_domains = df_ds.to_dict("records")

            ###DEFAULT DOMAIN ACCORDING 360 USER
            try:
                ds_index_360 = next((index for (index, d) in enumerate(records_domains) if d["id"] == user_info['domainId']), None)
                domain = st.selectbox(traslate("domain",lang), index=ds_index_360, options=records_domains, format_func=lambda record: f'{record["name"]}')
            except:
                domain = st.selectbox(traslate("domain",lang), options=records_domains, format_func=lambda record: f'{record["name"]}')
            st.session_state['domain'] = domain
        
        except Exception as exception:
            logging.error (exception)

            st.warning(traslate("error_getting_domains",lang), icon="⚠️")

    ##################### AREA #####################
    with c2:
        try:
            areas_names=list()
            areas_ids=list()

            areas_names.append("--") ##### FOR DOMAINS WITHOUT AREAS
            areas_ids.append(0) ##### FOR DOMAINS WITHOUT AREAS

            for item_domain in userDomains:
                if item_domain["deleted"]==False and domain["id"]==item_domain["id"]:
                    for item_area in item_domain['areas']:
                        if item_area['deleted']==False:
                            areas_names.append(item_area['name'])
                            areas_ids.append(item_area['id'])
                    
            
            df_areas = pd.DataFrame({"id": areas_ids, "name": areas_names})

            df_areas.sort_values(by=['name'], inplace=True, key=lambda x: x.str.lower())

            records_areas = df_areas.to_dict("records")

            ###DEFAULT AREA ACCORDING 360 USER
            try:
                area_index_360 = next((index for (index, d) in enumerate(records_areas) if d["id"] == user_info['areaId']), None)
                area = st.selectbox(traslate("area",lang),   index=area_index_360, options=records_areas, format_func=lambda record: f'{record["name"]}')
            except:
                area = st.selectbox(traslate("area",lang), options=records_areas, format_func=lambda record: f'{record["name"]}')

            st.session_state['area'] = area
                
        except Exception as exception:
            logging.error (exception)
            st.warning(traslate("error_getting_areas",lang), icon="⚠️")

    ##################### WORKSPACE ##################### 
    with c3:
        try:
            ws_names=list()
            ws_ids=list()

            if area['name']=="--":
                for item_domain in userDomains:
                    if item_domain["deleted"]==False and domain["id"]==item_domain["id"]:
                        for workspace in item_domain["workspaces"]:
                            if workspace["deleted"]==False:
                                ws_names.append(workspace['name'])
                                ws_ids.append(workspace['id'])
            else:
                for item_domain in userDomains:
                    for area_item in item_domain["areas"]:
                        if area_item["deleted"]==False and area_item['id']==area['id']: 
                            for workspace in area_item["workspaces"]:
                                if workspace["deleted"]==False:
                                    ws_names.append(workspace['name'])
                                    ws_ids.append(workspace['id'])
            
            df_workspaces = pd.DataFrame({"id": ws_ids, "name": ws_names})

            if df_workspaces.empty:
                st.warning(traslate("error_without_workspaces",lang), icon="⚠️")
            else:
                df_workspaces.sort_values(by=['name'], inplace=True, key=lambda x: x.str.lower())

                records_workspaces = df_workspaces.to_dict("records")

                ###DEFAULT WORKSPACE ACCORDING 360 USER
                try:
                    ws_index_360 = next((index for (index, d) in enumerate(records_workspaces) if d["id"] == user_info['workspaceId']), None)
                    workspace = st.selectbox(traslate("workspace",lang), index=ws_index_360, options=records_workspaces, format_func=lambda record: f'{record["name"]}')
                except:
                    workspace = st.selectbox(traslate("workspace",lang), options=records_workspaces, format_func=lambda record: f'{record["name"]}')

                st.session_state['workspace'] = workspace
        
        except Exception as exception:
            logging.error (exception)
            st.warning(traslate("error_getting_workspace",lang), icon="⚠️")

    ##################### CAMPAIGN ##################### 
    with c4:
        try:
            seasons = ds.Obteniendo_Campañas(workspace['id'],env)
            if len(seasons)==0:
                st.warning(traslate("error_without_campaigns",lang)+email, icon="⚠️")
            else:
                if seasons is not None:
                    seasons_names=list()
                    seasons_ids=list()
                
                    for item in seasons:
                        seasons_names.append(item['name'])
                        seasons_ids.append(item['id'])

                    df_seasons = pd.DataFrame({"id": seasons_ids, "name": seasons_names})

                    df_seasons.sort_values(by=['id'],ascending=False, inplace=True)

                    records_seasons = df_seasons.to_dict("records")

                    ###DEFAULT SEASON ACCORDING 360 USER
                    try:
                        season_index_360 = next((index for (index, d) in enumerate(records_seasons) if d["id"] == user_info['seasonId']), None)
                        season = st.selectbox(traslate("campaign",lang),index=season_index_360, options=records_seasons, format_func=lambda record: f'{record["name"]}')
                    except:
                        season = st.selectbox(traslate("campaign",lang), options=records_seasons, format_func=lambda record: f'{record["name"]}')

                    st.session_state['season'] = season
                else:
                    st.warning(traslate("error_getting_campaign",lang), icon="⚠️") 
        except Exception as exception:
            logging.error (exception)
            st.warning(traslate("error_getting_campaign",lang), icon="⚠️") 

    ##################### FARMS ##################### 
    try:
        if len(seasons)==0:
            st.warning(traslate("error_without_farms",lang)+email, icon="⚠️")
        else:
            farms = ds.Obteniendo_Establecimientos(workspace['id'],season["id"], env, email)
            if len(farms)==0:
                st.warning(traslate("error_without_farms",lang)+email, icon="⚠️")
            else:
                if farms is not None:
                    farms_names=list()
                    farms_ids=list()
                
                    for item in farms:
                        farms_names.append(item['name'])
                        farms_ids.append(item['id'])

                    df_farms = pd.DataFrame({"id": farms_ids, "name": farms_names})
                    df_farms.sort_values(by=['name'], inplace=True, key=lambda x: x.str.lower())

                    records_farms = df_farms.to_dict("records")

                    ###DEFAULT SEASON ACCORDING 360 USER
                    try:
                        farm_index_360 = next((index for (index, d) in enumerate(records_farms) if d["id"] == user_info['farmId']), None)
                        farm = st.selectbox(traslate("farm",lang), index=farm_index_360, options=records_farms, format_func=lambda record: f'{record["name"]}', help="Si cambia el establecimiento, se eliminarán los lotes cargados previamente.")
                    except:
                        farm = st.selectbox(traslate("farm",lang), options=records_farms, format_func=lambda record: f'{record["name"]}', help="Si cambia el establecimiento, se eliminarán los lotes cargados previamente.")
                    
                    try:
                        if farm!=st.session_state['farm'] and len(st.session_state['farm'])!=0:
                            ####### DELETE FIELDS  ######
                            del st.session_state['data']
                            del st.session_state['uploaded_files']
                    except:
                            pass
                    st.session_state['farm'] = farm
                else:
                    st.warning(traslate("error_getting_farms",lang), icon="⚠️") 
    except Exception as exception:
        logging.error (exception)
        st.warning(traslate("error_getting_farms",lang), icon="⚠️")
    
    st.markdown('----')

    ##################### FIELDS AND PARAMETERS ##################### 

    st.subheader(traslate("select_field_and_params",lang))

    ##################### PARAMETERS - OBJECTIVE ##################### 
    objective=None
    try:
        if st.session_state['request']==traslate("yields_processing",lang) or st.session_state['request']==traslate("app_processing",lang):
            options=[traslate("standar_processing",lang),traslate("see_work_progress", lang)]
            objective= st.selectbox(traslate("objective",lang), options=options, key="objetive_input")
    except Exception as exception:
        logging.error (exception)
        st.warning(traslate("error_objective",lang), icon="⚠️") 

    st.session_state['objective']=objective

    ##################### PARAMETERS - HARVEST DATE ONLY IN RINDES ##################### 

    c1, c2 = st.columns([3,3], gap="small")
    date_start_harvest= None
    date_end_harvest= None
    if st.session_state['request']==traslate("yields_processing",lang):
        with c1:
            date_start_harvest= st.date_input(traslate("harvest_start_date",lang), value=datetime.now() - relativedelta(years=2))
        with c2:    
            date_end_harvest=st.date_input(traslate("harvest_end_date",lang), value=datetime.now() - relativedelta(years=2))
            
    if date_end_harvest is not None and date_start_harvest is not None:
        if date_end_harvest<date_start_harvest:
            st.error(traslate("error_date_harvest",lang))
    
    st.session_state['date_start_harvest']=date_start_harvest
    st.session_state['date_end_harvest']=date_end_harvest

    #################### FIELDS  ##################### 

    try:
        if len(farms)==0:
            st.warning(traslate("error_without_fields",lang), icon="⚠️")
        else:        
            fields = ds.Obteniendo_Lotes(st.session_state['workspace']["id"],st.session_state['season']["id"], st.session_state['farm']["id"], env)
            
            if len(fields)==0:
                st.warning(traslate("error_without_fields",lang)+farm, icon="⚠️")
            else:
                if fields is not None:

                    fields_ids=list()
                    fields_names=list()
                    fields_cropIds=list()
                    fields_hybridIds=list()
                    fields_hectares=list()

                
                    for item in fields:
                        fields_ids.append(item['id'])
                        fields_names.append(item['name'])
                        fields_cropIds.append(item['cropId'])
                        fields_hybridIds.append(item['hybridId'])
                        fields_hectares.append(item['hectares'])


                    #df_fields = pd.DataFrame({"id": ['2','3'], "name": ['Lote 1', 'Lote 2']})
                    df_fields = pd.DataFrame({"id": fields_ids, "name": fields_names, "cropId": fields_cropIds,'hybridId':fields_hybridIds,"hectares":fields_hectares})

                    df_fields.sort_values(by=['name'], inplace=True, key=lambda x: x.str.lower())

                    records_fields = df_fields.to_dict("records")

                    ##################### FILEDS TO PROCESS ##################### 
                    
                    try:
                        if st.session_state['request'] ==traslate("app_processing",lang):
                            c1, c2, c3, c4= st.columns([3,3,3,3], gap="small")
                            with c1:
                                    field = st.selectbox(traslate("field",lang), options=records_fields, format_func=lambda record: f'{record["name"]}')
                                    with c2:
                                        hectares=st.text_input(traslate("hectares",lang), value=field['hectares'], disabled=True, key="hectares_input")

                                        tratamiento=st.selectbox(traslate("treatment",lang), ["Amendment","Fertilization","Foliar","Fungicide","Herbicide","Insecticide","Sowing"])
                                        if is_not_empty(tratamiento)==False: tratamiento=" "
                                    try:
                                        crops=ds.Obteniendo_Cultivo(lang, env)
                                        crops_id=list()
                                        crops_name=list()

                                        for item in crops:
                                            crops_id.append(item['id'])
                                            crops_name.append(item['name'])
                                        
                                        df_crops = pd.DataFrame({"id": crops_id, "name": crops_name})
                                        df_crops.sort_values(by=['name'], inplace=True)
                                        records_crops = df_crops.to_dict("records")

                                        index_crop_selected = next((index for (index, d) in enumerate(records_crops) if d["id"] == field["cropId"]), None)


                                        with c3:
                                            crop=st.selectbox (traslate("crop",lang),options=records_crops, index=index_crop_selected,format_func=lambda record: f'{record["name"]}')
                                            if is_not_empty(crop['name'])==False: crop=" "

                                            unidad=st.text_input (traslate("unity",lang), key="unidad_input")
                                            if is_not_empty(unidad)==False: unidad=" "

                                    except Exception as exception:
                                        logging.error (exception)
                                        st.warning(traslate("error_getting_crops",lang), icon="⚠️")  
                                                                
                                    canal1a4=st.selectbox(traslate("channel",lang), ["1", "2", "3","4"])
                                    if is_not_empty(canal1a4)==False: canal1a4=" "
                                    
                                    
                            with c4:
                            
                                hybrids=ds.Obteniendo_Hibrido(crop['id'], lang, env)

                                hybrids_id=list()
                                hybrids_name=list()

                                for item in hybrids:
                                    hybrids_id.append(item['id'])
                                    hybrids_name.append(item['name'])
                                
                                df_hybrids = pd.DataFrame({"id": hybrids_id, "name": hybrids_name})
                                df_hybrids.sort_values(by=['name'], inplace=True)
                                records_hybrids = df_hybrids.to_dict("records")

                                index_hybrid_selected = next((index for (index, d) in enumerate(records_hybrids) if d["id"] == field["hybridId"]), 0)
                                hibrido=st.selectbox (traslate("hybrid_variety",lang),options=records_hybrids, index=index_hybrid_selected,format_func=lambda record: f'{record["name"]}')

                                insumo=st.text_input (traslate("input",lang), key="insumo_input")
                                if is_not_empty(insumo)==False: insumo=" "
                                        
                            prescripcion=st.text_input (traslate("base_prescription",lang), help=(traslate("base_prescription_help",lang)), key="prescripcion_input")
                            if is_not_empty(prescripcion)==False: prescripcion=" "
                            
                        else: 
                            if st.session_state['request']==traslate("yields_processing",lang):
                                c1, c2, c3, c4 = st.columns([5,4,4,4], gap="small")
                                with c1:
                                        field = st.selectbox(traslate("field",lang), options=records_fields, format_func=lambda record: f'{record["name"]}')
                                        with c2:
                                            hectares=st.text_input(traslate("hectares",lang), value=field['hectares'], disabled=True, key="hectares_input")
                                            rinde_prom=st.text_input(traslate("average_yield",lang), key="rinde_prom_input")
                                            if is_not_empty(rinde_prom)==False: rinde_prom=" "
                                        with c3:    
                                            try:
                                                crops=ds.Obteniendo_Cultivo(lang, env)
                                                crops_id=list()
                                                crops_name=list()

                                                for item in crops:
                                                    crops_id.append(item['id'])
                                                    crops_name.append(item['name'])
                                                
                                                df_crops = pd.DataFrame({"id": crops_id, "name": crops_name})
                                                df_crops.sort_values(by=['name'], inplace=True)
                                                records_crops = df_crops.to_dict("records")

                                                index_crop_selected = next((index for (index, d) in enumerate(records_crops) if d["id"] == field["cropId"]), None)

                                                with c3:
                                                    crop=st.selectbox (traslate("crop",lang),options=records_crops, index=index_crop_selected,format_func=lambda record: f'{record["name"]}', help=traslate("crop_harvest",lang))
                                                    if is_not_empty(crop['name'])==False: crop=" "

                                                with c4:
                                                    hybrids=ds.Obteniendo_Hibrido(crop['id'], lang, env)
                                                    hybrids_id=list()
                                                    hybrids_name=list()

                                                    for item in hybrids:
                                                        hybrids_id.append(item['id'])
                                                        hybrids_name.append(item['name'])
                                                    
                                                    df_hybrids = pd.DataFrame({"id": hybrids_id, "name": hybrids_name})
                                                    df_hybrids.sort_values(by=['name'], inplace=True)
                                                    records_hybrids = df_hybrids.to_dict("records")

                                                    index_hybrid_selected = next((index for (index, d) in enumerate(records_hybrids) if d["id"] == field["hybridId"]), 0)
                                                    hibrido=st.selectbox (traslate("hybrid_variety",lang),options=records_hybrids, index=index_hybrid_selected,format_func=lambda record: f'{record["name"]}')
                                                    
                                            except Exception as exception:
                                                logging.error (exception)
                                                st.warning(traslate("error_getting_crops",lang), icon="⚠️")  
                                        
                                        
                                        ajuste_prom=st.selectbox(traslate("adjust_for_average_field",lang), [traslate("adjust_yes",lang), traslate("adjust_no",lang)])
                                        if is_not_empty(ajuste_prom)==False: ajuste_prom=" "
                            else:
                                if st.session_state['request']==traslate("productivity_maps",lang):
                                    c1, c2, c3 = st.columns([3,3,3], gap="small")
                                    with c1:
                                        try:
                                            field = st.selectbox(traslate("field",lang), options=records_fields, format_func=lambda record: f'{record["name"]}')
                                        except:
                                            st.warning(traslate("error_getting_fields",lang), icon="⚠️")
                                    with c2:
                                        hectares=st.text_input(traslate("hectares",lang), value=field['hectares'], disabled=True, key="hectares_input")
                                    with c3:
                                        num_clases=st.selectbox(label=traslate("number_of_classes",lang), options=["3","5","7"], index=2,key="num_clases_input")
                                        
                                    consideraciones=st.text_input(traslate("considerations",lang), key="consideraciones_input")
                                    
                                else:
                                    if st.session_state['request']==traslate("interpolated_maps",lang):
                                        c1, c2, c3= st.columns([3,2,2], gap="small")
                                        with c1:
                                            try:
                                                field = st.selectbox(traslate("field",lang), options=records_fields, format_func=lambda record: f'{record["name"]}')

                                            except Exception as exception:
                                                logging.error (exception)
                                                st.warning(traslate("error_getting_fields",lang), icon="⚠️")
                                        with c2:
                                            hectares=st.text_input(traslate("hectares",lang), value=field['hectares'], disabled=True, key="hectares_input")
                                            
                                        with c3:   

                                            formato=st.multiselect(traslate("format",lang), options=[traslate("options_format_raster",lang),traslate("options_format_interpolated_areas",lang)], key="formato_input")
                                        
                                        especificaciones=st.text_input(traslate("specifications",lang), key="especificaciones_input", value=' ')

                                        variable_interpolar=st.multiselect(traslate("variable_to_interpolate",lang), options=ds.Obteniendo_Variables(lang), key="variable_interpolar_input")
                    
                    except:
                        logging.info("local variable referenced before assignment")

                    col1, col2, col3 = st.columns(3)

                    
                    if 'data' not in st.session_state:      
                        st.session_state['data'] = pd.DataFrame()

                    submitButton = st.button(label = traslate("add_field",lang))
                    if submitButton:

                        if st.session_state['request'] ==traslate("app_processing",lang):
                            row = {traslate("field",lang): field["name"],traslate("hectares",lang):str(field['hectares']),traslate("crop",lang): crop['name'],traslate("hybrid_variety",lang):hibrido['name'],traslate("channel",lang): canal1a4,traslate("treatment",lang): tratamiento,traslate("unity",lang): unidad,traslate("input",lang): insumo,traslate("base_prescription",lang): prescripcion }
                        else: 
                            if st.session_state['request']==traslate("yields_processing",lang):
                                row = {traslate("field",lang): field["name"],traslate("hectares",lang):str(field['hectares']),traslate("crop_harvest",lang):crop['name'],traslate("hybrid_variety",lang):hibrido['name'],traslate("adjust_for_average_field",lang): ajuste_prom,traslate("average_yield",lang): rinde_prom}
                            else:
                                if st.session_state['request']==traslate("productivity_maps",lang):
                                    row = {traslate("field",lang): field["name"],traslate("hectares",lang):str(field['hectares']),traslate("number_of_classes",lang): num_clases,traslate("considerations",lang): consideraciones}
                                else:
                                    if st.session_state['request']==traslate("interpolated_maps",lang):
                                        if len(variable_interpolar)>0:
                                            if len(formato)>0:
                                                row = {traslate("field",lang): field["name"],traslate("hectares",lang):str(field['hectares']),traslate("variable_to_interpolate",lang): variable_interpolar,traslate("format",lang):formato,traslate("specifications",lang): especificaciones}
                                            else:
                                                st.warning(traslate("error_format",lang))    
                                        else:
                                            st.warning(traslate("error_variable_to_interpolate",lang))

                        new_df = pd.DataFrame([row])

                        d = pd.concat([st.session_state['data'], new_df], ignore_index=True)

                        if st.session_state['request']==traslate("app_processing",lang):
                            row_duplicated = any(d.duplicated(subset=[traslate("field",lang), traslate("hectares",lang),traslate("crop",lang),traslate("hybrid_variety",lang)]))
                            if row_duplicated:  #### ROW EXISTS IN DF 
                                df_temp = d.drop_duplicates(subset=[traslate("field",lang), traslate("hectares",lang),traslate("crop",lang),traslate("hybrid_variety",lang)],keep="first")
                                d=df_temp
                                d.reset_index(drop=True, inplace=True)
                                st.warning(traslate("error_duplicate_field_1",lang))
                        elif st.session_state['request']==traslate("yields_processing",lang):
                            row_duplicated = any(d.duplicated(subset=[traslate("field",lang), traslate("hectares",lang),traslate("crop_harvest",lang),traslate("hybrid_variety",lang)]))
                            if row_duplicated:  #### ROW EXISTS IN DF 
                                df_temp = d.drop_duplicates(subset=[traslate("field",lang), traslate("hectares",lang),traslate("crop_harvest",lang),traslate("hybrid_variety",lang)],keep="first")
                                d=df_temp
                                d.reset_index(drop=True, inplace=True)
                                st.warning(traslate("error_duplicate_field_1",lang))

                        elif st.session_state['request']==traslate("productivity_maps",lang) or st.session_state['request']==traslate("interpolated_maps",lang):    
                                row_duplicated = any(d.duplicated(subset=[traslate("field",lang), traslate("hectares",lang)]))
                                if row_duplicated:  #### ROW EXISTS IN DF 
                                    df_temp = d.drop_duplicates(subset=[traslate("field",lang), traslate("hectares",lang)],keep="first")
                                    d=df_temp
                                    d.reset_index(drop=True, inplace=True)
                                    st.warning(traslate("error_duplicate_field_2",lang))
                              

                        st.session_state['data'] = d

                        
                    try:
                        grid_table=createGrid(st.session_state['data']) 
                    except Exception as exc:
                        print (exc)
                        pass

                    deleteButtonField = st.button(traslate("delete_field",lang))
                    if deleteButtonField:
                        sel_row = grid_table["selected_rows"]
                        list_row_to_delete=[]
                        for index in sel_row:
                            list_row_to_delete.append(index['_selectedRowNodeInfo']['nodeRowIndex'])
                        
                        st.session_state['data']=st.session_state['data'].drop(list_row_to_delete)
                        st.session_state['data'].reset_index(drop=True, inplace=True)
                        st.experimental_rerun()
                else:
                    st.warning(traslate("error_processing_fields",lang), icon="⚠️") 

    except Exception as exception:
        logging.error(exception)
        st.warning(traslate("error_processing_fields",lang), icon="⚠️") 

    st.markdown('----')

    ##################### MONITORES #####################
    
    st.subheader(traslate("select_files",lang))

    if 'uploaded_files' not in st.session_state:      
        st.session_state['uploaded_files'] = pd.DataFrame()

    if st.session_state['request']==traslate("productivity_maps",lang):
        st.info(traslate("error_not_necesary_add_files",lang))
    else:
        with st.form(key='formMonitors', clear_on_submit=True):
            
            try:
                label_submit_button=traslate("add_monitor",lang)
                label_delete_button=traslate("delete_monitor",lang)
                if st.session_state['request']==traslate("yields_processing",lang):
                    monitor = st.selectbox(traslate("monitor",lang), options=ds.Obteniendo_Monitores("Rindes"))
                else: 
                    if st.session_state['request']==traslate("app_processing",lang):
                        monitor = st.selectbox(traslate("monitor",lang), options=ds.Obteniendo_Monitores("Aplicacion"))
                    else:
                        monitor=traslate("none",lang)
                        label_submit_button=traslate("add_file",lang)
                        label_delete_button=traslate("delete_file",lang)
            
            except Exception as exception:
                logging.error(exception)
                st.warning(traslate("error_getting_monitors",lang), icon="⚠️")
            
            upload_file= st.file_uploader(traslate("select_file",lang), accept_multiple_files=False)
            submitButton = st.form_submit_button(label = label_submit_button)
            if submitButton:
                if monitor is not None:
                    ##write ins3
                    monitors=[]
                    if upload_file is not None:
                        try:
                            bucket = "pedidos-de-procesamiento"

                            name = os.path.splitext(upload_file.name)[0][0:].strip()
                            extension = os.path.splitext(upload_file.name)[1].strip() 

                            upload_file.name=str(name).replace(" ", "")+"_"+str(datetime.today()).replace(" ", "_")+extension

                            with st.spinner(text=traslate("uploading_files",lang)):
                                link=upload_file_to_bucket(upload_file, bucket, upload_file.name)



                            row = {traslate("monitor_1",lang): monitor, traslate("file",lang): upload_file.name}
                            new_df = pd.DataFrame([row])
                            d = pd.concat([st.session_state['uploaded_files'], new_df], ignore_index=True)
                            st.session_state['uploaded_files'] = d  
                        except:
                            st.error(traslate("error_upload_files",lang), icon="🚨")
                            logging.error("Error when add s3 files")
                        

            
            try:
                grid_table=createGrid(st.session_state['uploaded_files'])   
            except:
                pass
            
            deleteButtonMonitor = st.form_submit_button(label=label_delete_button)
            if deleteButtonMonitor:
                try:
                    sel_row = grid_table["selected_rows"]
                    list_row_to_delete=[]
                    for index in sel_row:
                        list_row_to_delete.append(index['_selectedRowNodeInfo']['nodeRowIndex'])

                    st.session_state['uploaded_files']=st.session_state['uploaded_files'].drop(list_row_to_delete)
                    st.session_state['uploaded_files'].reset_index(drop=True, inplace=True)
                    st.experimental_rerun()
                
                except Exception as exception:
                    logging.error(exception)
                    st.error(traslate("error_delete_monitors",lang), icon="🚨")
    
    st.markdown('----')
    
    ##################### LIMIT DATE ##################### 
    st.subheader(traslate("additional_info",lang))

    st.info(traslate("processing_time",lang), icon="ℹ️")
    limit_date=get_limit_date(datetime.today())
    date_limit=st.date_input(label=traslate("date_limit",lang), value=limit_date,min_value=datetime.today())
    st.session_state['date_limit']=date_limit

    ##################### REASON ########################3
    reason= st.text_input(traslate("reason",lang), key="reason_input")
    st.session_state['reason']=reason

    ##################### COMENTARIOS ##################### 
    comments = st.text_area(traslate("comments",lang), key="comments_input")
    st.session_state['comments']=comments

    ##################### PARTICIPANTS ##################### 
    participants=st_tags(label=traslate("emails_for_notifications",lang), text=traslate("press_enter_for_add",lang), key="participants_input")
    st.session_state['participants']=participants

    ##################### SUBMIT ###########################

    st.button(label=traslate("create_request",lang), on_click=submit)

def submit():
        field_required=True
        lang=st.session_state['lang']
        env=st.session_state['env']
        try:
            #### CHECKING EMPTY REQUIRED FORM FIELDS ####
            if is_not_empty(st.session_state['request'])==False:
                field_required=False
                st.warning(traslate("error_mandatory_request",lang), icon="⚠️")
            if is_not_empty(st.session_state['domain']['name'])==False:
                field_required=False
                st.warning(traslate("error_mandatory_domain",lang), icon="⚠️")
            if is_not_empty(st.session_state['workspace']['name'])==False:
                field_required=False
                st.warning(traslate("error_mandatory_workspace",lang), icon="⚠️")
            if is_not_empty(st.session_state['season']['name'])==False:
                field_required=False
                st.warning(traslate("error_mandatory_campaign",lang), icon="⚠️")
            if is_not_empty(st.session_state['farm']['name'])==False:
                field_required=False
                st.warning(traslate("error_mandatory_farm",lang), icon="⚠️")
            if is_not_empty(str(st.session_state['date_limit']))==False:
                field_required=False
            if st.session_state['data'].empty:
                field_required=False
                st.warning(traslate("error_mandatory_fields",lang), icon="⚠️")

            if st.session_state['request']==traslate("productivity_maps",lang): ### FILES AND MONITORS MAY BE EMPTY###
                pass
            else:
                if st.session_state['uploaded_files'].empty:
                    field_required=False
                    if st.session_state['request'] ==traslate("app_processing",lang) or st.session_state['request'] ==traslate("yields_processing",lang):
                        st.warning(traslate("error_mandatory_monitors",lang), icon="⚠️")
                    else:
                        st.warning(traslate("error_files_monitors",lang), icon="⚠️") #### MAPAS INTERPOLADOS

            if validateParticipants(st.session_state['participants']) is False:
                field_required=False
                st.warning(traslate("error_mandatory_emails",lang), icon="⚠️")
            
            if field_required:
                with st.spinner(traslate("message_successful_request",lang)):
                    try:
                        ##flow jira
                        try:
                            area=st.session_state['area']['name']
                        except:
                            area=traslate("none",lang)
                        data={
                            "email": st.session_state['email'],
                            "request": st.session_state['request'],
                            "domain": st.session_state['domain']['name'],
                            "area": area,
                            "workspace": st.session_state['workspace']['name'],
                            "season": st.session_state['season']['name'],
                            "farm": st.session_state['farm']['name'],
                            "date_start_harvest":  str(st.session_state['date_start_harvest']),
                            "date_end_harvest": str(st.session_state['date_end_harvest']),
                            "date_limit": str(st.session_state['date_limit']),
                            "date_requested": str(datetime.today()),
                            "participants":st.session_state['participants'] if not None else [],
                            "reason": st.session_state['reason'],
                            "objective": st.session_state['objective'],
                            "comments": st.session_state['comments'],
                            
                        }
                        fields= st.session_state['data']
                        
                        monitors_uploaded=st.session_state['uploaded_files']

                        if create_issue_jira(data, fields, monitors_uploaded, lang, env): #Dataframe in session with data fields):
                            st.success(traslate("request_created_thank_you",lang),icon="✅")
                            ### DELETING VARIABLES SESSION ###
                            clear_data()
                            
                        else:
                            
                            st.error(traslate("error_create_request",lang),icon="🚨")
                    except Exception as exception:
                        logging.error (exception)
                        st.error(traslate("error_create_request",lang),icon="🚨")
            
        except Exception as exception:
            logging.error (exception)
            #### SOME FIELD EMPTY####
            st.error(traslate("error_create_request_fields",lang),icon="🚨")


#if __name__ == "__main__":
#    user_info={'email': "acuello@geoagro.com", 'language': 'es', 'env': 'test', 'domainId': None, 'areaId': None, 'workspaceId': None, 'seasonId': None, 'farmId': None}
#    main_app(user_info)


if __name__ == "__main__":
    try:
        params=st.experimental_get_query_params()
        if not params is False:
            token1=params['token1'][0]
            token2=params['token2'][0]
            user_info=decrypt_token(token1)
    except Exception as exception:
        print (exception)
        login_info = oauth.login(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
            )
        if login_info:
            user_id, user_email = login_info
            user_info={'email': user_email, 'language': 'es', 'env': 'prod', 'domainId': None, 'areaId': None, 'workspaceId': None, 'seasonId': None, 'farmId': None}
            
        else:
            logging.error("Not logged")
    
    if not user_info is False:
        main_app(user_info)
    else:
        st.error("Error accessing Datarequest. Please contact an administrator.")


# streamlit run app.py --server.port 8080
