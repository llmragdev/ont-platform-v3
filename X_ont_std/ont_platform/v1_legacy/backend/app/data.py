from __future__ import annotations

from copy import deepcopy


RAW_CUSTOMERS = {
    "C001": {
        "name": "Alpha Manufacturing",
        "segment": "Enterprise",
        "region": "Seoul",
        "risk_tier": "Low",
        "contract_terms": "Standard support terms, custom discount 7%",
        "owner": "kim.ops@example.com",
    },
    "C002": {
        "name": "Beta Retail",
        "segment": "SMB",
        "region": "Busan",
        "risk_tier": "Medium",
        "contract_terms": "Standard terms, finance review required over 5000",
        "owner": "finance.lead@example.com",
    },
    "C003": {
        "name": "Gamma Logistics",
        "segment": "Enterprise",
        "region": "Incheon",
        "risk_tier": "High",
        "contract_terms": "Restricted due to credit hold",
        "owner": "kim.ops@example.com",
    },
}

RAW_PRODUCTS = {
    "P001": {"name": "Industrial Sensor", "category": "Hardware", "unit_price": 270.0},
    "P002": {"name": "Analytics License", "category": "Software", "unit_price": 1200.0},
    "P003": {"name": "Support Package", "category": "Service", "unit_price": 500.0},
}

RAW_ORDERS = {
    "O001": {"customer_id": "C001", "order_date": "2026-04-01", "status": "Submitted"},
    "O002": {"customer_id": "C002", "order_date": "2026-04-03", "status": "Submitted"},
    "O003": {"customer_id": "C003", "order_date": "2026-04-05", "status": "Review"},
}

RAW_ORDER_ITEMS = {
    "OI001": {"order_id": "O001", "product_id": "P001", "quantity": 10},
    "OI002": {"order_id": "O001", "product_id": "P003", "quantity": 1},
    "OI003": {"order_id": "O002", "product_id": "P002", "quantity": 6},
    "OI004": {"order_id": "O002", "product_id": "P003", "quantity": 2},
    "OI005": {"order_id": "O003", "product_id": "P001", "quantity": 12},
    "OI006": {"order_id": "O003", "product_id": "P002", "quantity": 5},
}

DOCUMENTS = [
    {
        "id": "D001",
        "title": "Order Approval Policy",
        "visibility": ["Viewer", "Analyst", "AccountManager", "FinanceManager", "Admin"],
        "related_objects": ["Order", "Customer"],
        "text": (
            "Orders below 5000 can be approved by the account manager. "
            "Orders equal to or above 5000 require finance manager approval."
        ),
    },
    {
        "id": "D002",
        "title": "Enterprise Customer Contract Policy",
        "visibility": ["Analyst", "AccountManager", "FinanceManager", "Admin"],
        "related_objects": ["Customer"],
        "text": (
            "Enterprise customers require contract validation before fulfillment. "
            "Standard support terms apply unless a custom contract is registered."
        ),
    },
    {
        "id": "D003",
        "title": "Risk Review Guideline",
        "visibility": ["Analyst", "AccountManager", "FinanceManager", "Admin"],
        "related_objects": ["Customer", "Order"],
        "text": (
            "Low risk customers can proceed through normal approval. "
            "Medium or high risk customers require additional review."
        ),
    },
    {
        "id": "D004",
        "title": "Custom Pricing Agreement",
        "visibility": ["FinanceManager", "Admin"],
        "related_objects": ["Customer", "Order"],
        "text": "Custom pricing agreements can expose discount terms and require finance review.",
    },
]

USERS = {
    "analyst": {
        "id": "U001",
        "name": "Kim Ops",
        "email": "kim.ops@example.com",
        "role": "AccountManager",
        "regions": ["Seoul", "Incheon"],
        # 교육용 평문 비밀번호 → AppContext 초기화 시 해시로 변환됨
        "password": "analyst",
    },
    "finance": {
        "id": "U002",
        "name": "Finance Lead",
        "email": "finance.lead@example.com",
        "role": "FinanceManager",
        "regions": ["Seoul", "Busan", "Incheon"],
        "password": "finance",
    },
    "viewer": {
        "id": "U003",
        "name": "Read Only",
        "email": "viewer@example.com",
        "role": "Viewer",
        "regions": ["Seoul"],
        "password": "viewer",
    },
    "admin": {
        "id": "U004",
        "name": "System Admin",
        "email": "admin@example.com",
        "role": "Admin",
        "regions": ["Seoul", "Busan", "Incheon"],
        "password": "admin",
    },
}


def fresh_raw_data() -> dict:
    return {
        "customers": deepcopy(RAW_CUSTOMERS),
        "products": deepcopy(RAW_PRODUCTS),
        "orders": deepcopy(RAW_ORDERS),
        "order_items": deepcopy(RAW_ORDER_ITEMS),
        "documents": deepcopy(DOCUMENTS),
        "users": deepcopy(USERS),
    }
