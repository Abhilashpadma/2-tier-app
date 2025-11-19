from flask import Flask, render_template, request, jsonify
import mysql.connector
import os
import time
import sys

app = Flask(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql-service'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'dbuser'),
    'password': os.getenv('DB_PASSWORD', 'dbpassword'),
    'database': os.getenv('DB_NAME', 'keyvaluedb')
}

def get_db_connection():
    """Create and return a database connection with retry logic"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except mysql.connector.Error as err:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1} failed: {err}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")
                raise

def init_db():
    """Initialize the database table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyvalue_store (
                id INT AUTO_INCREMENT PRIMARY KEY,
                key_name VARCHAR(255) UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/store', methods=['POST'])
def store_value():
    """Store a key-value pair"""
    try:
        data = request.get_json()
        key = data.get('key')
        value = data.get('value')
        
        if not key or not value:
            return jsonify({'error': 'Both key and value are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert or update the key-value pair
        cursor.execute("""
            INSERT INTO keyvalue_store (key_name, value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE value = %s, updated_at = CURRENT_TIMESTAMP
        """, (key, value, value))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Value stored successfully', 'key': key, 'value': value}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retrieve/<key>')
def retrieve_value(key):
    """Retrieve a value by key"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM keyvalue_store WHERE key_name = %s", (key,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Key not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all')
def get_all():
    """Get all key-value pairs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM keyvalue_store ORDER BY created_at DESC")
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<key>', methods=['DELETE'])
def delete_value(key):
    """Delete a key-value pair"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM keyvalue_store WHERE key_name = %s", (key,))
        conn.commit()
        
        if cursor.rowcount > 0:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Key deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Key not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting application...")
    print(f"Connecting to database at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
