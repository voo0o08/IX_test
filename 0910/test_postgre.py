import psycopg2
from psycopg2 import sql

# Database connection parameters
db_params = {
    'dbname': 'INTERONE',
    'user': 'interx',
    'password': 'interx@504',
    'host': '192.168.160.199',
    'port': '15432'  # Default is 5432
}

# // 아래는 테스트 코드 이며, 접속해야 하는 테이블은 temp.api_datas_engel , temp.api_datas_lsm 두개의 테이블 입니다 . 
# // 해당 테이블에는 데이터가 많이 있으며, 데이터 조회 조건을 잘 못 지정할 경우 조회 시간이 매우 오래 걸립니다.  
# // 아래 방식으로 접속하며, 필요한 조회 조건을 생성하여 조회 하여야 합니다. 
# // select * from temp.api_datas_engel ade limit 1 
# // select * from temp.api_datas_lsm ade limit 1 

try:
    # Establish a connection to the PostgreSQL database 연결 
    conn = psycopg2.connect(**db_params)
    print("Connection established")

    # Create a cursor object
    cursor = conn.cursor()

    # Execute a SQL query
    cursor.execute("SELECT version();")

    # Fetch the result of the query
    db_version = cursor.fetchone()
    print("PostgreSQL database version:", db_version)

    # 난 테이블 수정은 하면 안되니까 일단 주석,,,
    # # Example of creating a table
    # cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS example_table (
    #         id SERIAL PRIMARY KEY,
    #         name VARCHAR(100),
    #         age INT
    #     );
    # """)
    # print("Table created successfully")

    # # Example of inserting data into the table
    # cursor.execute("""
    #     INSERT INTO example_table (name, age) VALUES (%s, %s);
    # """, ('John Doe', 1000))
    # print("Data inserted successfully")

    # Commit the transaction
    # conn.commit()
    
    test_table1 = "api_datas_engel"
    test_table2 = "api_datas_lsm"
    # Example of fetching data from the table
   
    # cursor.execute(f"SELECT * FROM temp.{test_table1} ade limit 1;")
    # SQL query to fetch rows where received_time and fscode match between the two tables
   
    query = f"""
    SELECT *
    FROM temp.{test_table1} ade
    WHERE ade.fscode = 'PD1004'
    LIMIT 10;
    """

    # Execute the SQL query
    cursor.execute(query)

    # Fetch the result of the query
    rows = cursor.fetchall()
    for row in rows:
        print(row)


except Exception as error:
    print("Error connecting to PostgreSQL database:", error)
finally:
    # Close the cursor and connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    print("Connection closed")