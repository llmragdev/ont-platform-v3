import re
from typing import List, Tuple, Optional
from data import repo

class OntologyService:
    @staticmethod
    def detect_objects(text: str) -> List[str]:
        # Simple regex to detect Cxxx, Oxxx, Pxxx, Dxxx
        customer_ids = re.findall(r'C\d{3}', text)
        order_ids = re.findall(r'O\d{3}', text)
        product_ids = re.findall(r'P\d{3}', text)
        doc_ids = re.findall(r'D\d{3}', text)
        return list(set(customer_ids + order_ids + product_ids + doc_ids))

    @staticmethod
    def verify_relationship(customer_id: str, order_id: str) -> bool:
        order = repo.get_order(order_id)
        if order and order["customerId"] == customer_id:
            return True
        return False

    @staticmethod
    def get_order_context(order_id: str):
        order = repo.get_order(order_id)
        if not order:
            return None
        
        customer = repo.get_customer(order["customerId"])
        products = [repo.get_product(pid) for pid in order["productIds"]]
        
        return {
            "order": order,
            "customer": customer,
            "products": products
        }
