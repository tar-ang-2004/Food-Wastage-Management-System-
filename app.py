from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = 'food_wastage_management_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            provider_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            address TEXT,
            city TEXT,
            contact TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receivers (
            receiver_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT,
            contact TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_listings (
            food_id INTEGER PRIMARY KEY,
            food_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date DATE NOT NULL,
            provider_id INTEGER,
            provider_type TEXT,
            location TEXT,
            food_type TEXT,
            meal_type TEXT,
            description TEXT,
            status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (provider_id) REFERENCES providers (provider_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            claim_id INTEGER PRIMARY KEY,
            food_id INTEGER,
            receiver_id INTEGER,
            status TEXT DEFAULT 'Pending',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (food_id) REFERENCES food_listings (food_id),
            FOREIGN KEY (receiver_id) REFERENCES receivers (receiver_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Load data from CSV files
def load_initial_data():
    """Load initial data from CSV files if database is empty"""
    conn = sqlite3.connect('food_wastage.db')
    
    # Check if tables are empty
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM providers")
    if cursor.fetchone()[0] == 0:
        # Load data from CSV files
        try:
            providers_df = pd.read_csv('Dataset/providers_data.csv')
            receivers_df = pd.read_csv('Dataset/receivers_data.csv')
            food_listings_df = pd.read_csv('Dataset/food_listings_data.csv')
            claims_df = pd.read_csv('Dataset/claims_data.csv')
            
            # Insert data into database
            providers_df.to_sql('providers', conn, if_exists='append', index=False)
            receivers_df.to_sql('receivers', conn, if_exists='append', index=False)
            food_listings_df.to_sql('food_listings', conn, if_exists='append', index=False)
            claims_df.to_sql('claims', conn, if_exists='append', index=False)
            
            print("Initial data loaded successfully!")
        except FileNotFoundError:
            print("CSV files not found. Starting with empty database.")
    
    conn.close()

# Initialize database on startup
init_db()
load_initial_data()

@app.route('/')
def index():
    """Home page with dashboard"""
    conn = sqlite3.connect('food_wastage.db')
    
    # Get dashboard statistics
    cursor = conn.cursor()
    
    # Total counts
    cursor.execute("SELECT COUNT(*) FROM providers")
    total_providers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM receivers")
    total_receivers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM food_listings WHERE status = 'Available'")
    available_food_items = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM claims WHERE status = 'Completed'")
    successful_claims = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM claims WHERE status = 'Pending'")
    pending_claims = cursor.fetchone()[0]
    
    # Total food quantity available
    cursor.execute("SELECT SUM(quantity) FROM food_listings WHERE status = 'Available'")
    total_quantity = cursor.fetchone()[0] or 0
    
    # Food expiring soon (within 3 days)
    three_days_from_now = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT COUNT(*) FROM food_listings 
        WHERE expiry_date <= ? AND status = 'Available'
    """, (three_days_from_now,))
    expiring_soon = cursor.fetchone()[0]
    
    # Recent claims
    cursor.execute("""
        SELECT c.claim_id, f.food_name, r.name, c.status, c.timestamp
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        JOIN receivers r ON c.receiver_id = r.receiver_id
        ORDER BY c.timestamp DESC LIMIT 5
    """)
    recent_claims = cursor.fetchall()
    
    conn.close()
    
    stats = {
        'total_providers': total_providers,
        'total_receivers': total_receivers,
        'available_food_items': available_food_items,
        'successful_claims': successful_claims,
        'pending_claims': pending_claims,
        'total_quantity': total_quantity,
        'expiring_soon': expiring_soon,
        'recent_claims': recent_claims
    }
    
    return render_template('index.html', stats=stats)

@app.route('/providers')
def providers():
    """List all providers"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM providers ORDER BY name")
    providers_list = cursor.fetchall()
    
    conn.close()
    return render_template('providers.html', providers=providers_list)

@app.route('/providers/add', methods=['GET', 'POST'])
def add_provider():
    """Add new provider"""
    if request.method == 'POST':
        name = request.form['name']
        provider_type = request.form['type']
        address = request.form['address']
        city = request.form['city']
        contact = request.form['contact']
        email = request.form['email']
        
        conn = sqlite3.connect('food_wastage.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO providers (name, type, address, city, contact, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, provider_type, address, city, contact, email))
        
        conn.commit()
        conn.close()
        
        flash('Provider added successfully!', 'success')
        return redirect(url_for('providers'))
    
    return render_template('add_provider.html')

@app.route('/receivers')
def receivers():
    """List all receivers"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM receivers ORDER BY name")
    receivers_list = cursor.fetchall()
    
    conn.close()
    return render_template('receivers.html', receivers=receivers_list)

@app.route('/receivers/add', methods=['GET', 'POST'])
def add_receiver():
    """Add new receiver"""
    if request.method == 'POST':
        name = request.form['name']
        receiver_type = request.form['type']
        city = request.form['city']
        contact = request.form['contact']
        email = request.form['email']
        
        conn = sqlite3.connect('food_wastage.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO receivers (name, type, city, contact, email)
            VALUES (?, ?, ?, ?, ?)
        """, (name, receiver_type, city, contact, email))
        
        conn.commit()
        conn.close()
        
        flash('Receiver added successfully!', 'success')
        return redirect(url_for('receivers'))
    
    return render_template('add_receiver.html')

@app.route('/food_listings')
def food_listings():
    """List all food items"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    # Get filter parameters
    food_type = request.args.get('food_type', '')
    status = request.args.get('status', '')
    expiring_soon = request.args.get('expiring_soon', '')
    
    query = """
        SELECT f.*, p.name as provider_name
        FROM food_listings f
        LEFT JOIN providers p ON f.provider_id = p.provider_id
        WHERE 1=1
    """
    params = []
    
    if food_type:
        query += " AND f.food_type = ?"
        params.append(food_type)
    
    if status:
        query += " AND f.status = ?"
        params.append(status)
    
    if expiring_soon:
        three_days_from_now = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        query += " AND f.expiry_date <= ?"
        params.append(three_days_from_now)
    
    query += " ORDER BY f.expiry_date"
    
    cursor.execute(query, params)
    food_items = cursor.fetchall()
    
    # Get filter options
    cursor.execute("SELECT DISTINCT food_type FROM food_listings")
    food_types = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('food_listings.html', 
                         food_items=food_items, 
                         food_types=food_types,
                         selected_food_type=food_type,
                         selected_status=status,
                         expiring_soon_filter=expiring_soon)

@app.route('/food_listings/add', methods=['GET', 'POST'])
def add_food_listing():
    """Add new food listing"""
    if request.method == 'POST':
        food_name = request.form['food_name']
        quantity = int(request.form['quantity'])
        expiry_date = request.form['expiry_date']
        provider_id = int(request.form['provider_id'])
        location = request.form['location']
        food_type = request.form['food_type']
        meal_type = request.form['meal_type']
        description = request.form['description']
        
        conn = sqlite3.connect('food_wastage.db')
        cursor = conn.cursor()
        
        # Get provider type
        cursor.execute("SELECT type FROM providers WHERE provider_id = ?", (provider_id,))
        provider_type = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO food_listings 
            (food_name, quantity, expiry_date, provider_id, provider_type, 
             location, food_type, meal_type, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (food_name, quantity, expiry_date, provider_id, provider_type, 
              location, food_type, meal_type, description))
        
        conn.commit()
        conn.close()
        
        flash('Food listing added successfully!', 'success')
        return redirect(url_for('food_listings'))
    
    # Get providers for dropdown
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    cursor.execute("SELECT provider_id, name FROM providers ORDER BY name")
    providers_list = cursor.fetchall()
    conn.close()
    
    return render_template('add_food_listing.html', providers=providers_list)

@app.route('/claims')
def claims():
    """List all claims"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    status_filter = request.args.get('status', '')
    
    query = """
        SELECT c.claim_id, f.food_name, f.quantity, r.name as receiver_name,
               r.type as receiver_type, c.status, c.timestamp, c.notes
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        JOIN receivers r ON c.receiver_id = r.receiver_id
    """
    
    params = []
    if status_filter:
        query += " WHERE c.status = ?"
        params.append(status_filter)
    
    query += " ORDER BY c.timestamp DESC"
    
    cursor.execute(query, params)
    claims_list = cursor.fetchall()
    
    conn.close()
    return render_template('claims.html', claims=claims_list, selected_status=status_filter)

@app.route('/claims/add', methods=['GET', 'POST'])
def add_claim():
    """Add new claim"""
    if request.method == 'POST':
        food_id = int(request.form['food_id'])
        receiver_id = int(request.form['receiver_id'])
        notes = request.form.get('notes', '')
        
        conn = sqlite3.connect('food_wastage.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO claims (food_id, receiver_id, notes)
            VALUES (?, ?, ?)
        """, (food_id, receiver_id, notes))
        
        conn.commit()
        conn.close()
        
        flash('Claim submitted successfully!', 'success')
        return redirect(url_for('claims'))
    
    # Get available food items and receivers
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.food_id, f.food_name, f.quantity, f.expiry_date, p.name as provider_name
        FROM food_listings f
        JOIN providers p ON f.provider_id = p.provider_id
        WHERE f.status = 'Available'
        ORDER BY f.expiry_date
    """)
    available_food = cursor.fetchall()
    
    cursor.execute("SELECT receiver_id, name, type FROM receivers ORDER BY name")
    receivers_list = cursor.fetchall()
    
    conn.close()
    
    return render_template('add_claim.html', food_items=available_food, receivers=receivers_list)

@app.route('/claims/update/<int:claim_id>', methods=['POST'])
def update_claim_status(claim_id):
    """Update claim status"""
    new_status = request.form['status']
    
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE claims SET status = ? WHERE claim_id = ?", (new_status, claim_id))
    
    # If claim is completed, update food listing status
    if new_status == 'Completed':
        cursor.execute("""
            UPDATE food_listings 
            SET status = 'Claimed' 
            WHERE food_id = (SELECT food_id FROM claims WHERE claim_id = ?)
        """, (claim_id,))
    elif new_status == 'Cancelled':
        cursor.execute("""
            UPDATE food_listings 
            SET status = 'Available' 
            WHERE food_id = (SELECT food_id FROM claims WHERE claim_id = ?)
        """, (claim_id,))
    
    conn.commit()
    conn.close()
    
    flash(f'Claim status updated to {new_status}!', 'success')
    return redirect(url_for('claims'))

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    # Claims by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM claims
        GROUP BY status
    """)
    claims_by_status = dict(cursor.fetchall())
    
    # Food types distribution
    cursor.execute("""
        SELECT food_type, COUNT(*) as count
        FROM food_listings
        GROUP BY food_type
    """)
    food_types_dist = dict(cursor.fetchall())
    
    # Provider types distribution
    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM providers
        GROUP BY type
    """)
    provider_types_dist = dict(cursor.fetchall())
    
    # Receiver types distribution
    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM receivers
        GROUP BY type
    """)
    receiver_types_dist = dict(cursor.fetchall())
    
    # Food waste prevention metrics
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN c.status = 'Completed' THEN f.quantity ELSE 0 END) as saved,
            SUM(CASE WHEN c.status = 'Cancelled' THEN f.quantity ELSE 0 END) as cancelled,
            SUM(f.quantity) as total
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
    """)
    waste_metrics = cursor.fetchone()
    
    # Monthly trends (last 6 months)
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', timestamp) as month,
            COUNT(*) as claims_count
        FROM claims
        WHERE timestamp >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', timestamp)
        ORDER BY month
    """)
    monthly_trends = dict(cursor.fetchall())
    
    conn.close()
    
    analytics_data = {
        'claims_by_status': claims_by_status,
        'food_types_dist': food_types_dist,
        'provider_types_dist': provider_types_dist,
        'receiver_types_dist': receiver_types_dist,
        'waste_metrics': {
            'saved': waste_metrics[0] or 0,
            'cancelled': waste_metrics[1] or 0,
            'total': waste_metrics[2] or 0
        },
        'monthly_trends': monthly_trends
    }
    
    return render_template('analytics.html', data=analytics_data)

@app.route('/analytics/custom-query', methods=['POST'])
def custom_query():
    """Execute custom SQL query"""
    try:
        query = request.form.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Query cannot be empty'})
        
        # Security check - only allow SELECT statements
        query_upper = query.upper().strip()
        if not query_upper.startswith('SELECT'):
            return jsonify({'success': False, 'error': 'Only SELECT queries are allowed for security reasons'})
        
        # Additional security checks
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                return jsonify({'success': False, 'error': f'Keyword "{keyword}" is not allowed'})
        
        conn = sqlite3.connect('food_wastage.db')
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        # Get column names
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Fetch results
        results = cursor.fetchall()
        
        conn.close()
        
        # Format results for display
        formatted_results = []
        for row in results:
            formatted_results.append(list(row))
        
        return jsonify({
            'success': True,
            'columns': columns,
            'data': formatted_results,
            'row_count': len(results)
        })
        
    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error: {str(e)}'})

@app.route('/analytics/query-suggestions')
def query_suggestions():
    """Get suggested queries for users"""
    suggestions = [
        {
            'title': 'Total Food Items by Provider Type',
            'query': 'SELECT p.type, COUNT(f.food_id) as total_items FROM providers p LEFT JOIN food_listings f ON p.provider_id = f.provider_id GROUP BY p.type ORDER BY total_items DESC;'
        },
        {
            'title': 'Claims Status Summary',
            'query': 'SELECT status, COUNT(*) as count FROM claims GROUP BY status ORDER BY count DESC;'
        },
        {
            'title': 'Food Items Expiring in Next 7 Days',
            'query': 'SELECT f.food_name, f.quantity, f.expiry_date, p.name as provider FROM food_listings f JOIN providers p ON f.provider_id = p.provider_id WHERE f.expiry_date <= date("now", "+7 days") AND f.status = "Available" ORDER BY f.expiry_date;'
        },
        {
            'title': 'Top 5 Most Active Providers',
            'query': 'SELECT p.name, p.type, COUNT(f.food_id) as food_items, COUNT(c.claim_id) as claims FROM providers p LEFT JOIN food_listings f ON p.provider_id = f.provider_id LEFT JOIN claims c ON f.food_id = c.food_id GROUP BY p.provider_id ORDER BY food_items DESC LIMIT 5;'
        },
        {
            'title': 'Receivers by Type and City',
            'query': 'SELECT city, type, COUNT(*) as count FROM receivers GROUP BY city, type ORDER BY city, count DESC;'
        },
        {
            'title': 'Monthly Claims Trend',
            'query': 'SELECT strftime("%Y-%m", timestamp) as month, COUNT(*) as claims_count FROM claims GROUP BY month ORDER BY month DESC LIMIT 12;'
        },
        {
            'title': 'Food Waste Reduction Impact',
            'query': 'SELECT f.food_type, SUM(CAST(REPLACE(f.quantity, " kg", "") AS REAL)) as total_quantity FROM food_listings f JOIN claims c ON f.food_id = c.food_id WHERE c.status = "Completed" GROUP BY f.food_type ORDER BY total_quantity DESC;'
        },
        {
            'title': 'Average Response Time for Claims',
            'query': 'SELECT AVG(julianday(date("now")) - julianday(date(timestamp))) as avg_response_days FROM claims WHERE status != "Pending";'
        }
    ]
    
    return jsonify({'success': True, 'suggestions': suggestions})

@app.route('/api/urgent_food')
def api_urgent_food():
    """API endpoint for urgent food items"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    days_threshold = request.args.get('days', 3)
    threshold_date = (datetime.now() + timedelta(days=int(days_threshold))).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT f.food_id, f.food_name, f.quantity, f.expiry_date, 
               p.name as provider_name, p.contact
        FROM food_listings f
        JOIN providers p ON f.provider_id = p.provider_id
        WHERE f.expiry_date <= ? AND f.status = 'Available'
        ORDER BY f.expiry_date
    """, (threshold_date,))
    
    urgent_items = []
    for row in cursor.fetchall():
        urgent_items.append({
            'food_id': row[0],
            'food_name': row[1],
            'quantity': row[2],
            'expiry_date': row[3],
            'provider_name': row[4],
            'provider_contact': row[5]
        })
    
    conn.close()
    return jsonify(urgent_items)

@app.route('/api/dashboard_stats')
def api_dashboard_stats():
    """API endpoint for dashboard statistics"""
    conn = sqlite3.connect('food_wastage.db')
    cursor = conn.cursor()
    
    # Get various statistics
    stats = {}
    
    # Daily claims for the last 7 days
    cursor.execute("""
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM claims
        WHERE timestamp >= date('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY date
    """)
    daily_claims = dict(cursor.fetchall())
    
    # Success rate by provider type
    cursor.execute("""
        SELECT p.type,
               COUNT(*) as total_claims,
               SUM(CASE WHEN c.status = 'Completed' THEN 1 ELSE 0 END) as completed_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        JOIN providers p ON f.provider_id = p.provider_id
        GROUP BY p.type
    """)
    provider_success = {}
    for row in cursor.fetchall():
        provider_type, total, completed = row
        success_rate = (completed / total * 100) if total > 0 else 0
        provider_success[provider_type] = {
            'total': total,
            'completed': completed,
            'success_rate': round(success_rate, 1)
        }
    
    conn.close()
    
    stats = {
        'daily_claims': daily_claims,
        'provider_success': provider_success
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
