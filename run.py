import os
from app import app

def setup_directories():
    # Create required directories with absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(base_dir, 'instance')
    uploads_dir = os.path.join(base_dir, 'uploads')
    
    # Create directories if they don't exist
    os.makedirs(instance_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Print directory information for debugging
    print(f"Instance directory: {instance_dir}")
    print(f"Uploads directory: {uploads_dir}")
    
    # Ensure directories are writable
    try:
        test_file = os.path.join(instance_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("Directory permissions verified successfully")
    except Exception as e:
        print(f"Error verifying directory permissions: {e}")
        raise

if __name__ == '__main__':
    setup_directories()
    app.run(debug=True, port=5000)
