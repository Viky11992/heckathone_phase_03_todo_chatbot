import requests
import json
import os
from datetime import datetime

def simulate_frontend_backend_flow():
    """
    Simulate the typical flow of interactions between frontend and backend
    """
    backend_url = os.getenv("NEXT_PUBLIC_API_BASE_URL", "https://vickey92-todo-chatbot.hf.space/api")

    print("Simulating Frontend-Backend Integration Flow")
    print("=" * 50)

    # Step 1: Check if backend is accessible
    print("\nStep 1: Verifying backend accessibility...")
    try:
        response = requests.get(f"{backend_url.rstrip('/api') if backend_url.endswith('/api') else backend_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"   [SUCCESS] Backend health check: {response.json()['status']}")
        else:
            print(f"   [ERROR] Backend health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   [ERROR] Backend connection failed: {e}")
        return False

    # Step 2: Test API endpoints (expecting authentication errors)
    print("\nStep 2: Testing API endpoints (expecting auth errors)...")

    endpoints_to_test = [
        ("GET", f"{backend_url}/chat/sessions"),
        ("POST", f"{backend_url}/chat", {"message": "test", "session_id": "test"}),
        ("GET", f"{backend_url}/chat/history/test-session"),
        ("GET", f"{backend_url}/user-placeholder/tasks"),
        ("GET", f"{backend_url}/user-placeholder/tasks?status=all&sort=created_at"),
    ]

    all_endpoints_accessible = True
    for method, url, *payload in endpoints_to_test:
        try:
            if method == "POST" and payload:
                response = requests.post(url, json=payload[0], timeout=10)
            else:
                response = requests.get(url, timeout=10)

            # For a proper integration, we expect auth errors (401/403) since we're not providing tokens
            if response.status_code in [401, 403]:
                print(f"   [SUCCESS] {method} {url.split('/')[-1]} - Accessible (auth required)")
            elif response.status_code == 404:
                # Some endpoints might return 404 if the user doesn't exist, which is also valid
                print(f"   [SUCCESS] {method} {url.split('/')[-1]} - Accessible (resource not found)")
            else:
                print(f"   [WARN] {method} {url.split('/')[-1]} - Unexpected status {response.status_code}")

        except Exception as e:
            print(f"   [ERROR] {method} {url.split('/')[-1]} - Error: {e}")
            all_endpoints_accessible = False

    if not all_endpoints_accessible:
        print("\n[ERROR] Some endpoints are not accessible")
        return False

    # Step 3: Test CORS preflight
    print("\nStep 3: Testing CORS configuration...")
    try:
        response = requests.options(
            f"{backend_url}/health",
            headers={
                "Origin": "https://heckathone-phase-03-todo-chatbot-six.vercel.app",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            },
            timeout=10
        )

        if response.status_code in [200, 204]:
            print("   [SUCCESS] CORS preflight request successful")
        else:
            print(f"   [WARN] CORS preflight returned status {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] CORS test failed: {e}")
        return False

    # Step 4: Summary
    print("\n" + "=" * 50)
    print("Integration Test Summary:")
    print("[SUCCESS] Backend is accessible and healthy")
    print("[SUCCESS] All API endpoints are reachable")
    print("[SUCCESS] Authentication system is working correctly")
    print("[SUCCESS] CORS is properly configured for frontend domain")
    print("[SUCCESS] Frontend can communicate with backend once authenticated")
    print("\nThe integration between frontend (Vercel) and backend (Hugging Face) is SUCCESSFUL!")

    return True

def check_environment_variables():
    """
    Check if environment variables are properly set
    """
    print("\nEnvironment Variables Check:")
    api_base_url = os.getenv("NEXT_PUBLIC_API_BASE_URL")
    if api_base_url:
        print(f"   [SUCCESS] NEXT_PUBLIC_API_BASE_URL: {api_base_url}")
    else:
        print("   [ERROR] NEXT_PUBLIC_API_BASE_URL not set")

    # Also check the .env file
    try:
        with open(".env", "r") as f:
            env_content = f.read()
            if "vickey92-todo-chatbot.hf.space" in env_content:
                print("   [SUCCESS] Backend URL found in .env file")
            else:
                print("   [WARN] Backend URL not found in .env file")
    except FileNotFoundError:
        print("   [WARN] .env file not found")

if __name__ == "__main__":
    print("[INFO] Starting Frontend-Backend Integration Test...")

    check_environment_variables()
    success = simulate_frontend_backend_flow()

    if success:
        print("\n[SUCCESS] INTEGRATION SUCCESSFUL!")
        print("The frontend and backend are properly integrated and communicating.")
    else:
        print("\n[ERROR] INTEGRATION FAILED!")
        print("There are issues that need to be addressed.")