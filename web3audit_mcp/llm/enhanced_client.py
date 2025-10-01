"""Enhanced LLM client with specialized prompts for Web3 security analysis."""

import asyncio
import json
import httpx
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, TaskID

from ..core.adapters import Finding
from ..config.settings import Web3AuditConfig

@dataclass
class LLMResponse:
    """Response from LLM analysis."""
    content: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SecurityPromptTemplates:
    """Specialized prompt templates for security analysis."""
    
    VULNERABILITY_ANALYSIS = """
You are a world-class smart contract security expert. Analyze the following vulnerability finding and provide detailed insights.

FINDING DETAILS:
- Tool: {tool}
- Rule ID: {rule_id}
- Title: {title}
- Description: {description}
- Severity: {severity}
- Files: {files}

CONTRACT CODE (if available):
{contract_code}

TOOL OUTPUT:
{tool_output}

Please provide:
1. **Severity Assessment**: Confirm or adjust the severity level with reasoning
2. **Exploitability**: How easily can this be exploited? (1-10 scale)
3. **Business Impact**: What are the potential consequences?
4. **False Positive Analysis**: Likelihood this is a false positive (0-100%)
5. **Detailed Explanation**: Technical explanation in simple terms
6. **Remediation Steps**: Specific code changes needed
7. **Prevention**: How to prevent similar issues

Format your response as JSON:
{{
    "severity_assessment": {{
        "confirmed_severity": "critical|high|medium|low|info",
        "reasoning": "explanation for severity level"
    }},
    "exploitability": {{
        "score": 1-10,
        "explanation": "how easily exploitable"
    }},
    "business_impact": "description of potential consequences",
    "false_positive_likelihood": 0-100,
    "detailed_explanation": "technical explanation in simple terms",
    "remediation_steps": ["step 1", "step 2", "..."],
    "prevention_measures": ["measure 1", "measure 2", "..."],
    "confidence": 0.0-1.0
}}
"""

    EXPLOIT_SCENARIO = """
You are a security researcher specializing in smart contract exploits. Generate a detailed exploit scenario for this vulnerability.

VULNERABILITY:
{vulnerability_summary}

CONTRACT CONTEXT:
{contract_context}

Create a step-by-step exploit scenario that includes:
1. **Attacker Setup**: What the attacker needs to prepare
2. **Exploit Steps**: Detailed sequence of actions
3. **Expected Outcome**: What the attacker gains
4. **Detection Difficulty**: How hard is this to detect
5. **Mitigation Urgency**: How quickly this needs to be fixed

Be specific about:
- Transaction sequences
- Contract interactions
- Economic incentives
- Technical requirements

Format as JSON:
{{
    "exploit_scenario": {{
        "attacker_setup": ["requirement 1", "requirement 2"],
        "exploit_steps": [
            {{"step": 1, "action": "description", "technical_details": "specifics"}},
            {{"step": 2, "action": "description", "technical_details": "specifics"}}
        ],
        "expected_outcome": "what attacker gains",
        "economic_impact": "estimated financial impact",
        "detection_difficulty": "easy|medium|hard",
        "mitigation_urgency": "immediate|high|medium|low"
    }},
    "confidence": 0.0-1.0
}}
"""

    CODE_REVIEW = """
You are conducting a comprehensive smart contract security review. Analyze this code for vulnerabilities, gas optimizations, and best practices.

CONTRACT CODE:
{contract_code}

FOCUS AREAS:
{focus_areas}

Provide analysis in these categories:
1. **Security Vulnerabilities**: Critical issues that could lead to loss of funds
2. **Access Control**: Authorization and permission issues  
3. **Economic Attacks**: MEV, front-running, price manipulation
4. **Gas Optimization**: Inefficient patterns and improvements
5. **Code Quality**: Best practices and maintainability
6. **Compliance**: Standards adherence (ERC-20, ERC-721, etc.)

For each issue found, provide:
- Severity level
- Location in code
- Explanation
- Recommended fix
- Code example of fix

Format as JSON with detailed findings array.
"""

    REMEDIATION_GUIDANCE = """
You are a smart contract developer providing fix recommendations. Given these security findings, provide comprehensive remediation guidance.

FINDINGS:
{findings_summary}

PROJECT CONTEXT:
- Framework: {framework}
- Solidity Version: {solidity_version}
- Dependencies: {dependencies}

Provide:
1. **Priority Matrix**: Order fixes by urgency and impact
2. **Implementation Plan**: Step-by-step remediation approach
3. **Code Examples**: Specific fixes with before/after code
4. **Testing Strategy**: How to verify fixes work
5. **Deployment Considerations**: Safe upgrade procedures
6. **Long-term Improvements**: Architectural recommendations

Include specific library recommendations (OpenZeppelin, etc.) and explain trade-offs.
"""

