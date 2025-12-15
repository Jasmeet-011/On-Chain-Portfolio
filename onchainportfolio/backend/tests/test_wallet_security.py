# backend/tests/test_wallet_security.py
"""
Security Tests for Wallet System

Tests user isolation, authentication, and wallet operations
to ensure User A cannot access User B's data.

Run with: pytest tests/test_wallet_security.py -v
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient

# Now import app
from app.main import app

client = TestClient(app)


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def user_a():
    """Create User A and return credentials"""
    response = client.post("/auth/signup", json={
        "name": "Alice",
        "email": f"alice_{pytest.timestamp}@test.com",
        "password": "password123"
    })
    assert response.status_code == 201, f"Signup failed: {response.text}"
    data = response.json()
    return {
        "token": data["access_token"],
        "user_id": data["user"]["id"],
        "email": f"alice_{pytest.timestamp}@test.com"
    }


@pytest.fixture
def user_b():
    """Create User B and return credentials"""
    response = client.post("/auth/signup", json={
        "name": "Bob",
        "email": f"bob_{pytest.timestamp}@test.com",
        "password": "password123"
    })
    assert response.status_code == 201, f"Signup failed: {response.text}"
    data = response.json()
    return {
        "token": data["access_token"],
        "user_id": data["user"]["id"],
        "email": f"bob_{pytest.timestamp}@test.com"
    }


@pytest.fixture(autouse=True)
def setup_timestamp():
    """Generate unique timestamp for test emails"""
    import time
    pytest.timestamp = int(time.time())


# ============================================================
# Test 1: Authentication & Token Verification
# ============================================================

def test_signup_creates_user():
    """Test that signup creates a new user"""
    import time
    email = f"test_{int(time.time())}@test.com"
    
    response = client.post("/auth/signup", json={
        "name": "Test User",
        "email": email,
        "password": "password123"
    })
    
    assert response.status_code == 201, f"Signup failed: {response.text}"
    data = response.json()
    
    # Check response structure
    assert "user" in data
    assert "access_token" in data
    assert data["user"]["email"] == email
    print(f"✅ User created: {data['user']['id']}")


def test_login_returns_token():
    """Test that login returns valid token"""
    import time
    email = f"login_{int(time.time())}@test.com"
    
    # Signup first
    client.post("/auth/signup", json={
        "name": "Login Test",
        "email": email,
        "password": "password123"
    })
    
    # Then login
    response = client.post("/auth/login", json={
        "email": email,
        "password": "password123"
    })
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    print(f"✅ Login successful, token received")


def test_invalid_token_rejected():
    """Test that invalid tokens are rejected"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_123"}
    )
    
    assert response.status_code == 401
    print(f"✅ Invalid token correctly rejected")


# ============================================================
# Test 2: User Isolation - Wallet Listing
# ============================================================

def test_users_cannot_see_each_others_wallets(user_a, user_b):
    """
    CRITICAL TEST: Verify User A cannot see User B's wallets
    
    Steps:
    1. User A adds wallet A1
    2. User B adds wallet B1
    3. User A fetches wallets → should only see A1
    4. User B fetches wallets → should only see B1
    """
    
    # User A adds wallet
    wallet_a = client.post(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_a['token']}"},
        json={
            "address": "0x" + "a" * 64,
            "label": "Alice Wallet",
            "type": "manual",
            "is_primary": True
        }
    )
    assert wallet_a.status_code == 201, f"Failed to add wallet A: {wallet_a.text}"
    wallet_a_data = wallet_a.json()
    print(f"✅ User A added wallet: {wallet_a_data['address'][:10]}...")
    
    # User B adds wallet
    wallet_b = client.post(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_b['token']}"},
        json={
            "address": "0x" + "b" * 64,
            "label": "Bob Wallet",
            "type": "manual",
            "is_primary": True
        }
    )
    assert wallet_b.status_code == 201, f"Failed to add wallet B: {wallet_b.text}"
    wallet_b_data = wallet_b.json()
    print(f"✅ User B added wallet: {wallet_b_data['address'][:10]}...")
    
    # User A fetches wallets
    a_wallets = client.get(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    assert a_wallets.status_code == 200, f"Failed to get wallets A: {a_wallets.text}"
    a_wallet_list = a_wallets.json()["wallets"]
    
    # User B fetches wallets
    b_wallets = client.get(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_b['token']}"}
    )
    assert b_wallets.status_code == 200, f"Failed to get wallets B: {b_wallets.text}"
    b_wallet_list = b_wallets.json()["wallets"]
    
    # CRITICAL ASSERTIONS
    assert len(a_wallet_list) == 1, f"❌ User A sees {len(a_wallet_list)} wallets, expected 1"
    assert len(b_wallet_list) == 1, f"❌ User B sees {len(b_wallet_list)} wallets, expected 1"
    
    assert a_wallet_list[0]["address"] == "0x" + "a" * 64, "❌ User A sees wrong wallet"
    assert b_wallet_list[0]["address"] == "0x" + "b" * 64, "❌ User B sees wrong wallet"
    
    # Verify User A does NOT see User B's wallet
    a_addresses = [w["address"] for w in a_wallet_list]
    assert "0x" + "b" * 64 not in a_addresses, "❌ SECURITY BREACH: User A can see User B's wallet!"
    
    # Verify User B does NOT see User A's wallet
    b_addresses = [w["address"] for w in b_wallet_list]
    assert "0x" + "a" * 64 not in b_addresses, "❌ SECURITY BREACH: User B can see User A's wallet!"
    
    print(f"✅ PASSED: User isolation verified - users can only see their own wallets")


