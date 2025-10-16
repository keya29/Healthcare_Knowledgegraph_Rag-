from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, DatabaseError
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB

def test_connection():
    print(f"Testing connection to Neo4j AuraDB...")
    print(f"URI: {NEO4J_URI}")
    print(f"Database: {NEO4J_DB}")
    
    try:
        # Create driver instance
        driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASS)
        )
        
        # Test basic connectivity
        print("Verifying connection...")
        driver.verify_connectivity()
        
        # Test database access
        with driver.session(database=NEO4J_DB) as session:
            # Try a simple query
            result = session.run("RETURN 1 as test")
            value = result.single()["test"]
            print(f"Successfully connected to Neo4j!")
            print(f"Test query result: {value}")
            
            # Get database info
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            component = result.single()
            if component:
                print(f"Neo4j version: {component['name']} {component['versions'][0]} {component['edition']}")
        
        driver.close()
        print("Connection test completed successfully!")
        
    except ServiceUnavailable as e:
        print(f"Connection failed - Service Unavailable: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify the following connection details in your Neo4j Aura console:")
        print(f"   - URI: {NEO4J_URI}")
        print(f"   - Database: {NEO4J_DB}")
        print("2. Check if your database instance is running in the Aura console")
        print("3. Ensure no firewall is blocking outbound connections to port 7687")
        print("4. Try accessing the Aura console in your browser")
    except DatabaseError as e:
        print(f"Database error: {str(e)}")
        print("Please check if the database name and credentials are correct")
    except Exception as e:
        print(f"Connection failed with error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    test_connection()