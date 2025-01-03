# **DASHCRAFT: Carfting DashBoards Effortlessly**

### **Overview**
The Dashcraft is a Flask-based web application that allows users to dynamically upload and visualize datasets using various chart types such as line charts, scatter plots, and pie charts. The application supports customizable attributes for analysis and includes a light/dark mode for enhanced user experience.

---

### **Features**
- **Dynamic Visualization:** Supports line charts, scatter plots, and pie charts.
- **Attribute Selection:** Customize X and Y axes for targeted data analysis.
- **Theme Toggle:** Light and dark mode options for improved accessibility.
- **Responsive Design:** A clean and modern UI built for all devices.
- **Sample Data Testing:** Preloaded CSV files to demonstrate functionality.

---

### **Technologies Used**
- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Data Handling:** Pandas, Matplotlib
- **Version Control:** Git & GitHub

---

### **Installation**

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/data-visualization-dashboard.git
   cd data-visualization-dashboard
   ```

2. **Set Up the Environment:**
   Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python app.py
   ```

4. **Open in Browser:**
   Access the application at `http://127.0.0.1:5000/`.

---

### **Usage**
1. Navigate to the homepage and upload your CSV file.
2. Customize your visualization by selecting data attributes (X and Y axes).
3. Choose the desired chart type (line, scatter, or pie chart).
4. Toggle between light and dark mode for better viewing.

---

### **Project Structure**
```plaintext
.
├── templates/
│   ├── index.html    # Homepage
│   ├── dashboard.html # Dashboard for visualizations
├── static/
│   ├── style.css     # Stylesheet for the application
├── app.py            # Flask application
├── requirements.txt  # Python dependencies
├── sample_data.csv   # Sample dataset for testing
```

---

### **Future Enhancements**
- Add support for additional chart types (e.g., bar charts, histograms).
- Implement advanced filtering and aggregation options.
- Enable database integration for persistent data storage.

---
