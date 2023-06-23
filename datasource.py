import requests
import streamlit as st
from secretManager import AWSSecret
import json
import boto3


urlApi_test="https://5aehyzfqovberehh7fwy57pf6u.appsync-api.us-east-1.amazonaws.com/graphql"
header_test = {"x-api-key": "da2-k4b5ifqbunhcvpj73vd4hdcrri"}

urlApi_prod = "https://3xrq2cixcbf3jjgtjjlqmqviqm.appsync-api.us-west-2.amazonaws.com/graphql"
header_prod = {"x-api-key": "da2-yawqn7mxdvdcxntgsqvlqopbb4"}

def Obteniendo_DominiosyAreas(email, env):
    try:
        query = (
            """
            query MyQuery {
                domains_areas_by_user(email:  "%s") {
                    id
                    name
                    deleted
                    areas {
                        id
                        name
                        deleted
                        workspaces {
                            id
                            name
                            deleted
                        }
                    }
                    workspaces{
                        id
                        name
                        deleted
                    }    
                }
                
            } """
            % email
        )
        
        if env=='test':
            request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)
        result = request.json()
        final_result= [item for item in result["data"]["domains_areas_by_user"] if not item['deleted']]
        return final_result
    except:
        return None

@st.cache
def Obteniendo_Dominios(email, env):
    try:
        query = (
            """
            query MyQuery {
                list_domains(email: "%s") {
                    id
                    name
                    deleted
                }
                
            } """
            % email
        )
        if env=='test':
            request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)
        
        result = request.json()
        final_result= [item for item in result["data"]["list_domains"] if not item['deleted']]
        return final_result
    except:
        return None


def Obteniendo_Workspaces(email, env):
    try:
        query = (
            """
            query MyQuery {
                list_workspaces(email: "%s") {
                    id
                    name
                    deleted
                }
                
            } """
            % email
        )
        if env=='test':
            request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)
        
        result = request.json()
        final_result= [item for item in result["data"]["list_workspaces"] if not item['deleted']]
        return final_result
    except:
        return None

@st.cache
def Obteniendo_Campañas(workspaceId, env):
    try:
        query = (
            """
        query MyQuery {
           list_seasons(workspaceId: %s) {
                id
                name
                deleted
            }       
        }         
            """
            % workspaceId
        )
        if env=='test':
            request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)     
        result = request.json()
        final_result= [item for item in result["data"]["list_seasons"] if not item['deleted']]
        return final_result
    except:
        return None


@st.cache
def Obtener_Id_usuario(email,env):
    try:
        query = (
        """
        query MyQuery {
             get_user(email: "%s") {
                id
            }
        }
        """
        % email
        )
        if env=='test':
            request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)      
        result = request.json()
        final_result= result["data"]["get_user"]["id"]
        return final_result
    except:
        return None
     

@st.cache
def Obteniendo_Establecimientos(workspaceId, seasonId, env, email):
    userId=Obtener_Id_usuario(email, env)
    if userId is not None:
        try:
            query = (
            """
            query MyQuery {
                list_farms(workspaceId: %s, seasonId: %s, userId: "%s") {
                    id
                    name
                    deleted
                }
            }
            """
            % (workspaceId, seasonId, userId)
            )
            if env=='test':
                request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
            else:
                request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)      
            result = request.json()
            final_result= [item for item in result["data"]["list_farms"] if not item['deleted']]
            return final_result
        except:
            return None
    else:
        return None

@st.cache
def Obteniendo_Lotes(workspaceId, seasonId, farmId,env):
    try:
        query = (
            """
            query MyQuery {
            list_fields(workspaceId: %s, seasonId: %s, farmId: %s) {
                id
                name
                cropId
                hybridId
                hectares
                }
            }
            """
            % (workspaceId, seasonId, farmId)
        )
        if env=='test':
            request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)
        result = request.json()
        return result["data"]["list_fields"]
    except:
        return None

@st.cache
def Obteniendo_Cultivo(lang, env):
    try:
        query = (
            """
            query MyQuery {
            list_crops(lang: "%s") {
                    id
                    name
                }
            }
            """
            % lang

        )
        if env=='test':
                request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)
        result = request.json()
        return result["data"]["list_crops"]
    except:
        return None

@st.cache
def Obteniendo_Hibrido(cropId,lang, env):
    try:
        query = (
            """
            query MyQuery {
            list_hybrids(cropId:%s, lang: "%s") {
                    id
                    name
                }
            }
            """
            %  (cropId,lang)

        )
        if env=='test':
            request = requests.post(urlApi_test, json={"query": query}, headers=header_test, timeout=60)
        else:
            request = requests.post(urlApi_prod, json={"query": query}, headers=header_prod, timeout=60)
        result = request.json()
        return result["data"]["list_hybrids"]
    except:
        return None

@st.cache
def Obteniendo_Monitores(monitor):
    if monitor is not None:
        secrets = json.loads(AWSSecret().get_secret(secret_name="prod/app/pedidosproc", region_name="us-east-1"))
        s3 = boto3.client(
            service_name="s3",
            region_name="us-east-1",
            aws_access_key_id=secrets["keyid"],
            aws_secret_access_key=secrets["secretkey"],
        )
        bucket_name = 'pedidosproc'
        s3_file_key = 'monitores/'+monitor
        csv_obj = s3.get_object(Bucket=bucket_name,Key=s3_file_key)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')
        list_monitor=csv_string.split("\n")
        list_monitor=list(filter(None, list_monitor))
        list_monitor.sort()
        return list_monitor
    
    else:
        return None

@st.cache
def Obteniendo_Variables(lang):
    try:
        secrets = json.loads(AWSSecret().get_secret(secret_name="prod/app/pedidosproc", region_name="us-east-1"))
        s3 = boto3.client(
                service_name="s3",
                region_name="us-east-1",
                aws_access_key_id=secrets["keyid"],
                aws_secret_access_key=secrets["secretkey"],
            )
        bucket_name = 'pedidosproc'
        if lang=="es":
            s3_file_key = 'variables/variables_es'
        else:
            if lang=="en":
                s3_file_key = 'variables/variables_en'
            else:
                s3_file_key = 'variables/variables_pt'

        csv_obj = s3.get_object(Bucket=bucket_name,Key=s3_file_key)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')
        list_variables=csv_string.split("\n")
        list_variables=list(filter(None, list_variables))
        list_variables.sort()
        return list_variables
    except:
        return None
  
