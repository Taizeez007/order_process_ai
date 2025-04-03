from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
import os
import googlemaps
import getpass
from pydantic import BaseModel,Field
import json
import trip_planner
from typing import Any
import requests
from trip_planner import llmtools
from langchain.tools import Tool
from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
#from langchain_core.runnables.config import RunnableConfig
import json


load_dotenv()  # Load environment variables

#define tool function
llm=llmtools()
query_vehicle_database =llm.query_vehicle_database
query_driver_database =llm.query_driver_database
add_driver_to_order = llm.add_driver_to_order
add_vehicle_to_order =llm.add_vehicle_to_order

#use pydantic for structured output
class Order(BaseModel):
    order_id:str
    order_name:str
    good_type:str
    pickup_locations:str
    dropoff_location:str

class OrderMatch(Order):
    order_id: str = Field(description="The ID of the order")
    driver_id: str = Field(description="The ID of the driver")
    driver_name: str = Field(description="The name of the driver")
    vehicle_type: str = Field(description="The type of the vehicle")
    vehicle_id: str = Field(description="The ID of the vehicle")

#reasoning_schema=ResponseSchema(name="reasoning", description="This is the reason for selecting the driver and vehicle")
response_schema=[
    ResponseSchema(name="order_id", description="The ID of the order"),
    ResponseSchema(name="driver_id", description="The ID of the driver"),
    ResponseSchema(name="driver_name", description="The name of the driver"),
    ResponseSchema(name="vehicle_type", description="The type of the vehicle"),
    ResponseSchema(name="vehicle_id", description="The ID of the vehicle"),
]

#craete structured output for response and reasoning

output_parser=StructuredOutputParser(response_schemas=response_schema)

format_instructions=output_parser.get_format_instructions()

#set recursion
#config=RunnableConfig(recursion_limit=30)
memory=MemorySaver()
LANGSMITH_API_KEY=os.environ.get("LANGSMITH_API_KEY")
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')
TAVILY_API_KEY=os.environ.get("TAVILY_API_KEY")

GOOGLE_MAP_API_KEY=os.environ.get("GOOGLE_MAP_API_KEY")
gmaps=googlemaps.Client(key=GOOGLE_MAP_API_KEY)

#define tools
if not os.environ.get('TAVILY_API_KEY'):

    os.environ['TAVILY_API_KEY']=getpass.getpass('tavily_api_key:\n')

search=TavilySearchResults(max_results=2)



# Create the Langchain Tools
search_vehicles_tool = Tool(
    name="SearchVehicles",
    func=query_vehicle_database,
    description="Searches the vehicle database for vehicles that can transport the specified goods and quantity.  Input should be goods (string) and quantity (int).  Returns a list of matching vehicle records (vehicle_id, vehicle_type)."
)

search_drivers_tool = Tool(
    name="SearchDrivers",
    func=query_driver_database,
    description="Searches the driver database for available drivers that can drive the specified vehicle type. Input should be vehicle_type (string). Returns a list of matching driver records (driver_id, driver_name)."
)

add_vehicle_to_order_tool = Tool(
    name="AddVehicleToOrder",
    func=add_vehicle_to_order,
    description="Adds the vehicle ID and type to the order data dictionary. Input should be order_data (dict), vehicle_id (int), and vehicle_type (string). Returns the updated order data dictionary."
)

add_driver_to_order_tool = Tool(
    name="AddDriverToOrder",
    func=add_driver_to_order,
    description="Adds the driver ID and name to the order data dictionary. Input should be order_data (dict), driver_id (int), and driver_name (string). Returns the updated order data dictionary."
)

