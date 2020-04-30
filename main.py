from flask import Flask, request, render_template
from bs4 import BeautifulSoup
import requests
import pandas as pd
import array
import numpy as np
import os
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route('/bot', methods=['POST'])
def bot():
    # getting the incoming message
    incoming_msg = request.values.get('Body', '').lower()
    # getting the co-ordinates
    print(request.values.get('Latitude'))

    # setting up the response message
    resp = MessagingResponse()
    msg = resp.message()


    ## --------- setting up the responded toggle -------- ###

    responded = False

    if 'help' in incoming_msg:
        start_check_count = 1
        out_welcome = '''   
            \n 1. You can ask me the statstics of the world 
            \n 2. Statistics of the India
            \n 3. Statistics based on the state
            \n 4. Nearest Hospital within 1.5 Km radius from your current location ( For this feature to activate , Please send your location as a message )
            \n Stay safe and healthy  👍👍
        ''' 
        msg.body(out_welcome)
        return str(resp)
    

    
    ## -------------- overall cases in india ------------------ ##

    India_stats_url = 'https://www.mohfw.gov.in/';
    stats_htm = requests.get(India_stats_url).content
    states_frame = pd.read_html(stats_htm)[0]
    result = BeautifulSoup(stats_htm, 'html.parser')

    # get the overall stats
    overall_stats = result.find_all('div',class_='site-stats-count')
    
    for overall_stat in overall_stats:
        overall_case_numbers = overall_stat.find_all('strong')
        case_array=list()
        # print(overall_title)
        for overall_case_number in overall_case_numbers:
            case_array.append(overall_case_number.text.strip())
    
   
    overall_cases_india = pd.DataFrame([case_array],columns=['Active Cases','Cured / Discharged','Deaths','Migrated'])  # overall cases in india as dataframe
   
    ### --------------- get the state wise data ---------------------- ### 
    for ind in states_frame.index:
        if ind <= 31:
            state_name = states_frame['Name of State / UT'][ind]
            ## ---------- get the state from the sentence -------- ###
            #print(incoming_msg.find(state_name))
            if state_name.lower().strip() in incoming_msg:
                print(ind)
                confirmed_cases = states_frame['Total Confirmed cases (Including 111 foreign Nationals)'][ind]
                Discharged = states_frame['Cured/Discharged/Migrated'][ind]
                Death = states_frame['Death'][ind]
                print(confirmed_cases,"|" ,Discharged, "|", Death)
                stats_message='''{} ----------------  Confirmed cases : {} | Cured/Discharged/Migrated :  {} | Death: {} '''.format(state_name, confirmed_cases,Discharged,Death)
                msg.body(stats_message)
                responded = True
                return str(resp)

     ### --------------------- world data -------------------------------- ###

    world_stats_url = 'https://www.worldometers.info/coronavirus/'
    world_stats_frame = pd.read_html(requests.get(world_stats_url).content)[0]
    world_total_cases = world_stats_frame['TotalCases'][0];
    world_total_recovery = world_stats_frame['TotalRecovered'][0];
    world_total_death = world_stats_frame['TotalDeaths'][0]
    print(world_total_cases,"|",world_total_recovery, "|" , world_total_death )
    

    ## -- location based hospitals display using maps --- ## 

    print(request.values.get('Latitude'))
    print(request.values.get('Longitude'))
    if request.values.get('Latitude'): 
        BASE_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        RADIUS = 1500 # meters -- need to make it customisable
        TYPE = 'hospital'
        KEY = os.getenv('GOOGLE_MAPS_API_KEY')
        LATITUDE = request.values.get('Latitude')
        LONGITUDE = request.values.get('Longitude')
        # fire up the request to get the hospital data using google maps api

        hospitals = requests.get(BASE_URL + '?location=' + LATITUDE +',' + LONGITUDE + '&radius=' + str(RADIUS) + '&type=' + TYPE + '&key=' + KEY ).json()
        
        out_msg = ''
        hospital_count = 5
        init_length = 0
        BOLD = ''
        print(len(hospitals['results']))
        for hospital in hospitals['results']:
            if init_length < hospital_count:
                print(hospital['name'])
                out_msg = ( 
                        '''
                        {}  Hospital Name  :   {} \n\n Hospital address : {} \n\n  -------------- \n''').format(out_msg,str(hospital['name']),str(hospital['vicinity']))
            
                print(out_msg)
                init_length = init_length + 1
        
        msg.body(out_msg)
        responded = True

        return str(resp)
        
        
    
    if 'india' in incoming_msg:
        # return a quote
        outgoing_message = 'Active Cases {} | Cured / Discharged {} | Deaths {} | Migrated {}'.format(str(overall_cases_india['Active Cases'].values[0]),str(overall_cases_india['Cured / Discharged'].values[0]),str(overall_cases_india['Deaths'].values[0]),str(overall_cases_india['Migrated'].values[0]))
        msg.body(outgoing_message)
        responded = True
    if 'world' in incoming_msg or 'overall' in incoming_msg:
        world_stats = 'Total Cases {} | Total Recovery {} | Total Death {}'.format(int(world_total_cases),int(world_total_recovery),int(world_total_death))
        msg.body(world_stats)
        responded = True
    if not responded:
        stats_msg = 'sorry !!!!'
        msg.body(stats_msg)
        responded = True
    return str(resp)


if __name__ == '__main__':
    app.run()