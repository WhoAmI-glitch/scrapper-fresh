---
name: attack-tree-construction
description: Build comprehensive attack trees to visualize threat paths. Use when mapping attack scenarios, identifying defense gaps, or communicating security risks to stakeholders.
---

# Attack Tree Construction

Systematic attack path visualization and analysis.

## When to Use This Skill

- Visualizing complex attack scenarios
- Identifying defense gaps and priorities
- Communicating risks to stakeholders
- Planning defensive investments
- Penetration test planning
- Security architecture review

## Core Concepts

### 1. Attack Tree Structure

```
                    [Root Goal]
                         |
            +------------+------------+
            |                         |
       [Sub-goal 1]              [Sub-goal 2]
       (OR node)                 (AND node)
            |                         |
      +-----+-----+             +-----+-----+
      |           |             |           |
   [Attack]   [Attack]      [Attack]   [Attack]
    (leaf)     (leaf)        (leaf)     (leaf)
```

### 2. Node Types

| Type     | Symbol    | Description             |
| -------- | --------- | ----------------------- |
| **OR**   | Oval      | Any child achieves goal |
| **AND**  | Rectangle | All children required   |
| **Leaf** | Box       | Atomic attack step      |

### 3. Attack Attributes

| Attribute     | Description             | Values             |
| ------------- | ----------------------- | ------------------ |
| **Cost**      | Resources needed        | $, $$, $$$         |
| **Time**      | Duration to execute     | Hours, Days, Weeks |
| **Skill**     | Expertise required      | Low, Medium, High  |
| **Detection** | Likelihood of detection | Low, Medium, High  |

## Template: Attack Tree Data Model

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
import json

class NodeType(Enum):
    OR = "or"
    AND = "and"
    LEAF = "leaf"

class Difficulty(Enum):
    TRIVIAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    EXPERT = 5

class Cost(Enum):
    FREE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

class DetectionRisk(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CERTAIN = 4

@dataclass
class AttackAttributes:
    difficulty: Difficulty = Difficulty.MEDIUM
    cost: Cost = Cost.MEDIUM
    detection_risk: DetectionRisk = DetectionRisk.MEDIUM
    time_hours: float = 8.0
    requires_insider: bool = False
    requires_physical: bool = False

@dataclass
class AttackNode:
    id: str
    name: str
    description: str
    node_type: NodeType
    attributes: AttackAttributes = field(default_factory=AttackAttributes)
    children: List['AttackNode'] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    cve_refs: List[str] = field(default_factory=list)

    def add_child(self, child: 'AttackNode') -> None:
        self.children.append(child)

    def calculate_path_difficulty(self) -> float:
        if self.node_type == NodeType.LEAF:
            return self.attributes.difficulty.value
        if not self.children:
            return 0
        child_difficulties = [c.calculate_path_difficulty() for c in self.children]
        if self.node_type == NodeType.OR:
            return min(child_difficulties)
        else:  # AND
            return max(child_difficulties)

    def calculate_path_cost(self) -> float:
        if self.node_type == NodeType.LEAF:
            return self.attributes.cost.value
        if not self.children:
            return 0
        child_costs = [c.calculate_path_cost() for c in self.children]
        if self.node_type == NodeType.OR:
            return min(child_costs)
        else:  # AND
            return sum(child_costs)

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "type": self.node_type.value,
            "attributes": {
                "difficulty": self.attributes.difficulty.name,
                "cost": self.attributes.cost.name,
                "detection_risk": self.attributes.detection_risk.name,
                "time_hours": self.attributes.time_hours,
            },
            "mitigations": self.mitigations,
            "children": [c.to_dict() for c in self.children]
        }

