import type { Customer, KnowledgeDocument, Order, Product, WorkflowEvent } from "@/types/ontology";

export const customers: Customer[] = [
  {
    id: "C001",
    name: "Alpha Manufacturing",
    segment: "Enterprise",
    region: "Seoul",
    riskTier: "Low",
  },
  {
    id: "C002",
    name: "Beta Retail",
    segment: "SMB",
    region: "Busan",
    riskTier: "Medium",
  },
];

export const products: Product[] = [
  { id: "P001", name: "Industrial Sensor", category: "Hardware" },
  { id: "P002", name: "Analytics License", category: "Software" },
  { id: "P003", name: "Support Package", category: "Service" },
];

export const orders: Order[] = [
  {
    id: "O001",
    customerId: "C001",
    status: "Submitted",
    amount: 3200,
    productIds: ["P001", "P003"],
  },
  {
    id: "O002",
    customerId: "C002",
    status: "Submitted",
    amount: 8200,
    productIds: ["P002"],
  },
];

export const documents: KnowledgeDocument[] = [
  {
    id: "D001",
    title: "Order Approval Policy",
    text: "Orders below 5000 can be approved by the account manager. Orders equal to or above 5000 require finance manager approval.",
  },
  {
    id: "D002",
    title: "Enterprise Customer Contract Policy",
    text: "Enterprise customers require contract validation before fulfillment. Standard support terms apply unless a custom contract is registered.",
  },
  {
    id: "D003",
    title: "Risk Review Guideline",
    text: "Low risk customers can proceed through normal approval. Medium or high risk customers require additional review.",
  },
];

export const workflowEvents: WorkflowEvent[] = [
  {
    id: "E001",
    objectId: "O003",
    action: "ApproveOrder",
    fromStatus: "Submitted",
    toStatus: "Approved",
    actor: "manager@example.com",
    occurredAt: "2026-05-07T09:10:00",
  },
];
