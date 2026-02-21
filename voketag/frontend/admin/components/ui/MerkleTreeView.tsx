"use client";

import { useState } from "react";
import type { MerkleNode } from "@/lib/api-client";

interface MerkleTreeViewProps {
  tree: MerkleNode | null;
  merkleRoot: string | null;
  leavesCount: number;
  className?: string;
}

const MAX_LEAVES_FOR_FULL_TREE = 16;

function truncate(s: string, len = 8) {
  if (!s) return "";
  return s.length <= len ? s : `${s.slice(0, len)}…`;
}

function TreeNode({ node, depth = 0 }: { node: MerkleNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.left || node.right;
  const isLeaf = !node.left && !node.right;

  return (
    <div className="flex flex-col items-center">
      <button
        type="button"
        onClick={() => hasChildren && setExpanded((e) => !e)}
        className={`
          group relative rounded-lg border px-3 py-1.5 font-mono text-xs transition-colors
          ${isLeaf ? "border-emerald-600/50 bg-emerald-900/20 text-emerald-300" : "border-amber-600/50 bg-amber-900/20 text-amber-300"}
          hover:border-amber-500/70 hover:bg-amber-900/30
          ${hasChildren ? "cursor-pointer" : ""}
        `}
        title={node.hash}
      >
        <span className="font-semibold">{truncate(node.hash, 10)}</span>
        {node.product_id && (
          <span className="ml-1.5 text-[10px] text-[#94a3b8]" title={node.product_id}>
            ({truncate(node.product_id, 6)})
          </span>
        )}
        {hasChildren && (
          <span className="ml-1 text-[#64748b]">{expanded ? "▼" : "▶"}</span>
        )}
      </button>
      {hasChildren && expanded && (
        <div className="mt-2 flex gap-8">
          {node.left && (
            <div className="flex flex-col items-center">
              <div className="mb-1 h-3 w-px bg-[#334155]" />
              <TreeNode node={node.left} depth={depth + 1} />
            </div>
          )}
          {node.right && (
            <div className="flex flex-col items-center">
              <div className="mb-1 h-3 w-px bg-[#334155]" />
              <TreeNode node={node.right} depth={depth + 1} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function MerkleTreeView({ tree, merkleRoot, leavesCount, className = "" }: MerkleTreeViewProps) {
  if (!tree) {
    return (
      <div className={`rounded-lg border border-[#334155] bg-[#0f172a] p-6 text-center text-sm text-[#94a3b8] ${className}`}>
        Árvore Merkle indisponível
      </div>
    );
  }

  const showFullTree = leavesCount <= MAX_LEAVES_FOR_FULL_TREE;

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex flex-wrap items-center gap-4 text-sm">
        <span className="text-[#94a3b8]">Root:</span>
        <code className="rounded bg-[#0f172a] px-2 py-1 font-mono text-amber-300" title={merkleRoot ?? ""}>
          {merkleRoot ? truncate(merkleRoot, 16) : "-"}
        </code>
        <span className="text-[#64748b]">•</span>
        <span className="text-[#94a3b8]">{leavesCount} folhas</span>
      </div>
      {showFullTree ? (
        <div className="overflow-x-auto rounded-lg border border-[#334155] bg-[#0f172a] p-6">
          <div className="inline-block min-w-0">
            <TreeNode node={tree} />
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-[#334155] bg-[#0f172a] p-6">
          <p className="text-sm text-[#94a3b8]">
            Árvore com {leavesCount} folhas — visualização simplificada (root acima)
          </p>
          <div className="mt-3 rounded border border-amber-600/30 bg-amber-900/10 px-3 py-2 font-mono text-xs text-amber-300" title={merkleRoot ?? ""}>
            Root: {merkleRoot ? truncate(merkleRoot, 24) : "-"}
          </div>
        </div>
      )}
    </div>
  );
}