@dataclass
class AttackTree:
    name: str
    description: str
    root: AttackNode
    version: str = "1.0"

    def find_easiest_path(self) -> List[AttackNode]:
        return self._find_path(self.root, minimize="difficulty")

    def find_cheapest_path(self) -> List[AttackNode]:
        return self._find_path(self.root, minimize="cost")

    def find_stealthiest_path(self) -> List[AttackNode]:
        return self._find_path(self.root, minimize="detection")

    def _find_path(self, node: AttackNode, minimize: str) -> List[AttackNode]:
        if node.node_type == NodeType.LEAF or not node.children:
            return [node]
        if node.node_type == NodeType.OR:
            best_path, best_score = None, float('inf')
            for child in node.children:
                child_path = self._find_path(child, minimize)
                score = self._path_score(child_path, minimize)
                if score < best_score:
                    best_score, best_path = score, child_path
            return [node] + (best_path or [])
        else:  # AND
            path = [node]
            for child in node.children:
                path.extend(self._find_path(child, minimize))
            return path

    def _path_score(self, path: List[AttackNode], metric: str) -> float:
        leaves = [n for n in path if n.node_type == NodeType.LEAF]
        if metric == "difficulty":
            return sum(n.attributes.difficulty.value for n in leaves)
        elif metric == "cost":
            return sum(n.attributes.cost.value for n in leaves)
        elif metric == "detection":
            return sum(n.attributes.detection_risk.value for n in leaves)
        return 0

    def get_all_leaf_attacks(self) -> List[AttackNode]:
        leaves = []
        self._collect_leaves(self.root, leaves)
        return leaves

    def _collect_leaves(self, node: AttackNode, leaves: List[AttackNode]) -> None:
        if node.node_type == NodeType.LEAF:
            leaves.append(node)
        for child in node.children:
            self._collect_leaves(child, leaves)

    def get_unmitigated_attacks(self) -> List[AttackNode]:
        return [n for n in self.get_all_leaf_attacks() if not n.mitigations]

    def export_json(self) -> str:
        return json.dumps({
            "name": self.name, "description": self.description,
            "version": self.version, "root": self.root.to_dict()
        }, indent=2)