#routing_tool function
def routing(start_address:str,destination_address:str) ->Any:
    url = "https://www.google.com/maps/dir/?api=1"

    route_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    
    start_geoaddress=gmaps.geocode(start_address)
    destination_geoaddress=gmaps.geocode(destination_address)

    start_lat=start_geoaddress[0]['geometry']['location']['lat']
    start_lng=start_geoaddress[0]['geometry']['location']['lng']

    dest_lat=destination_geoaddress[0]['geometry']['location']['lat']
    dest_lng=destination_geoaddress[0]['geometry']['location']['lng']
    try:
       response=gmaps.directions(
       origin=f'{start_lat},{start_lng}',
       destination=f"{dest_lat},{dest_lng}",
       mode="driving",
       )

    
       map_link = f"{url}"+"&origin="+f"{start_address}"+"&destination="+f"{destination_address}"+"&travelmode=driving"
       if response:
            route = response[0]['legs'][0]
            distance = route['distance']['text']
            duration= route['duration']['text']

            response = f"Total distance: {distance}, ETA: {duration}"
       else:
            response ="API is not responding, so fix API" #Change It back to API code being better at doing this then It can
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {e}"}
    except (KeyError, IndexError) as e:
        return {"error": f"Error parsing Google Maps API response: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

    except Exception as e:
        return f"An error occurred: {e}"
    

        
    return {distance,duration,map_link}

  


    
routing_tool = Tool(
    name="routing_tool",
    func=routing,
    description="Estimates the distance and travel time between two locations and provides a Google Maps link. Input should be two strings, representing the origin and destination addresses.  For example: 'routing_tool(origin=\"1600 Amphitheatre Parkway, Mountain View, CA\", destination=\"Empire State Building, New York, NY\")'",
)


#list of tools
tools=[search,routing_tool,search_vehicles_tool,
    search_drivers_tool,
    add_vehicle_to_order_tool,
    add_driver_to_order_tool]

model=ChatOpenAI(temperature=1.0,model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, max_retries=2)
agent_executor=create_react_agent(model,tools)

#dist1='5, Marina Road, Lagos Island, Lagos State, Nigeria'
#dist2="3 Nicolve Ave, Agege, Lagos, Nigeria"

order={"order_id":"1234567",
        "order_name":"fuel",
        "good_type":"petroleum",
        "capacity":10,
        "pickup_location":"12 shitta street,Dopemu,Agege,Lagos",
        "dropoff_location":"14 samaru road,Zaria,kaduna"}
query=f"""
You are an order matching agent. you recieved a new order with the following details: {order}

Your goal is to find a suitable vehicle and driver for this order and output the results in JSON format according to the following schema: {format_instructions}.

Here's how to process the order:

1. Use `SearchVehicles` to find a suitable vehicle for 'petroleum'.
2. **If no vehicles are found**, stop and respond with the JSON: `{{ "status": "failed", "reason": "No suitable vehicle found." }}`
3. If a vehicle is found, use the `vehicle_type` to `SearchDrivers` for an available driver.
4. **If no drivers are found** for the vehicle type, stop and respond with the JSON: `{{ "status": "failed", "reason": "No suitable driver found for the vehicle type." }}`
5. If a driver is found, select the driver name and driver id that perfectly fit for the order such that the output the `order_id`, `vehicle_id`, `vehicle_type`, `driver_name`, and `driver_id` in JSON format.
6. **Once both a vehicle and a driver are successfully matched**, stop and output the results in the JSON format specified above, including the `order_id`, `vehicle_id`, `vehicle_type`, `driver_name`, and `driver_id`.

"""   
#print(routing({dist1},{dist2}))
response=agent_executor.invoke({"message":[HumanMessage(content=query)]})

"""
import pprint
try:
    for step in agent_executor.stream(
        {"messages": [HumanMessage(content=query)]},
        config={'recursion_limit':90}
    ):
        if 'agent' in step and 'message' in step['agent']:
            pprint.pp(step['messages'])
       
      #print(f"step shown below {step}")
      #step["messages"][-1].pretty_print

except Exception as e:
    print(f"Error during agent execution: {e}")
    """
"""
model=model.bind_tools(tools)
response=model.invoke([HumanMessage(content=query)])
response.content
pprint.pp(response.content)
"""


from langchain.schema import OutputParserException
import pprint
try:
    final_response=response.content
    parsed_response=output_parser.parse(final_response)
    pprint.pp(parsed_response)
except OutputParserException as e:
    print(f"Error parsing agent output: {e}")
    print(f"Raw output: {final_response}")
