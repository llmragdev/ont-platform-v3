export type RiskTier = "Low" | "Medium" | "High";
export type OrderStatus = "Submitted" | "Approved" | "Rejected" | "Fulfilled" | "Closed";

export type Customer = {
  id: string;
  name: string;
  segment: string;
  region: string;
  riskTier: RiskTier;
};

export type Product = {
  id: string;
  name: string;
  category: string;
};

export type Order = {
  id: string;
  customerId: string;
  status: OrderStatus;
  amount: number;
  productIds: string[];
};

export type KnowledgeDocument = {
  id: string;
  title: string;
  text: string;
  score?: number;
};

export type WorkflowEvent = {
  id: string;
  objectId: string;
  action: string;
  fromStatus: string;
  toStatus: string;
  actor: string;
  occurredAt: string;
};
