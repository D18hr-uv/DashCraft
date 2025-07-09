import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) # Replace with a strong secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Route to redirect to if @login_required is used
login_manager.login_message_category = 'info'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    files = db.relationship('UserFile', backref='uploader', lazy=True)

    def __repr__(self):
        return f"User('{self.username}')"

# UserFile model
class UserFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(200), nullable=False) # Path to the stored CSV
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"UserFile('{self.filename}', User: '{self.uploader.username}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Dash app
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

# Placeholder for uploaded data - Will be replaced by user-specific data loading
# global_data = pd.DataFrame() # This will be removed or refactored

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {username}! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Flask route for homepage - protected
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST': # File upload handled here
        file = request.files.get('file')
        if file and file.filename != '':
            # Ensure user-specific directory exists
            user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
            if not os.path.exists(user_upload_dir):
                os.makedirs(user_upload_dir)

            # Sanitize filename
            filename = secure_filename(file.filename)
            if not filename: # Handle empty filename after sanitization
                flash('Invalid file name.', 'danger')
                return redirect(url_for('index'))
            filepath = os.path.join(user_upload_dir, filename)

            # Overwrite if file exists for simplicity, or implement versioning/prompt
            if os.path.exists(filepath):
                os.remove(filepath)
            file.save(filepath)

            # Update or create UserFile entry
            user_file_record = UserFile.query.filter_by(user_id=current_user.id).first()
            if user_file_record:
                user_file_record.filename = filename
                user_file_record.filepath = filepath
            else:
                user_file_record = UserFile(filename=filename, filepath=filepath, uploader=current_user)
                db.session.add(user_file_record)

            db.session.commit()
            flash('File uploaded successfully! You can now view it in the dashboard.', 'success')
            return redirect(url_for('dash_app.index')) # Redirect to Dash app

    # Check if user has existing data to display a message or link
    user_file = UserFile.query.filter_by(user_id=current_user.id).first()
    return render_template('index.html', user_file=user_file)

# Dash app URL is now protected by Flask-Login via the server instance
# Dash layout
dash_app.layout = html.Div([
    html.H1("Interactive Data Visualization Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Select Columns for X-Axis"),
        dcc.Dropdown(id='x-axis-column', placeholder='Select X-Axis', multi=False),
        
        html.Label("Select Columns for Y-Axis"),
        dcc.Dropdown(id='y-axis-column', placeholder='Select Y-Axis', multi=True),
        
        html.Label("Select Plot Type"),
        dcc.RadioItems(
            id='plot-type',
            options=[
                {'label': 'Line Chart', 'value': 'line'},
                {'label': 'Scatter Plot', 'value': 'scatter'},
                {'label': 'Pie Chart', 'value': 'pie'}
            ],
            value='line',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ], style={'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '10px', 'margin': '10px'}),
    
    dcc.Graph(id='data-graph'),
])

# Dash callbacks
@dash_app.callback(
    [Output('x-axis-column', 'options'),
     Output('y-axis-column', 'options'),
     Output('data-graph', 'figure')],
    [Input('x-axis-column', 'value'),
     Input('y-axis-column', 'value'),
     Input('plot-type', 'value')]
)
def update_graph(x_column, y_columns, plot_type):
    with app.app_context(): # Ensure access to current_user and db
        if not current_user.is_authenticated:
            return [], [], {'data': [], 'layout': {'title': 'Please log in to view data.'}}

        user_file_record = UserFile.query.filter_by(user_id=current_user.id).first()
        if not user_file_record:
            return [], [], {'data': [], 'layout': {'title': 'No data uploaded. Please upload a CSV file from the main page.'}}

        if not os.path.exists(user_file_record.filepath):
            app.logger.warning(f"File not found for user {current_user.id} at path {user_file_record.filepath}")
            return [], [], {'data': [], 'layout': {'title': f'Error: File not found. Please re-upload.'}}

        try:
            data = pd.read_csv(user_file_record.filepath)
            if data.empty:
                app.logger.info(f"CSV file is empty for user {current_user.id} at path {user_file_record.filepath}")
                return [], [], {'data': [], 'layout': {'title': 'Uploaded CSV is empty or could not be parsed correctly.'}}
        except Exception as e:
            app.logger.error(f"Error loading or parsing CSV for user {current_user.id} at path {user_file_record.filepath}: {e}")
            return [], [], {'data': [], 'layout': {'title': f'Error processing CSV: {str(e)[:100]}. Please check file format and content.'}}

        options = [{'label': col, 'value': col} for col in data.columns]
        figure = {'data': [], 'layout': {'title': 'Select data and plot type to visualize.'}}

        if x_column and y_columns and not data.empty:
            # Basic check if selected columns exist in the dataframe
            if x_column not in data.columns or not all(y_col in data.columns for y_col in y_columns):
                figure = {'data': [], 'layout': {'title': 'Selected column(s) not found in the current dataset. Please reselect.'}}
                return options, options, figure

            if plot_type == 'line':
                figure = {
                    'data': [
                        {'x': data[x_column], 'y': data[y], 'type': 'line', 'name': y}
                        for y in y_columns
                    ],
                    'layout': {'title': f'Line Chart: {", ".join(y_columns)} vs {x_column}'}
                }
            elif plot_type == 'scatter':
                figure = {
                    'data': [
                        {'x': data[x_column], 'y': data[y], 'mode': 'markers', 'name': y}
                        for y in y_columns
                    ],
                    'layout': {'title': f'Scatter Plot: {", ".join(y_columns)} vs {x_column}'}
                }
            elif plot_type == 'pie' and len(y_columns) == 1:
                y_col_pie = y_columns[0]
                # Further check for pie chart if the y_col_pie is valid
                if y_col_pie not in data.columns:
                    figure = {'data': [], 'layout': {'title': f'Column {y_col_pie} not found for Pie Chart.'}}
                    return options, options, figure

                # Attempt to convert pie chart values to numeric, handle errors
                try:
                    pie_values = pd.to_numeric(data[y_col_pie], errors='coerce').fillna(0)
                    if pie_values.sum() == 0: # Avoid pie chart with all zeros or all NaNs
                         figure = {'data': [], 'layout': {'title': f'Pie Chart values for {y_col_pie} are all zero or non-numeric.'}}
                         return options, options, figure
                except Exception as e:
                    app.logger.error(f"Error converting pie chart values for user {current_user.id}: {e}")
                    figure = {'data': [], 'layout': {'title': f'Error preparing data for Pie Chart: {str(e)[:100]}'}}
                    return options, options, figure

                figure = {
                    'data': [{
                        'labels': data[x_column],
                        'values': pie_values,
                        'type': 'pie'
                    }],
                    'layout': {'title': f'Pie Chart: {y_col_pie} by {x_column}'}
                }
            else:
                figure = {'data': [], 'layout': {'title': 'Please select valid X, Y columns and plot type for the loaded data.'}}

        return options, options, figure

