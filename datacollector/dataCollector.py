import os
import time
import requests
import pyodbc

# Use CoinGecko detailed API (works reliably, comprehensive data)
url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"

# SQL Server connection configuration from environment variables
instance_name = os.getenv('SQL_SERVER_HOST', 'sqlServer')         # The host name of the SQL server container
database_name = os.getenv('SQL_DATABASE', 'Cryptocurrency')       # The target database name
username = os.getenv('SQL_USERNAME', 'sa')                        # SQL Server administrator username
password = os.getenv('SA_PASSWORD') or os.getenv('SQL_PASSWORD')  # SQL Server password
port = os.getenv('SQL_PORT', '1433')                              # SQL Server inside the container listens on port 1433

if not password:
    raise ValueError("SA_PASSWORD (or SQL_PASSWORD) environment variable is required")

# Wait for 19 seconds before starting the loop (sync timing, wait for SQL Server to start)
time.sleep(19)

# Infinite loop to continuously fetch and save the price
while True:
    try:
        # Make a GET request to the CoinGecko API
        response = requests.get(url, timeout=10)
        
        # Check for rate limiting (429) or forbidden access (403)
        if response.status_code in (403, 429):
            print(f'API error {response.status_code}, waiting 60 seconds...')
            time.sleep(60)
            continue  # Skip DB logic and retry API call
        
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        # Extract the current Bitcoin price in USD from the response
        btc_price = float(data['market_data']['current_price']['usd'])
        
        print(f'Current BTC price: ${btc_price:,.2f}') 
    except requests.exceptions.RequestException as e:
        print(f'Error fetching price: {e}')
        time.sleep(30)
        continue  # Skip DB logic and retry API call
    except KeyError as e:
        print(f'Unexpected API response format: {e}')
        time.sleep(30)
        continue
    except Exception as e:
        print(f'Error fetching price: {e}')
        time.sleep(30)
        continue

    try:

        # First connect to master database to check/create the target database
        master_connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};' \
                          f'SERVER={instance_name},{port};' \
                          f'DATABASE=master;' \
                          f'UID={username};' \
                          f'PWD={password};'
        
        conn = pyodbc.connect(master_connection_string)
        conn.autocommit = True  # Required for CREATE DATABASE
        cursor = conn.cursor()
        
        # Check if Cryptocurrency database exists, create if not
        # Validate database name to prevent SQL injection (alphanumeric + underscore only)
        if not database_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid database name: {database_name}")
        cursor.execute(f"""
            IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{database_name}')
            BEGIN
                CREATE DATABASE [{database_name}]
                PRINT 'Database created'
            END
            ELSE
            BEGIN
                PRINT 'Database already exists'
            END
        """)
        conn.close()
        
        # Now connect to the target database
        connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};' \
                         f'SERVER={instance_name},{port};' \
                         f'DATABASE={database_name};' \
                         f'UID={username};' \
                         f'PWD={password};'

        # Establish connection to the SQL Server
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Ensure Bitcoin table exists
        # In SQL Server, INFORMATION_SCHEMA.TABLES is scoped to the current database context of the connection.
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Bitcoin')
            CREATE TABLE Bitcoin (
                DateTime datetime NOT NULL DEFAULT GETUTCDATE(),
                Price decimal(18, 8) NOT NULL
            )
        """)
        conn.commit()
        
        # Insert the current price and Pacific Time into the 'Bitcoin' table
        cursor.execute("""
            INSERT INTO Bitcoin (DateTime, Price) 
            VALUES (GETUTCDATE() AT TIME ZONE 'UTC' AT TIME ZONE 'Pacific Standard Time', ?)
        """, (btc_price))
        
        # Commit the transaction to save the changes
        conn.commit()
        
        # Close the connection
        conn.close()
    except pyodbc.Error as e:
        # If database operation fails, print the error (loop continues to next iteration)
        print(f'Error saving to database: {e}')
        time.sleep(10)
    except Exception as e:
        print(f'Unexpected database error: {e}')
        time.sleep(10)

    # Wait for 30 seconds before the next iteration to avoid overwhelming the API/DB
    time.sleep(30)
    