# ============================================================
# Test 3: User Isolation - Wallet Deletion
# ============================================================

def test_user_cannot_delete_other_users_wallet(user_a, user_b):
    """
    CRITICAL TEST: Verify User A cannot delete User B's wallet
    
    Steps:
    1. User B adds wallet B1
    2. User A tries to delete wallet B1
    3. Should fail (403 or 404)
    4. Verify wallet B1 still exists for User B
    """
    
    # User B adds wallet
    wallet_b = client.post(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_b['token']}"},
        json={
            "address": "0x" + "b" * 64,
            "label": "Bob Wallet",
            "type": "manual",
            "is_primary": True
        }
    )
    assert wallet_b.status_code == 201
    wallet_b_address = wallet_b.json()["address"]
    print(f"✅ User B created wallet: {wallet_b_address[:10]}...")
    
    # User A tries to delete User B's wallet
    delete_response = client.delete(
        f"/v1/wallets/{wallet_b_address}",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    
    # Should fail (either 400 bad request or 404 not found)
    # 404 is acceptable because wallet "doesn't exist" for User A
    # 400 is acceptable because deletion "failed"
    assert delete_response.status_code in [400, 404], \
        f"❌ Expected 400/404, got {delete_response.status_code}"
    
    print(f"✅ User A's delete attempt correctly rejected: {delete_response.status_code}")
    
    # Verify User B's wallet still exists
    b_wallets = client.get(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_b['token']}"}
    )
    assert b_wallets.status_code == 200
    b_wallet_list = b_wallets.json()["wallets"]
    
    assert len(b_wallet_list) == 1, "❌ User B's wallet was deleted!"
    assert b_wallet_list[0]["address"] == wallet_b_address, "❌ Wrong wallet in User B's list"
    
    print(f"✅ PASSED: User B's wallet still exists - User A could not delete it")


# ============================================================
# Test 4: User Isolation - Wallet Updates
# ============================================================

def test_user_cannot_update_other_users_wallet(user_a, user_b):
    """
    CRITICAL TEST: Verify User A cannot update User B's wallet label
    """
    
    # User B adds wallet
    wallet_b = client.post(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_b['token']}"},
        json={
            "address": "0x" + "b" * 64,
            "label": "Bob Original",
            "type": "manual",
            "is_primary": True
        }
    )
    assert wallet_b.status_code == 201
    wallet_b_address = wallet_b.json()["address"]
    print(f"✅ User B created wallet: {wallet_b_address[:10]}...")
    
    # User A tries to update User B's wallet
    update_response = client.patch(
        f"/v1/wallets/{wallet_b_address}/label",
        headers={"Authorization": f"Bearer {user_a['token']}"},
        json={"label": "Hacked by User A"}
    )
    
    # Should fail
    assert update_response.status_code in [400, 404], \
        f"❌ Expected 400/404, got {update_response.status_code}"
    
    print(f"✅ User A's update attempt correctly rejected: {update_response.status_code}")
    
    # Verify User B's wallet label unchanged
    b_wallets = client.get(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_b['token']}"}
    )
    b_wallet_list = b_wallets.json()["wallets"]
    
    assert b_wallet_list[0]["label"] == "Bob Original", "❌ Wallet label was changed!"
    
    print(f"✅ PASSED: User B's wallet label unchanged - User A could not modify it")


