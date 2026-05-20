"use client";
import type { Customer, Order } from "@/types/api";

function statusBadgeClass(status: string) {
  if (status === "Approved" || status === "Fulfilled" || status === "Closed") return "badge-low";
  if (status === "Rejected") return "badge-high";
  return "badge-medium";
}

function riskBadgeClass(tier: string) {
  if (tier === "Low") return "badge-low";
  if (tier === "Medium") return "badge-medium";
  if (tier === "High") return "badge-high";
  return "badge-neutral";
}

export function Explorer({
  customers,
  orders,
  onSelectOrder,
  selectedId,
}: {
  customers: Customer[];
  orders: Order[];
  onSelectOrder: (id: string) => void;
  selectedId: string | null;
}) {
  return (
    <div className="space-y-6">
      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">고객 (Customer)</h3>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>이름</th>
                <th>Segment</th>
                <th>Region</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((customer) => (
                <tr key={customer.id}>
                  <td>{customer.id}</td>
                  <td className="font-medium">{customer.name}</td>
                  <td>{customer.segment}</td>
                  <td>{customer.region}</td>
                  <td><span className={`badge ${riskBadgeClass(customer.risk_tier)}`}>{customer.risk_tier}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3 className="text-sm font-semibold">주문 (Order)</h3>
        </div>
        <div className="panel-body p-0">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr
                  key={order.id}
                  className={`clickable ${selectedId === order.id ? "active" : ""}`}
                  onClick={() => onSelectOrder(order.id)}
                >
                  <td className="font-semibold">{order.id}</td>
                  <td>{order.customer_id}</td>
                  <td>{order.order_date}</td>
                  <td>{order.amount.toLocaleString()}</td>
                  <td><span className={`badge ${statusBadgeClass(order.status)}`}>{order.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
