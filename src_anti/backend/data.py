from typing import List, Dict, Any
import copy

class Repository:
    def __init__(self):
        self.reset()

    def reset(self):
        self.customers = [
            {"id": "C001", "name": "Alpha Manufacturing", "segment": "Enterprise", "region": "Seoul", "riskTier": "Low"},
            {"id": "C002", "name": "Beta Retail", "segment": "SMB", "region": "Busan", "riskTier": "Medium"},
            {"id": "C003", "name": "Gamma Electronics", "segment": "Enterprise", "region": "Incheon", "riskTier": "High"}
        ]

        self.products = [
            {"id": "P001", "name": "Industrial Sensor", "category": "Hardware"},
            {"id": "P002", "name": "Analytics License", "category": "Software"},
            {"id": "P003", "name": "Support Package", "category": "Service"}
        ]

        self.orders = [
            {"id": "O001", "customerId": "C001", "status": "Submitted", "amount": 3200, "productIds": ["P001", "P003"]},
            {"id": "O002", "customerId": "C002", "status": "Submitted", "amount": 8200, "productIds": ["P002"]},
            {"id": "O003", "customerId": "C003", "status": "Approved", "amount": 12000, "productIds": ["P001", "P002", "P003"]}
        ]

        self.documents = [
            {"id": "D001", "title": "Order Approval Policy (주문 승인 정책)", "text": "Orders below 5000 can be approved by the account manager. Orders equal to or above 5000 require finance manager approval. 주문 승인 기준: 5,000 미만은 계정 관리자 승인 가능."},
            {"id": "D002", "title": "Enterprise Customer Contract Policy (고객 계약 정책)", "text": "Enterprise customers require contract validation before fulfillment. Standard support terms apply unless a custom contract is registered. 엔터프라이즈 고객은 계약 검증이 필요합니다."},
            {"id": "D003", "title": "Risk Review Guideline (리스크 검토 지침)", "text": "Low risk customers can proceed through normal approval. Medium or high risk customers require additional review. 리스크 등급이 낮음(Low)인 경우 정상 승인 프로세스를 따릅니다."}
        ]
        
        self.audit_events = []

    def get_customers(self):
        return self.customers

    def get_customer(self, customer_id: str):
        return next((c for c in self.customers if c["id"] == customer_id), None)

    def get_orders(self):
        return self.orders

    def get_order(self, order_id: str):
        return next((o for o in self.orders if o["id"] == order_id), None)

    def get_products(self):
        return self.products

    def get_product(self, product_id: str):
        return next((p for p in self.products if p["id"] == product_id), None)

    def get_documents(self):
        return self.documents

    def update_order_status(self, order_id: str, status: str):
        order = self.get_order(order_id)
        if order:
            order["status"] = status
            return True
        return False

    def add_audit_event(self, event: Dict[str, Any]):
        self.audit_events.append(event)

    def get_audit_events(self):
        return self.audit_events

# Global instance for easy access, but can be replaced for testing
repo = Repository()
