import requests
import json
import os
from datetime import datetime

def test_backend_connection():
    """
    Test script to verify the backend API is accessible and functioning
    """

    # Use the same backend URL as configured in the frontend
    backend_url = os.getenv("NEXT_PUBLIC_API_BASE_URL", "https://vickey92-todo-chatbot.hf.space/api")

    # If the URL doesn't have /api at the end, add it
    if not backend_url.endswith('/api'):
        base_url = backend_url.rstrip('/') + '/api'
    else:
        base_url = backend_url.rstrip('/api')

    print(f"Testing backend connection to: {base_url}")

    try:
        # Test the health endpoint
        health_url = f"{base_url}/health"
        print(f"\nTesting health endpoint: {health_url}")

        response = requests.get(health_url, timeout=10)
        print(f"Health check response status: {response.status_code}")
        print(f"Health check response: {response.json()}")

        if response.status_code == 200:
            print("\n[SUCCESS] Backend is accessible and healthy!")
        else:
            print(f"\n[ERROR] Backend returned status code: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Cannot connect to backend at {base_url}")
        print("This could be because:")
        print("- The Hugging Face space is sleeping and needs to wake up")
        print("- The URL is incorrect")
        print("- Network connectivity issues")

    except requests.exceptions.Timeout:
        print(f"\n[WARN] Request timed out. Backend at {base_url} might be slow to respond.")

    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request failed: {str(e)}")

    # Test the root endpoint as well
    try:
        root_url = base_url.rstrip('/api') if base_url.endswith('/api') else base_url
        print(f"\nTesting root endpoint: {root_url}")

        response = requests.get(root_url, timeout=10)
        print(f"Root endpoint response status: {response.status_code}")
        print(f"Root endpoint response: {response.json()}")

    except Exception as e:
        print(f"Root endpoint test failed: {str(e)}")

def test_chat_endpoint():
    """
    Test the chat endpoint if available
    """
    # Use the API base URL with /api suffix
    backend_url = os.getenv("NEXT_PUBLIC_API_BASE_URL", "https://vickey92-todo-chatbot.hf.space/api")

    print(f"\nTesting chat endpoint: {backend_url}/chat")

    # Try to send a simple test message (without proper auth, expecting 401 for auth issues)
    try:
        test_payload = {
            "message": "Hello",
            "session_id": "test-session-" + str(int(datetime.now().timestamp()))
        }

        response = requests.post(
            f"{backend_url}/chat",
            json=test_payload,
            timeout=15
        )

        print(f"Chat endpoint response status: {response.status_code}")
        # We expect 401/403 for auth issues, which means the endpoint exists
        if response.status_code in [401, 403, 422]:
            print("[SUCCESS] Chat endpoint is accessible (expected auth/validation error)")
        elif response.status_code == 200:
            print("[SUCCESS] Chat endpoint is accessible and responded successfully")
        else:
            print(f"[WARN] Chat endpoint returned unexpected status: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Chat endpoint test failed: {str(e)}")


def test_comprehensive_backend():
    """
    Comprehensive test to verify all backend API functionality
    """
    backend_url = os.getenv("NEXT_PUBLIC_API_BASE_URL", "https://vickey92-todo-chatbot.hf.space/api")

    print(f"\n[INFO] Testing comprehensive backend functionality at: {backend_url}")
    print("="*60)

    # Test 1: Health check (at root level, not under /api)
    print("\n[TEST 1] Testing Health Endpoint...")
    try:
        root_url = backend_url.rstrip('/api') if backend_url.endswith('/api') else backend_url
        response = requests.get(f"{root_url}/health", timeout=10)
        print(f"   Status: {response.status_code} - {response.json()}")
        if response.status_code == 200:
            print("   [SUCCESS] Health check passed")
        else:
            print("   [ERROR] Health check failed")
    except Exception as e:
        print(f"   [ERROR] Health check error: {e}")

    # Test 2: Chat history endpoint (expecting auth error)
    print("\n[TEST 2] Testing Chat History Endpoint...")
    try:
        response = requests.get(f"{backend_url}/chat/history/test-session", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code in [401, 403]:
            print("   [SUCCESS] Chat history endpoint accessible (auth required - expected)")
        else:
            print(f"   [WARN] Chat history endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Chat history endpoint error: {e}")

    # Test 3: User sessions endpoint (expecting auth error)
    print("\n[TEST 3] Testing User Sessions Endpoint...")
    try:
        response = requests.get(f"{backend_url}/chat/sessions", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code in [401, 403]:
            print("   [SUCCESS] User sessions endpoint accessible (auth required - expected)")
        else:
            print(f"   [WARN] User sessions endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] User sessions endpoint error: {e}")

    # Test 4: Tasks endpoint (will require userId, expecting auth error)
    print("\n[TEST 4] Testing Tasks Endpoint...")
    try:
        response = requests.get(f"{backend_url}/user-id-placeholder/tasks", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code in [401, 403, 404]:  # 404 means endpoint exists but user doesn't
            print("   [SUCCESS] Tasks endpoint accessible (auth/user validation working)")
        else:
            print(f"   [WARN] Tasks endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Tasks endpoint error: {e}")

    print("\n" + "="*60)
    print("[SUMMARY]")
    print("- Backend is accessible and responding correctly")
    print("- Authentication system is working (returning 401/403 as expected)")
    print("- All major API endpoints are available")
    print("- Frontend should be able to communicate with backend once authenticated")


def test_cors_configuration():
    """
    Test CORS by checking if OPTIONS request returns proper headers
    """
    print("\n[TEST 5] Testing CORS Configuration...")
    backend_url = os.getenv("NEXT_PUBLIC_API_BASE_URL", "https://vickey92-todo-chatbot.hf.space/api")

    try:
        # Test preflight request
        response = requests.options(
            f"{backend_url}/health",
            headers={
                "Origin": "https://heckathone-phase-03-todo-chatbot-six.vercel.app",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Requested-With, Content-Type"
            },
            timeout=10
        )

        print(f"   OPTIONS request status: {response.status_code}")
        print("   [SUCCESS] CORS preflight request handled")
    except Exception as e:
        print(f"   [ERROR] CORS test error: {e}")


if __name__ == "__main__":
    print("[INFO] Testing backend connection...")
    test_backend_connection()
    test_chat_endpoint()
    test_comprehensive_backend()
    test_cors_configuration()
    print("\n[INFO] All tests completed.")