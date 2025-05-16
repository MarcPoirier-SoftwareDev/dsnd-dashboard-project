from fasthtml.common import *
import matplotlib.pyplot as plt

# Import QueryBase, Employee, Team from employee_events
from employee_events import QueryBase, Employee, Team

# Import the load_model function from the utils.py file
from utils import load_model

"""
Below, we import the parent classes
you will use for subclassing
"""
from base_components import (
    Dropdown,
    BaseComponent,
    Radio,
    MatplotlibViz,
    DataTable
)

from combined_components import FormGroup, CombinedComponent

# Create a subclass of base_components/Dropdown called `ReportDropdown`
class ReportDropdown(Dropdown):
    # Overwrite the build_component method ensuring it has the same parameters as the parent class's method
    def build_component(self, entity_id, model):
        # Set the `label` attribute to the `name` attribute for the model
        #self.label = model.name
        self.label = f"{model.name} Selection"  # Example: "Employee Selection"
        # Return the output from the parent class's build_component method
        return super().build_component(entity_id, model)
    
    # Overwrite the `component_data` method with the same parameters as the parent class method
    def component_data(self, entity_id, model):
        # Get the options from the model
        options = model.get_user_options()
        if not options:
            return []  # Or raise an exception/log a warning
        print(f"Options for {model.name}: {options}")  # Or use logging
        # Swap the order of the tuple elements to (id, name)
        return [(str(opt[1]), opt[0]) for opt in options]

# Create a subclass of base_components/BaseComponent called `Header`
class Header(BaseComponent):
    # Overwrite the `build_component` method with the same parameters as the parent class
    def build_component(self, entity_id, model):
        # Using the model argument, return a FastHTML H1 object containing the model's name attribute
        return H1(model.name)

# Create a subclass of base_components/MatplotlibViz called `LineChart`
class LineChart(MatplotlibViz):
    # Overwrite the parent class's `visualization` method with the same parameters
    def visualization(self, asset_id, model):
        # Pass the `asset_id` argument to the model's `event_counts` method
        df = model.event_counts(asset_id)
        
        # Use pandas .fillna method to fill nulls with 0
        df = df.fillna(0)
        
        # Use pandas .set_index method to set the date column as the index
        df = df.set_index('event_date')
        
        # Sort the index
        df = df.sort_index()
        
        # Use the .cumsum method to change the data to cumulative counts
        df_cumsum = df.cumsum()
        
        # Set the dataframe columns to ['Positive', 'Negative']
        df_cumsum.columns = ['Positive', 'Negative']
        
        # Initialize a matplotlib subplot and assign the figure and axis to variables
        fig, ax = plt.subplots()
        
        # Call the .plot method for the cumulative counts dataframe
        df_cumsum.plot(ax=ax)
        
        # Pass the axis variable to `.set_axis_styling` with border_color and font_color set to black
        self.set_axis_styling(ax, bordercolor='black', fontcolor='black')
        
        # Set title and labels for x and y axis
        ax.set_title('Cumulative Events Over Time')
        ax.set_xlabel('Event Date')
        ax.set_ylabel('Cumulative Count')
        
        return fig

# Create a subclass of base_components/MatplotlibViz called `BarChart`
class BarChart(MatplotlibViz):
    # Create a `predictor` class attribute assigned to the output of `load_model`
    predictor = load_model()

    # Overwrite the parent class `visualization` method with the same parameters
    def visualization(self, asset_id, model):
        # Pass the `asset_id` to the `.model_data` method to receive data for the machine learning model
        data = model.model_data(asset_id)
        
        # Using the predictor class attribute, pass the data to `predict_proba`
        proba = self.predictor.predict_proba(data)
        
        # Index the second column of predict_proba output (probability of positive class)
        proba = proba[:, 1]
        
        # If the model's name attribute is "team", set `pred` to the mean of predict_proba output
        if model.name == "team":
            pred = proba.mean()
        # Otherwise set `pred` to the first value of predict_proba output
        else:
            pred = proba[0]
        
        # Initialize a matplotlib subplot
        fig, ax = plt.subplots()
        
        # Run the following code unchanged
        ax.barh([''], [pred])
        ax.set_xlim(0, 1)
        ax.set_title('Predicted Recruitment Risk', fontsize=20)
        
        # Pass the axis variable to `.set_axis_styling`
        self.set_axis_styling(ax)
        
        return fig

# Create a subclass of combined_components/CombinedComponent called `Visualizations`
class Visualizations(CombinedComponent):
    # Set the `children` class attribute to a list containing initialized instances of `LineChart` and `BarChart`
    children = [LineChart(), BarChart()]
    
    # Leave this line unchanged
    outer_div_type = Div(cls='grid')

# Create a subclass of base_components/DataTable called `NotesTable`
class NotesTable(DataTable):
    # Overwrite the `component_data` method with the same parameters as the parent class
    def component_data(self, entity_id, model):
        # Pass the entity_id to the model's .notes method and return the output
        return model.notes(entity_id)

PROXY_PREFIX = "/proxy/5001"
class DashboardFilters(FormGroup):
    id = "top-filters"
    action = f"{PROXY_PREFIX}/update_data"
    method = "POST"
    children = [
        Radio(
            values=["Employee", "Team"],
            name='profile_type',
            hx_get=f"{PROXY_PREFIX}/update_dropdown",
            hx_target='#selector'
        ),
        ReportDropdown(
            id="selector",
            name="user-selection"
        )
    ]

# Create a subclass of CombinedComponent called `Report`
class Report(CombinedComponent):
    # Set the `children` class attribute to a list containing initialized instances of Header, DashboardFilters, Visualizations, and NotesTable
    children = [
        Header(),
        DashboardFilters(),
        Visualizations(),
        NotesTable()
    ]

# Initialize a FastHTML app
app = FastHTML()

# Initialize the `Report` class
report = Report()

# Create a route for a GET request with the path set to the root
@app.get("/")
def index():
    # Call the initialized report, pass integer 1 and an instance of Employee, return the result
    return report(1, Employee())

# Create a route for a GET request with path parameterized for employee ID
@app.get("/employee/{entity_id}")
def employee(entity_id: str):
    try:
        entity_id = int(entity_id) # Validate as integer
        # Call the initialized report, pass the ID and an instance of Employee, return the result
        return report(entity_id, Employee())
    except ValueError:
        return "Invalid employee ID: must be an integer", 400
    except Exception as e:
        return f"Error generating report: {str(e)}", 500     

# Create a route for a GET request with path parameterized for team ID
@app.get("/team/{entity_id}")
def team(entity_id: str):
    try:
        entity_id = int(entity_id)  # Validate as integer
        # Call the initialized report, pass the ID and an instance of Team, return the result
        return report(entity_id, Team())        
    except ValueError:
        return "Invalid team ID: must be an integer", 400
    except Exception as e:
        return f"Error generating report: {str(e)}", 500


# Keep the below code unchanged!
@app.get('/update_dropdown')
def update_dropdown(r):
    dropdown = DashboardFilters.children[1]
    print('PARAM', r.query_params['profile_type'])
    if r.query_params['profile_type'] == 'Team':
        return dropdown(None, Team())
    elif r.query_params['profile_type'] == 'Employee':
        return dropdown(None, Employee())

@app.post('/update_data')
async def update_data(r):
    from fasthtml.common import RedirectResponse
    data = await r.form()
    profile_type = data._dict['profile_type']
    id = data._dict['user-selection']
    if profile_type == 'Employee':
        return RedirectResponse(f"/employee/{id}", status_code=303)
    elif profile_type == 'Team':
        return RedirectResponse(f"/team/{id}", status_code=303)

serve()