# ============================================================
# Test 5: Wallet Deletion - Can Delete Last Wallet
# ============================================================

def test_can_delete_last_wallet(user_a):
    """
    Test that user CAN delete their last remaining wallet
    
    This tests the bug fix: previously users were blocked from
    deleting their last wallet. Now they should be able to.
    """
    
    # User A adds 3 wallets
    for i in range(3):
        response = client.post(
            "/v1/wallets",
            headers={"Authorization": f"Bearer {user_a['token']}"},
            json={
                "address": "0x" + str(i) * 64,
                "label": f"Wallet {i+1}",
                "type": "manual",
                "is_primary": i == 0
            }
        )
        assert response.status_code == 201
    
    print(f"✅ Created 3 wallets for User A")
    
    # Verify 3 wallets exist
    wallets = client.get(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    wallet_list = wallets.json()["wallets"]
    assert len(wallet_list) == 3
    
    # Delete first wallet
    delete1 = client.delete(
        f"/v1/wallets/{'0x' + '0' * 64}",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    assert delete1.status_code == 204
    print(f"✅ Deleted wallet 1")
    
    # Delete second wallet
    delete2 = client.delete(
        f"/v1/wallets/{'0x' + '1' * 64}",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    assert delete2.status_code == 204
    print(f"✅ Deleted wallet 2")
    
    # Verify only 1 wallet remains
    wallets = client.get(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    wallet_list = wallets.json()["wallets"]
    assert len(wallet_list) == 1
    
    # NOW DELETE THE LAST WALLET (this should succeed)
    delete_last = client.delete(
        f"/v1/wallets/{'0x' + '2' * 64}",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    assert delete_last.status_code == 204, \
        f"❌ Could not delete last wallet! Status: {delete_last.status_code}"
    
    print(f"✅ Deleted last wallet (this should be allowed)")
    
    # Verify user now has 0 wallets
    wallets = client.get(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    wallet_list = wallets.json()["wallets"]
    assert len(wallet_list) == 0, "❌ Wallet still exists after deletion"
    
    print(f"✅ PASSED: User can delete all wallets including the last one")


# ============================================================
# Test 6: Chat Isolation & Scope
# ============================================================

def test_chat_only_uses_own_wallets(user_a, user_b):
    """
    CRITICAL TEST: Verify chat endpoint only uses authenticated user's wallets
    
    Steps:
    1. User A adds wallet A1
    2. User B adds wallet B1
    3. User A asks chat with scope="all"
    4. Response should only include wallet A1 (NOT B1)
    """
    
    # User A adds wallet
    client.post(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_a['token']}"},
        json={
            "address": "0x" + "a" * 64,
            "label": "Alice Wallet",
            "type": "manual",
            "is_primary": True
        }
    )
    
    # User B adds wallet
    client.post(
        "/v1/wallets",
        headers={"Authorization": f"Bearer {user_b['token']}"},
        json={
            "address": "0x" + "b" * 64,
            "label": "Bob Wallet",
            "type": "manual",
            "is_primary": True
        }
    )
    
    print(f"✅ Created wallets for both users")
    
    # User A asks chat with scope="all"
    chat_response = client.post(
        "/v1/chat",
        headers={"Authorization": f"Bearer {user_a['token']}"},
        json={
            "question": "What tokens do I hold?",
            "scope": "all"
        }
    )
    
    # Should succeed
    assert chat_response.status_code == 200, \
        f"❌ Chat failed: {chat_response.status_code} - {chat_response.text}"
    
    chat_data = chat_response.json()
    
    print(f"✅ Chat response received")
    
    # Check wallet_results
    assert "wallet_results" in chat_data, "❌ No wallet_results in response"
    wallet_results = chat_data["wallet_results"]
    
    # User A should only see 1 wallet (their own)
    assert len(wallet_results) == 1, \
        f"❌ User A sees {len(wallet_results)} wallets in chat, expected 1"
    
    # Verify it's User A's wallet
    assert wallet_results[0]["address"] == "0x" + "a" * 64, \
        "❌ Chat returned wrong wallet address"
    
    assert wallet_results[0]["label"] == "Alice Wallet", \
        "❌ Chat returned wrong wallet label"
    
    # Verify User B's wallet is NOT in results
    result_addresses = [r["address"] for r in wallet_results]
    assert "0x" + "b" * 64 not in result_addresses, \
        "❌ SECURITY BREACH: User A's chat includes User B's wallet!"
    
    print(f"✅ PASSED: Chat only includes User A's wallets")


def test_chat_scope_all_aggregates_multiple_wallets(user_a):
    """
    Test that chat with scope="all" aggregates data from all user's wallets
    """
    
    # User A adds 3 wallets
    for i in range(3):
        client.post(
            "/v1/wallets",
            headers={"Authorization": f"Bearer {user_a['token']}"},
            json={
                "address": "0x" + str(i) * 64,
                "label": f"Wallet {i+1}",
                "type": "manual",
                "is_primary": i == 0
            }
        )
    
    print(f"✅ Created 3 wallets for User A")
    
    # Ask chat with scope="all"
    chat_response = client.post(
        "/v1/chat",
        headers={"Authorization": f"Bearer {user_a['token']}"},
        json={
            "question": "What's my total portfolio?",
            "scope": "all"
        }
    )
    
    assert chat_response.status_code == 200, f"Chat failed: {chat_response.text}"
    chat_data = chat_response.json()
    
    # Check portfolio summary
    assert "portfolio" in chat_data
    portfolio = chat_data["portfolio"]
    
    # Should show 3 wallets
    assert portfolio["total_wallets"] == 3, \
        f"❌ Portfolio shows {portfolio['total_wallets']} wallets, expected 3"
    
    # Check wallet_results
    wallet_results = chat_data["wallet_results"]
    assert len(wallet_results) == 3, \
        f"❌ Only {len(wallet_results)} wallets analyzed, expected 3"
    
    print(f"✅ PASSED: Chat with scope='all' analyzes all 3 wallets")


def test_chat_scope_primary_only_uses_primary(user_a):
    """
    Test that chat with scope="primary" only uses primary wallet
    """
    
    # User A adds 3 wallets
    for i in range(3):
        client.post(
            "/v1/wallets",
            headers={"Authorization": f"Bearer {user_a['token']}"},
            json={
                "address": "0x" + str(i) * 64,
                "label": f"Wallet {i+1}",
                "type": "manual",
                "is_primary": i == 0  # First wallet is primary
            }
        )
    
    print(f"✅ Created 3 wallets (first is primary)")
    
    # Ask chat with scope="primary"
    chat_response = client.post(
        "/v1/chat",
        headers={"Authorization": f"Bearer {user_a['token']}"},
        json={
            "question": "What's my portfolio?",
            "scope": "primary"
        }
    )
    
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    
    # Should only analyze 1 wallet
    wallet_results = chat_data["wallet_results"]
    assert len(wallet_results) == 1, \
        f"❌ {len(wallet_results)} wallets analyzed, expected 1"
    
    # Should be the primary wallet
    assert wallet_results[0]["address"] == "0x" + "0" * 64, \
        "❌ Wrong wallet analyzed (should be primary)"
    
    print(f"✅ PASSED: Chat with scope='primary' only analyzes primary wallet")


# ============================================================
# Test Summary
# ============================================================

def test_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("🧪 SECURITY TEST SUITE COMPLETE")
    print("="*60)
    print("\n✅ If all tests passed, your security is EXCELLENT!")
    print("❌ If any tests failed, there are security vulnerabilities!")
    print("\nKey Tests:")
    print("  1. ✅ User isolation (wallet listing)")
    print("  2. ✅ User isolation (wallet deletion)")
    print("  3. ✅ User isolation (wallet updates)")
    print("  4. ✅ Can delete last wallet")
    print("  5. ✅ Chat isolation")
    print("  6. ✅ Chat scope (all/primary)")
    print("\n" + "="*60)