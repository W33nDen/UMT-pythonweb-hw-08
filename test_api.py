import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.auth import create_email_verification_token
from app.crud import verify_user

# Setup SQLite test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestContactsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def test_01_user_lifecycle(self):
        # 1. Signup user
        signup_data = {"email": "user1@example.com", "password": "securepassword"}
        response = self.client.post("/auth/signup", json=signup_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], "user1@example.com")
        self.assertFalse(data["is_verified"])

        # 2. Try to signup again (should get 409 Conflict)
        response = self.client.post("/auth/signup", json=signup_data)
        self.assertEqual(response.status_code, 409)

        # 3. Try to login before verifying email (should get 401 Unauthorized)
        response = self.client.post("/auth/login", json=signup_data)
        self.assertEqual(response.status_code, 401)
        self.assertIn("verify your email", response.json()["detail"])

        # 4. Generate verification token and verify user
        db = TestingSessionLocal()
        verify_user(db, "user1@example.com")
        db.close()

        # 5. Try to login again (should get 200 and access_token)
        response = self.client.post("/auth/login", json=signup_data)
        self.assertEqual(response.status_code, 200)
        token_data = response.json()
        self.assertIn("access_token", token_data)
        self.assertEqual(token_data["token_type"], "bearer")

        self.token = token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # 6. Check /users/me profile
        response = self.client.get("/users/me", headers=cls.headers if not hasattr(self, 'headers') else self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "user1@example.com")

    def test_02_contacts_scoping(self):
        # Let's signup a second user
        signup_data_2 = {"email": "user2@example.com", "password": "securepassword"}
        self.client.post("/auth/signup", json=signup_data_2)
        db = TestingSessionLocal()
        verify_user(db, "user2@example.com")
        db.close()

        # Login User 1
        login_response_1 = self.client.post("/auth/login", json={"email": "user1@example.com", "password": "securepassword"})
        token_1 = login_response_1.json()["access_token"]
        headers_1 = {"Authorization": f"Bearer {token_1}"}

        # Login User 2
        login_response_2 = self.client.post("/auth/login", json={"email": "user2@example.com", "password": "securepassword"})
        token_2 = login_response_2.json()["access_token"]
        headers_2 = {"Authorization": f"Bearer {token_2}"}

        # 1. Create a contact under User 1
        contact_data = {
            "first_name": "Ivan",
            "last_name": "Petrov",
            "email": "ivan.petrov@example.com",
            "phone": "+380509999999",
            "birthday": "1990-01-01",
            "additional_data": "Work colleague"
        }
        create_res = self.client.post("/contacts/", json=contact_data, headers=headers_1)
        self.assertEqual(create_res.status_code, 201)
        contact_id = create_res.json()["id"]

        # 2. Get contacts for User 1 (should find the contact)
        get_res_1 = self.client.get("/contacts/", headers=headers_1)
        self.assertEqual(get_res_1.status_code, 200)
        self.assertEqual(len(get_res_1.json()), 1)
        self.assertEqual(get_res_1.json()[0]["first_name"], "Ivan")

        # 3. Get contacts for User 2 (should be empty!)
        get_res_2 = self.client.get("/contacts/", headers=headers_2)
        self.assertEqual(get_res_2.status_code, 200)
        self.assertEqual(len(get_res_2.json()), 0)

        # 4. User 2 tries to retrieve User 1's contact directly (should get 404 Not Found)
        direct_res_2 = self.client.get(f"/contacts/{contact_id}", headers=headers_2)
        self.assertEqual(direct_res_2.status_code, 404)

        # 5. User 1 retrieves their contact directly (should succeed)
        direct_res_1 = self.client.get(f"/contacts/{contact_id}", headers=headers_1)
        self.assertEqual(direct_res_1.status_code, 200)
        self.assertEqual(direct_res_1.json()["first_name"], "Ivan")

        # 6. User 2 tries to update User 1's contact (should get 404 Not Found)
        update_data = {"first_name": "Ivan Modified"}
        update_res_2 = self.client.put(f"/contacts/{contact_id}", json=update_data, headers=headers_2)
        self.assertEqual(update_res_2.status_code, 404)

        # 7. User 1 updates their contact (should succeed)
        update_res_1 = self.client.put(f"/contacts/{contact_id}", json=update_data, headers=headers_1)
        self.assertEqual(update_res_1.status_code, 200)
        self.assertEqual(update_res_1.json()["first_name"], "Ivan Modified")

        # 8. User 2 tries to delete User 1's contact (should get 404 Not Found)
        delete_res_2 = self.client.delete(f"/contacts/{contact_id}", headers=headers_2)
        self.assertEqual(delete_res_2.status_code, 404)

        # 9. User 1 deletes their contact (should succeed)
        delete_res_1 = self.client.delete(f"/contacts/{contact_id}", headers=headers_1)
        self.assertEqual(delete_res_1.status_code, 200)

    def test_03_rate_limiting_and_cors(self):
        # 1. Login to get token
        login_response = self.client.post("/auth/login", json={"email": "user1@example.com", "password": "securepassword"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Trigger Rate Limiting on /users/me (limit is 10/minute)
        # Note: 1 request was already made in test_01_user_lifecycle, so we make 9 more to hit the limit.
        for i in range(9):
            response = self.client.get("/users/me", headers=headers)
            self.assertEqual(response.status_code, 200)

        # 11th request should trigger rate limit (429 Too Many Requests)
        response = self.client.get("/users/me", headers=headers)
        self.assertEqual(response.status_code, 429)

        # 3. Test CORS headers on simple OPTIONS request
        cors_headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        }
        response = self.client.options("/", headers=cors_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access-control-allow-origin", response.headers)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")


if __name__ == "__main__":
    unittest.main()
