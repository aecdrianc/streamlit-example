from atlassian import ServiceDesk 
import json
import logging
from helper import traslate, get_secret
from datetime import datetime, timedelta
import requests


def format_data_to_jira_post(data, fields, monitors, lang):

    #### ADD DATA FIELDS ####
    if data["request"] ==traslate("app_processing",lang):
        description="*Solicitado por:*\n |"+data["email"]+"|\n""*Pedido*\n |"+data["request"]+"|\n"+"*Dominio*\n |"+data["domain"]+"|\n"+"*Area*\n |"+data["area"]+"|\n"+"*Workspace*\n |"+data["workspace"]+"|\n"+"*Campaña*\n |"+data["season"] +"|\n"+"*Establecimiento*\n |"+data["farm"] +"|\n"+"*Fecha de pedido*\n |"+data["date_requested"]+"|\n*Fecha límite*\n |"+data["date_limit"]+"|\n"+"*Razón*\n |"+data["reason"] +"|\n"+"*Objetivo*\n |"+data["objective"]+"|\n"+"*Comentarios*\n |"+data["comments"]+"|\n"
        title_table_fields="*Lotes a procesar:*\n||*Lote*||*Hectáreas*||*Cultivo*||*Híbrido/Variedad*||*Canal*||*Tratamiento*||*Unidad*||*Insumo*||*Prescripción Base (separados por comas)*||\n"
        rows_table_fields=""
        for index, row in fields.iterrows():
            rows_table_fields=rows_table_fields+"|"+row[traslate("field",lang)]+"|"+row[traslate("hectares",lang)]+"|"+ row[traslate("crop",lang)]+"|"+ row[traslate("hybrid_variety",lang)]+"|"+row[traslate("channel",lang)]+"|"+row[traslate("treatment",lang)]+"|"+row[traslate("unity",lang)]+"|"+row[traslate("input",lang)]+"|"+row[traslate("base_prescription",lang)]+"|\n"
    else: 
        if data["request"] == traslate("yields_processing",lang):
            description="*Solicitado por:*\n |"+data["email"]+"|\n""*Pedido*\n |"+data["request"]+"|\n"+"*Dominio*\n |"+data["domain"]+"|\n"+"*Area*\n |"+data["area"]+"|\n"+"*Workspace*\n |"+data["workspace"]+"|\n"+"*Campaña*\n |"+data["season"] +"|\n"+"*Establecimiento*\n |"+data["farm"] +"|\n"+"*Fecha inicio cosecha*\n |"+data["date_start_harvest"]+"|\n"+"*Fecha final cosecha*\n |"+data["date_end_harvest"]+"|\n"+"*Fecha de pedido*\n |"+data["date_requested"]+"|\n*Fecha límite*\n |"+data["date_limit"]+"|\n"+"*Razón*\n |"+data["reason"] +"|\n"+"*Objetivo*\n |"+data["objective"]+"|\n"+"*Comentarios*\n |"+data["comments"]+"|\n"
            title_table_fields="*Fields to process:*\n||*Lote*||*Hectáreas*||*Cultivo (al momento de cosecha)*||*Híbrido/Variedad*||*Ajustar por Rinde Promedio*||*Rinde Promedio [tn/ha]*||\n"
            rows_table_fields=""
            for index, row in fields.iterrows():
                rows_table_fields=rows_table_fields+"|"+row[traslate("field",lang)]+"|"+row[traslate("hectares",lang)]+"|"+ row[traslate("crop_harvest",lang)]+"|"+ row[traslate("hybrid_variety",lang)]+"|"+row[traslate("adjust_for_average_field",lang)]+"|"+row[traslate("average_yield",lang)]+"|"+"|\n"
        else:
            description="*Solicitado por:*\n |"+data["email"]+"|\n""*Pedido*\n |"+data["request"]+"|\n"+"*Dominio*\n |"+data["domain"]+"|\n"+"*Area*\n |"+data["area"]+"|\n"+"*Workspace*\n |"+data["workspace"]+"|\n"+"*Campaña*\n |"+data["season"] +"|\n"+"*Establecimiento*\n |"+data["farm"] +"|\n"+"*Fecha de pedido*\n |"+data["date_requested"]+"|\n*Fecha límite*\n |"+data["date_limit"]+"|\n"+"*Razón*\n |"+data["reason"] +"|\n"+"*Comentarios*\n |"+data["comments"]+"|\n"
            if data["request"] ==traslate("productivity_maps",lang):
                title_table_fields="*Fields to process:*\n||*Lote*||*Hectáreas*||*Número de clases*||*Consideraciones*||\n"
                rows_table_fields=""
                for index, row in fields.iterrows():
                    rows_table_fields=rows_table_fields+"|"+row[traslate("field",lang)]+"|"+row[traslate("hectares",lang)]+"|"+ row[traslate("number_of_classes",lang)]+"|"+row[traslate("considerations",lang)]+"|\n"
            else:
                if data["request"]==traslate("interpolated_maps",lang):
                    title_table_fields="*Fields to process:*\n||*Lote*||*Hectáreas*||*Variable a interpolar*||*Formato*||*Especificaciones*||\n"
                    rows_table_fields=""
                    for index, row in fields.iterrows():
                       rows_table_fields=rows_table_fields+"|"+row[traslate("field",lang)]+"|"+row[traslate("hectares",lang)]+"|"+str(' & '.join(row[traslate("variable_to_interpolate",lang)]))+"|"+str(' & '.join(row[traslate("format",lang)]))+"|"+row[traslate("specifications",lang)]+"|\n"
                    
    
    #### ADD DATA MONITORS AND FILES ####
    title_table_monitors="*Monitores y Archivos a Procesar:*\n||*Monitor*||*Nombre del Archivo*||*Link*||\n"
    rows_table_monitors=""
    bucket_name="https://pedidos-de-procesamiento.s3.amazonaws.com/"
    for index, monitor_item in monitors.iterrows():
        rows_table_monitors=rows_table_monitors+"|"+monitor_item[traslate("monitor_1",lang)]+"|"+ monitor_item[traslate("file",lang)]+"|"+bucket_name+monitor_item[traslate("file",lang)]+"|\n"
    return description+title_table_fields+rows_table_fields+title_table_monitors+rows_table_monitors