class EnhancedLLMClient:
    """Enhanced LLM client with specialized security analysis capabilities."""
    
    def __init__(self, config: Web3AuditConfig, console: Console):
        self.config = config
        self.console = console
        self.base_url = "http://localhost:11434"  # Ollama default
        self.model = config.model.default_model
        self.templates = SecurityPromptTemplates()
        
    async def analyze_vulnerability(self, finding: Finding, contract_code: str = "") -> LLMResponse:
        """Analyze a vulnerability finding with LLM assistance."""
        
        prompt = self.templates.VULNERABILITY_ANALYSIS.format(
            tool=finding.tool,
            rule_id=finding.rule_id,
            title=finding.title,
            description=finding.description,
            severity=finding.severity,
            files=json.dumps(finding.files, indent=2),
            contract_code=contract_code[:2000],  # Limit code length
            tool_output=finding.tool_output[:1000]  # Limit output length
        )
        
        try:
            response = await self._generate_completion(prompt)
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response)
                return LLMResponse(
                    content=response,
                    confidence=analysis.get("confidence", 0.7),
                    reasoning=analysis.get("detailed_explanation", ""),
                    metadata={"analysis_type": "vulnerability", "finding_id": finding.id}
                )
            except json.JSONDecodeError:
                # Fallback to text response
                return LLMResponse(
                    content=response,
                    confidence=0.6,
                    reasoning="LLM provided text analysis",
                    metadata={"analysis_type": "vulnerability", "format": "text"}
                )
                
        except Exception as e:
            self.console.print(f"[red]LLM analysis failed: {e}[/red]")
            return LLMResponse(
                content=f"Analysis failed: {e}",
                confidence=0.0,
                reasoning="Error occurred during analysis",
                metadata={"error": str(e)}
            )
    
    async def generate_exploit_scenario(self, finding: Finding, contract_context: str = "") -> LLMResponse:
        """Generate detailed exploit scenario for a vulnerability."""
        
        vulnerability_summary = f"""
        Title: {finding.title}
        Description: {finding.description}
        Severity: {finding.severity}
        Tool: {finding.tool}
        """
        
        prompt = self.templates.EXPLOIT_SCENARIO.format(
            vulnerability_summary=vulnerability_summary,
            contract_context=contract_context[:1500]
        )
        
        try:
            response = await self._generate_completion(prompt)
            
            try:
                scenario = json.loads(response)
                return LLMResponse(
                    content=response,
                    confidence=scenario.get("confidence", 0.7),
                    reasoning="Generated exploit scenario",
                    metadata={"analysis_type": "exploit_scenario", "finding_id": finding.id}
                )
            except json.JSONDecodeError:
                return LLMResponse(
                    content=response,
                    confidence=0.6,
                    reasoning="Generated text-based exploit scenario",
                    metadata={"analysis_type": "exploit_scenario", "format": "text"}
                )
                
        except Exception as e:
            self.console.print(f"[red]Exploit scenario generation failed: {e}[/red]")
            return LLMResponse(
                content=f"Scenario generation failed: {e}",
                confidence=0.0,
                reasoning="Error occurred during scenario generation",
                metadata={"error": str(e)}
            )
    
    async def comprehensive_code_review(self, contract_code: str, focus_areas: List[str] = None) -> LLMResponse:
        """Perform comprehensive code review with LLM."""
        
        if focus_areas is None:
            focus_areas = [
                "reentrancy vulnerabilities",
                "access control issues", 
                "integer overflow/underflow",
                "unchecked external calls",
                "gas optimization opportunities"
            ]
        
        prompt = self.templates.CODE_REVIEW.format(
            contract_code=contract_code[:4000],  # Limit for context window
            focus_areas=", ".join(focus_areas)
        )
        
        try:
            response = await self._generate_completion(prompt, max_tokens=2000)
            
            return LLMResponse(
                content=response,
                confidence=0.8,
                reasoning="Comprehensive code review completed",
                metadata={"analysis_type": "code_review", "focus_areas": focus_areas}
            )
            
        except Exception as e:
            self.console.print(f"[red]Code review failed: {e}[/red]")
            return LLMResponse(
                content=f"Code review failed: {e}",
                confidence=0.0,
                reasoning="Error occurred during code review",
                metadata={"error": str(e)}
            )
    
    async def generate_remediation_guidance(self, findings: List[Finding], project_context: Dict[str, str] = None) -> LLMResponse:
        """Generate comprehensive remediation guidance."""
        
        if project_context is None:
            project_context = {
                "framework": "unknown",
                "solidity_version": "unknown", 
                "dependencies": "unknown"
            }
        
        findings_summary = []
        for finding in findings[:10]:  # Limit to top 10 findings
            findings_summary.append({
                "title": finding.title,
                "severity": finding.severity,
                "description": finding.description[:200]
            })
        
        prompt = self.templates.REMEDIATION_GUIDANCE.format(
            findings_summary=json.dumps(findings_summary, indent=2),
            framework=project_context.get("framework", "unknown"),
            solidity_version=project_context.get("solidity_version", "unknown"),
            dependencies=project_context.get("dependencies", "unknown")
        )
        
        try:
            response = await self._generate_completion(prompt, max_tokens=2500)
            
            return LLMResponse(
                content=response,
                confidence=0.8,
                reasoning="Generated comprehensive remediation guidance",
                metadata={"analysis_type": "remediation", "findings_count": len(findings)}
            )
            
        except Exception as e:
            self.console.print(f"[red]Remediation guidance generation failed: {e}[/red]")
            return LLMResponse(
                content=f"Remediation guidance failed: {e}",
                confidence=0.0,
                reasoning="Error occurred during guidance generation",
                metadata={"error": str(e)}
            )
    
    async def _generate_completion(self, prompt: str, max_tokens: int = 1500) -> str:
        """Generate completion using Ollama API."""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.model.temperature,
                "top_p": self.config.model.top_p,
                "num_predict": min(max_tokens, self.config.model.max_tokens)
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
    
    async def batch_analyze_findings(self, findings: List[Finding], progress: Progress, task_id: TaskID) -> List[LLMResponse]:
        """Analyze multiple findings in batch with progress tracking."""
        
        responses = []
        total_findings = len(findings)
        
        for i, finding in enumerate(findings):
            progress.update(
                task_id, 
                description=f"LLM analyzing finding {i+1}/{total_findings}: {finding.title[:50]}...",
                completed=i,
                total=total_findings
            )
            
            # Only analyze high and critical severity findings with LLM to save time
            if finding.severity in ["critical", "high"]:
                response = await self.analyze_vulnerability(finding)
                responses.append(response)
            else:
                # Create a basic response for lower severity findings
                responses.append(LLMResponse(
                    content=f"Basic analysis: {finding.description}",
                    confidence=0.5,
                    reasoning="Lower severity finding, basic analysis applied",
                    metadata={"analysis_type": "basic", "finding_id": finding.id}
                ))
            
            # Small delay to prevent overwhelming the LLM
            await asyncio.sleep(0.1)
        
        progress.update(task_id, completed=total_findings)
        return responses
    
    def enhance_finding_with_llm(self, finding: Finding, llm_response: LLMResponse) -> Finding:
        """Enhance a finding with LLM analysis results."""
        
        # Try to extract structured data from LLM response
        try:
            analysis = json.loads(llm_response.content)
            
            # Update severity if LLM suggests different level
            if "severity_assessment" in analysis:
                confirmed_severity = analysis["severity_assessment"].get("confirmed_severity")
                if confirmed_severity and confirmed_severity != finding.severity:
                    finding.severity = confirmed_severity
            
            # Enhance recommendation with LLM suggestions
            if "remediation_steps" in analysis:
                remediation_steps = analysis["remediation_steps"]
                if remediation_steps:
                    finding.recommendation = "\n".join([
                        finding.recommendation,
                        "\nLLM-Enhanced Remediation:",
                        *[f"• {step}" for step in remediation_steps]
                    ])
            
            # Add exploit scenario if available
            if "exploit_scenario" in analysis:
                finding.exploit_scenario = json.dumps(analysis["exploit_scenario"], indent=2)
            
            # Update confidence based on LLM analysis
            llm_confidence = analysis.get("confidence", 0.7)
            finding.confidence = (finding.confidence + llm_confidence) / 2
            
        except json.JSONDecodeError:
            # If not JSON, append as text enhancement
            finding.recommendation += f"\n\nLLM Analysis:\n{llm_response.content[:500]}"
        
        return finding
