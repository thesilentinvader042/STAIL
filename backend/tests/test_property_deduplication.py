"""
tests/test_property_deduplication.py

Property-based test for location deduplication bug.

This test demonstrates the location deduplication bug in the create_property() endpoint.
When two properties are created with identical address components, they should link to the
SAME Location record. Currently, the bug creates DIFFERENT Location records.

Expected behavior on UNFIXED code:
  - Test FAILS: property_1.location_id != property_2.location_id (bug confirmed)

Expected behavior on FIXED code:
  - Test PASSES: property_1.location_id == property_2.location_id (bug fixed)

**Validates: Requirements 2.1, 2.2, 2.3**
"""
import uuid
from typing import Annotated

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st
from sqlalchemy.orm import Session

from app.db.models.models import Location, Property


# ── Strategy Definitions ──────────────────────────────────────────────────────

def location_create_payload_strategy() -> st.SearchStrategy:
    """
    Generate PropertyCreate payloads with location data.
    
    This strategy creates realistic address data that can be used to test
    location deduplication. The strategy constrains to valid inputs.
    """
    return st.fixed_dictionaries({
        "title": st.just("Test Property"),
        "property_type": st.just("RESIDENTIAL"),
        "transaction_type": st.just("SALE"),
        "asking_price": st.just(5000000.0),
        "location": st.fixed_dictionaries({
            "address_line_1": st.just("123 MG Road"),
            "address_line_2": st.none(),
            "locality": st.just("Bangalore"),
            "city": st.just("Bangalore"),
            "state_code": st.just("KA"),
            "pin_code": st.just("560001"),
        }),
    })


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def test_user(client: TestClient):
    """Create and return a test user with auth headers."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "dedup_test@example.com",
            "full_name": "Dedup Test User",
            "password": "TestPassword123",
        },
    )
    assert r.status_code == 201
    
    login_r = client.post(
        "/api/v1/auth/login",
        json={"email": "dedup_test@example.com", "password": "TestPassword123"},
    )
    assert login_r.status_code == 200
    token = login_r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    user_data = r.json()
    return user_data, headers


# ── Bug Condition Exploration Tests ───────────────────────────────────────────

class TestLocationDeduplicationBugCondition:
    """
    Property 1: Bug Condition - Location Deduplication on Create
    
    Demonstrates the location deduplication bug where two properties with
    identical addresses should link to the SAME Location record, but currently
    link to DIFFERENT Location records (the bug).
    
    **Expected outcome on unfixed code**: TEST FAILS
    Counterexample: property_1.location_id (UUID: a1b2...) != property_2.location_id (UUID: e5f6...)
    
    **Expected outcome on fixed code**: TEST PASSES
    Both properties link to same Location UUID
    """

    def test_identical_addresses_should_share_location_id(
        self, client: TestClient, test_user, db: Session
    ):
        """
        Core bug test: Two properties with identical address components
        should link to the SAME Location record UUID.
        
        Current (buggy) behavior: Creates two different Location records
        Expected (fixed) behavior: Reuses the same Location record
        """
        _, headers = test_user

        # Property 1: Create with specific address
        prop1_payload = {
            "title": "Property 1 - Same Address",
            "property_type": "RESIDENTIAL",
            "transaction_type": "SALE",
            "asking_price": 5000000.0,
            "location": {
                "address_line_1": "123 MG Road",
                "address_line_2": None,
                "locality": "Bangalore",
                "city": "Bangalore",
                "state_code": "KA",
                "pin_code": "560001",
            },
        }

        r1 = client.post("/api/v1/properties/", json=prop1_payload, headers=headers)
        assert r1.status_code == 201
        prop1_data = r1.json()
        prop1_id = uuid.UUID(prop1_data["id"])
        prop1_location_id = uuid.UUID(prop1_data["location"]["id"])

        # Property 2: Create with identical address components
        prop2_payload = {
            "title": "Property 2 - Same Address",
            "property_type": "RESIDENTIAL",
            "transaction_type": "SALE",
            "asking_price": 4500000.0,
            "location": {
                "address_line_1": "123 MG Road",  # Identical
                "address_line_2": None,           # Identical
                "locality": "Bangalore",          # Identical
                "city": "Bangalore",              # Identical
                "state_code": "KA",               # Identical
                "pin_code": "560001",             # Identical
            },
        }

        r2 = client.post("/api/v1/properties/", json=prop2_payload, headers=headers)
        assert r2.status_code == 201
        prop2_data = r2.json()
        prop2_id = uuid.UUID(prop2_data["id"])
        prop2_location_id = uuid.UUID(prop2_data["location"]["id"])

        # Query properties from database to verify relationship
        prop1_from_db = db.query(Property).filter(
            Property.property_id == prop1_id
        ).first()
        assert prop1_from_db is not None
        assert prop1_from_db.location_id == prop1_location_id

        prop2_from_db = db.query(Property).filter(
            Property.property_id == prop2_id
        ).first()
        assert prop2_from_db is not None
        assert prop2_from_db.location_id == prop2_location_id

        # CRITICAL ASSERTION: Both properties should link to SAME Location
        # BUG: This fails because prop1_location_id != prop2_location_id
        # FIXED: This passes because both link to same location_id
        assert prop1_from_db.location_id == prop2_from_db.location_id, (
            f"BUG CONFIRMED: property_1.location_id ({prop1_from_db.location_id}) "
            f"!= property_2.location_id ({prop2_from_db.location_id}). "
            f"Expected both to link to the same Location record when addresses are identical."
        )

        # Additional verification: Location record should exist and be retrievable
        location = db.query(Location).filter(
            Location.location_id == prop1_from_db.location_id
        ).first()
        assert location is not None, "Location record should exist"
        assert location.address_line_1 == "123 MG Road"
        assert location.city == "Bangalore"
        assert location.state_code == "KA"

    def test_identical_addresses_with_address_line_2(
        self, client: TestClient, test_user, db: Session
    ):
        """
        Test location deduplication with optional address_line_2 field.
        
        When address_line_2 is provided, two properties with identical
        address_line_2 should still share the same Location.
        """
        _, headers = test_user

        address_line_2 = "Apt 505"

        # Property 1
        prop1_payload = {
            "title": "Apartment with Line 2 - 1",
            "property_type": "RESIDENTIAL",
            "transaction_type": "SALE",
            "asking_price": 6000000.0,
            "location": {
                "address_line_1": "456 Church Street",
                "address_line_2": address_line_2,
                "locality": "Indiranagar",
                "city": "Bangalore",
                "state_code": "KA",
                "pin_code": "560038",
            },
        }

        r1 = client.post("/api/v1/properties/", json=prop1_payload, headers=headers)
        assert r1.status_code == 201
        prop1_id = uuid.UUID(r1.json()["id"])
        prop1_location_id = uuid.UUID(r1.json()["location"]["id"])

        # Property 2: Identical address including address_line_2
        prop2_payload = {
            "title": "Apartment with Line 2 - 2",
            "property_type": "RESIDENTIAL",
            "transaction_type": "SALE",
            "asking_price": 5800000.0,
            "location": {
                "address_line_1": "456 Church Street",     # Identical
                "address_line_2": address_line_2,          # Identical
                "locality": "Indiranagar",                 # Identical
                "city": "Bangalore",                       # Identical
                "state_code": "KA",                        # Identical
                "pin_code": "560038",                      # Identical
            },
        }

        r2 = client.post("/api/v1/properties/", json=prop2_payload, headers=headers)
        assert r2.status_code == 201
        prop2_id = uuid.UUID(r2.json()["id"])
        prop2_location_id = uuid.UUID(r2.json()["location"]["id"])

        # Query from database
        prop1_from_db = db.query(Property).filter(
            Property.property_id == prop1_id
        ).first()
        prop2_from_db = db.query(Property).filter(
            Property.property_id == prop2_id
        ).first()

        # Both should link to same Location
        assert prop1_from_db.location_id == prop2_from_db.location_id, (
            f"BUG: Properties with identical addresses (including address_line_2) "
            f"should link to same Location. "
            f"Got {prop1_from_db.location_id} vs {prop2_from_db.location_id}"
        )

    def test_different_addresses_create_different_locations(
        self, client: TestClient, test_user, db: Session
    ):
        """
        Sanity check: Different addresses should still create different Locations.
        This test should PASS on both unfixed and fixed code.
        """
        _, headers = test_user

        # Property 1: Address A
        prop1_payload = {
            "title": "Property at Address A",
            "property_type": "RESIDENTIAL",
            "transaction_type": "SALE",
            "asking_price": 5000000.0,
            "location": {
                "address_line_1": "100 Address A",
                "address_line_2": None,
                "locality": "Locality A",
                "city": "City A",
                "state_code": "AA",
                "pin_code": "000001",
            },
        }

        r1 = client.post("/api/v1/properties/", json=prop1_payload, headers=headers)
        assert r1.status_code == 201
        prop1_id = uuid.UUID(r1.json()["id"])
        prop1_location_id = uuid.UUID(r1.json()["location"]["id"])

        # Property 2: Address B (different)
        prop2_payload = {
            "title": "Property at Address B",
            "property_type": "RESIDENTIAL",
            "transaction_type": "SALE",
            "asking_price": 5000000.0,
            "location": {
                "address_line_1": "200 Address B",  # DIFFERENT
                "address_line_2": None,
                "locality": "Locality B",           # DIFFERENT
                "city": "City B",                   # DIFFERENT
                "state_code": "BB",                 # DIFFERENT
                "pin_code": "000002",               # DIFFERENT
            },
        }

        r2 = client.post("/api/v1/properties/", json=prop2_payload, headers=headers)
        assert r2.status_code == 201
        prop2_id = uuid.UUID(r2.json()["id"])
        prop2_location_id = uuid.UUID(r2.json()["location"]["id"])

        # Query from database
        prop1_from_db = db.query(Property).filter(
            Property.property_id == prop1_id
        ).first()
        prop2_from_db = db.query(Property).filter(
            Property.property_id == prop2_id
        ).first()

        # Different addresses should have different Location IDs
        assert prop1_from_db.location_id != prop2_from_db.location_id, (
            f"Different addresses should create different Locations. "
            f"Got same location_id for different addresses."
        )

    def test_multiple_properties_same_location_consolidation(
        self, client: TestClient, test_user, db: Session
    ):
        """
        Test that when multiple properties (3+) are created with identical addresses,
        all should link to the same Location record.
        """
        _, headers = test_user

        address = {
            "address_line_1": "789 Main Street",
            "address_line_2": None,
            "locality": "Downtown",
            "city": "Metropolis",
            "state_code": "MP",
            "pin_code": "100001",
        }

        location_ids = []

        # Create 3 properties with identical address
        for i in range(3):
            payload = {
                "title": f"Property {i+1} - Same Address",
                "property_type": "RESIDENTIAL",
                "transaction_type": "SALE",
                "asking_price": 5000000.0 + (i * 100000),
                "location": address.copy(),
            }

            r = client.post("/api/v1/properties/", json=payload, headers=headers)
            assert r.status_code == 201
            location_id = uuid.UUID(r.json()["location"]["id"])
            location_ids.append(location_id)

        # All properties should have the same location_id
        # BUG: This fails because location_ids will be [uuid1, uuid2, uuid3]
        # FIXED: This passes because location_ids will be [uuid1, uuid1, uuid1]
        assert all(lid == location_ids[0] for lid in location_ids), (
            f"BUG: All properties with identical addresses should link to same Location. "
            f"Got location_ids: {location_ids}"
        )

        # Verify only 1 Location record exists for this address
        locations = db.query(Location).filter(
            Location.address_line_1 == "789 Main Street",
            Location.city == "Metropolis",
        ).all()
        assert len(locations) == 1, (
            f"Expected 1 Location record for the address, but found {len(locations)}. "
            f"This indicates the bug created duplicate Locations."
        )
