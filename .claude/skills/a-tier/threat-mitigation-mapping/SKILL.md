---
name: threat-mitigation-mapping
description: Map identified threats to appropriate security controls and mitigations. Use when prioritizing security investments, creating remediation plans, or validating control effectiveness.
---

# Threat Mitigation Mapping

Connect threats to controls for effective security planning.

## When to Use This Skill

- Prioritizing security investments
- Creating remediation roadmaps
- Validating control coverage
- Designing defense-in-depth
- Security architecture review

## Core Concepts

### Control Categories

- **Preventive**: Stop attacks before they occur (firewall, input validation)
- **Detective**: Identify attacks in progress (IDS, log monitoring)
- **Corrective**: Respond and recover (incident response, backup restore)

### Control Layers

| Layer           | Examples                             |
| --------------- | ------------------------------------ |
| **Network**     | Firewall, WAF, DDoS protection       |
| **Application** | Input validation, authentication     |
| **Data**        | Encryption, access controls          |
| **Endpoint**    | EDR, patch management                |
| **Process**     | Security training, incident response |

## Template: Mitigation Model

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

class ControlType(Enum):
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"

class ControlLayer(Enum):
    NETWORK = "network"
    APPLICATION = "application"
    DATA = "data"
    ENDPOINT = "endpoint"
    PROCESS = "process"
    PHYSICAL = "physical"

class ImplementationStatus(Enum):
    NOT_IMPLEMENTED = "not_implemented"
    PARTIAL = "partial"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"