```

## Template: Attack Tree Builder

```python
class AttackTreeBuilder:
    """Fluent builder for attack trees."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._node_stack: List[AttackNode] = []
        self._root: Optional[AttackNode] = None

    def goal(self, id: str, name: str, description: str = "") -> 'AttackTreeBuilder':
        self._root = AttackNode(id=id, name=name, description=description, node_type=NodeType.OR)
        self._node_stack = [self._root]
        return self

    def or_node(self, id: str, name: str, description: str = "") -> 'AttackTreeBuilder':
        node = AttackNode(id=id, name=name, description=description, node_type=NodeType.OR)
        self._current().add_child(node)
        self._node_stack.append(node)
        return self

    def and_node(self, id: str, name: str, description: str = "") -> 'AttackTreeBuilder':
        node = AttackNode(id=id, name=name, description=description, node_type=NodeType.AND)
        self._current().add_child(node)
        self._node_stack.append(node)
        return self

    def attack(self, id: str, name: str, description: str = "",
               difficulty: Difficulty = Difficulty.MEDIUM, cost: Cost = Cost.MEDIUM,
               detection: DetectionRisk = DetectionRisk.MEDIUM, time_hours: float = 8.0,
               mitigations: List[str] = None) -> 'AttackTreeBuilder':
        node = AttackNode(
            id=id, name=name, description=description, node_type=NodeType.LEAF,
            attributes=AttackAttributes(difficulty=difficulty, cost=cost,
                                        detection_risk=detection, time_hours=time_hours),
            mitigations=mitigations or []
        )
        self._current().add_child(node)
        return self

    def end(self) -> 'AttackTreeBuilder':
        if len(self._node_stack) > 1:
            self._node_stack.pop()
        return self

    def build(self) -> AttackTree:
        if not self._root:
            raise ValueError("No root goal defined")
        return AttackTree(name=self.name, description=self.description, root=self._root)

    def _current(self) -> AttackNode:
        if not self._node_stack:
            raise ValueError("No current node")
        return self._node_stack[-1]
```

## Template: Attack Path Analysis

```python
from typing import Set, Tuple

class AttackPathAnalyzer:
    """Analyze attack paths and coverage."""

    def __init__(self, tree: AttackTree):
        self.tree = tree

    def get_all_paths(self) -> List[List[AttackNode]]:
        paths = []
        self._collect_paths(self.tree.root, [], paths)
        return paths

    def _collect_paths(self, node: AttackNode, current_path: List[AttackNode],
                       all_paths: List[List[AttackNode]]) -> None:
        current_path = current_path + [node]
        if node.node_type == NodeType.LEAF or not node.children:
            all_paths.append(current_path)
            return
        if node.node_type == NodeType.OR:
            for child in node.children:
                self._collect_paths(child, current_path, all_paths)
        else:  # AND - combine all children
            child_paths = []
            for child in node.children:
                child_sub_paths = []
                self._collect_paths(child, [], child_sub_paths)
                child_paths.append(child_sub_paths)
            for combo in self._combine_and_paths(child_paths):
                all_paths.append(current_path + combo)

    def _combine_and_paths(self, child_paths):
        if not child_paths:
            return [[]]
        result = [[]]
        for paths in child_paths:
            result = [existing + path for existing in result for path in paths]
        return result

    def calculate_path_metrics(self, path: List[AttackNode]) -> Dict:
        leaves = [n for n in path if n.node_type == NodeType.LEAF]
        return {
            "steps": len(leaves),
            "total_difficulty": sum(n.attributes.difficulty.value for n in leaves),
            "total_cost": sum(n.attributes.cost.value for n in leaves),
            "total_time_hours": sum(n.attributes.time_hours for n in leaves),
            "max_detection_risk": max((n.attributes.detection_risk.value for n in leaves), default=0),
            "requires_insider": any(n.attributes.requires_insider for n in leaves),
            "requires_physical": any(n.attributes.requires_physical for n in leaves),
        }

    def identify_critical_nodes(self) -> List[Tuple[AttackNode, int]]:
        paths = self.get_all_paths()
        node_counts: Dict[str, Tuple[AttackNode, int]] = {}
        for path in paths:
            for node in path:
                if node.id not in node_counts:
                    node_counts[node.id] = (node, 0)
                node_counts[node.id] = (node, node_counts[node.id][1] + 1)
        return sorted(node_counts.values(), key=lambda x: x[1], reverse=True)

    def coverage_analysis(self, mitigated_attacks: Set[str]) -> Dict:
        all_paths = self.get_all_paths()
        blocked = [p for p in all_paths if {n.id for n in p if n.node_type == NodeType.LEAF} & mitigated_attacks]
        open_paths = [p for p in all_paths if p not in blocked]
        return {
            "total_paths": len(all_paths),
            "blocked_paths": len(blocked),
            "open_paths": len(open_paths),
            "coverage_percentage": len(blocked) / len(all_paths) * 100 if all_paths else 0,
        }

    def prioritize_mitigations(self) -> List[Dict]:
        critical_nodes = self.identify_critical_nodes()
        total_paths = len(self.get_all_paths())
        return sorted([
            {"attack": n.name, "attack_id": n.id, "paths_blocked": count,
             "coverage_impact": count / total_paths * 100,
             "difficulty": n.attributes.difficulty.name, "mitigations": n.mitigations}
            for n, count in critical_nodes
            if n.node_type == NodeType.LEAF and n.mitigations
        ], key=lambda x: x["coverage_impact"], reverse=True)
```

## Best Practices

### Do's

- **Start with clear goals** - Define what attacker wants
- **Be exhaustive** - Consider all attack vectors
- **Attribute attacks** - Cost, skill, and detection
- **Update regularly** - New threats emerge
- **Validate with experts** - Red team review

### Don'ts

- **Don't oversimplify** - Real attacks are complex
- **Don't ignore dependencies** - AND nodes matter
- **Don't forget insider threats** - Not all attackers are external
- **Don't skip mitigations** - Trees are for defense planning
- **Don't make it static** - Threat landscape evolves
