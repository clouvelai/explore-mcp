"""
Documentation-based discovery for git repositories.

Extracts MCP server information from README files, code comments, and configuration
without actually running the server.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DocTool:
    """A tool discovered from documentation."""
    name: str
    description: str
    parameters: List[Dict] = None
    source: str = "documentation"  # "readme", "code", "config"
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class DocResource:
    """A resource discovered from documentation."""
    name: str
    description: str
    uri_template: Optional[str] = None
    mime_type: Optional[str] = None
    source: str = "documentation"
    confidence: float = 1.0


@dataclass
class DocPrompt:
    """A prompt discovered from documentation."""
    name: str
    description: str
    arguments: List[Dict] = None
    source: str = "documentation" 
    confidence: float = 1.0


@dataclass
class DocumentationDiscoveryResult:
    """Result of documentation-based discovery."""
    tools: List[DocTool]
    resources: List[DocResource]
    prompts: List[DocPrompt]
    description: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    repository_url: Optional[str] = None
    language: Optional[str] = None
    discovered_at: datetime = None
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class DocumentationDiscovery:
    """Discovers MCP server capabilities from git repository documentation."""
    
    def __init__(self):
        # Patterns for finding tools in different formats
        self.tool_patterns = [
            # Python @mcp.tool decorators
            r'@mcp\.tool\(\)\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):\s*"""([^"]+)"""',
            r'@mcp\.tool\s*\n\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):\s*"""([^"]+)"""',
            
            # FastMCP patterns
            r'@app\.tool\(\)\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):\s*"""([^"]+)"""',
            
            # TypeScript/JavaScript patterns
            r'tools:\s*\{\s*([a-zA-Z_][a-zA-Z0-9_]*):.*?description:\s*["\']([^"\']+)["\']',
            r'name:\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\'].*?description:\s*["\']([^"\']+)["\']',
            
            # README tool listings
            r'##?\s+([A-Za-z_][A-Za-z0-9_\s]*)\s*\n([^#\n]{10,200})',
            r'\*\*([a-zA-Z_][a-zA-Z0-9_]*)\*\*[:\s]*([^*\n]{10,200})',
        ]
        
        # Patterns for resources
        self.resource_patterns = [
            r'@mcp\.resource\(\)\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):\s*"""([^"]+)"""',
            r'resources:\s*\{\s*([a-zA-Z_][a-zA-Z0-9_]*):.*?description:\s*["\']([^"\']+)["\']',
        ]
        
        # Patterns for prompts  
        self.prompt_patterns = [
            r'@mcp\.prompt\(\)\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):\s*"""([^"]+)"""',
            r'prompts:\s*\{\s*([a-zA-Z_][a-zA-Z0-9_]*):.*?description:\s*["\']([^"\']+)["\']',
        ]
    
    def discover_from_repository(self, repo_path: Path) -> DocumentationDiscoveryResult:
        """
        Perform documentation-based discovery on a git repository.
        
        Args:
            repo_path: Path to the cloned repository
            
        Returns:
            Documentation discovery result
        """
        tools = []
        resources = []
        prompts = []
        
        # Extract metadata from repository
        metadata = self._extract_metadata(repo_path)
        
        # Parse README files
        readme_tools, readme_resources, readme_prompts = self._parse_readme_files(repo_path)
        tools.extend(readme_tools)
        resources.extend(readme_resources)
        prompts.extend(readme_prompts)
        
        # Parse source code files
        code_tools, code_resources, code_prompts = self._parse_source_code(repo_path)
        tools.extend(code_tools)
        resources.extend(code_resources)
        prompts.extend(code_prompts)
        
        # Parse configuration files
        config_tools, config_resources, config_prompts = self._parse_config_files(repo_path)
        tools.extend(config_tools)
        resources.extend(config_resources)
        prompts.extend(config_prompts)
        
        # Remove duplicates
        tools = self._deduplicate_tools(tools)
        resources = self._deduplicate_resources(resources)
        prompts = self._deduplicate_prompts(prompts)
        
        return DocumentationDiscoveryResult(
            tools=tools,
            resources=resources,
            prompts=prompts,
            **metadata
        )
    
    def _extract_metadata(self, repo_path: Path) -> Dict:
        """Extract repository metadata."""
        metadata = {}
        
        # Try package.json for Node.js projects
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    metadata.update({
                        "description": data.get("description"),
                        "version": data.get("version"),
                        "author": data.get("author"),
                        "repository_url": data.get("repository", {}).get("url") if isinstance(data.get("repository"), dict) else data.get("repository"),
                        "language": "javascript"
                    })
            except:
                pass
        
        # Try pyproject.toml for Python projects
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            metadata["language"] = "python"
            # Could parse TOML here for more metadata
        
        # Try setup.py for Python projects
        setup_py = repo_path / "setup.py"
        if setup_py.exists() and not metadata.get("language"):
            metadata["language"] = "python"
        
        return metadata
    
    def _parse_readme_files(self, repo_path: Path) -> Tuple[List[DocTool], List[DocResource], List[DocPrompt]]:
        """Parse README files for tool information."""
        tools = []
        resources = []
        prompts = []
        
        readme_files = [
            repo_path / "README.md",
            repo_path / "README.txt", 
            repo_path / "readme.md",
            repo_path / "docs" / "README.md"
        ]
        
        for readme_file in readme_files:
            if readme_file.exists():
                try:
                    content = readme_file.read_text(encoding='utf-8')
                    
                    # Look for tools section
                    tools.extend(self._extract_tools_from_text(content, "readme"))
                    
                    # Look for API/endpoint listings
                    resources.extend(self._extract_resources_from_text(content, "readme"))
                    
                except Exception as e:
                    print(f"⚠️  Could not parse {readme_file}: {e}")
        
        return tools, resources, prompts
    
    def _parse_source_code(self, repo_path: Path) -> Tuple[List[DocTool], List[DocResource], List[DocPrompt]]:
        """Parse source code files for MCP decorators and patterns."""
        tools = []
        resources = []
        prompts = []
        
        # Common MCP server file patterns
        patterns = [
            "**/*.py",
            "**/server.py",
            "**/main.py",
            "**/*.ts",
            "**/*.js",
            "**/server.ts",
            "**/index.ts"
        ]
        
        processed_files = set()
        
        for pattern in patterns:
            for file_path in repo_path.glob(pattern):
                if file_path in processed_files:
                    continue
                processed_files.add(file_path)
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Extract tools using patterns
                    tools.extend(self._extract_tools_from_code(content, str(file_path.relative_to(repo_path))))
                    resources.extend(self._extract_resources_from_code(content, str(file_path.relative_to(repo_path))))
                    prompts.extend(self._extract_prompts_from_code(content, str(file_path.relative_to(repo_path))))
                    
                except Exception as e:
                    print(f"⚠️  Could not parse {file_path}: {e}")
        
        return tools, resources, prompts
    
    def _parse_config_files(self, repo_path: Path) -> Tuple[List[DocTool], List[DocResource], List[DocPrompt]]:
        """Parse configuration files for MCP definitions."""
        tools = []
        resources = []
        prompts = []
        
        # Look for MCP-specific config files
        config_files = [
            repo_path / "mcp.json",
            repo_path / "mcp-config.json", 
            repo_path / ".mcp" / "config.json"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file) as f:
                        data = json.load(f)
                        
                    # Extract tools from config
                    if "tools" in data:
                        for tool_name, tool_data in data["tools"].items():
                            tools.append(DocTool(
                                name=tool_name,
                                description=tool_data.get("description", ""),
                                parameters=tool_data.get("parameters", []),
                                source="config",
                                confidence=1.0
                            ))
                    
                    # Extract resources from config
                    if "resources" in data:
                        for resource_name, resource_data in data["resources"].items():
                            resources.append(DocResource(
                                name=resource_name,
                                description=resource_data.get("description", ""),
                                uri_template=resource_data.get("uri_template"),
                                source="config",
                                confidence=1.0
                            ))
                            
                except Exception as e:
                    print(f"⚠️  Could not parse config {config_file}: {e}")
        
        return tools, resources, prompts
    
    def _extract_tools_from_text(self, text: str, source: str) -> List[DocTool]:
        """Extract tools from README or documentation text."""
        tools = []
        
        # Look for tool sections
        tool_section_patterns = [
            r'#+\s*(Tools?|Functions?|Commands?|API)\s*\n(.*?)(?=\n#+|\n\n\n|\Z)',
            r'\*\*(Tools?|Functions?|Commands?)\*\*\s*\n(.*?)(?=\n\*\*|\n\n\n|\Z)'
        ]
        
        for pattern in tool_section_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section_content = match.group(2)
                
                # Extract individual tools from the section
                tool_matches = re.finditer(r'[-*]\s*`?([a-zA-Z_][a-zA-Z0-9_]*)`?[:\s]*([^\n]{10,200})', section_content)
                for tool_match in tool_matches:
                    name = tool_match.group(1).strip()
                    description = tool_match.group(2).strip()
                    
                    tools.append(DocTool(
                        name=name,
                        description=description,
                        source=source,
                        confidence=0.8  # Lower confidence for text-based extraction
                    ))
        
        return tools
    
    def _extract_tools_from_code(self, code: str, file_path: str) -> List[DocTool]:
        """Extract tools from source code using patterns."""
        tools = []
        
        for pattern in self.tool_patterns:
            matches = re.finditer(pattern, code, re.DOTALL)
            for match in matches:
                name = match.group(1).strip()
                description = match.group(2).strip()
                
                # Clean up description
                description = re.sub(r'\s+', ' ', description).strip()
                
                tools.append(DocTool(
                    name=name,
                    description=description,
                    source=f"code:{file_path}",
                    confidence=0.9  # High confidence for code-based extraction
                ))
        
        return tools
    
    def _extract_resources_from_text(self, text: str, source: str) -> List[DocResource]:
        """Extract resources from documentation text.""" 
        resources = []
        
        # Look for API endpoint patterns
        endpoint_patterns = [
            r'(GET|POST|PUT|DELETE)\s+(/[^\s]+)\s*[:\-]\s*([^\n]{10,100})',
            r'`(/[^`]+)`\s*[:\-]\s*([^\n]{10,100})'
        ]
        
        for pattern in endpoint_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 3:
                    method, uri, description = match.groups()
                    name = f"{method.lower()}_{uri.replace('/', '_').replace('{', '').replace('}', '')}"
                else:
                    uri, description = match.groups()
                    name = uri.replace('/', '_').replace('{', '').replace('}', '')
                
                resources.append(DocResource(
                    name=name.strip(),
                    description=description.strip(),
                    uri_template=uri.strip(),
                    source=source,
                    confidence=0.7
                ))
        
        return resources
    
    def _extract_resources_from_code(self, code: str, file_path: str) -> List[DocResource]:
        """Extract resources from source code."""
        resources = []
        
        for pattern in self.resource_patterns:
            matches = re.finditer(pattern, code, re.DOTALL)
            for match in matches:
                name = match.group(1).strip()
                description = match.group(2).strip()
                
                resources.append(DocResource(
                    name=name,
                    description=description,
                    source=f"code:{file_path}",
                    confidence=0.9
                ))
        
        return resources
    
    def _extract_prompts_from_code(self, code: str, file_path: str) -> List[DocPrompt]:
        """Extract prompts from source code."""
        prompts = []
        
        for pattern in self.prompt_patterns:
            matches = re.finditer(pattern, code, re.DOTALL)
            for match in matches:
                name = match.group(1).strip()
                description = match.group(2).strip()
                
                prompts.append(DocPrompt(
                    name=name,
                    description=description,
                    source=f"code:{file_path}",
                    confidence=0.9
                ))
        
        return prompts
    
    def _deduplicate_tools(self, tools: List[DocTool]) -> List[DocTool]:
        """Remove duplicate tools, keeping highest confidence version."""
        tool_dict = {}
        for tool in tools:
            if tool.name not in tool_dict or tool.confidence > tool_dict[tool.name].confidence:
                tool_dict[tool.name] = tool
        return list(tool_dict.values())
    
    def _deduplicate_resources(self, resources: List[DocResource]) -> List[DocResource]:
        """Remove duplicate resources."""
        resource_dict = {}
        for resource in resources:
            if resource.name not in resource_dict or resource.confidence > resource_dict[resource.name].confidence:
                resource_dict[resource.name] = resource
        return list(resource_dict.values())
    
    def _deduplicate_prompts(self, prompts: List[DocPrompt]) -> List[DocPrompt]:
        """Remove duplicate prompts."""
        prompt_dict = {}
        for prompt in prompts:
            if prompt.name not in prompt_dict or prompt.confidence > prompt_dict[prompt.name].confidence:
                prompt_dict[prompt.name] = prompt
        return list(prompt_dict.values())