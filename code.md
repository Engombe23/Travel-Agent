# Travel Agent System Design

The system is structured through a programming paradigm called object-oriented programming (OOP).

## Sections

### 1. Agents

As the system involves 4 agents (planner, flight, hotel and activity), each agent is inside the agents/ folder and has its own class, running its individual role in the system

### 2. API Adapters

The API adapters are found in the /adapters folder. This is used for when API keys for the hotel and activity have reached their limit so for instance, using either TripAdvisor or Booking for hotels should be fine.

### 3. Models

Pydantic models were created for each agent to be used in LangChain to match the respective agent. For instance, the flight agent uses the Flight & Airport models in flight.py and airport.py.

The models are given attributes and are part of the schema for the application.

They are located in the models/ folder.

### 4. Services (the scripts that run the external APIs like in api-index.js)

Each agent is connected to its own service (API key), which run the API responses for the flight, hotel and activity. They are located in the services/ folder.

### 5. Tools

Tools are important to for agents to run on LangChain and LangGraph. They are located in the tools/ folder.
Each agent will have its own tool to run where it calles the respective 'service', the script that runs the API responses

### 6. Graph

The graph/ folder is where the system will be using LangGraph to update the "state" of each agent as it returns its reponse to be added to the graph.

A "PlannerState" model was created which links to the PlannerAgent in planner_agent.py. The role of the model is that every time the script runs the flight or hotel agents, the flight and hotel info is updated in the state.

### 7. agent.py

The main script to run the application.

Run the command "python agent.py" to show the CLI output.

### 8. Airport Dataset

Found in the /data folder. It was used to match airport IATA codes with cities as the Google Flights API uses IATA codes.

### 9. Conclusion

Overall, the system works like this:

Agent -> Service -> Tool

The agents are matched with their own "models" and the state is updated after flight info, for instance has been received by the agent.