def create_issue_jira(data,fields, monitors, lang, env): 

    if env=="test":
        summary="TEST - "+data["request"]+" - "+data["workspace"]+" - "+data["farm"]
    else:
        summary=data["request"]+" - "+data["workspace"]+" - "+data["farm"]

    issue = {
            "summary":summary,
            'description': format_data_to_jira_post(data, fields, monitors, lang),
            'customfield_10076':data['date_limit']
            }
    
    secret=get_secret("prod/api/jira_user","us-east-1")
    try:
        sd = ServiceDesk(
            url='https://geoagro1.atlassian.net',
            username=secret['user_jira'],
            password=secret['password_jira'],
            cloud=True)

        participants_to_submit_in_jira=list()

        data["participants"].append("servicios@geoagro.com")
        
        for participant in data["participants"]:
            customers_in_jira=sd.get_customers(service_desk_id="6", query=str(participant).strip().lower(), start=0, limit=10000)

            try:
                account_id=customers_in_jira['values'][0]['accountId'] ####  
                participants_to_submit_in_jira.append(account_id)

            except: ###PARTICIPANT NOT EXIST IN JIRA, MUST BE CREATED
                try:
                    customer_created=sd.create_customer(participant, participant)
                    participants_to_submit_in_jira.append(customer_created["accountId"])
                except:
                    logging.error("Error in customer creation")    
        

        try:
            sd.create_customer_request("6","45",issue,data["email"],participants_to_submit_in_jira)
            return True
        except Exception as ex:
            print (ex)
            logging.error("Error with issue creation")    
            return False
    except:
        logging.error("Error in ServiceDesk")    
    