class Effectiveness(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

@dataclass
class SecurityControl:
    id: str
    name: str
    description: str
    control_type: ControlType
    layer: ControlLayer
    effectiveness: Effectiveness
    implementation_cost: str
    maintenance_cost: str
    status: ImplementationStatus = ImplementationStatus.NOT_IMPLEMENTED
    mitigates_threats: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    compliance_refs: List[str] = field(default_factory=list)

    def coverage_score(self) -> float:
        mult = {ImplementationStatus.NOT_IMPLEMENTED: 0.0, ImplementationStatus.PARTIAL: 0.5,
                ImplementationStatus.IMPLEMENTED: 0.8, ImplementationStatus.VERIFIED: 1.0}
        return self.effectiveness.value * mult[self.status]

@dataclass
class Threat:
    id: str
    name: str
    category: str  # STRIDE category
    description: str
    impact: str
    likelihood: str
    risk_score: float

@dataclass
class MitigationMapping:
    threat: Threat
    controls: List[SecurityControl]
    residual_risk: str = "Unknown"

    def calculate_coverage(self) -> float:
        if not self.controls: return 0.0
        total = sum(c.coverage_score() for c in self.controls)
        max_possible = len(self.controls) * Effectiveness.VERY_HIGH.value
        return (total / max_possible) * 100 if max_possible > 0 else 0

    def has_defense_in_depth(self) -> bool:
        layers = set(c.layer for c in self.controls if c.status != ImplementationStatus.NOT_IMPLEMENTED)
        return len(layers) >= 2

    def has_control_diversity(self) -> bool:
        types = set(c.control_type for c in self.controls if c.status != ImplementationStatus.NOT_IMPLEMENTED)
        return len(types) >= 2

@dataclass
class MitigationPlan:
    name: str
    threats: List[Threat] = field(default_factory=list)
    controls: List[SecurityControl] = field(default_factory=list)
    mappings: List[MitigationMapping] = field(default_factory=list)

    def get_unmapped_threats(self) -> List[Threat]:
        mapped = {m.threat.id for m in self.mappings}
        return [t for t in self.threats if t.id not in mapped]

    def get_gaps(self) -> List[Dict]:
        gaps = []
        for m in self.mappings:
            cov = m.calculate_coverage()
            if cov < 50:
                gaps.append({"threat": m.threat.id, "threat_name": m.threat.name,
                             "coverage": cov, "issue": "Insufficient coverage"})
            if not m.has_defense_in_depth():
                gaps.append({"threat": m.threat.id, "threat_name": m.threat.name,
                             "coverage": cov, "issue": "No defense in depth"})
            if not m.has_control_diversity():
                gaps.append({"threat": m.threat.id, "threat_name": m.threat.name,
                             "coverage": cov, "issue": "No control diversity"})
        return gaps
```

## Template: Control Library

```python
class ControlLibrary:
    STANDARD_CONTROLS = {
        "AUTH-001": SecurityControl("AUTH-001", "Multi-Factor Authentication",
            "Require MFA for all authentication", ControlType.PREVENTIVE,
            ControlLayer.APPLICATION, Effectiveness.HIGH, "Medium", "Low",
            mitigates_threats=["SPOOFING"], technologies=["TOTP", "WebAuthn"],
            compliance_refs=["PCI-DSS 8.3", "NIST 800-63B"]),
        "VAL-001": SecurityControl("VAL-001", "Input Validation Framework",
            "Validate and sanitize all input", ControlType.PREVENTIVE,
            ControlLayer.APPLICATION, Effectiveness.HIGH, "Medium", "Medium",
            mitigates_threats=["TAMPERING", "INJECTION"],
            technologies=["Joi", "Yup", "Pydantic"]),
        "VAL-002": SecurityControl("VAL-002", "Web Application Firewall",
            "Filter malicious requests", ControlType.PREVENTIVE,
            ControlLayer.NETWORK, Effectiveness.MEDIUM, "Medium", "Medium",
            mitigates_threats=["TAMPERING", "INJECTION", "DOS"],
            technologies=["AWS WAF", "Cloudflare"]),
        "ENC-001": SecurityControl("ENC-001", "Data Encryption at Rest",
            "Encrypt sensitive data in storage", ControlType.PREVENTIVE,
            ControlLayer.DATA, Effectiveness.HIGH, "Medium", "Low",
            mitigates_threats=["INFORMATION_DISCLOSURE"],
            technologies=["AES-256", "KMS"], compliance_refs=["PCI-DSS 3.4"]),
        "ENC-002": SecurityControl("ENC-002", "TLS Encryption",
            "Encrypt data in transit", ControlType.PREVENTIVE,
            ControlLayer.NETWORK, Effectiveness.HIGH, "Low", "Low",
            mitigates_threats=["INFORMATION_DISCLOSURE", "TAMPERING"],
            technologies=["TLS 1.3"]),
        "LOG-001": SecurityControl("LOG-001", "Security Event Logging",
            "Log security-relevant events", ControlType.DETECTIVE,
            ControlLayer.APPLICATION, Effectiveness.MEDIUM, "Low", "Medium",
            mitigates_threats=["REPUDIATION"],
            technologies=["ELK", "Splunk"]),
        "ACC-001": SecurityControl("ACC-001", "Role-Based Access Control",
            "RBAC for authorization", ControlType.PREVENTIVE,
            ControlLayer.APPLICATION, Effectiveness.HIGH, "Medium", "Medium",
            mitigates_threats=["ELEVATION_OF_PRIVILEGE", "INFORMATION_DISCLOSURE"]),
        "AVL-001": SecurityControl("AVL-001", "Rate Limiting",
            "Limit request rates", ControlType.PREVENTIVE,
            ControlLayer.APPLICATION, Effectiveness.MEDIUM, "Low", "Low",
            mitigates_threats=["DENIAL_OF_SERVICE"]),
    }

    def get_controls_for_threat(self, category: str) -> List[SecurityControl]:
        return [c for c in self.STANDARD_CONTROLS.values() if category in c.mitigates_threats]

    def get_controls_by_layer(self, layer: ControlLayer) -> List[SecurityControl]:
        return [c for c in self.STANDARD_CONTROLS.values() if c.layer == layer]

    def recommend_controls(self, threat: Threat, existing: List[str]) -> List[SecurityControl]:
        return [c for c in self.get_controls_for_threat(threat.category) if c.id not in existing]
```

## Template: Mitigation Analysis

```python
class MitigationAnalyzer:
    def __init__(self, plan: MitigationPlan, library: ControlLibrary):
        self.plan = plan
        self.library = library

    def overall_risk_reduction(self) -> float:
        if not self.plan.mappings: return 0.0
        weighted = sum(m.threat.risk_score * m.calculate_coverage() for m in self.plan.mappings)
        total = sum(m.threat.risk_score for m in self.plan.mappings)
        return weighted / total if total > 0 else 0

    def critical_gaps(self) -> List[Dict]:
        gaps = self.plan.get_gaps()
        critical = {t.id for t in self.plan.threats if t.impact == "Critical"}
        return [g for g in gaps if g["threat"] in critical]

    def generate_roadmap(self) -> List[Dict]:
        roadmap = []
        for gap in self.plan.get_gaps():
            mapping = next((m for m in self.plan.mappings if m.threat.id == gap["threat"]), None)
            if mapping:
                phase = 1 if mapping.threat.impact == "Critical" else 2
                for c in self.library.get_controls_for_threat(mapping.threat.category):
                    if c.status == ImplementationStatus.NOT_IMPLEMENTED:
                        roadmap.append({"threat": gap["threat"], "control": c.name,
                                        "phase": phase, "priority": mapping.threat.impact})
        return roadmap[:10]

    def defense_in_depth_analysis(self) -> Dict[str, List[str]]:
        coverage = {layer.value: [] for layer in ControlLayer}
        for m in self.plan.mappings:
            for c in m.controls:
                if c.status in [ImplementationStatus.IMPLEMENTED, ImplementationStatus.VERIFIED]:
                    coverage[c.layer.value].append(c.id)
        return coverage
```

## Best Practices

### Do's
- **Map all threats** - No threat should be unmapped
- **Layer controls** - Defense in depth is essential
- **Mix control types** - Preventive, detective, corrective
- **Track effectiveness** - Measure and improve
- **Review regularly** - Controls degrade over time

### Don'ts
- **Don't rely on single controls** - Single points of failure
- **Don't ignore cost** - ROI matters
- **Don't skip testing** - Untested controls may fail
- **Don't set and forget** - Continuous improvement
- **Don't ignore people/process** - Technology alone isn't enough
