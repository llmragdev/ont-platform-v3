'use client';

// Author: Claude
// Date: 2026-06-20
// Purpose: 온톨로지 엔티티 관계 그래프 시각화 (vis-network 통합)

import React, { useEffect, useRef } from 'react';

interface OntologyEntity {
  entity_name?: string;
  entity?: string;
  description?: string;
  relation?: string;
  target?: string;
  confidence?: number;
}

interface OntologyGraphProps {
  entities: OntologyEntity[];
}

/**
 * OntologyGraph Component
 *
 * vis-network 라이브러리를 사용하여 엔티티 간의 관계를 그래프로 시각화합니다.
 * 현재는 간단한 SVG 기반 구현이며, 나중에 vis-network로 교체 가능합니다.
 */
export const OntologyGraph: React.FC<OntologyGraphProps> = ({ entities }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!entities || entities.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Canvas 크기 설정
    const container = containerRef.current;
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = 300;
    }

    // 백그라운드
    ctx.fillStyle = '#f9fafb';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 엔티티 추출 (중복 제거)
    const uniqueNodes = new Set<string>();
    entities.forEach((e) => {
      const name = e.entity_name || e.entity || 'Unknown';
      const target = e.target || '';
      uniqueNodes.add(name);
      if (target) uniqueNodes.add(target);
    });

    const nodes = Array.from(uniqueNodes).map((name, idx) => ({
      id: idx,
      label: name,
      x: 50 + (idx % 3) * (canvas.width / 3) + 20,
      y: 50 + Math.floor(idx / 3) * 100,
    }));

    const nodeMap = new Map(nodes.map(n => [n.label, n]));

    // 엣지 그리기
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;

    entities.forEach((entity) => {
      const fromName = entity.entity_name || entity.entity || '';
      const toName = entity.target || '';
      const from = nodeMap.get(fromName);
      const to = nodeMap.get(toName);

      if (from && to) {
        // 화살표 그리기
        const headlen = 15;
        const angle = Math.atan2(to.y - from.y, to.x - from.x);

        // 선
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x - Math.cos(angle) * 35, to.y - Math.sin(angle) * 35);
        ctx.stroke();

        // 화살표 헤드
        ctx.beginPath();
        ctx.moveTo(to.x - Math.cos(angle) * 35, to.y - Math.sin(angle) * 35);
        ctx.lineTo(
          to.x - Math.cos(angle) * 35 - Math.cos(angle - Math.PI / 6) * headlen,
          to.y - Math.sin(angle) * 35 - Math.sin(angle - Math.PI / 6) * headlen
        );
        ctx.moveTo(to.x - Math.cos(angle) * 35, to.y - Math.sin(angle) * 35);
        ctx.lineTo(
          to.x - Math.cos(angle) * 35 - Math.cos(angle + Math.PI / 6) * headlen,
          to.y - Math.sin(angle) * 35 - Math.sin(angle + Math.PI / 6) * headlen
        );
        ctx.stroke();

        // 관계 레이블
        const labelX = (from.x + to.x) / 2;
        const labelY = (from.y + to.y) / 2 - 10;
        ctx.fillStyle = '#059669';
        ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(entity.relation || '', labelX, labelY);
      }
    });

    // 노드 원 그리기
    nodes.forEach((node) => {
      // 원
      ctx.fillStyle = '#10b981';
      ctx.beginPath();
      ctx.arc(node.x, node.y, 30, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = '#059669';
      ctx.lineWidth = 2;
      ctx.stroke();

      // 텍스트
      ctx.fillStyle = 'white';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      // 길이 제한 (최대 6글자)
      const label = node.label.length > 6 ? node.label.slice(0, 6) + '...' : node.label;
      ctx.fillText(label, node.x, node.y);
    });

  }, [entities]);

  if (!entities || entities.length === 0) {
    return (
      <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
        <p>온톨로지 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="w-full bg-white border-2 border-gray-200 rounded-lg overflow-hidden"
    >
      <canvas
        ref={canvasRef}
        className="w-full"
        style={{ display: 'block' }}
      />
      <p className="text-xs text-gray-500 p-2 text-center bg-gray-50">
        엔티티 관계 그래프 (원: 엔티티, 화살표: 관계)
      </p>
    </div>
  );
};
